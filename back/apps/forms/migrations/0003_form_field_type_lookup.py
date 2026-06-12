from django.db import migrations


FIELD_TYPE_VALUES = [
    "Integer",
    "Double",
    "Decimal",
    "String",
    "Text",
    "Date",
    "DateTime",
    "Boolean",
    "Lookup",
    "ForeignKey",
]


def _forward(apps, schema_editor):
    Form = apps.get_model("forms", "Form")
    FormField = apps.get_model("forms", "FormField")
    Lookup = apps.get_model("lookups", "Lookup")
    LookupValue = apps.get_model("lookups", "LookupValue")

    lookup, _ = Lookup.objects.get_or_create(
        name="FieldType",
        defaults={"description": "Supported runtime field types"},
    )
    for value in FIELD_TYPE_VALUES:
        LookupValue.objects.get_or_create(lookup=lookup, value=value)

    form = Form.objects.filter(table_name="form_field").first()
    if not form:
        return

    FormField.objects.filter(form=form, name="type").update(type="Lookup", lookup_id=lookup.id)


def _backward(apps, schema_editor):
    Form = apps.get_model("forms", "Form")
    FormField = apps.get_model("forms", "FormField")

    form = Form.objects.filter(table_name="form_field").first()
    if not form:
        return

    FormField.objects.filter(form=form, name="type").update(type="String", lookup_id=None)


class Migration(migrations.Migration):
    dependencies = [
        ("forms", "0002_fix_user_user_group_fk_metadata"),
        ("lookups", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(_forward, _backward),
    ]

