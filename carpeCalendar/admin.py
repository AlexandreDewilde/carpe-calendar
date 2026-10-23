from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from .models import Event
from .models import EventDates
from .models import Category
from .models import Place
from .models import AcademicPeriod

class EventAdmin(ModelAdmin):
    list_display = ['title', 'location', 'saved_location', 'organizer', 'category', 'validated', 'get_dates', 'form_link', 'facebook_link', 'email_organizer', 'created_at']
    list_editable = ["validated"]
    list_filter = ["validated", "category", "created_at", "updated_at"]
    search_fields = ["title", "location"]
    actions = ["validate_selected_events", "invalidate_selected_events", "renew_edit_links"]
    readonly_fields = ["edit_link"]
    exclude = ["edit_token"]
    list_per_page = 10

    @admin.action(description="Validate selected events")
    def validate_selected_events(self, request, queryset):
        queryset.update(validated=True)

    @admin.action(description="Invalidate selected events")
    def invalidate_selected_events(self, request, queryset):
        queryset.update(validated=False)

    @admin.action(description="Create a new organizer edit link")
    def renew_edit_links(self, request, queryset):
        for event in queryset:
            event.renew_edit_token()
            event.save(update_fields=["edit_token", "edit_token_expires_at"])

    @admin.display(description="Organizer edit link")
    def edit_link(self, obj):
        # Send this link to an organizer who lost theirs; use the "new edit link" action if it expired
        if not obj.edit_token:
            return "-"
        url = reverse("edit_event", args=[obj.id, obj.edit_token])
        return format_html('<a href="{}">{}</a> (expires {})', url, url, obj.edit_token_expires_at)

    def get_dates(self, obj):
        return "|\n".join([str(date) for date in obj.eventdates_set.all()])

class EventDatesAdmin(ModelAdmin):
    list_display = ['event', 'start', 'end']
    list_filter = ['event']
    search_fields = ['event']
    list_editable = ['start', 'end']


class CategoryAdmin(ModelAdmin):
    list_display = ['name', 'parent']
    list_filter = ['parent']
    list_editable = ['parent']

class PlaceAdmin(ModelAdmin):
    list_display = ['name', 'address', 'latitude', 'longitude']
    list_editable = ['address', 'latitude', 'longitude']

class AcademicPeriodAdmin(ModelAdmin):
    list_display = ['name', 'start', 'end', 'numbered', 'first_week_number']
    list_filter = ['name']

admin.site.register(Event, EventAdmin)
admin.site.register(EventDates, EventDatesAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Place, PlaceAdmin)
admin.site.register(AcademicPeriod, AcademicPeriodAdmin)
