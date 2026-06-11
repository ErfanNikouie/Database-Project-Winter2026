# Generated manually for system folder menus without a bound form

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("menus", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="menu",
            name="form",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="menus",
                to="forms.form",
            ),
        ),
    ]

