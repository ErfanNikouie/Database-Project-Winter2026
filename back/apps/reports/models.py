from __future__ import annotations

from django.db import models


class Report(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, default="")
    base_form = models.ForeignKey("forms.Form", on_delete=models.PROTECT, related_name="reports")

    class Meta:
        db_table = "report"
        ordering = ["name", "id"]

    def __str__(self) -> str:
        return self.name


class ReportExpressionType(models.TextChoices):
    DIRECT = "Direct", "Direct"
    AGGREGATE = "Aggregate", "Aggregate"
    LATEST = "Latest", "Latest"
    EXISTS = "Exists", "Exists"
    GROUPED_AGGREGATE = "GroupedAggregate", "GroupedAggregate"


class ReportAggregationType(models.TextChoices):
    NONE = "None", "None"
    COUNT = "Count", "Count"
    SUM = "Sum", "Sum"
    AVG = "Avg", "Avg"
    MIN = "Min", "Min"
    MAX = "Max", "Max"


class ReportSortDirection(models.TextChoices):
    ASC = "asc", "ASC"
    DESC = "desc", "DESC"


class ReportField(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="fields")
    form = models.ForeignKey("forms.Form", on_delete=models.PROTECT, related_name="report_fields", null=True, blank=True)
    form_field = models.ForeignKey(
        "forms.FormField",
        on_delete=models.PROTECT,
        related_name="report_fields",
        null=True,
        blank=True,
    )
    display_order = models.IntegerField(default=0)
    display_name = models.CharField(max_length=150, blank=True, default="")

    expression_type = models.CharField(
        max_length=32,
        choices=ReportExpressionType.choices,
        default=ReportExpressionType.DIRECT,
    )
    aggregation_type = models.CharField(
        max_length=16,
        choices=ReportAggregationType.choices,
        default=ReportAggregationType.NONE,
    )
    target_field = models.ForeignKey(
        "forms.FormField",
        on_delete=models.PROTECT,
        related_name="report_target_fields",
        null=True,
        blank=True,
    )
    related_form = models.ForeignKey(
        "forms.Form",
        on_delete=models.PROTECT,
        related_name="report_related_fields",
        null=True,
        blank=True,
    )
    sort_field = models.ForeignKey(
        "forms.FormField",
        on_delete=models.PROTECT,
        related_name="report_sort_fields",
        null=True,
        blank=True,
    )
    sort_direction = models.CharField(
        max_length=4,
        choices=ReportSortDirection.choices,
        default=ReportSortDirection.DESC,
    )
    filter_expression = models.TextField(blank=True, default="")
    group_by_flag = models.BooleanField(default=False)

    class Meta:
        db_table = "report_field"
        ordering = ["display_order", "id"]

    def __str__(self) -> str:
        if self.display_name:
            display = self.display_name
        elif self.form_field:
            display = self.form_field.name
        else:
            display = f"field_{self.id}"
        return f"{self.report.name} - {display}"

