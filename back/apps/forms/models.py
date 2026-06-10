from django.db import models
from django.utils import timezone


class Form(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    table_name = models.CharField(max_length=100, unique=True)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "form"

    def __str__(self) -> str:
        return self.name


class FormFieldType(models.TextChoices):
    INTEGER = "Integer", "Integer"
    DOUBLE = "Double", "Double"
    DECIMAL = "Decimal", "Decimal"
    STRING = "String", "String"
    TEXT = "Text", "Text"
    DATE = "Date", "Date"
    DATETIME = "DateTime", "DateTime"
    BOOLEAN = "Boolean", "Boolean"
    LOOKUP = "Lookup", "Lookup"
    FOREIGN_KEY = "ForeignKey", "ForeignKey"


class FormField(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="fields")
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=FormFieldType.choices)
    mandatory = models.BooleanField(default=False)
    unique = models.BooleanField(default=False)
    lookup = models.ForeignKey("lookups.Lookup", null=True, blank=True, on_delete=models.SET_NULL)
    foreign_key_table = models.CharField(max_length=100, blank=True, default="")
    foreign_key_field = models.CharField(max_length=100, blank=True, default="id")
    default_value = models.CharField(max_length=255, blank=True, default="")
    sort_order = models.IntegerField(default=0)
    is_system = models.BooleanField(default=False)

    class Meta:
        db_table = "form_field"
        unique_together = ("form", "name")
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"{self.form.table_name}.{self.name}"

