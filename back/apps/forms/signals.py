from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.forms.models import Form, FormField
from apps.forms.services.schema_service import SchemaService


@receiver(post_save, sender=Form)
def on_form_saved(sender, instance: Form, created: bool, **kwargs):
    if created and not instance.is_system:
        SchemaService.create_dynamic_table(instance)


@receiver(pre_save, sender=FormField)
def on_form_field_pre_save(sender, instance: FormField, **kwargs):
    if instance.pk:
        instance._previous_state = FormField.objects.filter(pk=instance.pk).first()  # noqa: SLF001


@receiver(post_save, sender=FormField)
def on_form_field_saved(sender, instance: FormField, created: bool, **kwargs):
    if instance.form.is_system:
        return
    if created:
        SchemaService.add_field(instance.form, instance)
        return
    previous = getattr(instance, "_previous_state", None)
    if isinstance(previous, FormField):
        SchemaService.update_field(instance.form, previous, instance)


@receiver(post_delete, sender=FormField)
def on_form_field_deleted(sender, instance: FormField, **kwargs):
    if not instance.form.is_system:
        SchemaService.drop_field(instance.form, instance.name)


@receiver(post_delete, sender=Form)
def on_form_deleted(sender, instance: Form, **kwargs):
    if not instance.is_system:
        SchemaService.drop_dynamic_table(instance)


