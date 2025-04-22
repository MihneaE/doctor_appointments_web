from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime

# For optional SMS using Twilio (install twilio package):
# pip install twilio
from twilio.rest import Client as TwilioClient

# For optional push notifications, you might use pywebpush or FCM. We'll just show a placeholder.
# from pywebpush import webpush, WebPushException  # or your chosen push library

from .models import NotificationSetting, Appointment, SiteMessage

serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

def send_appointment_notification(appointment: Appointment):
    """Send a notification about the newly created appointment based on user preferences."""
    client_obj = appointment.client  # The 'Client' instance
    doctor_obj = appointment.doctor
    user = client_obj.user  # The Django 'User' instance
    notification_setting, created = NotificationSetting.objects.get_or_create(user=user)

    # Build a message subject & body
    subject = "Your Appointment is Confirmed!"
    body = (
        f"Hello {user.username},\n\n"
        f"Your appointment with Dr. {appointment.doctor_name} on "
        f"{appointment.start_date.strftime('%Y-%m-%d %H:%M')} has been booked.\n\n"
        "Thank you for using our service!\n"
    )

    # 1. Send Email
    if notification_setting.email_notifications and user.email:

        # Combine the date and time fields into datetime objects
        start_datetime = datetime.combine(appointment.start_date, appointment.start_time)
        end_datetime = datetime.combine(appointment.start_date, appointment.end_time)

        # Calculate the difference in minutes
        duration_minutes = int((end_datetime - start_datetime).total_seconds() // 60)

        if appointment.appointment_type == 'in_clinic':
                token = serializer.dumps(appointment.id, salt="appointment-confirmation")
                confirmation_link = f'{settings.RESET_LINK_BASE_URL}/confirm-appointment-by-link/{token}/'

                send_mail(
                    subject='Appointment Confirmation',
                    message=(
                        f"Dear {client_obj.user.first_name} {client_obj.user.last_name},\n\n"
                        f"Your appointment details are as follows: In clinic Appointment\n"
                        f"Doctor: Dr. {doctor_obj.user.first_name} {doctor_obj.user.last_name}\n"
                        f"Clinic: {doctor_obj.clinic_hospital}\n"
                        f"Address: {doctor_obj.address}\n"
                        f"Date: {appointment.start_date}\n"
                        f"Time: {appointment.start_time} - {appointment.end_time}\n"
                        f"Duration: {duration_minutes} minutes\n\n"
                        f"To confirm your appointment, please click the following link:\n"
                        f"{confirmation_link}\n\n"
                        f"Thank you,\n"
                        f"Your Clinic Team"
                    ),
                    from_email='mihnea.encean2@gmail.com',
                    recipient_list=['mihnea.encean1@gmail.com'],
                    fail_silently=False,
                )
        
        if appointment.appointment_type == 'online':
            token = serializer.dumps(appointment.id, salt="appointment-confirmation")
            confirmation_link = f'{settings.RESET_LINK_BASE_URL}/confirm-appointment-by-link/{token}/'

            send_mail(
                    subject='Appointment Confirmation',
                    message=(
                        f"Dear {client_obj.user.first_name} {client_obj.user.last_name},\n\n"
                        f"Your appointment details are as follows: Online Appointment\n"
                        f"Doctor: Dr. {doctor_obj.user.first_name} {doctor_obj.user.last_name}\n"
                        f"Date: {appointment.start_date}\n"
                        f"Time: {appointment.start_time} - {appointment.end_time}\n"
                        f"Duration: {duration_minutes} minutes\n\n"
                        f"To confirm your appointment, please click the following link:\n"
                        f"{confirmation_link}\n\n"
                        f"Thank you,\n"
                        f"Your Clinic Team"
                    ),
                    from_email='mihnea.encean2@gmail.com',
                    recipient_list=['mihnea.encean1@gmail.com'],
                    fail_silently=False,
                )

    '''
    # 2. Send SMS (example using Twilio)
    if notification_setting.sms_notifications:
        # Make sure to store your Twilio credentials in settings or environment variables
        phone_number = client_obj.contact  # The CharField in Client
        if phone_number:
            twilio_client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            twilio_client.messages.create(
                body="SMS text here ...",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
    '''

    # 3. Site (In-App) Notification
    if notification_setting.site_notifications:
        # This is where you might create an "InAppNotification" object or similar.
        # We'll just illustrate with a pseudo-model "SiteMessage."
        # You'd show these messages in the user's dashboard or notifications center.
        SiteMessage.objects.create(
            user=user,
            title="Appointment Confirmation",
            message=body
        )

    # 4. Push Notification (web or mobile)
    if notification_setting.push_notifications and notification_setting.push_endpoint:
        # Example placeholder using a pseudo method "send_push" 
        # to illustrate. If you implement web push or FCM,
        # you'd call those APIs here.
        push_message = {
            "title": "Appointment Confirmed",
            "body": f"Appointment with Dr. {appointment.doctor_name} on {appointment.start_date}"
        }
        send_push(notification_setting, push_message)

def send_push(notification_setting, message):
    """
    Placeholder for sending web push or mobile push notifications
    using stored subscription data or device tokens.
    """
    # e.g., using pywebpush
    # webpush(
    #     subscription_info={
    #         "endpoint": notification_setting.push_endpoint,
    #         "keys": {
    #             "p256dh": notification_setting.push_p256dh,
    #             "auth": notification_setting.push_auth
    #         }
    #     },
    #     data=json.dumps(message),
    #     vapid_private_key=settings.WEBPUSH_PRIVATE_KEY,
    #     vapid_claims={"sub": "mailto:admin@example.com"}
    # )
    pass