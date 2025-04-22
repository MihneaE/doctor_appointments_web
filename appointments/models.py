from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut


class Doctor(models.Model):
    # Core user relation
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')

    # Professional details
    specialization = models.CharField(max_length=100, null=True, blank=True)
    qualification = models.CharField(max_length=200, null=True, blank=True)
    experience = models.TextField(null=True, blank=True)
    certifications = models.TextField(null=True, blank=True)
    professional_description = models.TextField(null=True, blank=True)

    # Work details
    clinic_hospital = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    #availability = models.TextField(null=True, blank=True)
    services = models.TextField(null=True, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Contact details
    contact = models.CharField(max_length=15, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    languages_spoken = models.CharField(max_length=200, null=True, blank=True)

    # Additional details
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female')],
        null=True,
        blank=True
    )
    rating = models.FloatField(default=0.0, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    clinic_picture = models.ImageField(upload_to='clinic_pictures/', null=True, blank=True) 

    latitude = models.FloatField(null=True, blank=True, default=0.0)  # New field for latitude
    longitude = models.FloatField(null=True, blank=True, default=0.0)  # New field for longitude

    # Availability Fields
    TIME_CHOICES = [(f"{hour:02}:00", f"{hour:02}:00") for hour in range(24)]  # Dropdown for every hour

    monday_start = models.CharField(max_length=5, choices=TIME_CHOICES, null=True, blank=True)
    monday_end = models.CharField(max_length=5, choices=TIME_CHOICES, null=True, blank=True)

    tuesday_start = models.CharField(max_length=5, choices=TIME_CHOICES, null=True, blank=True)
    tuesday_end = models.CharField(max_length=5, choices=TIME_CHOICES, null=True, blank=True)

    wednesday_start = models.CharField(max_length=5, choices=TIME_CHOICES, null=True, blank=True)
    wednesday_end = models.CharField(max_length=5, choices=TIME_CHOICES, null=True, blank=True)

    thursday_start = models.CharField(max_length=5, choices=TIME_CHOICES, null=True, blank=True)
    thursday_end = models.CharField(max_length=5, choices=TIME_CHOICES, null=True, blank=True)

    friday_start = models.CharField(max_length=5, choices=TIME_CHOICES, null=True, blank=True)
    friday_end = models.CharField(max_length=5, choices=TIME_CHOICES, null=True, blank=True)


    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} - {self.specialization or 'No Specialization'}"

    def fetch_coordinates(self):
        if self.address:
            try:
                geolocator = Nominatim(user_agent="client_geocoder")
                location = geolocator.geocode(self.address, timeout=10)
                if location:
                    self.latitude = location.latitude
                    self.longitude = location.longitude
                    self.save()  # Save the updated coordinates to the database
                    return self.latitude, self.longitude
                else:
                    return None, None
            except GeocoderTimedOut:
                return None, None
        return None, None


class Client(models.Model):
    # Core user relation
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')

    # Personal details
    contact = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    latitude = models.FloatField(null=True, blank=True, default=0.0)  # New field for latitude
    longitude = models.FloatField(null=True, blank=True, default=0.0)  # New field for longitude

    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female')],
        null=True,
        blank=True
    )
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)    

    def __str__(self):
        return f"{self.user.username}'s Client Profile"

    def fetch_coordinates(self):
        if self.address:
            try:
                geolocator = Nominatim(user_agent="client_geocoder")
                location = geolocator.geocode(self.address, timeout=10)
                if location:
                    self.latitude = location.latitude
                    self.longitude = location.longitude
                    self.save()  # Save the updated coordinates to the database
                    return self.latitude, self.longitude
                else:
                    return None, None
            except GeocoderTimedOut:
                return None, None
        return None, None


class MedicalSpecialty(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class Comment(models.Model):
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name='comments')

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_comments')
    user_photo = models.ImageField(upload_to='comment_photos/', null=True, blank=True)

    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    content = models.TextField()
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"Comment by {self.user.username if self.user else 'Anonymous'} on Dr. {self.doctor.user.username}"

    class Meta:
        ordering = ['-created_at']  # Order by newest first

class Slot(models.Model):
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name='slots')
    day = models.CharField(
        max_length=10,
        choices=[
            ('Monday', 'Monday'),
            ('Tuesday', 'Tuesday'),
            ('Wednesday', 'Wednesday'),
            ('Thursday', 'Thursday'),
            ('Friday', 'Friday'),
            ('Saturday', 'Saturday'),
            ('Sunday', 'Sunday'),
        ]
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    first_week_reserved = models.BooleanField(default=False)  # Indicates reservation status for week 1
    second_week_reserved = models.BooleanField(default=False)  # Indicates reservation status for week 2

    class Meta:
        unique_together = ('doctor', 'day', 'start_time', 'end_time')  # Prevent duplicate slots
        ordering = ['day', 'start_time']  # Order by day and time

    def __str__(self):
        first_status = "Reserved" if self.first_week_reserved else "Available"
        second_status = "Reserved" if self.second_week_reserved else "Available"
        return f"{self.doctor.user.username} - {self.day} {self.start_time}-{self.end_time} (Week 1: {first_status}, Week 2: {second_status})"


APPOINTMENT_TYPE_CHOICES = (
    ('in_clinic', 'In Clinic'),
    ('online', 'Online'),
)

class Appointment(models.Model):
    # Doctor Details

    # Appointment Type: In Clinic or Online
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES, default='in_clinic')

    platform = models.CharField(max_length=50, blank=True, null=True, help_text="Platform used for online appointments (e.g., Jitsi, Zoom)")
    call_link = models.URLField(blank=True, null=True, help_text="Video call link for online appointments")
    
    doctor_fk = models.ForeignKey(
        'appointments.Doctor', 
        on_delete=models.CASCADE,
        related_name='appointments',
        null=True,
        blank=True
    )

    doctor_id = models.IntegerField()  # Reference ID of the doctor
    doctor_name = models.CharField(max_length=100)
    doctor_gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    doctor_contact = models.CharField(max_length=15)  # Phone number of the doctor
    doctor_address = models.TextField(null=True, blank=True)
    doctor_clinic = models.CharField(max_length=100)

    # General Appointment Details
    start_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.IntegerField(help_text="Duration in minutes")
    status = models.BooleanField(default=False, help_text="Indicates if the appointment is confirmed")  
    one_time_only = models.BooleanField(default=False)
    repeat_every = models.IntegerField(null=True, blank=True, help_text="Number of units to repeat")
    unit = models.CharField(
        max_length=10,
        choices=[('week', 'Week'), ('month', 'Month')],
        null=True,
        blank=True
    )
    end_date = models.DateField(null=True, blank=True)

    # Client Details

    client_fk = models.ForeignKey(
        'appointments.Client', 
        on_delete=models.CASCADE,
        related_name='appointments',
        null=True,
        blank=True
    )

    client_id = models.IntegerField() 
    client_name = models.CharField(max_length=100)
    client_gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    client_contact = models.CharField(max_length=15)  # Phone number of the client
    client_address = models.TextField(null=True, blank=True)
    client_date_of_birth = models.DateField(null=True, blank=True) 

    def __str__(self):
        return f"Appointment with Dr. {self.doctor_name} for {self.client_name} on {self.start_date}"

    class Meta:
        ordering = ['start_date', 'start_time']

    @property
    def time_status(self):
        """Dynamically calculates whether the appointment is active or finished."""
        current_time = now()
        appointment_datetime = datetime.combine(self.start_date, self.end_time)

        if appointment_datetime > current_time:
            return 'active'
        else:
            return 'finished'

    @property
    def client(self):
        return self.client_fk

    @property
    def doctor(self):
        return self.doctor_fk

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, related_name='cities', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.country.name})"

class ChatSession(models.Model):
    """
    Represents a conversation between a specific doctor and a patient (client).
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='chats')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)

    # Optionally track if it's active/archived, etc.
    # is_active = models.BooleanField(default=True)
    # Fields to track if the chat has been read by each participant.
    read_by_doctor = models.BooleanField(default=False)
    read_by_client = models.BooleanField(default=False)


    def __str__(self):
        return f"ChatSession #{self.id} (Doctor: {self.doctor}, Patient: {self.patient})"

class ChatMessage(models.Model):
    """
    Each message in a chat session.
    """
    ROLE_CHOICES = (
        ('doctor', 'Doctor'),
        ('client', 'Client'),
    )

    chat = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    sender_role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message #{self.id} in ChatSession #{self.chat.id}"

class NotificationSetting(models.Model):
    """
    Stores how a user wants to receive notifications
    and any push subscription details if applicable.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_setting'
    )

    # Notification channel toggles
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    site_notifications = models.BooleanField(default=True)  # In-app messaging

    # Fields for storing push subscription information (e.g., for web push)
    push_endpoint = models.CharField(max_length=500, blank=True, null=True)
    push_p256dh = models.CharField(max_length=200, blank=True, null=True)
    push_auth = models.CharField(max_length=200, blank=True, null=True)

    # --- NEW TEXT STYLE FIELDS ---
    font_family = models.CharField(max_length=50, default='Arial')
    font_size = models.PositiveIntegerField(default=16)
    font_weight = models.CharField(max_length=10, default='normal')  # e.g., 'normal', 'bold', 'lighter'

    # Theme fields
    theme = models.CharField(max_length=10, default='light')  # "light", "dark", or "custom"
    background_color = models.CharField(max_length=7, default='#FFFFFF')  # e.g., "#ffffff"
    text_color = models.CharField(max_length=7, default='#000000')

    def __str__(self):
        return f"NotificationSetting for {self.user.username}"

class SiteMessage(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='site_messages'
    )
    title = models.CharField(max_length=100)
    message = models.TextField()

    def __str__(self):
        return f"SiteMessage for {self.user.username} - {self.title}"