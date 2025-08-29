from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

app_name = 'recommendations'

urlpatterns = [
    path('venues/<int:venue_id>/similar/', 
         csrf_exempt(views.VenueRecommendationsView.as_view()), 
         name='similar-venues'),
    path('venues/personalized/', 
         csrf_exempt(views.PersonalizedRecommendationsView.as_view()), 
         name='personalized-recommendations'),
]