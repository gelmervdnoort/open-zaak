# Generated by Django 2.2.4 on 2019-12-20 14:39

from django.db import migrations, models
import django.db.models.deletion
import django_loose_fk.fields


class Migration(migrations.Migration):

    dependencies = [
        ("zaken", "0023_auto_20191220_1430"),
    ]

    operations = [
        migrations.AddField(
            model_name="zaakeigenschap",
            name="eigenschap",
            field=django_loose_fk.fields.FkOrURLField(
                blank=False,
                fk_field="_eigenschap",
                null=False,
                url_field="_eigenschap_url",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="zaakeigenschap",
            name="_eigenschap",
            field=models.ForeignKey(
                blank=True,
                help_text="URL-referentie naar het RESULTAATTYPE (in de Catalogi API).",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="catalogi.Eigenschap",
            ),
        ),
        migrations.AddConstraint(
            model_name="zaakeigenschap",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        models.Q(_eigenschap__isnull=True, _negated=True),
                        ("_eigenschap_url", ""),
                    ),
                    models.Q(
                        ("_eigenschap__isnull", True),
                        models.Q(_eigenschap_url="", _negated=True),
                    ),
                    _connector="OR",
                ),
                name="_eigenschap_or__eigenschap_url_filled",
            ),
        ),
    ]
