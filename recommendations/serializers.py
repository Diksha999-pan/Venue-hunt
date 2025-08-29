from rest_framework import serializers
from venues.models import Venue

class RecommendedVenueSerializer(serializers.ModelSerializer):
    similarity_score = serializers.FloatField(read_only=True, required=False)
    average_rating = serializers.FloatField(read_only=True, required=False, default=0)
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Venue
        fields = [
            'id', 'name', 'description', 'address',
            'capacity', 'price_per_person', 'has_parking',
            'has_wifi', 'has_sound_system', 'has_catering',
            'average_rating', 'similarity_score', 'primary_image'
        ]
        
    def get_primary_image(self, obj):
        try:
            primary_image = obj.images.filter(is_primary=True).first() or obj.images.first()
            if primary_image:
                return primary_image.image.url
            return None
        except:
            return None