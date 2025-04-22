from django.contrib import admin
from .models import MedicalSpecialty
from .models import Doctor
from .models import Client
from .models import Comment
from .models import Slot
from .models import Appointment
from .models import Country, City
from modeltranslation.admin import TranslationAdmin
from .models import ChatSession, ChatMessage, NotificationSetting, SiteMessage

admin.site.register(MedicalSpecialty)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'clinic_hospital', 'rating', 'gender')
    list_filter = ('specialization', 'gender')
    search_fields = ('user__username', 'specialization', 'clinic_hospital')
    fieldsets = (
        (None, {'fields': ('user', 'specialization', 'qualification', 'experience', 'certifications', 'professional_description')}),
        ('Work Details', {'fields': ('clinic_hospital', 'address', 'services', 'consultation_fee')}),
        ('Contact Details', {'fields': ('contact', 'website', 'languages_spoken')}),
        ('Availability', {
            'fields': (
                ('monday_start', 'monday_end'),
                ('tuesday_start', 'tuesday_end'),
                ('wednesday_start', 'wednesday_end'),
                ('thursday_start', 'thursday_end'),
                ('friday_start', 'friday_end'),
            )
        }),
        ('Additional Details', {'fields': ('date_of_birth', 'gender', 'rating', 'profile_picture', 'clinic_picture')}),
    )

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('user', 'contact', 'gender', 'date_of_birth')
    search_fields = ('user__username', 'contact', 'address')
    list_filter = ('gender',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'user', 'rating', 'created_at')
    search_fields = ('doctor__user__username', 'user__username', 'content')
    list_filter = ('rating', 'created_at')

@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day', 'start_time', 'end_time', 'first_week_reserved', 'second_week_reserved')
    list_filter = ('day', 'first_week_reserved', 'second_week_reserved', 'doctor')
    search_fields = ('doctor__user__username',)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'doctor_name', 
        'doctor_clinic', 
        'client_name', 
        'client_date_of_birth',  # Added client date of birth
        'start_date', 
        'start_time', 
        'end_time', 
        'duration', 
        'one_time_only', 
        'status'  # Added status
    )
    list_filter = ('doctor_clinic', 'one_time_only', 'start_date', 'status')  # Added status to filters
    search_fields = ('doctor_name', 'client_name', 'doctor_clinic', 'client_contact')
    ordering = ('start_date', 'start_time')


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    search_fields = ('name', 'country__name')

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor', 'client', 'created_at', 'read_by_doctor', 'read_by_client')
    list_filter = ('read_by_doctor', 'read_by_client', 'created_at')
    search_fields = ('doctor__user__username', 'client__user__username')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'sender', 'sender_role', 'created_at')
    list_filter = ('sender_role', 'created_at')
    search_fields = ('sender__username', 'content')

@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notifications', 'sms_notifications', 'push_notifications', 'site_notifications')
    list_filter = ('email_notifications', 'sms_notifications', 'push_notifications', 'site_notifications')
    search_fields = ('user__username',)

@admin.register(SiteMessage)
class SiteMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title')
    search_fields = ('user__username', 'title')


admin.site.site_header = "Doctor Appointments Admin"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Welcome to the Admin Dashboard"

