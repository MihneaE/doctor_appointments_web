# Generated by Django 5.1.5 on 2025-02-20 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0025_remove_doctor_city_remove_doctor_country'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='city',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='doctor',
            name='country',
            field=models.TextField(blank=True, null=True),
        ),
    ]
