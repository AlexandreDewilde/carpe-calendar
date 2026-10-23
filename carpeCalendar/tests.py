import datetime
import zoneinfo

from django.test import TestCase

from carpeCalendar.models import Event, EventDates, Category, Place

BRUSSELS = zoneinfo.ZoneInfo('Europe/Brussels')


class SmokeTests(TestCase):
    # Quick end-to-end checks of every page, so dependency updates can be validated in CI

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Soirée', description='')
        cls.other_place = Place.objects.create(name='Autre')
        cls.place = Place.objects.create(name='Grand-Place')
        cls.event = Event.objects.create(title='Validated event', location='Grand-Place', saved_location=cls.place, category=cls.category, validated=True)
        EventDates.objects.create(
            event=cls.event,
            start=datetime.datetime(2026, 10, 22, 20, 0, tzinfo=BRUSSELS),
            end=datetime.datetime(2026, 10, 22, 23, 0, tzinfo=BRUSSELS),
        )
        hidden = Event.objects.create(title='Pending event', location='Grand-Place', saved_location=cls.place, category=cls.category)
        EventDates.objects.create(
            event=hidden,
            start=datetime.datetime(2026, 10, 23, 20, 0, tzinfo=BRUSSELS),
            end=datetime.datetime(2026, 10, 23, 23, 0, tzinfo=BRUSSELS),
        )

    def test_calendar_page(self):
        response = self.client.get('/calendar/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Soirée')

    def test_events_only_returns_validated(self):
        response = self.client.get('/events/', {'start': '2026-10-19T00:00:00+02:00', 'end': '2026-10-26T00:00:00+01:00'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([event['title'] for event in response.json()], ['Validated event'])

    def test_event_page(self):
        response = self.client.get(f'/event/{self.event.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Validated event')

    def test_add_event_creates_pending_event(self):
        self.assertEqual(self.client.get('/add-event').status_code, 200)
        response = self.client.post('/add-event', {
            'title': 'New event',
            'organizer': 'Carpe',
            'location': 'Somewhere else',
            'category': 'Soirée',
            'start': '2026-11-02T20:00',
            'end': '2026-11-02T23:00',
        })
        self.assertContains(response, 'alert-success')
        event = Event.objects.get(title='New event')
        self.assertFalse(event.validated)
        self.assertEqual(event.saved_location, self.other_place)
        self.assertEqual(event.eventdates_set.count(), 1)

    def test_qr_code_page(self):
        self.assertEqual(self.client.get('/create-qr-code').status_code, 200)

    def test_admin_login_page(self):
        self.assertEqual(self.client.get('/admin/login/').status_code, 200)
