# Generated by Django 5.1.1 on 2024-09-25 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpeCalendar', '0012_event_blind_friendly_event_deaf_friendly_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
