from django.db.models.signals import post_migrate
from django.dispatch import receiver

from apps.forms.services.bootstrap_service import BootstrapService


@receiver(post_migrate)
def bootstrap_hrms(sender, **kwargs):
    BootstrapService.bootstrap()

