from django.db import models
from django.contrib.auth import get_user_model
from venues.models import Venue

class VenueSimilarityCache(models.Model):
    """Cache for venue similarity scores to avoid recomputing frequently"""
    source_venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='source_similarities')
    target_venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='target_similarities')
    similarity_score = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('source_venue', 'target_venue')
        indexes = [
            models.Index(fields=['source_venue', 'similarity_score']),
        ]

class UserVenueInteraction(models.Model):
    """Track user interactions with venues for personalized recommendations"""
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=20, choices=[
        ('view', 'Viewed'),
        ('book', 'Booked'),
        ('favorite', 'Favorited')
    ])
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
        ]
