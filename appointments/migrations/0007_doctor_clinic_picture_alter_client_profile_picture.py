# Generated by Django 5.1.4 on 2024-12-29 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0006_doctor_date_of_birth_client'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='clinic_picture',
            field=models.ImageField(blank=True, null=True, upload_to='clinic_pictures/'),
        ),
        migrations.AlterField(
            model_name='client',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profile_pictures/'),
        ),
    ]
