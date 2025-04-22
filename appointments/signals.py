from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Appointment
from .utils import send_appointment_notification  

@receiver(post_save, sender=Appointment)
def appointment_created(sender, instance, created, **kwargs):
    """
    When a new appointment is created, send a notification
    based on the user's notification settings.
    """
    if created:
        send_appointment_notification(instance)