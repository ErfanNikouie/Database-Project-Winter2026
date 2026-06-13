from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forms", "0003_form_field_type_lookup"),
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reportfield",
            name="form",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="report_fields",
                to="forms.form",
            ),
        ),
        migrations.AlterField(
            model_name="reportfield",
            name="form_field",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="report_fields",
                to="forms.formfield",
            ),
        ),
        migrations.AddField(
            model_name="reportfield",
            name="aggregation_type",
            field=models.CharField(
                choices=[
                    ("None", "None"),
                    ("Count", "Count"),
                    ("Sum", "Sum"),
                    ("Avg", "Avg"),
                    ("Min", "Min"),
                    ("Max", "Max"),
                ],
                default="None",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="reportfield",
            name="expression_type",
            field=models.CharField(
                choices=[
                    ("Direct", "Direct"),
                    ("Aggregate", "Aggregate"),
                    ("Latest", "Latest"),
                    ("Exists", "Exists"),
                    ("GroupedAggregate", "GroupedAggregate"),
                ],
                default="Direct",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="reportfield",
            name="filter_expression",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="reportfield",
            name="group_by_flag",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="reportfield",
            name="related_form",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="report_related_fields",
                to="forms.form",
            ),
        ),
        migrations.AddField(
            model_name="reportfield",
            name="sort_direction",
            field=models.CharField(choices=[("asc", "ASC"), ("desc", "DESC")], default="desc", max_length=4),
        ),
        migrations.AddField(
            model_name="reportfield",
            name="sort_field",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="report_sort_fields",
                to="forms.formfield",
            ),
        ),
        migrations.AddField(
            model_name="reportfield",
            name="target_field",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="report_target_fields",
                to="forms.formfield",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="reportfield",
            unique_together=set(),
        ),
    ]

