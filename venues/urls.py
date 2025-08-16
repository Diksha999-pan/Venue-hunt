from django.urls import path
from . import views

app_name = 'venues'

urlpatterns = [
    path('', views.VenueListView.as_view(), name='venue_list'),
    path('<int:pk>/', views.VenueDetailView.as_view(), name='venue_detail'),
    path('dashboard/', views.VendorDashboardView.as_view(), name='vendor_dashboard'),
    path('my-venues/', views.MyVenuesListView.as_view(), name='my_venues'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('add/', views.VenueCreateView.as_view(), name='venue_add'),
    path('<int:pk>/edit/', views.VenueUpdateView.as_view(), name='venue_edit'),
    path('<int:pk>/delete/', views.VenueDeleteView.as_view(), name='venue_delete'),
]
