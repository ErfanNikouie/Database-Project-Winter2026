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


class ReportField(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="fields")
    form = models.ForeignKey("forms.Form", on_delete=models.PROTECT, related_name="report_fields")
    form_field = models.ForeignKey("forms.FormField", on_delete=models.PROTECT, related_name="report_fields")
    display_order = models.IntegerField(default=0)
    display_name = models.CharField(max_length=150, blank=True, default="")

    class Meta:
        db_table = "report_field"
        ordering = ["display_order", "id"]
        unique_together = ("report", "form_field")

    def __str__(self) -> str:
        display = self.display_name or self.form_field.name
        return f"{self.report.name} - {display}"

