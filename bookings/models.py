from django.db import models
from django.conf import settings

class Booking(models.Model):
    venue = models.ForeignKey('venues.Venue', on_delete=models.CASCADE)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    number_of_guests = models.PositiveIntegerField()
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    )
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_id = models.CharField(max_length=100, blank=True, null=True)  # Order ID
    transaction_id = models.CharField(max_length=100, blank=True, null=True)  # Payment ID
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Total booking amount
    is_advance_payment = models.BooleanField(default=False)  # True if only advance payment (20%)
    
    # Event categories
    EVENT_CATEGORY_CHOICES = (
        ('formal', 'Formal'),
        ('informal', 'Informal'),
    )
    event_category = models.CharField(max_length=10, choices=EVENT_CATEGORY_CHOICES, default='informal')
    
    # Event types
    EVENT_TYPE_CHOICES = (
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
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Booking for {self.venue.name} by {self.organizer.username}"

    class Meta:
        ordering = ['-created_at']
