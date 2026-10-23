import datetime
import zoneinfo
from unittest import mock

import icalendar

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from carpeCalendar.models import Event, EventDates, Category, Place, AcademicPeriod

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

    def test_events_without_saved_location(self):
        self.event.saved_location = None
        self.event.save()
        response = self.client.get('/events/', {'start': '2026-10-19T00:00:00+02:00', 'end': '2026-10-26T00:00:00+01:00'})
        self.assertEqual(response.json()[0]['saved_location'], {'name': 'Autre'})

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
            'category': self.category.id,
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


class CategoryTreeTests(TestCase):

    def test_subcategories_are_nested_in_filters_and_form(self):
        sport = Category.objects.create(name='Sport', description='')
        Category.objects.create(name='Football', parent=sport, description='')
        Category.objects.create(name='Concert', description='')

        response = self.client.get('/calendar/')
        tree = [(category.name, [child.name for child, _ in children]) for category, children in response.context['category_tree']]
        self.assertEqual(tree, [('Concert', []), ('Sport', ['Football'])])

        response = self.client.get('/add-event')
        labels = [label for _, label in response.context['categories']]
        self.assertEqual(labels, ['Concert', 'Sport', '\u00a0\u00a0\u00a0↳ Football'])


class IcsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name='Soirée', description='')
        cls.event = Event.objects.create(title='Concert, jazz', location='Aula Magna', category=category, validated=True)
        cls.date = EventDates.objects.create(
            event=cls.event,
            start=datetime.datetime(2026, 11, 2, 20, 0, tzinfo=BRUSSELS),
            end=datetime.datetime(2026, 11, 2, 23, 0, tzinfo=BRUSSELS),
        )
        Event.objects.create(title='Pending', location='Aula Magna', category=category)

    def test_event_ics(self):
        response = self.client.get(f'/event/{self.event.id}/ics')
        self.assertEqual(response['Content-Type'], 'text/calendar; charset=utf-8')
        calendar = icalendar.Calendar.from_ical(response.content)
        [event] = calendar.walk('VEVENT')
        self.assertEqual(str(event['summary']), 'Concert, jazz')
        self.assertEqual(event.decoded('dtstart'), self.date.start)
        self.assertIn(f'/event/{self.event.id}/', str(event['url']))

    def test_pending_event_ics_is_not_found(self):
        pending = Event.objects.get(title='Pending')
        self.assertEqual(self.client.get(f'/event/{pending.id}/ics').status_code, 404)

    @mock.patch('django.utils.timezone.now', return_value=datetime.datetime(2026, 10, 24, tzinfo=datetime.UTC))
    def test_calendar_feed(self, _):
        response = self.client.get('/calendar.ics')
        calendar = icalendar.Calendar.from_ical(response.content)
        self.assertEqual([str(event['summary']) for event in calendar.walk('VEVENT')], ['Concert, jazz'])


class EditLinkTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Soirée', description='')
        Place.objects.create(name='Autre')

    def submit(self, url, **fields):
        data = {
            'title': 'Quiz',
            'organizer': 'Carpe',
            'location': 'Aula Magna',
            'category': self.category.id,
            'email_organizer': 'orga@example.com',
            'start': '2026-11-02T20:00',
            'end': '2026-11-02T23:00',
        } | fields
        return self.client.post(url, data)

    @override_settings(EMAIL_HOST='smtp.example.com')
    def test_new_event_gets_an_edit_link_by_email(self):
        response = self.submit('/add-event')
        event = Event.objects.get(title='Quiz')
        self.assertTrue(event.edit_token)
        self.assertAlmostEqual(event.edit_token_expires_at, timezone.now() + datetime.timedelta(days=30), delta=datetime.timedelta(minutes=1))
        edit_url = f'/event/{event.id}/edit/{event.edit_token}'
        self.assertContains(response, edit_url)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['orga@example.com'])
        self.assertIn(edit_url, mail.outbox[0].body)

    def test_no_email_without_email_server(self):
        self.submit('/add-event')
        self.assertEqual(len(mail.outbox), 0)

    def test_organizer_edits_event(self):
        self.submit('/add-event')
        event = Event.objects.get(title='Quiz')
        event.validated = True
        event.save()
        edit_url = f'/event/{event.id}/edit/{event.edit_token}'

        response = self.client.get(edit_url)
        self.assertContains(response, 'value="Quiz"')
        self.assertContains(response, 'value="2026-11-02T20:00"')

        response = self.submit(edit_url, title='Quiz musical', start='2026-11-03T20:00', end='2026-11-03T22:00')
        self.assertContains(response, 'Vos modifications ont été enregistrées')
        event.refresh_from_db()
        self.assertEqual(event.title, 'Quiz musical')
        self.assertFalse(event.validated)
        self.assertEqual([date.start for date in event.eventdates_set.all()], [datetime.datetime(2026, 11, 3, 20, 0, tzinfo=BRUSSELS)])
        self.assertEqual(Event.objects.count(), 1)

    def test_wrong_or_expired_token_is_refused(self):
        self.submit('/add-event')
        event = Event.objects.get(title='Quiz')
        self.assertEqual(self.client.get(f'/event/{event.id}/edit/wrong').status_code, 403)

        event.edit_token_expires_at = timezone.now() - datetime.timedelta(seconds=1)
        event.save()
        self.assertEqual(self.client.get(f'/event/{event.id}/edit/{event.edit_token}').status_code, 403)
        response = self.submit(f'/event/{event.id}/edit/{event.edit_token}', title='Hacked')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Event.objects.filter(title='Hacked').exists())


class WeekImageTests(TestCase):

    def test_week_poster(self):
        category = Category.objects.create(name='Soirée', description='')
        AcademicPeriod.objects.create(name='S', start=datetime.date(2026, 9, 14), end=datetime.date(2026, 12, 20), numbered=True)
        event = Event.objects.create(title='Quiz', location='Grand-Place', category=category, validated=True)
        EventDates.objects.create(
            event=event,
            start=datetime.datetime(2026, 10, 23, 20, 0, tzinfo=BRUSSELS),
            end=datetime.datetime(2026, 10, 23, 23, 0, tzinfo=BRUSSELS),
        )
        pending = Event.objects.create(title='Pending', location='Grand-Place', category=category)
        EventDates.objects.create(
            event=pending,
            start=datetime.datetime(2026, 10, 23, 20, 0, tzinfo=BRUSSELS),
            end=datetime.datetime(2026, 10, 23, 23, 0, tzinfo=BRUSSELS),
        )

        response = self.client.get('/week-image/', {'date': '2026-10-21'})
        self.assertEqual(response.context['monday'], datetime.date(2026, 10, 19))
        self.assertEqual(response.context['week_label'], 'S6')
        self.assertContains(response, 'Vendredi 23 octobre')
        self.assertContains(response, '20:00')
        self.assertContains(response, 'Quiz')
        self.assertNotContains(response, 'Pending')


class ProgressiveWebAppTests(TestCase):

    def test_manifest(self):
        response = self.client.get('/manifest.webmanifest')
        self.assertEqual(response['Content-Type'], 'application/manifest+json')
        manifest = response.json()
        self.assertEqual(manifest['start_url'], '/calendar/')
        self.assertEqual({icon['sizes'] for icon in manifest['icons']}, {'192x192', '512x512'})

    def test_service_worker_served_from_root(self):
        response = self.client.get('/sw.js')
        self.assertEqual(response['Content-Type'], 'application/javascript')
        self.assertEqual(response['Cache-Control'], 'no-cache')
        self.assertContains(response, 'const OFFLINE_PAGES = ["/calendar/"]')

    def test_pages_link_manifest_and_register_worker(self):
        response = self.client.get('/calendar/')
        self.assertContains(response, '<link rel="manifest" href="/manifest.webmanifest">')
        self.assertContains(response, 'navigator.serviceWorker.register("/sw.js")')


class TranslationTests(TestCase):

    def test_french_by_default(self):
        response = self.client.get('/calendar/')
        self.assertContains(response, '<html lang="fr">')
        self.assertContains(response, 'Ajouter un événement')

    def test_english_from_browser_language(self):
        response = self.client.get('/calendar/', headers={'Accept-Language': 'en-GB,en;q=0.9'})
        self.assertContains(response, '<html lang="en">')
        self.assertContains(response, 'Add an event')
        self.assertContains(response, 'Subscribe to the calendar')

    def test_language_switcher(self):
        response = self.client.post('/i18n/setlang/', {'language': 'en', 'next': '/add-event'})
        self.assertRedirects(response, '/add-event', fetch_redirect_response=False)
        response = self.client.get('/add-event')
        self.assertContains(response, 'Basic information')
