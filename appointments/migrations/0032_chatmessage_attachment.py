# Generated by Django 5.1.5 on 2025-02-25 20:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0031_chatsession_chatmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='attachment',
            field=models.FileField(blank=True, null=True, upload_to='chat_attachments/'),
        ),
    ]
