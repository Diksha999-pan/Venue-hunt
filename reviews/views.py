from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.contrib import messages
from django.http import HttpResponseForbidden
from venues.models import Review, Venue
from .forms import ReviewForm
from bookings.models import Booking
from django.db.models import Avg, Count

@login_required
def add_review(request, booking_id):
    """View for adding a review for a completed booking"""
    booking = get_object_or_404(Booking, pk=booking_id)
    
    # Check if user is the organizer of this booking
    if request.user != booking.organizer:
        messages.error(request, "You can only review bookings that you have made.")
        return redirect('bookings:my_bookings')
    
    # Check if booking is completed (confirmed and past event date)
    if booking.status != 'confirmed' or booking.payment_status != 'paid':
        messages.error(request, "You can only review confirmed and paid bookings.")
        return redirect('bookings:booking_detail', pk=booking.pk)
    
    # Check if a review already exists
    try:
        existing_review = Review.objects.get(booking=booking)
        messages.info(request, "You have already reviewed this booking.")
        return redirect('reviews:edit_review', review_id=existing_review.pk)
    except Review.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.venue = booking.venue
            review.reviewer = request.user
            review.save()
            
            messages.success(request, "Thank you for your review!")
            return redirect('bookings:booking_detail', pk=booking.pk)
    else:
        form = ReviewForm()
    
    return render(request, 'reviews/review_form.html', {
        'form': form,
        'booking': booking,
        'venue': booking.venue,
    })

@login_required
def edit_review(request, review_id):
    """View for editing an existing review"""
    review = get_object_or_404(Review, pk=review_id)
    
    # Check if user is the reviewer
    if request.user != review.reviewer:
        return HttpResponseForbidden("You can only edit your own reviews.")
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Your review has been updated!")
            return redirect('bookings:booking_detail', pk=review.booking.pk)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'reviews/review_form.html', {
        'form': form,
        'booking': review.booking,
        'venue': review.venue,
        'is_edit': True,
    })

@login_required
def delete_review(request, review_id):
    """View for deleting a review"""
    review = get_object_or_404(Review, pk=review_id)
    
    # Check if user is the reviewer
    if request.user != review.reviewer:
        return HttpResponseForbidden("You can only delete your own reviews.")
    
    booking_id = review.booking.id
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, "Your review has been deleted.")
        return redirect('bookings:booking_detail', pk=booking_id)
    
    return render(request, 'reviews/delete_review.html', {
        'review': review,
    })

class VenueReviewsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View for venue owners to see all reviews for their venues"""
    model = Review
    template_name = 'reviews/venue_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def test_func(self):
        return self.request.user.user_type == 'vendor'

    def get_queryset(self):
        # Get all venues owned by the user
        user_venues = Venue.objects.filter(owner=self.request.user)
        
        # Get reviews for these venues with related data
        reviews = Review.objects.filter(venue__in=user_venues)\
            .select_related('venue', 'reviewer', 'booking')\
            .order_by('-created_at')

        # Apply filters if any
        venue_id = self.request.GET.get('venue')
        rating = self.request.GET.get('rating')
        
        if venue_id:
            reviews = reviews.filter(venue_id=venue_id)
        if rating:
            reviews = reviews.filter(rating=rating)
            
        return reviews

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_venues = Venue.objects.filter(owner=self.request.user)
        
        # Get venue stats
        venue_stats = []
        for venue in user_venues:
            venue_reviews = Review.objects.filter(venue=venue)
            stats = venue_reviews.aggregate(
                avg_rating=Avg('rating'),
                total_reviews=Count('id')
            )
            venue_stats.append({
                'venue': venue,
                'avg_rating': stats['avg_rating'] or 0,
                'total_reviews': stats['total_reviews']
            })
        
        context.update({
            'active_tab': 'reviews',
            'venues': user_venues,
            'venue_stats': venue_stats,
            'selected_venue': self.request.GET.get('venue'),
            'selected_rating': self.request.GET.get('rating'),
        })
        return context
