from django import forms
from .models import Booking
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime

class BookingForm(forms.ModelForm):
    event_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Select the date for your event"
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text="Select the start time"
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        help_text="Select the end time"
    )
    
    is_advance_payment = forms.BooleanField(
        required=False,
        initial=False,
        label="Pay 20% Advance Only",
        help_text="Check this to pay 20% advance now and the remaining amount later",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Booking
        fields = ['event_date', 'start_time', 'end_time', 'number_of_guests', 
                 'event_category', 'event_type', 'special_requests', 'is_advance_payment']
        widgets = {
            'number_of_guests': forms.NumberInput(attrs={'class': 'form-control'}),
            'event_category': forms.Select(attrs={'class': 'form-control'}),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'special_requests': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        event_date = cleaned_data.get('event_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        number_of_guests = cleaned_data.get('number_of_guests')
        event_type = cleaned_data.get('event_type')
        venue = getattr(self.instance, 'venue', None)

        if not venue:
            raise ValidationError("Venue is required")

        # Check if date is not in the past
        if event_date and event_date < timezone.now().date():
            raise ValidationError("Event date cannot be in the past")

        # Check if end time is after start time
        if start_time and end_time and start_time >= end_time:
            raise ValidationError("End time must be after start time")

        # Check if number of guests is within venue capacity
        if number_of_guests and venue.capacity < number_of_guests:
            raise ValidationError(
                f"Number of guests cannot exceed venue capacity of {venue.capacity}"
            )
            
        # Validate that the event type is supported by the venue
        if event_type and venue.supported_events != 'other' and event_type != venue.supported_events:
            raise ValidationError(
                f"This venue only supports '{dict(venue._meta.get_field('supported_events').choices).get(venue.supported_events)}' events"
            )

        # Check if venue is available for the selected date and time
        if event_date and start_time and end_time:
            conflicts = Booking.objects.filter(
                venue=venue,
                event_date=event_date,
                status='confirmed'
            ).exclude(pk=self.instance.pk)

            for booking in conflicts:
                if (start_time <= booking.end_time and 
                    end_time >= booking.start_time):
                    raise ValidationError(
                        "The venue is already booked during this time period"
                    )

        return cleaned_data
