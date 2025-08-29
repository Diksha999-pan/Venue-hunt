from django import forms
from .models import Venue, VenueImage

class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ['name', 'description', 'address', 'latitude', 'longitude', 
                 'capacity', 'price_per_person', 'event_category', 'supported_events', 
                 'has_parking', 'has_wifi', 'has_sound_system', 'has_catering']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }
    
    # Add JavaScript to dynamically update supported_events options based on selected event_category
    class Media:
        js = ('js/venue_form.js',)
