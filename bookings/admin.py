from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('venue', 'organizer', 'event_date', 'status', 'event_type', 'created_at')
    list_filter = ('status', 'event_type', 'event_date')
    search_fields = ('venue__name', 'organizer__username', 'special_requests')
    date_hierarchy = 'event_date'
