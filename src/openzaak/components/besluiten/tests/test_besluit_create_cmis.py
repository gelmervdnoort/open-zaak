from datetime import date

from django.test import override_settings

from freezegun import freeze_time
from rest_framework import status
from vng_api_common.tests import TypeCheckMixin, reverse

from openzaak.components.catalogi.tests.factories import BesluitTypeFactory
from openzaak.components.documenten.tests.factories import (
    EnkelvoudigInformatieObjectFactory,
)
from openzaak.components.zaken.tests.factories import ZaakFactory
from openzaak.utils.tests import APICMISTestCase, JWTAuthMixin

from ..constants import VervalRedenen
from ..models import Besluit
from .factories import BesluitFactory, BesluitInformatieObjectFactory
from .utils import get_operation_url, serialise_eio


@override_settings(CMIS_ENABLED=True)
class BesluitCreateCMISTests(TypeCheckMixin, JWTAuthMixin, APICMISTestCase):

    heeft_alle_autorisaties = True

    @freeze_time("2018-09-06T12:08+0200")
    def test_us162_voeg_besluit_toe_aan_zaak(self):
        zaak = ZaakFactory.create(zaaktype__concept=False)
        zaak_url = reverse(zaak)
        besluittype = BesluitTypeFactory.create(concept=False)
        besluittype_url = reverse(besluittype)
        besluittype.zaaktypen.add(zaak.zaaktype)
        io = EnkelvoudigInformatieObjectFactory.create(
            informatieobjecttype__concept=False
        )
        io_url = reverse(io)
        self.adapter.register_uri("GET", io_url, json=serialise_eio(io, io_url))
        besluittype.informatieobjecttypen.add(io.informatieobjecttype)

        with self.subTest(part="besluit_create"):
            url = get_operation_url("besluit_create")

            response = self.client.post(
                url,
                {
                    "verantwoordelijke_organisatie": "517439943",  # RSIN
                    "identificatie": "123123",
                    "besluittype": f"http://testserver{besluittype_url}",
                    "zaak": f"http://testserver{zaak_url}",
                    "datum": "2018-09-06",
                    "toelichting": "Vergunning verleend.",
                    "ingangsdatum": "2018-10-01",
                    "vervaldatum": "2018-11-01",
                    "vervalreden": VervalRedenen.tijdelijk,
                },
            )

            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, response.data
            )
            self.assertResponseTypes(
                response.data,
                (
                    ("url", str),
                    ("identificatie", str),
                    ("verantwoordelijke_organisatie", str),
                    ("besluittype", str),
                    ("zaak", str),
                    ("datum", str),
                    ("toelichting", str),
                    ("bestuursorgaan", str),
                    ("ingangsdatum", str),
                    ("vervaldatum", str),
                    ("vervalreden", str),
                    ("publicatiedatum", type(None)),
                    ("verzenddatum", type(None)),
                    ("uiterlijke_reactiedatum", type(None)),
                ),
            )

            self.assertEqual(Besluit.objects.count(), 1)

            besluit = Besluit.objects.get()
            self.assertEqual(besluit.verantwoordelijke_organisatie, "517439943")
            self.assertEqual(besluit.besluittype, besluittype)
            self.assertEqual(besluit.zaak, zaak)
            self.assertEqual(besluit.datum, date(2018, 9, 6))
            self.assertEqual(besluit.toelichting, "Vergunning verleend.")
            self.assertEqual(besluit.ingangsdatum, date(2018, 10, 1))
            self.assertEqual(besluit.vervaldatum, date(2018, 11, 1))
            self.assertEqual(besluit.vervalreden, VervalRedenen.tijdelijk)

        with self.subTest(part="besluitinformatieobject_create"):
            url = get_operation_url("besluitinformatieobject_create")

            response = self.client.post(
                url,
                {
                    "besluit": reverse(besluit),
                    "informatieobject": f"http://testserver{io_url}",
                },
            )

            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, response.data
            )
            self.assertResponseTypes(
                response.data, (("url", str), ("informatieobject", str))
            )

            self.assertEqual(besluit.besluitinformatieobject_set.count(), 1)
            self.assertEqual(
                besluit.besluitinformatieobject_set.get().informatieobject.uuid, io.uuid
            )

    def test_opvragen_informatieobjecten_besluit(self):
        besluit1, besluit2 = BesluitFactory.create_batch(2)

        besluit1_uri = reverse(besluit1)
        besluit2_uri = reverse(besluit2)

        for counter in range(3):
            eio = EnkelvoudigInformatieObjectFactory.create()
            eio_url = eio.get_url()
            self.adapter.register_uri("GET", eio_url, json=serialise_eio(eio, eio_url))
            BesluitInformatieObjectFactory.create(
                besluit=besluit1, informatieobject=eio_url
            )

        for counter in range(2):
            eio = EnkelvoudigInformatieObjectFactory.create()
            eio_url = eio.get_url()
            self.adapter.register_uri("GET", eio_url, json=serialise_eio(eio, eio_url))
            BesluitInformatieObjectFactory.create(
                besluit=besluit2, informatieobject=eio_url
            )

        base_uri = get_operation_url("besluitinformatieobject_list")

        response1 = self.client.get(
            base_uri,
            {"besluit": f"http://openzaak.nl{besluit1_uri}"},
            HTTP_HOST="openzaak.nl",
        )
        self.assertEqual(len(response1.data), 3)

        response2 = self.client.get(
            base_uri,
            {"besluit": f"http://openzaak.nl{besluit2_uri}"},
            HTTP_HOST="openzaak.nl",
        )
        self.assertEqual(len(response2.data), 2)

    def test_besluit_create_fail_besluittype_max_length(self):
        zaak = ZaakFactory.create(zaaktype__concept=False)
        zaak_url = reverse(zaak)

        url = get_operation_url("besluit_create")

        response = self.client.post(
            url,
            {
                "verantwoordelijke_organisatie": "517439943",  # RSIN
                "identificatie": "123123",
                "besluittype": f"http://testserver/{'x'*1000}",
                "zaak": f"http://testserver{zaak_url}",
                "datum": "2018-09-06",
                "toelichting": "Vergunning verleend.",
                "ingangsdatum": "2018-10-01",
                "vervaldatum": "2018-11-01",
                "vervalreden": VervalRedenen.tijdelijk,
            },
        )

        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.data
        )

        max_length_errors = [
            e
            for e in response.data["invalid_params"]
            if e["name"] == "besluittype" and e["code"] == "max_length"
        ]
        self.assertEqual(len(max_length_errors), 1)
