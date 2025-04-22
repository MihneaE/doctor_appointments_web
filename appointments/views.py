from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.decorators import login_required
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings
from django.contrib.auth import logout
from .forms import ProfilePictureForm
from .models import Doctor
from .models import MedicalSpecialty
from .models import Client
from .models import Comment
from .models import Slot
from .models import Appointment
from .models import Country
from .models import City
from .models import ChatSession
from .models import ChatMessage
from .models import NotificationSetting
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest
from datetime import datetime, timedelta
from django.http import JsonResponse
import json
import pdb
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import calendar
from itsdangerous import URLSafeTimedSerializer
from django.utils.timezone import now
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet
from .serializers import MedicalSpecialtySerializer
from .celery_tasks import process_data
from django.http import HttpResponseNotAllowed
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import math
import stripe
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import get_language
from django.db.models import F
from django.db.models import Max
import uuid

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView, OAuth2CallbackView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

stripe.api_key = settings.STRIPE_SECRET_KEY

class MedicalSpecialtyViewSet(ModelViewSet):
    queryset = MedicalSpecialty.objects.all()
    serializer_class = MedicalSpecialtySerializer


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the Haversine distance between two points on the Earth.
    :param lat1: Latitude of the first point (in degrees)
    :param lon1: Longitude of the first point (in degrees)
    :param lat2: Latitude of the second point (in degrees)
    :param lon2: Longitude of the second point (in degrees)
    :return: Distance in kilometers
    """
    # Radius of Earth in kilometers
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Differences in latitudes and longitudes
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    # Haversine formula
    a = math.sin(delta_lat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance in kilometers
    distance = R * c
    return distance

def exemple_celery_function_process_data_view(request):
    if request.method == "POST":
        task_result = process_data.delay("Hello World!")
        return JsonResponse({"message": "Task has been queued", "task_id": task_result.id})
    
    return render(request, 'appointments/test_celery.html')

def get_custom_page_range(current, total):
    """
    Returns a list of page numbers and ellipsis markers to display in the pagination bar.
    
    Rules:
      - If total pages is small (<=7), show all pages.
      - Otherwise:
          • If current page is near the beginning (<=3), show pages 1,2,3 (and if current==3 also include 4),
            then an ellipsis, then the last three pages.
          • If current page is near the end (>= total-2), show the first page, then an ellipsis,
            then pages total-3, total-2, total-1, and total.
          • Otherwise (current in the middle), show the first page, an ellipsis, a sliding window
            of [current-1, current, current+1], another ellipsis, and then the last three pages.
      - Finally, when outputting the list, if there's a gap of more than 1 between two numbers, insert an ellipsis.
    """
   
    if total <= 7:
        return list(range(1, total + 1))
    
    pages = set()
    
    if current <= 3:
        pages.update(range(1, 4))
        if current == 3:
            pages.add(4)
    else:
        pages.add(1)
    
    if current > 3 and current < total - 2:
        pages.update([current - 1, current, current + 1])

    if current >= total - 2:
        pages.update(range(total - 3, total + 1))
    else:
        pages.update(range(total - 2, total + 1))

    sorted_pages = sorted(pages)

    final = []
    prev = None
    for page in sorted_pages:
        if prev is not None and page - prev > 1:
            final.append("...")
        final.append(page)
        prev = page

    return final


@csrf_exempt
def process_payment_normal(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Create a PaymentIntent
            payment_intent = stripe.PaymentIntent.create(
                amount=199,         # 1.99 USD in smallest currency unit
                currency="usd",
                payment_method=data["payment_method_id"],
                confirmation_method="automatic",  # Automatic confirmation
                confirm=True,  # Automatically confirm
                return_url="http://127.0.0.1:8000/normal_payment/",
            )

            if payment_intent.status == "requires_action":
                return JsonResponse({
                    "requires_action": True,
                    "client_secret": payment_intent.client_secret
                })

            return JsonResponse({"success": True, "payment_intent_status": payment_intent.status})
        except stripe.error.CardError as e:
            return JsonResponse({"error": str(e)})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return JsonResponse({"error": "Something went wrong. Please try again."})

    return JsonResponse({"error": "Invalid request method."})

@csrf_exempt
def process_payment_plus(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Create a PaymentIntent
            payment_intent = stripe.PaymentIntent.create(
                amount=499,         # 4.99 USD in smallest currency unit
                currency="usd",
                payment_method=data["payment_method_id"],
                confirmation_method="automatic",  # Automatic confirmation
                confirm=True,  # Automatically confirm
                return_url="http://127.0.0.1:8000/plus_payment/",
            )

            if payment_intent.status == "requires_action":
                return JsonResponse({
                    "requires_action": True,
                    "client_secret": payment_intent.client_secret
                })

            return JsonResponse({"success": True, "payment_intent_status": payment_intent.status})
        except stripe.error.CardError as e:
            return JsonResponse({"error": str(e)})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return JsonResponse({"error": "Something went wrong. Please try again."})

    return JsonResponse({"error": "Invalid request method."})

def home(request):
    payment_intent = stripe.PaymentIntent.retrieve("pi_3QmyhrKKSSs4op9c00yHZjl2")
    print(payment_intent.status)

    query = request.GET.get('q')

    if query:
        medical_specialties = MedicalSpecialty.objects.filter(name__icontains=query)
    else:
        medical_specialties = MedicalSpecialty.objects.all()

    countrys = Country.objects.all()
    citys = City.objects.all()

    # Convert to a list of dicts
    country_list = [{"id": c.id, "name": c.name} for c in countrys]
    city_list = [{"id": ct.id, "name": ct.name, "country": ct.country_id} for ct in citys]
    spec_list = [{"id": s.id, "name": s.name} for s in medical_specialties]

    total_specialties = MedicalSpecialty.objects.count()
    total_doctors = Doctor.objects.count()
    total_appointments = Appointment.objects.count()
    total_users = User.objects.count()

    current_messages = []
    old_messages = []
    if request.user.is_authenticated:
        two_weeks_ago = timezone.now() - timedelta(weeks=2)
        # Determine the role of the user and get their chat sessions.
        if hasattr(request.user, 'doctor_profile'):
            chats = ChatSession.objects.filter(doctor=request.user.doctor_profile).annotate(
                last_msg_time=Max('messages__created_at')
            )
            for chat in chats:
                last_msg = chat.messages.order_by('-created_at').first()
                if last_msg:
                    data = {
                        'chat_id': chat.id,
                        'partner_name': chat.client.user.username,
                        'partner_photo': chat.client.profile_picture,  # Assuming an ImageField.
                        'last_message': last_msg.content,
                        'last_message_time': last_msg.created_at,
                    }
                    if last_msg.created_at >= two_weeks_ago:
                        current_messages.append(data)
                    else:
                        old_messages.append(data)
        elif hasattr(request.user, 'client_profile'):
            chats = ChatSession.objects.filter(client=request.user.client_profile).annotate(
                last_msg_time=Max('messages__created_at')
            )
            for chat in chats:
                last_msg = chat.messages.order_by('-created_at').first()
                if last_msg:
                    data = {
                        'chat_id': chat.id,
                        'partner_name': chat.doctor.user.username,
                        'partner_photo': chat.doctor.profile_picture,
                        'last_message': last_msg.content,
                        'last_message_time': last_msg.created_at,
                    }
                    if last_msg.created_at >= two_weeks_ago:
                        current_messages.append(data)
                    else:
                        old_messages.append(data)


    return render(request, 'appointments/home.html', {
        'medical_specialties': medical_specialties,
        "country_json": json.dumps(country_list),
        "city_json": json.dumps(city_list),
        "spec_json": json.dumps(spec_list),
        'total_specialties': total_specialties,
        'total_doctors': total_doctors,
        'total_appointments': total_appointments,
        'total_users': total_users,
        'current_messages': current_messages,
        'old_messages': old_messages,
    }, )

def specialty_details(request, specialty_name):
    query = request.GET.get('q')

    doctors = Doctor.objects.filter(specialization__iexact=specialty_name)

    if query:
        doctors = doctors.filter(user__username__icontains=query)

    gender = request.GET.get('gender')
    if gender in ['male', 'female']:
        doctors = doctors.filter(gender__iexact=gender)

    experience = request.GET.get('experience')

    if experience:
        try:
            experience = int(experience)
            doctors = doctors.filter(experience__gte=experience)
        except ValueError:
            pass

    fee = request.GET.get('fee')
    if fee == 'low':
        doctors = doctors.filter(consultation_fee__lt=500)
    elif fee == 'medium':
        doctors = doctors.filter(consultation_fee__gte=500, consultation_fee__lte=1000)
    elif fee == 'high':
        doctors = doctors.filter(consultation_fee__gt=1000)

    sort = request.GET.get('sort')
    if sort == 'fee-low':
        doctors = doctors.order_by('consultation_fee')
    elif sort == 'fee-high':
        doctors = doctors.order_by('-consultation_fee')

    try:
        client = request.user.client_profile
        client_lat = client.latitude
        client_lon = client.longitude
    except AttributeError:
        return render(request, 'appointments/doctors_page.html', {
            'specialty_name': specialty_name,
            'doctors': [],
            'error': 'Client location not available.'
        })

    if client_lat is not None and client_lon is not None:
        for doctor in doctors:
            if doctor.latitude is not None and doctor.longitude is not None:
                doctor.distance = haversine_distance(client_lat, client_lon, doctor.latitude, doctor.longitude)
            else:
                doctor.distance = None
    else:
        for doctor in doctors:
            doctor.distance = None

    if sort == 'distance':
        doctors = sorted(doctors, key=lambda x: x.distance if x.distance is not None else float('inf'))

    for doctor in doctors:
        print(str(doctor.latitude) + ' ' + str(doctor.longitude) + ' ' + str(doctor.distance))


    return render(request, 'appointments/doctors_page.html', {'specialty_name': specialty_name, 'doctors': doctors})

def book_now(request, country_name, city_name, specialty_name):
    query = request.GET.get('q')

    doctors = Doctor.objects.filter(country__iexact=country_name, city__iexact=city_name, specialization__iexact=specialty_name)

    if query:
        doctors = doctors.filter(user__username__icontains=query)

    gender = request.GET.get('gender')
    if gender in ['male', 'female']:
        doctors = doctors.filter(gender__iexact=gender)

    experience = request.GET.get('experience')

    if experience:
        try:
            experience = int(experience)
            doctors = doctors.filter(experience__gte=experience)
        except ValueError:
            pass

    fee = request.GET.get('fee')
    if fee == 'low':
        doctors = doctors.filter(consultation_fee__lt=500)
    elif fee == 'medium':
        doctors = doctors.filter(consultation_fee__gte=500, consultation_fee__lte=1000)
    elif fee == 'high':
        doctors = doctors.filter(consultation_fee__gt=1000)

    sort = request.GET.get('sort')
    if sort == 'fee-low':
        doctors = doctors.order_by('consultation_fee')
    elif sort == 'fee-high':
        doctors = doctors.order_by('-consultation_fee')

    try:
        client = request.user.client_profile
        client_lat = client.latitude
        client_lon = client.longitude
    except AttributeError:
        return render(request, 'appointments/doctors_page.html', {
            'specialty_name': specialty_name,
            'doctors': [],
            'error': 'Client location not available.'
        })

    if client_lat is not None and client_lon is not None:
        for doctor in doctors:
            if doctor.latitude is not None and doctor.longitude is not None:
                doctor.distance = haversine_distance(client_lat, client_lon, doctor.latitude, doctor.longitude)
            else:
                doctor.distance = None
    else:
        for doctor in doctors:
            doctor.distance = None

    if sort == 'distance':
        doctors = sorted(doctors, key=lambda x: x.distance if x.distance is not None else float('inf'))

    for doctor in doctors:
        print(str(doctor.latitude) + ' ' + str(doctor.longitude) + ' ' + str(doctor.distance))

    return render(request, 'appointments/doctors_page.html', {'country_name': country_name, 'city_name': city_name, 'specialty_name': specialty_name, 'doctors': doctors})

@login_required
def add_comment(request, doctor_username):
    if request.method == 'POST':
        doctor = get_object_or_404(Doctor, user__username=doctor_username)
        
        # Get user photo from either Doctor or Client profile
        user_photo = None
        try:
            if hasattr(request.user, 'doctor_profile'):
                user_photo = request.user.doctor_profile.profile_picture
            elif hasattr(request.user, 'client_profile'):
                user_photo = request.user.client_profile.profile_picture
        except:
            pass
            
        content = request.POST.get('content')
        rating = request.POST.get('rating')

        Comment.objects.create(
            doctor=doctor,
            user=request.user,
            user_photo=user_photo,
            rating=rating,
            content=content,
        )

        return redirect('view_doctor_profile_by_cli', username=doctor_username)

@login_required
def update_profile_picture(request):
    if request.user.groups.filter(name='Doctor').exists():
        profile, created = Doctor.objects.get_or_create(user=request.user)
    elif request.user.groups.filter(name='Client').exists():
        profile, created = Client.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        print("POST request received")
        form = ProfilePictureForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            print("Form is valid")
            form.save()
            print("Profile photo updated")

            if request.user.groups.filter(name='Doctor').exists():
                return redirect('doctor_profile')
            elif request.user.groups.filter(name='Client').exists():
                return redirect('client_profile')
            
        else:
            print("Form is invalid")
    else:
        form = ProfilePictureForm(instance=profile)

@login_required
def update_client_profile(request):
    try:
        client = request.user.client_profile  
    except Client.DoesNotExist:
        messages.error(request, "Client profile not found.")
        return redirect('client_profile')  

    if request.method == 'POST':
        username = request.POST.get('username')
        real_name = request.POST.get('real_name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        address = request.POST.get('address')
        date_of_birth = request.POST.get("date_of_birth")
        gender = request.POST.get("gender")

        user = client.user
        user.username = username
        if real_name:  # Split real name into first and last name
            name_parts = real_name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        user.email = email
        user.save()

        # Update client fields
        client.contact = contact
        client.address = address
        client.gender = gender

        if address:
            client.fetch_coordinates()

        if date_of_birth: 
            try:
                client.date_of_birth = date_of_birth  
            except ValidationError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
                return render(request, 'appointments/client_profile.html', {"client": client})
        else:
            client.date_of_birth = None 

        client.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('client_profile')

@login_required
def update_doctor_profile_proffessional(request):
    try:
        doctor = request.user.doctor_profile  
    except Doctor.DoesNotExist:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_profile')

    if request.method == 'POST':
        specialization = request.POST.get('specialization')
        qualification = request.POST.get('qualification')
        experience = request.POST.get('experience')
        certifications = request.POST.get('certifications')
        professional_description = request.POST.get('professional_description')

        doctor.specialization = specialization
        doctor.qualification = qualification
        doctor.experience = experience
        doctor.certifications = certifications
        doctor.professional_description = professional_description

        doctor.save()
        messages.success(request, "Professional details updated successfully!")
        return redirect('doctor_profile') 

@login_required
def update_doctor_profile_work(request):
    try:
        doctor = request.user.doctor_profile  
    except Doctor.DoesNotExist:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_profile')

    if request.method == 'POST':
        clinic_hospital = request.POST.get('clinic_hospital')
        address = request.POST.get('address')
        city = request.POST.get('city')
        country = request.POST.get('country')
        availability = request.POST.get('availability')
        services = request.POST.get('services')
        consultation_fee = request.POST.get('consultation_fee')

        doctor.clinic_hospital = clinic_hospital
        doctor.address = address
        doctor.city = city
        doctor.country = country
        doctor.availability = availability
        doctor.services = services

        doctor.fetch_coordinates()

        try:
            doctor.consultation_fee = float(consultation_fee) if consultation_fee else None
        except ValueError:
            messages.error(request, "Invalid consultation fee. Please enter a valid number.")
            return render(request, 'appointments/doctor_profile.html', {"doctor": doctor})

        doctor.save()
        messages.success(request, "Work details updated successfully!")
        return redirect('doctor_profile')  

@login_required
def update_doctor_profile_details(request):
    try:
        doctor = request.user.doctor_profile  
    except Doctor.DoesNotExist:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_profile')

    if request.method == 'POST':
        contact = request.POST.get('contact', '').strip()
        website = request.POST.get('website', '').strip()
        
        doctor.contact = contact
        doctor.website = website
        
        doctor.save()
        messages.success(request, "Contact details updated successfully!")
        return redirect('doctor_profile')

@login_required
def update_doctor_profile_additional(request):
    try:
        doctor = request.user.doctor_profile  
    except Doctor.DoesNotExist:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_profile')

    if request.method == 'POST':
        # Check both potential field names for real name
        real_name = request.POST.get('realName') or request.POST.get('real_name')
        email = request.POST.get('email', '').strip() 
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        rating = request.POST.get('rating')
        languages_spoken = request.POST.get('languages_spoken')
        
        # Update user fields
        if real_name:
            name_parts = real_name.strip().split(' ', 1)
            doctor.user.first_name = name_parts[0]
            doctor.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            
        if email:
            doctor.user.email = email
            
        doctor.user.save()

        # Update doctor fields
        doctor.languages_spoken = languages_spoken  
        doctor.date_of_birth = date_of_birth if date_of_birth else None
        doctor.gender = gender
        
        try:
            # Convert rating to float but keep current value if empty
            if rating:
                doctor.rating = float(rating)
            # Don't set to 0.0 if empty - keep the current value
        except ValueError:
            messages.error(request, "Invalid rating value.")
            return render(request, 'appointments/doctor_profile.html', {"doctor": doctor})

        doctor.save()
        messages.success(request, "Additional details updated successfully!")
        return redirect('doctor_profile')

@login_required
def update_doctor_profile_availability(request):
    try:
        doctor = request.user.doctor_profile  
    except Doctor.DoesNotExist:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_profile')

    if request.method == 'POST':
        doctor.monday_start = request.POST.get('monday_start')
        doctor.monday_end = request.POST.get('monday_end')
        doctor.tuesday_start = request.POST.get('tuesday_start')
        doctor.tuesday_end = request.POST.get('tuesday_end')
        doctor.wednesday_start = request.POST.get('wednesday_start')
        doctor.wednesday_end = request.POST.get('wednesday_end')
        doctor.thursday_start = request.POST.get('thursday_start')
        doctor.thursday_end = request.POST.get('thursday_end')
        doctor.friday_start = request.POST.get('friday_start')
        doctor.friday_end = request.POST.get('friday_end')


        doctor.save()
        messages.success(request, "Availability details updated successfully!")
        return redirect('doctor_profile')  

@login_required
def generate_and_save_slots(request):
    if request.method == 'POST':
        try:
            doctor = request.user.doctor_profile  
        except Doctor.DoesNotExist:
            messages.error(request, "Doctor profile not found.")
            return redirect('doctor_profile') 
        
        try:
            # Parse JSON body
            data = json.loads(request.body)
            appointment_duration = int(data.get('appointment_duration'))  # Default to 30 minutes
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'status': 'error', 'message': 'Invalid data or appointment duration.'}, status=400)

        print(appointment_duration)

        # Availability data
        availability = {
            'Monday': {'start': doctor.monday_start, 'end': doctor.monday_end},
            'Tuesday': {'start': doctor.tuesday_start, 'end': doctor.tuesday_end},
            'Wednesday': {'start': doctor.wednesday_start, 'end': doctor.wednesday_end},
            'Thursday': {'start': doctor.thursday_start, 'end': doctor.thursday_end},
            'Friday': {'start': doctor.friday_start, 'end': doctor.friday_end},
        }

        created_slots = []  # Track created slots for the response

        # Iterate through each day
        for day, times in availability.items():
            start_time = times['start']
            end_time = times['end']

            if not start_time or not end_time:  # Skip days without availability
                continue

            # Parse start and end times
            start_time = datetime.strptime(start_time, '%H:%M').time()
            end_time = datetime.strptime(end_time, '%H:%M').time()

            # Generate slots for the day
            current_time = datetime.combine(datetime.today(), start_time)
            end_datetime = datetime.combine(datetime.today(), end_time)

            while current_time.time() < end_time:
                slot_start = current_time.time()
                slot_end = (current_time + timedelta(minutes=appointment_duration)).time()

                # Ensure slot_end doesn't exceed end_time
                if slot_end > end_time:
                    break

                # Save the slot to the database
                slot, created = Slot.objects.get_or_create(
                    doctor=doctor,
                    day=day,
                    start_time=slot_start,
                    end_time=slot_end,
                    #defaults={'reserved': False}
                )
                if created:
                    created_slots.append({
                        'day': day,
                        'start_time': slot_start.strftime('%H:%M'),
                        'end_time': slot_end.strftime('%H:%M')
                    })

                current_time += timedelta(minutes=appointment_duration)

        # Return success response with created slots
        return JsonResponse({'status': 'success', 'created_slots': created_slots})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def get_slots(request):
    if request.user.is_authenticated:
        doctor = request.user.doctor_profile  # Assuming the user is a doctor
        slots = Slot.objects.filter(doctor=doctor).order_by('day', 'start_time')

        slots_by_day = {}
        for slot in slots:
            if slot.day not in slots_by_day:
                slots_by_day[slot.day] = []
            slots_by_day[slot.day].append({
                'id': slot.id,  # Include slot ID
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'first_week_reserved': slot.first_week_reserved,
                'second_week_reserved': slot.second_week_reserved
            })

        return JsonResponse({'status': 'success', 'slots': slots_by_day})

    return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)

def delete_all_slots(request):
    if request.user.is_authenticated:
        doctor = request.user.doctor_profile
        Slot.objects.filter(doctor=doctor).delete()
        return JsonResponse({'status': 'success', 'message': 'All slots deleted successfully'})

    return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)

def delete_slot(request, slot_id):
    if request.user.is_authenticated:
        try:
            doctor = request.user.doctor_profile
            slot = Slot.objects.get(id=slot_id, doctor=doctor)

            print(slot)
            slot.delete()
            return JsonResponse({'status': 'success', 'message': 'Slot deleted successfully'})
        except Slot.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Slot not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=401)

@login_required
def check_slots(request):
    if request.method == 'GET':
        try:
            doctor = request.user.doctor_profile
        except Doctor.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Doctor profile not found.'}, status=404)

        slots_exist = Slot.objects.filter(doctor=doctor).exists()

        return JsonResponse({'status': 'success', 'slots_exist': slots_exist})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

@login_required
def add_manual_slot(request):
    if request.method == 'POST':
        try:
            doctor = request.user.doctor_profile
        except Doctor.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Doctor profile not found.'}, status=404)

        data = json.loads(request.body)
        day = data.get('day')  # Get the day from the request
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')

        try:
            # Parse start and end times
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()

            if start_time >= end_time:
                return JsonResponse({'status': 'error', 'message': 'Start time must be before end time.'}, status=400)

            # Check if slot overlaps with existing ones for the same day
            overlapping_slots = Slot.objects.filter(
                doctor=doctor,
                day=day,
                start_time__lt=end_time,
                end_time__gt=start_time
            )

            if overlapping_slots.exists():
                return JsonResponse({'status': 'error', 'message': 'Slot overlaps with an existing one.'}, status=400)

            # Create the new slot
            Slot.objects.create(
                doctor=doctor,
                day=day,  # Use the specified day
                start_time=start_time,
                end_time=end_time,
                #reserved=False
            )

            return JsonResponse({'status': 'success', 'message': 'Slot successfully created.'})

        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid time format.'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


@login_required
def fetch_slots_for_two_weeks(request, doctor_username):
    try:
        # Retrieve the doctor based on the username
        doctor = get_object_or_404(Doctor, user__username=doctor_username)

        # Today's date
        today = datetime.today().date()

        # Generate the next 14 days with their corresponding day names and week numbers
        next_two_weeks = []
        for i in range(14):
            current_date = today + timedelta(days=i)
            day_name = current_date.strftime('%A')
            week_number = 1 if i < 7 else 2  # First week: days 0-6, Second week: days 7-13
            next_two_weeks.append({
                'date': current_date,
                'day_name': day_name,
                'week': week_number
            })

        # Extract unique day names to minimize database queries
        unique_day_names = {day['day_name'] for day in next_two_weeks}

        # Query slots matching the day names for the doctor
        slots = Slot.objects.filter(
            doctor=doctor,
            day__in=unique_day_names
        ).order_by('day', 'start_time')

        # Organize slots by day name for quick access
        slots_by_day = {}
        for slot in slots:
            slots_by_day.setdefault(slot.day, []).append({
                'id': slot.id,
                'start_time': slot.start_time.strftime('%I:%M %p'),
                'end_time': slot.end_time.strftime('%I:%M %p'),
                'start_time_24h': slot.start_time.strftime('%H:%M'),
                'end_time_24h': slot.end_time.strftime('%H:%M'),
                'first_week_reserved': slot.first_week_reserved,
                'second_week_reserved': slot.second_week_reserved
            })

        # Prepare the slots data structured by date, filtering based on reservation status
        slots_by_date = {}
        for entry in next_two_weeks:
            date = entry['date']
            date_str = date.strftime('%Y-%m-%d')
            day_name = entry['day_name']
            week = entry['week']
            all_slots = slots_by_day.get(day_name, [])

            # Filter slots based on the week and reservation status
            if week == 1:
                available_slots = [
                    {
                        'start_time': slot['start_time'],
                        'end_time': slot['end_time'],
                        'start_time_24h': slot['start_time_24h'],
                        'end_time_24h': slot['end_time_24h']
                    }
                    for slot in all_slots if not slot['first_week_reserved']
                ]
            else:
                available_slots = [
                    {
                        'start_time': slot['start_time'],
                        'end_time': slot['end_time'],
                        'start_time_24h': slot['start_time_24h'],
                        'end_time_24h': slot['end_time_24h']
                    }
                    for slot in all_slots if not slot['second_week_reserved']
                ]

            slots_by_date[date_str] = available_slots

        return JsonResponse({'status': 'success', 'slots': slots_by_date})

    except Exception as e:
        # Log the exception if necessary
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def fetch_slots_for_two_weeks_by_id(request, doctor_id):
    try:
        doctor = get_object_or_404(Doctor, id=doctor_id)  # Get the doctor by id

        # Define the next 14 days with their corresponding dates and day names
        today = datetime.today()
        next_two_weeks = [
            {
                'date': today + timedelta(days=i),
                'day_name': (today + timedelta(days=i)).strftime('%A')
            }
            for i in range(14)
        ]

        # Extract unique day names to minimize database queries
        unique_day_names = {day['day_name'] for day in next_two_weeks}

        # Determine the week (first or second) for each day in the next two weeks
        slots_by_date = {}
        for i, entry in enumerate(next_two_weeks):
            date_obj = entry['date']
            day_name = entry['day_name']
            reserved_field = 'first_week_reserved' if i < 7 else 'second_week_reserved'

            # Query slots for the specific day and exclude reserved slots
            slots = Slot.objects.filter(
                doctor=doctor,
                day=day_name,
                **{reserved_field: False}  # Exclude reserved slots
            ).order_by('start_time')

            # Format slots for JSON response
            formatted_slots = [
                {
                    'start_time': slot.start_time.strftime('%I:%M %p'),
                    'end_time': slot.end_time.strftime('%I:%M %p'),
                    'start_time_24h': slot.start_time.strftime('%H:%M'),
                    'end_time_24h': slot.end_time.strftime('%H:%M'),
                }
                for slot in slots
            ]

            # Add slots to the corresponding date
            date_str = date_obj.strftime('%Y-%m-%d')
            slots_by_date[date_str] = formatted_slots

            print(doctor_id)

        return JsonResponse({'status': 'success', 'slots': slots_by_date})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



@login_required
def book_appointment(request):
    if request.method == 'POST':
        try:
            # Get form data
            appointment_type = request.POST.get('appointment_type', 'in_clinic')

            if appointment_type == 'in_clinic':

                doctor_id = request.POST.get('doctor_id')
                date = request.POST.get('start_date')
                start_time = request.POST.get('start_time')
                end_time = request.POST.get('end_time')
                clinic = request.POST.get('clinic')
                one_time = request.POST.get('one_time') == 'on'  # Checkbox checked
                repeat_every = request.POST.get('repeat_every')
                repeat_unit = request.POST.get('repeat_unit')
                end_date = request.POST.get('end_date')

                # Validate required fields
                if not all([doctor_id, date, start_time, end_time, clinic]):
                    return JsonResponse({'error': 'All required fields must be provided.'}, status=400)

                # Convert strings to datetime
                try:
                    start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
                    end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
                except ValueError:
                    return JsonResponse({'error': 'Invalid date or time format.'}, status=400)

                # Validate time logic
                if start_datetime >= end_datetime:
                    return JsonResponse({'error': 'Start time must be earlier than end time.'}, status=400)

                # Convert date to day of the week
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    return JsonResponse({'error': 'Invalid date format.'}, status=400)

                day_of_week = calendar.day_name[date_obj.weekday()]  # E.g., "Monday"

                # Determine the current date
                today = datetime.today().date()
                selected_date = date_obj.date()
                delta_days = (selected_date - today).days

                if delta_days < 0:
                    return JsonResponse({'error': 'Selected date is in the past.'}, status=400)
                elif 0 <= delta_days < 7:
                    # Week 1
                    reserved_field = 'first_week_reserved'
                elif 7 <= delta_days < 14:
                    # Week 2
                    reserved_field = 'second_week_reserved'
                else:
                    return JsonResponse({'error': 'Selected date is beyond the reservation period (14 days).'}, status=400)

                slot_exists = Slot.objects.filter(
                    doctor_id=doctor_id,
                    day=day_of_week,
                    start_time=start_datetime.time(),
                    end_time=end_datetime.time(),
                    **{reserved_field: False}  # Dynamically set the reserved field
                ).exists()

                if not slot_exists:
                    return JsonResponse({'error': 'The selected slot does not exist.'}, status=400)

                # Get the doctor
                doctor = get_object_or_404(Doctor, id=doctor_id)

                # Get the client profile
                try:
                    client = request.user.client_profile
                except AttributeError:
                    return JsonResponse({'error': 'Client profile not found.'}, status=400)


                # Handle one-time appointments
                if one_time:

                    appointment = Appointment.objects.create(
                        appointment_type=appointment_type,
                        platform=None,
                        call_link=None,

                        doctor_fk=doctor,
                        doctor_id=doctor.id,
                        doctor_name=f"{doctor.user.first_name} {doctor.user.last_name}",
                        doctor_gender=doctor.gender,
                        doctor_contact=doctor.contact,
                        doctor_address=doctor.address,
                        doctor_clinic=doctor.clinic_hospital,

                        start_date=start_datetime.date(),
                        start_time=start_datetime.time(),
                        end_time=end_datetime.time(),
                        duration=(end_datetime - start_datetime).seconds // 60,
                        status=False,
                        one_time_only=True,

                        client_fk=client,
                        client_id=client.user.id,
                        client_name=f"{client.user.first_name} {client.user.last_name}",
                        client_gender=client.gender,
                        client_contact=client.contact,
                        client_address = client.address,
                        client_date_of_birth = client.date_of_birth,
                    )

                    # Generate the email confirmation link
                    token = serializer.dumps(appointment.id, salt="appointment-confirmation")
                    confirmation_link = 'http://localhost:8000/confirm-appointment-by-link/{token}/'

                    send_mail(
                        subject='Appointment Confirmation',
                        message=(
                            f"Dear {client.user.first_name} {client.user.last_name},\n\n"
                            f"Your appointment details are as follows: In clinic Appointment\n"
                            f"Doctor: Dr. {doctor.user.first_name} {doctor.user.last_name}\n"
                            f"Clinic: {doctor.clinic_hospital}\n"
                            f"Address: {doctor.address}\n"
                            f"Date: {start_datetime.date()}\n"
                            f"Time: {start_datetime.time()} - {end_datetime.time()}\n"
                            f"Duration: {(end_datetime - start_datetime).seconds // 60} minutes\n\n"
                            f"To confirm your appointment, please click the following link:\n"
                            f"{confirmation_link}\n\n"
                            f"Thank you,\n"
                            f"Your Clinic Team"
                        ),
                        from_email='mihnea.encean2@gmail.com',
                        recipient_list=['mihnea.encean1@gmail.com'],
                        fail_silently=False,
                    )


                    messages.success(request, "Appointment booked successfully! An email has been sent to confirm your appointment. Please check your inbox.")

                    return redirect('client_appointments')
                    #return JsonResponse({'success': 'Appointment booked successfully!'}, status=200)

                if not one_time:
                    # Validate repeat fields
                    if not all([repeat_every, repeat_unit, end_date]):
                        return JsonResponse({'error': 'All recurring fields must be provided.'}, status=400)

                    try:
                        # Convert repeat_every to integer
                        repeat_every = int(repeat_every)

                        # Convert end_date to datetime
                        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                    except ValueError:
                        return JsonResponse({'error': 'Invalid repeat_every or end_date format.'}, status=400)

                    # Validate date logic
                    if end_date_obj < start_datetime.date():
                        return JsonResponse({'error': 'End date must be later than start date.'}, status=400)

                    start_date_obj = start_datetime.date()
                    total_days = (end_date_obj - start_date_obj).days

                    if repeat_unit == 'week':
                        step = 7 * repeat_every
                    elif repeat_unit == 'month':
                        # Approximate 1 month as 30 days
                        step = 30 * repeat_every
                    else:
                        return JsonResponse({'error': 'Invalid repeat unit.'}, status=400)

                    num_appointments = (total_days // step) + 1
                    no_of_appointments = 0

                    for i in range(num_appointments):

                        current_date = start_date_obj + timedelta(days=step * i)

                        if current_date > end_date_obj:
                            break
                        # Create the appointment
                        appointment = Appointment.objects.create(
                            appointment_type=appointment_type,
                            platform=None,
                            call_link=None,

                            doctor_fk=doctor,
                            doctor_id=doctor.id,
                            doctor_name=f"Dr. {doctor.user.first_name} {doctor.user.last_name}",
                            doctor_gender=doctor.gender,
                            doctor_contact=doctor.contact,
                            doctor_address=doctor.address,
                            doctor_clinic=doctor.clinic_hospital,

                            start_date=current_date,
                            start_time=start_datetime.time(),
                            end_time=end_datetime.time(),
                            duration=(end_datetime - start_datetime).seconds // 60,
                            status=False,
                            one_time_only=False,

                            client_fk=client,
                            client_id=client.user.id,
                            client_name=f"{client.user.first_name} {client.user.last_name}",
                            client_gender=client.gender,
                            client_contact=client.contact,
                            client_address=client.address,
                            client_date_of_birth=client.date_of_birth,
                        )

                        # Send email for the first appointment
                        if i == 0:
                            token = serializer.dumps(appointment.id, salt="appointment-confirmation")
                            confirmation_link = f'{settings.RESET_LINK_BASE_URL}/confirm-appointment-by-link/{token}/'

                            send_mail(
                                subject='Appointment Confirmation',
                                message=(
                                    f"Dear {client.user.first_name} {client.user.last_name},\n\n"
                                    f"Your appointment details are as follows: In clinic Appointment\n"
                                    f"Doctor: Dr. {doctor.user.first_name} {doctor.user.last_name}\n"
                                    f"Clinic: {doctor.clinic_hospital}\n"
                                    f"Address: {doctor.address}\n"
                                    f"Date: {current_date}\n"
                                    f"Time: {start_datetime.time()} - {end_datetime.time()}\n"
                                    f"Duration: {(end_datetime - start_datetime).seconds // 60} minutes\n\n"
                                    f"To confirm your appointment, please click the following link:\n"
                                    f"{confirmation_link}\n\n"
                                    f"Thank you,\n"
                                    f"Your Clinic Team"
                                ),
                                from_email='mihnea.encean2@gmail.com',
                                recipient_list=['mihnea.encean1@gmail.com'],
                                fail_silently=False,
                            )

                        no_of_appointments += 1

                messages.success(request, f"{no_of_appointments} recurring appointments booked successfully! Please check your inbox for details.")
                return redirect('client_appointments')

            elif appointment_type == 'online':

                doctor_id = request.POST.get('doctor_id')
                date = request.POST.get('start_date')
                start_time = request.POST.get('start_time')
                end_time = request.POST.get('end_time')
                one_time = request.POST.get('one_time') == 'on'  
                repeat_every = request.POST.get('repeat_every')
                repeat_unit = request.POST.get('repeat_unit')
                end_date = request.POST.get('end_date')

                print(date)
                print(start_time)
                print(end_time)
                print("Ok")

                # Validate required fields
                if not all([doctor_id, date, start_time, end_time]):
                    return JsonResponse({'error': 'All required fields must be provided.'}, status=400)

                # Convert strings to datetime
                try:
                    start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
                    end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
                except ValueError:
                    return JsonResponse({'error': 'Invalid date or time format.'}, status=400)

                # Validate time logic
                if start_datetime >= end_datetime:
                    return JsonResponse({'error': 'Start time must be earlier than end time.'}, status=400)

                # Convert date to day of the week
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    return JsonResponse({'error': 'Invalid date format.'}, status=400)

                day_of_week = calendar.day_name[date_obj.weekday()]  # E.g., "Monday"

                # Determine the current date
                today = datetime.today().date()
                selected_date = date_obj.date()
                delta_days = (selected_date - today).days

                if delta_days < 0:
                    return JsonResponse({'error': 'Selected date is in the past.'}, status=400)
                elif 0 <= delta_days < 7:
                    # Week 1
                    reserved_field = 'first_week_reserved'
                elif 7 <= delta_days < 14:
                    # Week 2
                    reserved_field = 'second_week_reserved'
                else:
                    return JsonResponse({'error': 'Selected date is beyond the reservation period (14 days).'}, status=400)

                slot_exists = Slot.objects.filter(
                    doctor_id=doctor_id,
                    day=day_of_week,
                    start_time=start_datetime.time(),
                    end_time=end_datetime.time(),
                    **{reserved_field: False}  # Dynamically set the reserved field
                ).exists()

                if not slot_exists:
                    return JsonResponse({'error': 'The selected slot does not exist.'}, status=400)

                # Get the doctor
                doctor = get_object_or_404(Doctor, id=doctor_id)

                # Get the client profile
                try:
                    client = request.user.client_profile
                except AttributeError:
                    return JsonResponse({'error': 'Client profile not found.'}, status=400)

                # Generate a unique room name using uuid

                # Handle one-time appointments
                if one_time:

                    appointment = Appointment.objects.create(
                        appointment_type=appointment_type,
                        platform="Jitsi Meet Platform",
                        call_link="Link will be displayed after confirmation",

                        doctor_fk=doctor,
                        doctor_id=doctor.id,
                        doctor_name=f"{doctor.user.first_name} {doctor.user.last_name}",
                        doctor_gender=doctor.gender,
                        doctor_contact=doctor.contact,
                        doctor_address=doctor.address,
                        doctor_clinic=doctor.clinic_hospital,

                        start_date=start_datetime.date(),
                        start_time=start_datetime.time(),
                        end_time=end_datetime.time(),
                        duration=(end_datetime - start_datetime).seconds // 60,
                        status=False,
                        one_time_only=True,

                        client_fk=client,
                        client_id=client.user.id,
                        client_name=f"{client.user.first_name} {client.user.last_name}",
                        client_gender=client.gender,
                        client_contact=client.contact,
                        client_address = client.address,
                        client_date_of_birth = client.date_of_birth,
                    )

                    # Generate the email confirmation link
                    token = serializer.dumps(appointment.id, salt="appointment-confirmation")
                    confirmation_link = 'http://localhost:8000/confirm-appointment-by-link/{token}/'

                    send_mail(
                        subject='Appointment Confirmation',
                        message=(
                            f"Dear {client.user.first_name} {client.user.last_name},\n\n"
                            f"Your appointment details are as follows: Online Appointment\n"
                            f"Doctor: Dr. {doctor.user.first_name} {doctor.user.last_name}\n"
                            f"Date: {start_datetime.date()}\n"
                            f"Time: {start_datetime.time()} - {end_datetime.time()}\n"
                            f"Duration: {(end_datetime - start_datetime).seconds // 60} minutes\n\n"
                            f"To confirm your appointment, please click the following link:\n"
                            f"{confirmation_link}\n\n"
                            f"Thank you,\n"
                            f"Your Clinic Team"
                        ),
                        from_email='mihnea.encean2@gmail.com',
                        recipient_list=['mihnea.encean1@gmail.com'],
                        fail_silently=False,
                    )


                    messages.success(request, "Appointment booked successfully! An email has been sent to confirm your appointment. Please check your inbox.")

                    return redirect('client_appointments')
                    #return JsonResponse({'success': 'Appointment booked successfully!'}, status=200)

                if not one_time:
                    # Validate repeat fields
                    if not all([repeat_every, repeat_unit, end_date]):
                        return JsonResponse({'error': 'All recurring fields must be provided.'}, status=400)

                    try:
                        # Convert repeat_every to integer
                        repeat_every = int(repeat_every)

                        # Convert end_date to datetime
                        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                    except ValueError:
                        return JsonResponse({'error': 'Invalid repeat_every or end_date format.'}, status=400)

                    # Validate date logic
                    if end_date_obj < start_datetime.date():
                        return JsonResponse({'error': 'End date must be later than start date.'}, status=400)

                    start_date_obj = start_datetime.date()
                    total_days = (end_date_obj - start_date_obj).days

                    if repeat_unit == 'week':
                        step = 7 * repeat_every
                    elif repeat_unit == 'month':
                        # Approximate 1 month as 30 days
                        step = 30 * repeat_every
                    else:
                        return JsonResponse({'error': 'Invalid repeat unit.'}, status=400)

                    num_appointments = (total_days // step) + 1
                    no_of_appointments = 0

                    for i in range(num_appointments):

                        current_date = start_date_obj + timedelta(days=step * i)

                        if current_date > end_date_obj:
                            break
                        # Create the appointment
                        appointment = Appointment.objects.create(
                            appointment_type=appointment_type,
                            platform="Jitsi Meet Platform",
                            call_link="Link will be displayed after confirmation",

                            doctor_fk=doctor,
                            doctor_id=doctor.id,
                            doctor_name=f"Dr. {doctor.user.first_name} {doctor.user.last_name}",
                            doctor_gender=doctor.gender,
                            doctor_contact=doctor.contact,
                            doctor_address=doctor.address,
                            doctor_clinic=doctor.clinic_hospital,

                            start_date=current_date,
                            start_time=start_datetime.time(),
                            end_time=end_datetime.time(),
                            duration=(end_datetime - start_datetime).seconds // 60,
                            status=False,
                            one_time_only=False,

                            client_fk=client,
                            client_id=client.user.id,
                            client_name=f"{client.user.first_name} {client.user.last_name}",
                            client_gender=client.gender,
                            client_contact=client.contact,
                            client_address=client.address,
                            client_date_of_birth=client.date_of_birth,
                        )

                        # Send email for the first appointment
                        if i == 0:
                            token = serializer.dumps(appointment.id, salt="appointment-confirmation")
                            confirmation_link = f'{settings.RESET_LINK_BASE_URL}/confirm-appointment-by-link/{token}/'

                            send_mail(
                                subject='Appointment Confirmation',
                                message=(
                                    f"Dear {client.user.first_name} {client.user.last_name},\n\n"
                                    f"Your appointment details are as follows: Online Appointment\n"
                                    f"Doctor: Dr. {doctor.user.first_name} {doctor.user.last_name}\n"
                                    f"Date: {current_date}\n"
                                    f"Time: {start_datetime.time()} - {end_datetime.time()}\n"
                                    f"Duration: {(end_datetime - start_datetime).seconds // 60} minutes\n\n"
                                    f"To confirm your appointment, please click the following link:\n"
                                    f"{confirmation_link}\n\n"
                                    f"Thank you,\n"
                                    f"Your Clinic Team"
                                ),
                                from_email='mihnea.encean2@gmail.com',
                                recipient_list=['mihnea.encean1@gmail.com'],
                                fail_silently=False,
                            )

                        no_of_appointments += 1

                messages.success(request, f"{no_of_appointments} recurring appointments booked successfully! Please check your inbox for details.")
                return redirect('client_appointments')

        except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)


def confirm_appointment(request, token):
    try:
        appointment_id = serializer.loads(token, salt="appointment-confirmation", max_age=3600)  # Token valid for 1 hour
        appointment = Appointment.objects.get(id=appointment_id)

        if appointment.status:
            messages.info(request, "This appointment has already been confirmed.")
        else:
            unique_room = str(uuid.uuid4())
            appointment.call_link = f"https://meet.jit.si/{unique_room}"

            appointment.status = True
            appointment.save()
            messages.success(request, "Your appointment has been successfully confirmed!")
    except (Appointment.DoesNotExist, ValueError):
        messages.error(request, "Invalid or expired confirmation link.")

    return redirect('client_appointments')


@login_required
def upload_clinic_photo(request):
    if request.method == 'POST':
        clinic_photo = request.FILES.get('clinic_photo')
        if clinic_photo:
            doctor = request.user.doctor_profile
            doctor.clinic_picture = clinic_photo
            doctor.save()
            return redirect('doctor_profile')  


def create_account(request):
    return render(request, 'appointments/create_account.html')

def custom_logout(request):
    logout(request)
    return redirect('home')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember') 

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:

                login(request, user)

                if remember_me:
                    request.session.set_expiry(1209600)  # 2 weeks in seconds
                else:
                    request.session.set_expiry(0)

                messages.success(request, "You are now logged in.")

                next_url = request.GET.get('next', 'home')  
                return redirect(next_url)
            else:
                messages.error(request, "Your account is deactivated. Please contact support.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'registration/login.html')

def register_doctor(request):
    errors = {}

    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('realname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        repassword = request.POST.get('repassword')

        if not request.POST.get('terms'):
            errors['terms'] = "You must agree to the Terms and Conditions."

        if password != repassword:
            errors['password'] = "Passwords do not match."

        if User.objects.filter(email=email).exists():
            errors['email'] = "This email address already exists."

        if errors:
            return render(request, 'appointments/register_doctor.html', {'errors': errors})

        user = User.objects.create_user(
            username=username,  
            email=email,
            password=password, 
            first_name=name.split(' ')[0],  
            last_name=' '.join(name.split(' ')[1:])  
        )

        doctor_group, created = Group.objects.get_or_create(name='Doctor')
        user.groups.add(doctor_group)

        Doctor.objects.create(user=user)

        messages.success(request, "Account created successfully! Please log in.")
        return redirect('login')  

    return render(request, 'appointments/register_doctor.html')

def register_client(request):
    errors = {}

    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('realname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        repassword = request.POST.get('repassword')

        if not request.POST.get('terms'):
            errors['terms'] = "You must agree to the Terms and Conditions."

        if password != repassword:
            errors['password'] = "Passwords do not match."

        if User.objects.filter(email=email).exists():
            errors['email'] = "This email address already exists."

        if errors:
            return render(request, 'appointments/register_client.html', {'errors': errors})

        user = User.objects.create_user(
            username=username,  
            email=email,
            password=password, 
            first_name=name.split(' ')[0],  
            last_name=' '.join(name.split(' ')[1:])  
        )

        client_group, created = Group.objects.get_or_create(name='Client')
        user.groups.add(client_group)

        Client.objects.create(user=user)

        messages.success(request, "Account created successfully! Please log in.")
        return redirect('login')  

    return render(request, 'appointments/register_client.html')


def send_reset_email_client(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            # Get the specific user based on both email and client group
            user = User.objects.filter(
                email=email,
                groups__name='Client'
            ).first()  

            

            if not user:
                messages.error(request, 'No client account is associated with this email.')
                return redirect('client_profile')

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_link = f'{settings.RESET_LINK_BASE_URL}/reset-password-by-link/{uid}/{token}/'
            
            send_mail(
                subject='Password Reset Request',
                message=f'Click this link to reset your password: {reset_link}',
                from_email='mihnea.encean2@gmail.com',  
                recipient_list=[email],
                fail_silently=False,
            )

            messages.success(request, 'Email sent successfully! Please check your inbox.')
           
            return redirect('client_profile')

        except Exception as e:
            messages.error(request, 'An error occurred while sending the reset email. Please try again.')
            return redirect('client_profile')

    return redirect('client_profile')

def send_reset_email_doctor(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        print(f"Attempting to send reset email to: {email}")  # Debug print
        
        try:
            # Get the specific user based on both email and doctor group
            user = User.objects.filter(
                email=email,
                groups__name='Doctor'
            ).first()
            
            if not user:
                messages.error(request, 'No doctor account is associated with this email.')
                return redirect('doctor_profile')

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f'{settings.RESET_LINK_BASE_URL}/reset-password-by-link/{uid}/{token}/'
            
            print(f"Generated reset link: {reset_link}")  # Debug print

            send_mail(
                subject='Password Reset Request',
                message=f'Click this link to reset your password: {reset_link}',
                from_email='mihnea.encean2@gmail.com',
                recipient_list=[email],
                fail_silently=False,
            )
            
            messages.success(request, 'Email sent successfully! Please check your inbox.')
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")  # Debug print
            messages.error(request, f'An error occurred while sending the reset email: {str(e)}')
        
        return redirect('doctor_profile')

    return redirect('doctor_profile')

def send_reset_email_general(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # Check if the email exists in the database
        user = User.objects.filter(email=email).first()

        if user:
            # Generate the reset link
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f'{settings.RESET_LINK_BASE_URL}/reset-password-by-link/{uid}/{token}/'

            # Send the email
            send_mail(
                subject='Password Reset Request',
                message=f'Click this link to reset your password: {reset_link}',
                from_email='mihnea.encean2@gmail.com',  
                recipient_list=[email],
                fail_silently=False,
            )

            # Return a success response
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': True})

    return render(request, 'forgot_password.html')  

def send_contact_site_email(request):
    if request.method == 'POST':
        first_name = request.POST.get('firstName')
        last_name = request.POST.get('lastName')
        prefix = request.POST.get('prefix')
        mobile_phone = request.POST.get('mobile', '').strip()  
        email = request.POST.get('email')
        message = request.POST.get('message')
        captcha = request.POST.get('captcha')
        captcha_index = request.POST.get('captchaIndex', '0')

        email_error = None
        captcha_error = None
        mobile_phone_error = None
        message_error = None

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            email_error = "Invalid email address"

        expected_captcha = 'qVpXayk'
        expected_captcha2 = 'flextime'
        expected_captcha3 = 'LYNN'

        try:
            captcha_index = int(captcha_index)
        except ValueError:
            captcha_index = 0  

        if captcha_index == 0:
            expected = expected_captcha
        elif captcha_index == 1:
            expected = expected_captcha2
        elif captcha_index == 2:
            expected = expected_captcha3
        else:
            expected = expected_captcha  # default

        if captcha != expected:
            captcha_error = "Invalid CAPTCHA. Please try again."

        if not mobile_phone.isdigit():
            mobile_phone_error = "Mobile phone must contain only digits."
        elif len(mobile_phone) not in [9, 10]:
            mobile_phone_error = "Mobile phone must be 9 or 10 digits long."
        elif len(mobile_phone) == 10:
            prefix_digits = re.sub(r'\D', '', prefix or '')
            
            if not prefix_digits:
                mobile_phone_error = "Invalid country prefix format."
            elif mobile_phone[0] != prefix_digits[-1]:
                mobile_phone_error = ("First digit doesn't match with prefix.")

        if len(message.strip()) < 10:
            message_error = "The message must be at least 10 characters long."

        if email_error or captcha_error or mobile_phone_error or message_error:
            return render(request, 'appointments/contact.html', {
                'email_error': email_error,
                'captcha_error': captcha_error,
                'mobile_phone_error': mobile_phone_error,
                'message_error': message_error,
                'form_data': request.POST  # Pass back the form data for persistence
            })

        subject = f"Contact Form Submission from {first_name} {last_name}"
        body = (
            f"You have received a new contact form submission:\n\n"
            f"Name: {first_name} {last_name}\n"
            f"Mobile Phone: {mobile_phone}\n"
            f"Email: {email}\n\n"
            f"Message:\n{message}\n"
        )
        recipient_list = ['mihnea.encean2@gmail.com']  

        try:
        
            send_mail(
                subject,
                body,
                email,  
                recipient_list,
                fail_silently=False,  
            )

            success_message = "Thank you! Your message has been sent successfully."
            return render(request, 'appointments/contact.html', {'success_message': success_message}) 
        except Exception as e:
            print(traceback.format_exc())  
            error_message = f"Failed to send email: {str(e)}"
            return JsonResponse({'status': 'error', 'message': error_message})
        

def reset_password_view(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
                return render(request, 'appointments/reset_password.html', {'validlink': True})

            user.set_password(new_password)
            user.save()
            messages.success(request, "Password reset successfully! Please log in with your new password.")
            return redirect('login')

        return render(request, 'appointments/reset_password.html', {'validlink': True})
    else:
        messages.error(request, "The reset password link is invalid or expired.")
        return render(request, 'appointments/reset_password.html', {'validlink': False})

def about(request):
    # Fetch the latest comments from the database
    testimonials = Comment.objects.all().order_by('-created_at')[:3]  # Get the 3 most recent comments
    
    return render(request, 'appointments/about.html', {'testimonials': testimonials})

@login_required
def doctor_appointments(request):
    try:
        doctor = request.user.doctor_profile
    except Doctor.DoesNotExist:
        messages.error(request, "Doctor profile not found.")

    current_time = timezone.now()
    today = current_time.date()
    now_time = current_time.time()

    search_query = request.GET.get('q', '')

    appointments = Appointment.objects.filter(doctor_id=doctor.id)

    if search_query:
        appointments = appointments.filter(
            Q(client_name__icontains=search_query) |
            Q(client_contact__icontains=search_query) |
            Q(client_date_of_birth__icontains=search_query)
        )

    # Order the results (if needed)
    appointments = appointments.order_by('-start_date', '-start_time')

    # Define finished and active conditions
    finished_condition = Q(start_date__lt=today) | Q(start_date=today, end_time__lte=now_time)
    active_condition = Q(start_date__gt=today) | Q(start_date=today, end_time__gt=now_time)

    # Finished in-clinic appointments
    finished_in_clinic_appointments_filtered = appointments.filter(appointment_type='in_clinic').filter(finished_condition)

    # Finished online appointments
    finished_online_appointments_filtered = appointments.filter(appointment_type='online').filter(finished_condition)

    # Active in-clinic appointments
    active_in_clinic_appointments_filtered = appointments.filter(appointment_type='in_clinic').filter(active_condition)

    # Active online appointments
    active_online_appointments_filtered = appointments.filter(appointment_type='online').filter(active_condition)

    in_clinic_appointments_filtered = appointments.filter(appointment_type='in_clinic')
    online_appointments_filtered = appointments.filter(appointment_type='online')

    total_appointments = appointments.count()
    finished_appointments = finished_in_clinic_appointments_filtered.count() + finished_online_appointments_filtered.count()
    active_appointments = active_in_clinic_appointments_filtered.count() + active_online_appointments_filtered.count()
    in_clinic_appointments = in_clinic_appointments_filtered.count()
    online_appointments = online_appointments_filtered.count()

    paginator = Paginator(in_clinic_appointments_filtered, 10)
    page_number = request.GET.get('page', 1)

    paginator2 = Paginator(finished_in_clinic_appointments_filtered, 10)
    page_number2 = request.GET.get('page2', 1)

    paginator3 = Paginator(active_in_clinic_appointments_filtered, 10)
    page_number3 = request.GET.get('page3', 1)

    paginator4 = Paginator(online_appointments_filtered, 10)
    page_number4 = request.GET.get('page4', 1)

    paginator5 = Paginator(finished_online_appointments_filtered, 10)
    page_number5 = request.GET.get('page5', 1)

    paginator6 = Paginator(active_online_appointments_filtered, 10)
    page_number6 = request.GET.get('page6', 1)

    try:
        appointments_page = paginator.page(page_number)
    except PageNotAnInteger:
        appointments_page = paginator.page(1)
    except EmptyPage:
        appointments_page = paginator.page(paginator.num_pages)

    try:
        appointments_page2 = paginator2.page(page_number2)
    except PageNotAnInteger:
        appointments_page2 = paginator2.page(1)
    except EmptyPage:
        appointments_page2 = paginator2.page(paginator2.num_pages)

    try:
        appointments_page3 = paginator3.page(page_number3)
    except PageNotAnInteger:
        appointments_page3 = paginator3.page(1)
    except EmptyPage:
        appointments_page3 = paginator3.page(paginator3.num_pages)

    try:
        appointments_page4 = paginator4.page(page_number4)
    except PageNotAnInteger:
        appointments_page4 = paginator4.page(1)
    except EmptyPage:
        appointments_page4 = paginator4.page(paginator4.num_pages)

    try:
        appointments_page5 = paginator5.page(page_number5)
    except PageNotAnInteger:
        appointments_page5 = paginator5.page(1)
    except EmptyPage:
        appointments_page5 = paginator5.page(paginator5.num_pages)

    try:
        appointments_page6 = paginator6.page(page_number6)
    except PageNotAnInteger:
        appointments_page6 = paginator6.page(1)
    except EmptyPage:
        appointments_page6 = paginator6.page(paginator6.num_pages)

    # Compute the custom page range
    custom_page_range = get_custom_page_range(appointments_page.number, paginator.num_pages)
    custom_page_range2 = get_custom_page_range(appointments_page2.number, paginator2.num_pages)
    custom_page_range3 = get_custom_page_range(appointments_page3.number, paginator3.num_pages)
    custom_page_range4 = get_custom_page_range(appointments_page4.number, paginator4.num_pages)
    custom_page_range5 = get_custom_page_range(appointments_page5.number, paginator5.num_pages)
    custom_page_range6 = get_custom_page_range(appointments_page6.number, paginator6.num_pages)

    context  = {
        'appointments': appointments,
        'active_in_clinic_appointments_filtered': active_in_clinic_appointments_filtered,
        'finished_in_clinic_appointments_filtered': finished_in_clinic_appointments_filtered,
        'active_online_appointments_filtered': active_online_appointments_filtered,
        'finished_online_appointments_filtered': finished_online_appointments_filtered,
        'total_appointments': total_appointments,
        'finished_appointments': finished_appointments,
        'active_appointments': active_appointments,
        'in_clinic_appointments': in_clinic_appointments,
        'online_appointments': online_appointments,
        'current_date': current_time.strftime('%d %b %Y'),
        'today': today,
        'now_time': now_time,
        'appointments_page': appointments_page,  
        'paginator': paginator,
        'custom_page_range': custom_page_range,
        'appointments_page2': appointments_page2,  
        'paginator2': paginator2,
        'custom_page_range2': custom_page_range2,
        'appointments_page3': appointments_page3,  
        'paginator3': paginator3,
        'custom_page_range3': custom_page_range3,
        'appointments_page4': appointments_page4,  
        'paginator4': paginator4,
        'custom_page_range4': custom_page_range4,
        'appointments_page5': appointments_page5,  
        'paginator5': paginator5,
        'custom_page_range5': custom_page_range5,
        'appointments_page6': appointments_page6,  
        'paginator6': paginator6,
        'custom_page_range6': custom_page_range6,
    }

    return render(request, 'appointments/doctor_appointments.html', context)

@login_required
def client_appointments(request):
    try:
        client = request.user.client_profile  
    except Client.DoesNotExist:
        messages.error(request, "Client profile not found.")

    current_time = timezone.now()
    today = current_time.date()
    now_time = current_time.time()

    search_query = request.GET.get('q', '')
    selected_filter = request.GET.get('filter', 'all')

    appointments = Appointment.objects.filter(client_id=request.user.id)

    if search_query:
        appointments = appointments.filter(
            Q(doctor_name__icontains=search_query) |
            Q(doctor_contact__icontains=search_query) |
            Q(doctor_clinic__icontains=search_query) 
        )

    # Order the results (if needed)
    appointments = appointments.order_by('-start_date', '-start_time')

    # Define finished and active conditions
    finished_condition = Q(start_date__lt=today) | Q(start_date=today, end_time__lte=now_time)
    active_condition = Q(start_date__gt=today) | Q(start_date=today, end_time__gt=now_time)

    # Finished in-clinic appointments
    finished_in_clinic_appointments_filtered = appointments.filter(appointment_type='in_clinic').filter(finished_condition)

    # Finished online appointments
    finished_online_appointments_filtered = appointments.filter(appointment_type='online').filter(finished_condition)

    # Active in-clinic appointments
    active_in_clinic_appointments_filtered = appointments.filter(appointment_type='in_clinic').filter(active_condition)

    # Active online appointments
    active_online_appointments_filtered = appointments.filter(appointment_type='online').filter(active_condition)

    in_clinic_appointments_filtered = appointments.filter(appointment_type='in_clinic')
    online_appointments_filtered = appointments.filter(appointment_type='online')

    total_appointments = appointments.count()
    finished_appointments = finished_in_clinic_appointments_filtered.count() + finished_online_appointments_filtered.count()
    active_appointments = active_in_clinic_appointments_filtered.count() + active_online_appointments_filtered.count()
    in_clinic_appointments = in_clinic_appointments_filtered.count()
    online_appointments = online_appointments_filtered.count()

    paginator = Paginator(in_clinic_appointments_filtered, 10)
    page_number = request.GET.get('page', 1)

    paginator2 = Paginator(finished_in_clinic_appointments_filtered, 10)
    page_number2 = request.GET.get('page2', 1)

    paginator3 = Paginator(active_in_clinic_appointments_filtered, 10)
    page_number3 = request.GET.get('page3', 1)

    paginator4 = Paginator(online_appointments_filtered, 10)
    page_number4 = request.GET.get('page4', 1)

    paginator5 = Paginator(finished_online_appointments_filtered, 10)
    page_number5 = request.GET.get('page5', 1)

    paginator6 = Paginator(active_online_appointments_filtered, 10)
    page_number6 = request.GET.get('page6', 1)

    try:
        appointments_page = paginator.page(page_number)
    except PageNotAnInteger:
        appointments_page = paginator.page(1)
    except EmptyPage:
        appointments_page = paginator.page(paginator.num_pages)

    try:
        appointments_page2 = paginator2.page(page_number2)
    except PageNotAnInteger:
        appointments_page2 = paginator2.page(1)
    except EmptyPage:
        appointments_page2 = paginator2.page(paginator2.num_pages)

    try:
        appointments_page3 = paginator3.page(page_number3)
    except PageNotAnInteger:
        appointments_page3 = paginator3.page(1)
    except EmptyPage:
        appointments_page3 = paginator3.page(paginator3.num_pages)

    try:
        appointments_page4 = paginator4.page(page_number4)
    except PageNotAnInteger:
        appointments_page4 = paginator4.page(1)
    except EmptyPage:
        appointments_page4 = paginator4.page(paginator4.num_pages)

    try:
        appointments_page5 = paginator5.page(page_number5)
    except PageNotAnInteger:
        appointments_page5 = paginator5.page(1)
    except EmptyPage:
        appointments_page5 = paginator5.page(paginator5.num_pages)

    try:
        appointments_page6 = paginator6.page(page_number6)
    except PageNotAnInteger:
        appointments_page6 = paginator6.page(1)
    except EmptyPage:
        appointments_page6 = paginator6.page(paginator6.num_pages)

    # Compute the custom page range
    custom_page_range = get_custom_page_range(appointments_page.number, paginator.num_pages)
    custom_page_range2 = get_custom_page_range(appointments_page2.number, paginator2.num_pages)
    custom_page_range3 = get_custom_page_range(appointments_page3.number, paginator3.num_pages)
    custom_page_range4 = get_custom_page_range(appointments_page4.number, paginator4.num_pages)
    custom_page_range5 = get_custom_page_range(appointments_page5.number, paginator5.num_pages)
    custom_page_range6 = get_custom_page_range(appointments_page6.number, paginator6.num_pages)

    context  = {
        'appointments': appointments,
        'active_in_clinic_appointments_filtered': active_in_clinic_appointments_filtered,
        'finished_in_clinic_appointments_filtered': finished_in_clinic_appointments_filtered,
        'active_online_appointments_filtered': active_online_appointments_filtered,
        'finished_online_appointments_filtered': finished_online_appointments_filtered,
        'total_appointments': total_appointments,
        'finished_appointments': finished_appointments,
        'active_appointments': active_appointments,
        'in_clinic_appointments': in_clinic_appointments,
        'online_appointments': online_appointments,
        'current_date': current_time.strftime('%d %b %Y'),
        'today': today,
        'now_time': now_time,
        'appointments_page': appointments_page,  
        'paginator': paginator,
        'custom_page_range': custom_page_range,
        'appointments_page2': appointments_page2,  
        'paginator2': paginator2,
        'custom_page_range2': custom_page_range2,
        'appointments_page3': appointments_page3,  
        'paginator3': paginator3,
        'custom_page_range3': custom_page_range3,
        'appointments_page4': appointments_page4,  
        'paginator4': paginator4,
        'custom_page_range4': custom_page_range4,
        'appointments_page5': appointments_page5,  
        'paginator5': paginator5,
        'custom_page_range5': custom_page_range5,
        'appointments_page6': appointments_page6,  
        'paginator6': paginator6,
        'custom_page_range6': custom_page_range6,
    }

    return render(request, 'appointments/client_appointments.html', context)

def client_profile(request):
    try:
        client = request.user.client_profile  
    except Client.DoesNotExist:
        messages.error(request, "Client profile not found.")
    
    return render(request, 'appointments/client_profile.html', {"client" : client})

def doctor_profile(request):
    try:
        doctor = request.user.doctor_profile
    except Doctor.DoesNotExist:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_profile')

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    hours = list(range(24))
    minutes = list(range(0, 60, 10))

    # Create a list of availability items
    availability_list = []
    for day in days:
        day_lower = day.lower()
        availability_list.append({
            'day': day,                   # e.g. "Monday"
            'day_lower': day_lower,       # e.g. "monday"
            'start': getattr(doctor, f"{day_lower}_start", None),
            'end': getattr(doctor, f"{day_lower}_end", None),
        })

    duration_list = [i for i in range(10, 121, 10)] 

    context = {
        "doctor": doctor,
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "availability_list": availability_list,
        'duration_list': duration_list,
    }

    return render(request, 'appointments/doctor_profile.html', context)

@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(ChatSession, pk=chat_id)
    user = request.user

    if hasattr(user, 'doctor_profile') and user == chat.doctor.user:
        user_role = 'doctor'
        partner = chat.client
        chat.read_by_doctor = True
        chat.save()
    elif hasattr(user, 'client_profile') and user == chat.client.user:
        user_role = 'client'
        partner = chat.doctor
        chat.read_by_client = True
        chat.save()
    else:
        return HttpResponseForbidden("You are not part of this conversation.")

    messages_qs = chat.messages.order_by('created_at')

    # Handle POST message creation
    if request.method == 'POST':
        msg_content = request.POST.get('message', '')
        attached_file = request.FILES.get('attachment')  # <-- your file

        if hasattr(user, 'doctor_profile'):
            chat.read_by_doctor = True
            chat.read_by_client = False
        if hasattr(user, 'client_profile'):
            chat.read_by_client = True
            chat.read_by_doctor = False
        
        chat.save()

        if msg_content.strip() or attached_file:
            ChatMessage.objects.create(
                chat=chat,
                sender=user,
                sender_role=user_role,
                content=msg_content,
                attachment=attached_file,
            )
            return redirect('chat_detail', chat_id=chat_id)

    # Build contacts and new_chat_contacts lists (you can extract this into a helper function)
    contacts = []
    new_chat_contacts = []

    # Example logic (you would replicate your previous logic here)
    # For instance, if user is a doctor:
    try:
        doctor = user.doctor_profile
    except Doctor.DoesNotExist:
        doctor = None
    try:
        client = user.client_profile
    except Client.DoesNotExist:
        client = None

    if doctor:
        chat_sessions = ChatSession.objects.filter(doctor=doctor)
        # Build contacts list
        for c in chat_sessions:
            contacts.append({
                'chat_id': c.id,
                'partner_name': c.client.user.username,
                'partner_photo': c.client.profile_picture,
                'last_message': c.messages.order_by('-created_at').first().content if c.messages.exists() else "",
            })
        # Build new_chat_contacts from your logic
        # ...
    elif client:
        chat_sessions = ChatSession.objects.filter(client=client)
        for c in chat_sessions:
            contacts.append({
                'chat_id': c.id,
                'partner_name': c.doctor.user.username,
                'partner_photo': c.doctor.profile_picture,
                'last_message': c.messages.order_by('-created_at').first().content if c.messages.exists() else "",
            })
        # Build new_chat_contacts accordingly
        # ...

    context = {
        'chat': chat,
        'messages': messages_qs,
        'selected_user': partner,
        'user_role': user_role,
        'user': user,
        'contacts': contacts,
        'new_chat_contacts': new_chat_contacts,
    }

    return render(request, 'appointments/message_chat.html', context)

@login_required
def chat_detail_from_doctor_profile(request, username):
    try:
        client = request.user.client_profile
    except Client.DoesNotExist:
        client = None

    doctor = get_object_or_404(Doctor, user__username=username)
    
    chat_session = ChatSession.objects.filter(client=client, doctor=doctor).first()
    
    return redirect('chat_detail', chat_id=chat_session.id)
    

@login_required
def start_new_chat(request):
    if request.method == 'POST':
        # Determine if the current user is a doctor or a client
        try:
            doctor = request.user.doctor_profile
        except Doctor.DoesNotExist:
            doctor = None

        try:
            client = request.user.client_profile
        except Client.DoesNotExist:
            client = None

        # Get the selected contact ID from the form
        selected_username = request.POST.get('contact_username')
        if not selected_username:
            messages.error(request, "No contact selected.")

        # If the user is a doctor, then the selected contact should be a client
        if doctor:
            try:
                selected_client = Client.objects.get(user__username=selected_username)
            except Client.DoesNotExist:
                messages.error(request, "Selected client does not exist.")
                return redirect('message_chat')
            # Check if a chat session already exists
            chat = ChatSession.objects.filter(doctor=doctor, client=selected_client).first()
            if not chat:
                chat = ChatSession.objects.create(doctor=doctor, client=selected_client)

            chat_message = ChatMessage.objects.create(chat=chat, sender=request.user, sender_role='doctor', content="Conversation initiated.")
        # If the user is a client, then the selected contact should be a doctor
        elif client:
            try:
                selected_doctor = Doctor.objects.get(user__username=selected_username)
            except Doctor.DoesNotExist:
                messages.error(request, "Selected doctor does not exist.")
                return redirect('message_chat')
            chat = ChatSession.objects.filter(doctor=selected_doctor, client=client).first()
            if not chat:
                chat = ChatSession.objects.create(doctor=selected_doctor, client=client)

            chat_message = ChatMessage.objects.create(chat=chat, sender=request.user, sender_role='client', content="Conversation initiated.")
        else:
            messages.error(request, "User is neither a doctor nor a client.")
            return redirect('message_chat')

        # At this point, a chat session exists.
        # Redirect to the main message_chat view where the new chat will appear in contacts.
        return redirect('message_chat')
    else:
        # For GET requests, simply redirect to the main chat view.
        return redirect('message_chat')

@login_required
def filter_chats(request):
    
    user = request.user

    # Retrieve filter criteria from GET parameters
    order = request.GET.get('order')              # Expected: "asc" or "desc"
    message_status = request.GET.get('message_status')  # Expected: "read" or "unread"

    # Determine the user role and filter chats accordingly
    if hasattr(user, 'doctor_profile'):
        # Filter chats where the user is the doctor
        chats = ChatSession.objects.filter(doctor=user.doctor_profile)
        # Annotate each chat with the time of its latest message
        chats = chats.annotate(last_msg_time=Max('messages__created_at'))
        if message_status:
            if message_status == 'unread':
                chats = chats.filter(read_by_doctor=False)
            elif message_status == 'read':
                chats = chats.filter(read_by_doctor=True)
    elif hasattr(user, 'client_profile'):
        # Filter chats where the user is the client
        chats = ChatSession.objects.filter(client=user.client_profile)
        chats = chats.annotate(last_msg_time=Max('messages__created_at'))
        if message_status:
            if message_status == 'unread':
                chats = chats.filter(read_by_client=False)
            elif message_status == 'read':
                chats = chats.filter(read_by_client=True)
    else:
        # If the user is neither, return an empty queryset.
        chats = ChatSession.objects.none()

    # Order the chats by the annotated latest message time.
    if order == 'asc':
        chats = chats.order_by('last_msg_time')
    else:  # Default to descending order if order is "desc" or not provided.
        chats = chats.order_by('-last_msg_time')

    # Build a list of chat contacts to pass to the template.
    contacts = []
    for chat in chats:
        if hasattr(user, 'doctor_profile'):
            partner_name = chat.client.user.username
            partner_photo = chat.client.profile_picture
        else:
            partner_name = chat.doctor.user.username
            partner_photo = chat.doctor.profile_picture
        # Get the last message (if any)
        last_message = chat.messages.order_by('-created_at').first()
        contacts.append({
            'chat_id': chat.id,
            'partner_name': partner_name,
            'partner_photo': partner_photo,
            'last_message': last_message.content if last_message else "",
        })

    context = {
        'contacts': contacts,
        'order': order,
        'message_status': message_status,
    }

    return render(request, 'appointments/message_chat.html', context)

def contact(request):
    return render(request, 'appointments/contact.html')

def plus_payment(request):
    return render(request, 'appointments/plus_payment.html',
     {    "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY   })

def normal_payment(request):
    return render(request, 'appointments/normal_payment.html', 
    {    "stripe_publishable_key": settings.STRIPE_PUBLISHABLE_KEY   }
    )

def free_payment(request):
    return render(request, 'appointments/free_payment.html')

def subscription(request):
    return render(request, 'appointments/subscription.html')

@login_required
def message_chat(request):
    try:
        doctor = request.user.doctor_profile  # if there's a OneToOne from Doctor to User
    except Doctor.DoesNotExist:
        doctor = None

    try:
        client = request.user.client_profile  # if there's a OneToOne from Client to User
    except Client.DoesNotExist:
        client = None

    clients_only_one_time = []
    doctors_only_one_time = []

    # Gather all chat sessions for this user, either as doctor or client
    if doctor:
        # Chat sessions where the doctor is me
        chat_sessions = ChatSession.objects.filter(doctor=doctor)
        appointments = Appointment.objects.filter(doctor_contact=doctor.contact)
        clients = Client.objects.all()

        clients_only_one_time = []

        for client in clients:
            for appointment in appointments:
                if client.id == appointment.client_id:
                    clients_only_one_time.append(client)
                    break
        
    elif client:
        # Chat sessions where the client is me
        chat_sessions = ChatSession.objects.filter(client=client)
        appointments = Appointment.objects.filter(client_contact=client.contact)
        doctors = Doctor.objects.all()

        doctors_only_one_time = []

        for doctor in doctors:
            for appointment in appointments:
                if doctor.id == appointment.doctor_id:
                    doctors_only_one_time.append(doctor)
                    break
    else:
        # If user is neither a recognized doctor nor client,
        # you might handle an error or return an empty list
        chat_sessions = ChatSession.objects.none()

    query = request.GET.get('q', '')

    #print(doctors_only_one_time)

    # Build a list of "contacts" to render in the template
    contacts = []

    for chat in chat_sessions:
        
        # Figure out who the "other" person is in this chat
        if doctor:
            # I'm the doctor; the other is the chat.client
            partner_name = chat.client.user.username  # or a field on `Client`
            # You could also store a profile picture for the client if you want
            partner_photo = chat.client.profile_picture  # placeholder

            for client in clients_only_one_time:
                if client.id == chat.client.id:
                    clients_only_one_time.remove(client)
        elif client:
            # I'm the client; the other is the chat.doctor
            partner_name = chat.doctor.user.username
            partner_photo = chat.doctor.profile_picture

            for doctor in doctors_only_one_time:
                if doctor.id == chat.doctor.id:
                    doctors_only_one_time.remove(doctor)

        # Get the last message (most recent) for snippet
        last_msg = chat.messages.order_by('-created_at').first()
        last_msg_text = last_msg.content if last_msg else ""

        contacts.append({
            'chat_id': chat.id,
            'partner_name': partner_name,
            'partner_photo': partner_photo,
            'last_message': last_msg_text,
        })

    if query:
        contacts_filtered = []

        for contact in contacts:
            if query.lower() in contact['partner_name'].lower():
                contacts_filtered.append(contact)

        contacts = contacts_filtered

    new_chat_contacts = []

    if doctor:
        for client in clients_only_one_time:
            client_username = client.user.username
            client_profile_picture = client.profile_picture

            new_chat_contacts.append({
                'username': client_username,
                'profile_picture': client.profile_picture,
            })
    
    if client:
        for doctor in doctors_only_one_time:
            doctor_username = doctor.user.username
            doctor_profile_picture = doctor.profile_picture

            new_chat_contacts.append({
                'username': doctor_username,
                'profile_picture': doctor.profile_picture,
            })

    print(contacts)

    return render(request, 'appointments/message_chat.html', { 'contacts': contacts, 'new_chat_contacts': new_chat_contacts} )

def forgot_password(request):
    return render(request, 'appointments/forgot_password.html')

def app_settings(request):
    setting, created = NotificationSetting.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        custom_theme = bool(request.POST.get('custom_theme'))
        selected_theme = request.POST.get('theme', 'light')
        bg_color = request.POST.get('background_color', '#FFFFFF')
        txt_color = request.POST.get('text_color', '#000000')

        if custom_theme:
            setting.theme = 'custom'
            setting.background_color = bg_color
            setting.text_color = txt_color
        else:
            setting.theme = selected_theme
            if selected_theme == 'dark':
                setting.background_color = '#000000'
                setting.text_color = '#FFFFFF'
            else:
                setting.background_color = '#FFFFFF'
                setting.text_color = '#000000'

        setting.email_notifications = bool(request.POST.get('emailNotifications'))
        setting.sms_notifications = bool(request.POST.get('smsNotifications'))
        setting.site_notifications = bool(request.POST.get('inAppNotifications'))
        setting.push_notifications = bool(request.POST.get('pushNotifications'))

        setting.font_family = request.POST.get('font_family', 'Arial')
        setting.font_size = int(request.POST.get('font_size', 16))
        setting.font_weight = request.POST.get('font_weight', 'normal')
        
        setting.save()

        return redirect('settings')

    return render(request, 'appointments/settings.html', {
        'setting': setting
    })

def search_results(request):
    query = request.GET.get('q', '')

    return render(request, 'appointments/search_results.html', {'query': query})

def view_doctor_profile_by_cli(request, username):
    doctor = get_object_or_404(Doctor, user__username=username)
    
    try:
        client = request.user.client_profile
    except AttributeError:
        return JsonResponse({'error': 'Client profile not found.'}, status=400)

    user_has_appointment = False

    if request.user.is_authenticated:
        # Use the foreign key relationships instead of the integer ID fields
        user_has_appointment = Appointment.objects.filter(
            doctor_fk=doctor, 
            client_fk=client,
        ).exists()

        print(user_has_appointment)

    return render(request, 'appointments/view_doctor_profile_by_cli.html', {'doctor': doctor, 'user_has_appointment': user_has_appointment })

@login_required
def check_new_messages(request, chat_id):
    """
    API endpoint to check for new messages in a chat.
    Returns JSON with new messages since the last_id provided.
    """
    chat = get_object_or_404(ChatSession, pk=chat_id)
    last_id = request.GET.get('last_id', 0)
    
    # Get messages newer than the last_id
    new_messages = ChatMessage.objects.filter(
        chat=chat,
        id__gt=last_id
    ).order_by('created_at')
    
    # Format messages for JSON response
    messages_data = []
    for msg in new_messages:
        message_data = {
            'id': msg.id,
            'content': msg.content,
            'is_sender': msg.sender == request.user,
            'created_at': msg.created_at.isoformat()
        }
        
        # Add attachment URL if exists
        if msg.attachment:
            message_data['attachment'] = msg.attachment.url
            
        messages_data.append(message_data)
    
    return JsonResponse({
        'new_messages': messages_data
    })

@login_required
def delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)
        
        # Check if the comment belongs to the current user
        if comment.user == request.user:
            # Get the doctor username for redirection
            doctor_username = comment.doctor.user.username
            comment.delete()
            messages.success(request, "Your comment has been deleted successfully.")
            return redirect('view_doctor_profile_by_cli', username=doctor_username)
        else:
            messages.error(request, "You don't have permission to delete this comment.")
            return redirect('home')
    except Comment.DoesNotExist:
        messages.error(request, "Comment not found.")
        return redirect('home')



