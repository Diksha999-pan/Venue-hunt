from django.contrib import admin
from .models import Venue, VenueImage, Review

class VenueImageInline(admin.TabularInline):
    model = VenueImage
    extra = 1

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'capacity', 'price_per_person', 'supported_events', 'created_at')
    list_filter = ('supported_events', 'has_parking', 'has_wifi', 'has_sound_system', 'has_catering')
    search_fields = ('name', 'description', 'address')
    inlines = [VenueImageInline, ReviewInline]

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('venue', 'reviewer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('venue__name', 'reviewer__username', 'comment')
