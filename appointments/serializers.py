from rest_framework import serializers
from .models import MedicalSpecialty

class MedicalSpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalSpecialty
        fields = '__all__'