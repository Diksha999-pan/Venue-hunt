from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from venues.models import Venue
from .serializers import RecommendedVenueSerializer
from .recommendation_engine import VenueRecommender
from .models import UserVenueInteraction
import logging

logger = logging.getLogger(__name__)

# Create a singleton instance of the recommender
recommender = VenueRecommender()

class VenueRecommendationsView(APIView):
    """API endpoint for getting venue recommendations"""
    permission_classes = []  # Allow any user to get recommendations
    
    def get(self, request, venue_id):
        """Get similar venues for a given venue ID"""
        try:
            logger.info(f"Received recommendation request for venue_id: {venue_id}")
            
            # Ensure venue exists
            try:
                venue = Venue.objects.get(pk=venue_id)
                logger.info(f"Found venue: {venue.name}")
            except Venue.DoesNotExist:
                logger.error(f"Venue {venue_id} not found")
                return Response(
                    {"error": "Venue not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get total number of venues
            total_venues = Venue.objects.count()
            logger.info(f"Total venues in database: {total_venues}")
            
            if total_venues < 2:
                return Response(
                    {"error": "Not enough venues for recommendations"},
                    status=status.HTTP_200_OK
                )
            
            # Record interaction for authenticated users
            if request.user.is_authenticated:
                UserVenueInteraction.objects.create(
                    user=request.user,
                    venue=venue,
                    interaction_type='view'
                )
            
            try:
                # Get recommendations
                similar_venues = recommender.get_similar_venues(venue_id)
                
                # Ensure we have venues
                if not similar_venues:
                    logger.info(f"No similar venues found for venue_id: {venue_id}")
                    return Response([])
                
                serializer = RecommendedVenueSerializer(similar_venues, many=True)
                logger.info(f"Returning {len(similar_venues)} similar venues for venue_id: {venue_id}")
                return Response(serializer.data)
                
            except Exception as e:
                logger.error(f"Error getting recommendations: {str(e)}")
                return Response(
                    {"error": "Failed to compute recommendations"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PersonalizedRecommendationsView(APIView):
    """API endpoint for getting personalized venue recommendations"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get personalized recommendations based on user history"""
        try:
            recommended_venues = recommender.get_personalized_recommendations(
                user=request.user
            )
            serializer = RecommendedVenueSerializer(recommended_venues, many=True)
            
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
