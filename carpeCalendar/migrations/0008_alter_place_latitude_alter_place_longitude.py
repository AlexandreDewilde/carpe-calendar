# Generated by Django 5.0.7 on 2024-07-22 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carpeCalendar', '0007_place_parent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='place',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='place',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
    ]