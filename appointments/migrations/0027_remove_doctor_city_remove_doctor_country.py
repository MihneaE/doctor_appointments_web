# Generated by Django 5.1.5 on 2025-02-20 13:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0026_doctor_city_doctor_country'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='doctor',
            name='city',
        ),
        migrations.RemoveField(
            model_name='doctor',
            name='country',
        ),
    ]
