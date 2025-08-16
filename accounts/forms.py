from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=[('organizer', 'Event Organizer'), ('vendor', 'Venue Owner')], required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'address', 'profile_picture', 'user_type', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.address = self.cleaned_data['address']
        user.user_type = self.cleaned_data['user_type']
        if self.cleaned_data.get('profile_picture'):
            user.profile_picture = self.cleaned_data['profile_picture']
        
        if commit:
            user.save()
        return user

class ProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    profile_picture = forms.ImageField(required=False, widget=forms.FileInput)

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone_number', 
                 'address', 'profile_picture')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make user_type read-only if it's already set
        if self.instance and self.instance.pk:
            # Add a read-only display of user type
            self.fields['user_type_display'] = forms.CharField(
                disabled=True,
                required=False,
                initial=self.instance.get_user_type_display(),
                label="Account Type"
            )
