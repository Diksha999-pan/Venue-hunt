from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('organizer', 'Event Organizer'),
        ('vendor', 'Venue Owner'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', 
                                      default='profile_pics/default-profile.png',
                                      null=True, blank=True)
    
    def __str__(self):
        return self.username

    def get_profile_picture_url(self):
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return self.profile_picture.url
        return self.profile_picture.field.default
