import datetime
import urllib.parse
import zoneinfo
from collections import defaultdict

import icalendar
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.templatetags.static import static
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils import translation
from django.utils.translation import gettext as _

from carpeCalendar.models import Event, EventDates, Category, Place, AcademicPeriod
from carpeCalendar.forms import EventForm

def home(request):
    return redirect('calendar')

def category_tree():
    # Categories as (category, children) pairs, with children nested the same way
    children = defaultdict(list)
    for category in Category.objects.order_by('name'):
        children[category.parent_id].append(category)
    seen = set()

    def build(parent_id):
        tree = []
        for category in children[parent_id]:
            # Guard against a category set as its own ancestor in the admin
            if category.id not in seen:
                seen.add(category.id)
                tree.append((category, build(category.id)))
        return tree

    return build(None)

def category_choices(tree=None, depth=0):
    # Flattened tree for a <select>, children indented under their parent
    choices = []
    for category, children in (category_tree() if tree is None else tree):
        choices.append((category.id, "\u00a0\u00a0\u00a0" * depth + ("↳ " if depth else "") + category.name))
        choices += category_choices(children, depth + 1)
    return choices

def calendar(request):
    places = Place.objects.all()
    periods = list(AcademicPeriod.objects.values('name', 'start', 'end', 'numbered', 'first_week_number'))
    subscribe_url = 'webcal://' + request.get_host() + reverse('calendar_ics')
    return render(request, 'calendar.html', {'category_tree': category_tree(), 'places': places, 'periods': periods, 'subscribe_url': subscribe_url})

def events(request):
    start = request.GET.get('start', None)
    end = request.GET.get('end', None)
    end_dt = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S%z')
    start_dt = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S%z')
    if (end_dt - start_dt).days > 90:
        return JsonResponse([], safe=False)
    dates_lst = list(EventDates.objects.filter(Q(Q(start__range=[start, end]) | Q(end__range=[start, end]) | Q(start__lte=start, end__gte=end)), event__validated=True).select_related('event', 'event__category', 'event__saved_location'))
    events_lst = []
    for date in dates_lst:
        events_lst.append(model_to_dict(date.event) | {'start': date.start, 'end': date.end, 'category': model_to_dict(date.event.category), 'saved_location': model_to_dict(date.event.saved_location) if date.event.saved_location else {'name': 'Autre'}})
    return JsonResponse(events_lst, safe=False)

def event(request, event_id):
    event = Event.objects.get(id=event_id)
    if event.validated == False:
        return render(request, 'event.html', {'status': 403})
    dates = EventDates.objects.filter(event=event)
    return render(request, 'event.html', {'event': event, 'dates': dates, 'map_url': map_url(event)})

def map_url(event):
    # Google Maps search links open the maps app on phones
    place = event.saved_location
    if place and place.latitude is not None and place.longitude is not None:
        query = f"{place.latitude},{place.longitude}"
    elif place and place.address:
        query = place.address
    else:
        query = f"{event.location}, Louvain-la-Neuve"
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(query)

def ics_event(request, date):
    event = date.event
    url = request.build_absolute_uri(reverse('event', args=[event.id]))
    ics = icalendar.Event()
    ics.add('uid', f"eventdate-{date.id}@agenda.carpestudentem.be")
    ics.add('dtstamp', event.updated_at)
    ics.add('dtstart', date.start)
    ics.add('dtend', date.end)
    ics.add('summary', event.title)
    ics.add('location', event.location)
    ics.add('description', f"{event.description}\n\n{url}" if event.description else url)
    ics.add('url', url)
    ics.add('categories', [event.category.name])
    return ics

def ics_response(request, dates, filename):
    calendar = icalendar.Calendar()
    calendar.add('prodid', '-//CarpeStudentem//Agenda du Carpe//FR')
    calendar.add('version', '2.0')
    calendar.add('x-wr-calname', 'Agenda du Carpe')
    calendar.add('x-wr-timezone', 'Europe/Brussels')
    # Ask subscribed calendar apps to refresh every 6 hours
    calendar.add('refresh-interval', datetime.timedelta(hours=6), parameters={'VALUE': 'DURATION'})
    calendar.add('x-published-ttl', 'PT6H')
    for date in dates:
        calendar.add_component(ics_event(request, date))
    response = HttpResponse(calendar.to_ical(), content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def calendar_ics(request):
    # Subscription feed: from a month ago to a year ahead
    now = timezone.now()
    dates = EventDates.objects.filter(
        event__validated=True,
        end__gte=now - datetime.timedelta(days=30),
        start__lte=now + datetime.timedelta(days=365),
    ).select_related('event', 'event__category').order_by('start')
    return ics_response(request, dates, 'agenda-carpe.ics')

def event_ics(request, event_id):
    event = get_object_or_404(Event, id=event_id, validated=True)
    dates = event.eventdates_set.select_related('event', 'event__category').order_by('start')
    return ics_response(request, dates, f'evenement-{event.id}.ics')

def week_image(request):
    # Poster of a week's events, to download as an image for social media
    try:
        day = datetime.date.fromisoformat(request.GET.get('date', ''))
    except ValueError:
        day = timezone.localdate(timezone=BRUSSELS)
    monday = day - datetime.timedelta(days=day.weekday())
    sunday = monday + datetime.timedelta(days=6)
    week_start = datetime.datetime.combine(monday, datetime.time(), tzinfo=BRUSSELS)
    week_end = week_start + datetime.timedelta(days=7)
    dates = EventDates.objects.filter(
        event__validated=True, start__gte=week_start, start__lt=week_end,
    ).select_related('event').order_by('start')
    # Templates render times in UTC (TIME_ZONE), so convert to Brussels time here
    days = defaultdict(list)
    for date in dates:
        start = timezone.localtime(date.start, BRUSSELS)
        days[start.date()].append({'time': start.strftime('%H:%M'), 'event': date.event})
    return render(request, 'week_image.html', {
        'monday': monday,
        'sunday': sunday,
        'week_label': AcademicPeriod.week_label(monday),
        'days': sorted(days.items()),
        'previous_week': monday - datetime.timedelta(days=7),
        'next_week': monday + datetime.timedelta(days=7),
    })

def manifest(request):
    # Lets phones install the site as an app (progressive web app)
    return JsonResponse({
        'name': 'Agenda du Carpe',
        'short_name': 'Agenda Carpe',
        'description': _("Les événements de Louvain-la-Neuve, par le CarpeStudentem"),
        'lang': translation.get_language(),
        'start_url': reverse('calendar'),
        'scope': '/',
        'display': 'standalone',
        'background_color': '#ffffff',
        'theme_color': '#C52224',
        'icons': [
            {'src': static('images/icon-192.png'), 'sizes': '192x192', 'type': 'image/png'},
            {'src': static('images/icon-512.png'), 'sizes': '512x512', 'type': 'image/png'},
            {'src': static('images/icon-maskable-512.png'), 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
    }, content_type='application/manifest+json')

def service_worker(request):
    # Served from the root so it controls every page; never cached so updates reach users
    response = render(request, 'sw.js', content_type='application/javascript')
    response['Cache-Control'] = 'no-cache'
    return response

def create_qr_code(request):
    return render(request, 'create_qr_code.html')

EVENT_FIELDS = [
    'title', 'description', 'organizer', 'location', 'category', 'facebook_link', 'email_organizer', 'form_link',
    'pmr_friendly', 'deaf_friendly', 'blind_friendly', 'neurodiversity_friendly', 'granz_filled',
]
BRUSSELS = zoneinfo.ZoneInfo('Europe/Brussels')

def save_event(event, form, starts, ends):
    # Save the form's fields and replace the event's dates, all or nothing
    for field in EVENT_FIELDS:
        setattr(event, field, form.cleaned_data[field])
    location = form.cleaned_data['location']
    event.saved_location = Place.objects.filter(name__iexact=location).first() or Place.objects.get(name='Autre')
    dates = [
        (datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M').replace(tzinfo=BRUSSELS),
         datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M').replace(tzinfo=BRUSSELS))
        for start, end in zip(starts, ends)
    ]
    if not dates:
        raise ValueError("An event needs at least one date")
    with transaction.atomic():
        event.save()
        event.eventdates_set.all().delete()
        EventDates.objects.bulk_create([EventDates(event=event, start=start, end=end) for start, end in dates])

def edit_url(request, event):
    return request.build_absolute_uri(reverse('edit_event', args=[event.id, event.edit_token]))

def send_edit_link(request, event):
    if not (event.email_organizer and settings.EMAIL_HOST):
        return
    expires = timezone.localtime(event.edit_token_expires_at, BRUSSELS).strftime('%d/%m/%Y')
    # Sent in the language the organizer used to submit the event
    send_mail(
        _("Votre événement « %(title)s » sur l'Agenda du Carpe") % {'title': event.title},
        _(
            "Bonjour,\n\n"
            "Merci d'avoir ajouté « %(title)s » à l'Agenda du Carpe. Il sera visible dès qu'il aura été validé.\n\n"
            "Pour le modifier jusqu'au %(expires)s, utilisez ce lien (ne le partagez pas) :\n%(url)s\n\n"
            "L'équipe du CarpeStudentem"
        ) % {'title': event.title, 'expires': expires, 'url': edit_url(request, event)},
        None,
        [event.email_organizer],
        fail_silently=True,
    )

def event_form_values(event):
    # Form values of a saved event, in the same shape as submitted data: strings, with empty fields as ""
    initial = model_to_dict(event, fields=EVENT_FIELDS)
    dates = [
        (timezone.localtime(date.start, BRUSSELS).strftime('%Y-%m-%dT%H:%M'), timezone.localtime(date.end, BRUSSELS).strftime('%Y-%m-%dT%H:%M'))
        for date in event.eventdates_set.order_by('start')
    ]
    return {
        'initial': {key: '' if value is None else str(value) if key == 'category' else value for key, value in initial.items()},
        'dates': dates or [('', '')],
    }

def event_form_page(request, event=None):
    # Shared by adding an event and by the organizer editing it through their edit link
    context = {
        'categories': category_choices(),
        'places': list(Place.objects.exclude(name='Autre').values_list('name', flat=True)),
        'editing': event is not None,
        'dates': [('', '')],
    }
    if request.method != 'POST':
        if event is not None:
            context |= event_form_values(event)
        return render(request, 'add_event.html', context)

    data = request.POST
    starts = data.getlist('start')
    ends = data.getlist('end')
    form = EventForm(data)
    error_context = context | {'status': 'error', 'initial': data, 'dates': list(zip(starts, ends)) or [('', '')]}
    if not form.is_valid():
        return render(request, 'add_event.html', error_context | {'messages': form.errors})

    is_new = event is None
    if is_new:
        event = Event()
        event.renew_edit_token()
    # Organizer changes are reviewed again before they are published
    event.validated = False
    try:
        save_event(event, form, starts, ends)
    except Exception as e:
        print(e)
        return render(request, 'add_event.html', error_context)

    if is_new:
        send_edit_link(request, event)
    else:
        context |= event_form_values(event)
    return render(request, 'add_event.html', context | {
        'status': 'success' if is_new else 'updated',
        'edit_url': edit_url(request, event),
        'edit_expires_at': event.edit_token_expires_at,
        **model_to_dict(event),
    })

def add_event_page(request):
    return event_form_page(request)

def edit_event(request, event_id, token):
    event = get_object_or_404(Event, id=event_id)
    if not event.edit_token_is_valid(token):
        return render(request, 'edit_link_invalid.html', status=403)
    return event_form_page(request, event)
