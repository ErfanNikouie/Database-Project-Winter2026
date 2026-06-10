from django.db import models


class Lookup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "lookup"

    def __str__(self) -> str:
        return self.name


class LookupValue(models.Model):
    lookup = models.ForeignKey(Lookup, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=255)

    class Meta:
        db_table = "lookup_value"
        ordering = ["value"]
        unique_together = ("lookup", "value")

    def __str__(self) -> str:
        return f"{self.lookup.name}: {self.value}"

