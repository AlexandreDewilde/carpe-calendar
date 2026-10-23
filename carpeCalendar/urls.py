from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('calendar/', views.calendar, name='calendar'),
    path('event/<int:event_id>/', views.event, name='event'),
    path('event/<int:event_id>/ics', views.event_ics, name='event_ics'),
    path('calendar.ics', views.calendar_ics, name='calendar_ics'),
    path('events/', views.events, name='events'),
    path('add-event', views.add_event_page, name='add_event'),
    path('event/<int:event_id>/edit/<str:token>', views.edit_event, name='edit_event'),
    path('create-qr-code', views.create_qr_code, name='create_qr_code'),
    path('week-image/', views.week_image, name='week_image'),
    path('manifest.webmanifest', views.manifest, name='manifest'),
    path('sw.js', views.service_worker, name='service_worker'),
]
