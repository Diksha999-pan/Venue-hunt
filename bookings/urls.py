from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('create/<int:venue_id>/', views.create_booking, name='create_booking'),
    path('<int:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('<int:pk>/receipt/', views.download_receipt, name='download_receipt'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('venue-bookings/', views.venue_bookings, name='venue_bookings'),
    path('<int:pk>/update-status/<str:status>/', views.update_booking_status, name='update_booking_status'),
    path('<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
]
