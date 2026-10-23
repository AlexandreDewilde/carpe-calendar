import datetime

from django.db import migrations

# Periods previously hardcoded in calendar.js, for 2024-2025
PERIODS = [
    ("S", "2024-09-16", "2024-12-29", True, 0),
    ("Blocus", "2024-12-30", "2025-01-05", False, 1),
    ("Examens", "2025-01-13", "2025-02-02", False, 1),
    ("Congé", "2025-02-03", "2025-02-09", False, 1),
    ("S", "2025-02-10", "2025-04-27", True, 1),
    ("Congé", "2025-04-28", "2025-05-11", False, 1),
    ("S", "2025-05-12", "2025-05-25", True, 12),
    ("Blocus", "2025-05-26", "2025-06-08", False, 1),
    ("Examens", "2025-06-09", "2025-07-06", False, 1),
]


def seed(apps, schema_editor):
    AcademicPeriod = apps.get_model('carpeCalendar', 'AcademicPeriod')
    for name, start, end, numbered, first_week_number in PERIODS:
        AcademicPeriod.objects.create(
            name=name,
            start=datetime.date.fromisoformat(start),
            end=datetime.date.fromisoformat(end),
            numbered=numbered,
            first_week_number=first_week_number,
        )


def unseed(apps, schema_editor):
    AcademicPeriod = apps.get_model('carpeCalendar', 'AcademicPeriod')
    for name, start, end, _, _ in PERIODS:
        AcademicPeriod.objects.filter(name=name, start=start, end=end).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('carpeCalendar', '0015_academicperiod'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
