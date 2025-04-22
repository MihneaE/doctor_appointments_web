from django.urls import path, include
from . import views

from django.contrib.auth import views as auth_views

from django.contrib.auth.views import PasswordResetConfirmView

from rest_framework.routers import DefaultRouter
from .views import MedicalSpecialtyViewSet

from django.views.i18n import set_language

router = DefaultRouter()
router.register('medical-specialities', MedicalSpecialtyViewSet, basename='medical-specialty')

urlpatterns = [
    path('', views.home, name='home'), 
    path('about/', views.about, name='about'),
    path('doctor_appointments/', views.doctor_appointments, name='doctor_appointments'), 
    path('client_appointments/', views.client_appointments, name='client_appointments'), 
    path('create-account/', views.create_account, name='create_account'),  
    path('login/', views.login_view, name='login'),  
    path('register-doctor/', views.register_doctor, name='register_doctor'),  
    path('register-client/', views.register_client, name='register_client'), 
    path('search/', views.search_results, name='search_results'),
    path('subscription/', views.subscription, name='subscription'),
    path('message_chat/', views.message_chat, name='message_chat'),
    path('contact/', views.contact, name='contact'),
    path('client_profile/', views.client_profile, name='client_profile'),
    path('doctor_profile/', views.doctor_profile, name='doctor_profile'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('plus_payment/', views.plus_payment, name='plus_payment'),
    path('normal_payment/', views.normal_payment, name='normal_payment'),
    path('free_payment/', views.free_payment, name='free_payment'),

    path('send-reset-email-client/', views.send_reset_email_client, name='send_reset_email_client'),
    path('send-reset-email-doctor/', views.send_reset_email_doctor, name='send_reset_email_doctor'),
    path('send-reset-email-general/', views.send_reset_email_general, name='send_reset_email_general'),
    path('reset-password-by-link/<uidb64>/<token>/', views.reset_password_view, name='reset_password'),
    path('confirm-appointment-by-link/<str:token>/', views.confirm_appointment, name='confirm_appointment'),

    path('logout/', views.custom_logout, name='logout'),
    path('update-photo/', views.update_profile_picture, name='update_photo'),

    path('specialty/<str:specialty_name>/', views.specialty_details, name='specialty_details'),
    path('book_now/<str:country_name>/<str:city_name>/<str:specialty_name>/', views.book_now, name='book_now'),

    path('update-client-profile/', views.update_client_profile, name='update_client_profile'),
    path('update-doctor-profile-proffessional/', views.update_doctor_profile_proffessional, name='update_doctor_profile_proffessional'),
    path('update-doctor-profile-work/', views.update_doctor_profile_work, name='update_doctor_profile_work'),
    path('update-doctor-profile-details/', views.update_doctor_profile_details, name='update_doctor_profile_details'),
    path('update-doctor-profile-additional/', views.update_doctor_profile_additional, name='update_doctor_profile_additional'),
    path('update-doctor-profile-availability/', views.update_doctor_profile_availability, name='update_doctor_profile_availability'),
    path('upload-clinic-photo/', views.upload_clinic_photo, name='upload_clinic_photo'),
    path('generate-slots/', views.generate_and_save_slots, name='generate_slots'),
    path('get-slots/', views.get_slots, name='get_slots'),
    path('delete-all-slots/', views.delete_all_slots, name='delete_all_slots'),
    path('delete-slot/<int:slot_id>/', views.delete_slot, name='delete_slot'),
    path('check-slots/', views.check_slots, name='check_slots'),
    path('add-manual-slot/', views.add_manual_slot, name='add_manual_slot'),
    path('view_doctor_profile_by_cli/<str:doctor_username>/fetch_slots/', views.fetch_slots_for_two_weeks, name='fetch_slots'),

    path('fetch_slots_by_id/<int:doctor_id>/', views.fetch_slots_for_two_weeks_by_id, name='fetch_slots_by_id'),

    #path('check_slot_availability/', views.check_slot_availability, name='check_slot_availability'),
    path('book_appointment/', views.book_appointment, name='book_appointment'),

    path('view_doctor_profile_by_cli/<str:username>/', views.view_doctor_profile_by_cli, name='view_doctor_profile_by_cli'),
    path('view_doctor_profile_by_cli/<str:doctor_username>/add_comment/', views.add_comment, name='add_comment'),
    path('delete_comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),

    path('send_contact_site_email/', views.send_contact_site_email, name='send_contact_site_email'),

    path('api/v1/', include(router.urls)),

    path("test_celery/", views.exemple_celery_function_process_data_view, name="test_celery"),

    path("process-payment-normal/", views.process_payment_normal, name="process_payment_normal"),
    path("process-payment-plus/", views.process_payment_plus, name="process_payment_plus"),

    path('i18n/setlang/', set_language, name='set_language'),

    path('chat_detail/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('start_new_chat/', views.start_new_chat, name='start_new_chat'),
    path('filter_chats/', views.filter_chats, name='filter_chats'),
    path('check_new_messages/<int:chat_id>/', views.check_new_messages, name='check_new_messages'),
    path('chat_detail_from_doctor_profile/<str:username>/', views.chat_detail_from_doctor_profile, name='chat_detail_from_doctor_profile'),

    path('settings/', views.app_settings, name='settings'),
    
    # Include allauth's other routes (so that callbacks etc. still work)
    path("accounts/", include("allauth.urls")),
]