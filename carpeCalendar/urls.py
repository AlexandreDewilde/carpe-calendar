from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("calendar/", views.calendar, name="calendar"),
    path("event/<int:event_id>/", views.event, name="event"),
    path("events/", views.events, name="events"),
    path("add-event", views.add_event_page, name="add_event"),
    path("create-qr-code", views.create_qr_code, name="create_qr_code"),
]
