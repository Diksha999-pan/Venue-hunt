from django.db import models
from django.conf import settings

class Venue(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    capacity = models.PositiveIntegerField()
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Amenities
    has_parking = models.BooleanField(default=False)
    has_wifi = models.BooleanField(default=False)
    has_sound_system = models.BooleanField(default=False)
    has_catering = models.BooleanField(default=False)
    
    # Event categories and types supported
    EVENT_CATEGORY_CHOICES = (
        ('formal', 'Formal'),
        ('informal', 'Informal'),
    )
    event_category = models.CharField(max_length=10, choices=EVENT_CATEGORY_CHOICES, default='informal')
    
    EVENT_TYPES = (
        # Formal Events
        ('conference', 'Conference'),
        ('business_meeting', 'Business Meeting'),
        ('product_launch', 'Product Launch'),
        ('seminar_workshop', 'Seminar & Workshop'),
        ('award_ceremony', 'Award Ceremony'),
        # Informal Events
        ('birthday_party', 'Birthday Party'),
        ('casual_gathering', 'Casual Get Together'),
        ('wedding', 'Wedding'),
        ('engagement', 'Engagement'),
        ('games_night', 'Games Night'),
        ('anniversary', 'Anniversary'),
        ('other', 'Other'),
    )
    supported_events = models.CharField(max_length=20, choices=EVENT_TYPES, default='other')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class VenueImage(models.Model):
    venue = models.ForeignKey(Venue, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='venue_images/')
    is_primary = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Image for {self.venue.name}"

class Review(models.Model):
    venue = models.ForeignKey(Venue, related_name='reviews', on_delete=models.CASCADE)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='review', null=True, blank=True)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        unique_together = ('venue', 'reviewer')
    
    def __str__(self):
        return f"Review for {self.venue.name} by {self.reviewer.username}"
