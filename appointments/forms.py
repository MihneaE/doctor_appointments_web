from django import forms
from .models import Doctor

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['profile_picture']