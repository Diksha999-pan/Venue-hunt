from django import forms
from venues.models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 
                                             'placeholder': 'Share your experience with this venue...'}),
        }
