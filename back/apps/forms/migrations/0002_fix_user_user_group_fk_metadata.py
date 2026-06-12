from django.db import migrations


def _forward(apps, schema_editor):
    Form = apps.get_model("forms", "Form")
    FormField = apps.get_model("forms", "FormField")

    form = Form.objects.filter(table_name="user_user_group").first()
    if not form:
        return

    FormField.objects.filter(form=form, name="user_id").update(
        type="ForeignKey",
        foreign_key_table="user",
        foreign_key_field="id",
    )
    FormField.objects.filter(form=form, name="usergroup_id").update(
        type="ForeignKey",
        foreign_key_table="user_group",
        foreign_key_field="id",
    )


def _backward(apps, schema_editor):
    Form = apps.get_model("forms", "Form")
    FormField = apps.get_model("forms", "FormField")

    form = Form.objects.filter(table_name="user_user_group").first()
    if not form:
        return

    FormField.objects.filter(form=form, name="user_id").update(
        type="Integer",
        foreign_key_table="",
        foreign_key_field="id",
    )
    FormField.objects.filter(form=form, name="usergroup_id").update(
        type="Integer",
        foreign_key_table="",
        foreign_key_field="id",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("forms", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(_forward, _backward),
    ]

