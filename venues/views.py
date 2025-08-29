from django.shortcuts import render
from django.views.generic import ListView, DetailView, TemplateView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Avg
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.forms import modelformset_factory
from .models import Venue, VenueImage
from .forms import VenueForm

class VenueListView(ListView):
    model = Venue
    template_name = 'venues/venue_list.html'
    context_object_name = 'venues'
    paginate_by = 9

    def get_queryset(self):
        # Annotate venues with their average rating
        from django.db.models import Avg, Count
        queryset = Venue.objects.all().annotate(
            average_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ).order_by('-created_at')
        
        # Search filter
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(address__icontains=search_query)
            )
        
        # Event category filter
        event_category = self.request.GET.get('event_category')
        if event_category:
            queryset = queryset.filter(event_category=event_category)
        
        # Event type filter
        event_type = self.request.GET.get('event_type')
        if event_type:
            queryset = queryset.filter(supported_events=event_type)
        
        # Price range filter
        price_range = self.request.GET.get('price_range')
        if price_range:
            if price_range == '0-100':
                queryset = queryset.filter(price_per_person__lte=100)
            elif price_range == '100-500':
                queryset = queryset.filter(price_per_person__gt=100, price_per_person__lte=500)
            elif price_range == '500-1000':
                queryset = queryset.filter(price_per_person__gt=500, price_per_person__lte=1000)
            elif price_range == '1000+':
                queryset = queryset.filter(price_per_person__gt=1000)
        
        # Capacity filter
        capacity = self.request.GET.get('capacity')
        if capacity:
            if capacity == '1-50':
                queryset = queryset.filter(capacity__lte=50)
            elif capacity == '51-100':
                queryset = queryset.filter(capacity__gt=50, capacity__lte=100)
            elif capacity == '101-200':
                queryset = queryset.filter(capacity__gt=100, capacity__lte=200)
            elif capacity == '201+':
                queryset = queryset.filter(capacity__gt=200)
        
        # Location filter
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(address__icontains=location)
        
        # Date filter (availability check)
        date = self.request.GET.get('date')
        if date:
            # Exclude venues that have bookings on the selected date
            queryset = queryset.exclude(
                bookings__date=date,
                bookings__status='confirmed'
            )
        
        # Rating filter
        rating = self.request.GET.get('rating')
        if rating:
            min_rating = int(rating)
            queryset = queryset.filter(average_rating__gte=min_rating)
        
        # Amenity filters
        if self.request.GET.get('parking'):
            queryset = queryset.filter(has_parking=True)
        if self.request.GET.get('wifi'):
            queryset = queryset.filter(has_wifi=True)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Preserve filter parameters in pagination links
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_params'] = query_params.urlencode()
        return context

class MyVenuesListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Venue
    template_name = 'venues/my_venues.html'
    context_object_name = 'venues'
    paginate_by = 10

    def test_func(self):
        return self.request.user.user_type == 'vendor'

    def get_queryset(self):
        return Venue.objects.filter(owner=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'venues'
        return context

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class VenueDetailView(DetailView):
    model = Venue
    template_name = 'venues/venue_detail.html'
    context_object_name = 'venue'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venue = self.get_object()
        
        # Get reviews for this venue with pagination
        from django.core.paginator import Paginator
        try:
            from reviews.models import Review
            reviews = Review.objects.filter(venue=venue).order_by('-created_at')
            
            # Paginate reviews
            paginator = Paginator(reviews, 5)  # 5 reviews per page
            page_number = self.request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            # Calculate average rating
            from django.db.models import Avg, Count
            rating_stats = reviews.aggregate(
                average=Avg('rating'),
                count=Count('id')
            )
            
            context['venue_reviews'] = page_obj
            context['page_obj'] = page_obj
            context['venue_rating'] = rating_stats if rating_stats['count'] > 0 else None
            
        except:
            # If the reviews app doesn't exist or there's an error
            context['venue_reviews'] = []
            context['venue_rating'] = None
            
        return context

class VendorDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'venues/vendor_dashboard.html'

    def test_func(self):
        return self.request.user.user_type == 'vendor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venues = Venue.objects.filter(owner=self.request.user)
        venue_ids = venues.values_list('id', flat=True)
        
        # Get bookings for these venues
        from bookings.models import Booking
        all_bookings = Booking.objects.filter(venue_id__in=venue_ids)
        recent_bookings = all_bookings.order_by('-created_at')[:5]
        pending_bookings = all_bookings.filter(status='pending')
        
        context.update({
            'venues': venues,
            'venues_count': venues.count(),
            'recent_bookings': recent_bookings,
            'pending_bookings_count': pending_bookings.count(),
            'total_bookings_count': all_bookings.count(),
            'active_tab': 'overview',
            # Default values for metrics that might not be available
            'average_rating': 0,
            'total_reviews': 0,
        })
        return context

class VenueCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Venue
    template_name = 'venues/venue_form.html'
    form_class = VenueForm
    success_url = reverse_lazy('venues:vendor_dashboard')

    def test_func(self):
        return self.request.user.user_type == 'vendor'

    def form_valid(self, form):
        # Set the owner
        form.instance.owner = self.request.user
        
        # Make sure latitude and longitude are saved if they were provided
        if form.cleaned_data.get('latitude') and form.cleaned_data.get('longitude'):
            form.instance.latitude = form.cleaned_data.get('latitude')
            form.instance.longitude = form.cleaned_data.get('longitude')
            
        response = super().form_valid(form)
        
        # Handle image uploads
        images = self.request.FILES.getlist('venue_images')
        for i, image in enumerate(images):
            VenueImage.objects.create(
                venue=self.object,
                image=image,
                is_primary=(i == 0 and not self.object.images.filter(is_primary=True).exists())
            )
        
        return response

class VenueUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Venue
    template_name = 'venues/venue_form.html'
    form_class = VenueForm
    success_url = reverse_lazy('venues:vendor_dashboard')

    def test_func(self):
        venue = self.get_object()
        return self.request.user == venue.owner
        
    def form_valid(self, form):
        # Make sure latitude and longitude are saved if they were provided
        if form.cleaned_data.get('latitude') and form.cleaned_data.get('longitude'):
            form.instance.latitude = form.cleaned_data.get('latitude')
            form.instance.longitude = form.cleaned_data.get('longitude')
            
        response = super().form_valid(form)
        
        # Handle new image uploads
        images = self.request.FILES.getlist('venue_images')
        for image in images:
            VenueImage.objects.create(
                venue=self.object,
                image=image,
                is_primary=not self.object.images.filter(is_primary=True).exists()
            )
        
        # Handle primary image selection
        primary_image_id = self.request.POST.get('primary_image')
        if primary_image_id:
            self.object.images.filter(is_primary=True).update(is_primary=False)
            self.object.images.filter(id=primary_image_id).update(is_primary=True)
            
        # Handle image deletions
        delete_images = self.request.POST.getlist('delete_images')
        if delete_images:
            self.object.images.filter(id__in=delete_images).delete()
            
        return response

class VenueDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Venue
    template_name = 'venues/venue_confirm_delete.html'
    success_url = reverse_lazy('venues:vendor_dashboard')

    def test_func(self):
        venue = self.get_object()
        return self.request.user == venue.owner

def home_page_venues(request):
    # Get venues with images for the slideshow
    venues_with_images = Venue.objects.filter(images__isnull=False).distinct()
    
    # Annotate with average rating to sort by popularity
    from django.db.models import Avg, Count
    popular_venues = venues_with_images.annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).order_by('-avg_rating', '-review_count', '-created_at')[:5]  # Get top 5 for slideshow
    
    # If there are fewer than 5 popular venues, just get the most recent ones
    if popular_venues.count() < 5 and venues_with_images.exists():
        remaining_count = 5 - popular_venues.count()
        recent_venues = venues_with_images.exclude(
            id__in=popular_venues.values_list('id', flat=True)
        ).order_by('-created_at')[:remaining_count]
        
        # Combine the querysets
        from itertools import chain
        from django.db.models import QuerySet
        featured_venues = list(chain(popular_venues, recent_venues))
    else:
        featured_venues = popular_venues
    
    return render(request, 'home.html', {'featured_venues': featured_venues})

class AnalyticsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'venues/analytics.html'

    def test_func(self):
        return self.request.user.user_type == 'vendor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's venues
        venues = Venue.objects.filter(owner=self.request.user)
        venue_ids = venues.values_list('id', flat=True)
        
        # Get bookings for these venues
        from bookings.models import Booking
        from django.db.models import Count, Sum, Avg
        from django.db.models.functions import TruncMonth, TruncDay
        import datetime
        
        # All bookings
        all_bookings = Booking.objects.filter(venue_id__in=venue_ids)
        
        # Calculate revenue
        total_revenue = all_bookings.filter(payment_status='paid').aggregate(
            total=Sum('amount_paid')
        )['total'] or 0
        
        # Bookings by month (last 6 months)
        six_months_ago = datetime.datetime.now() - datetime.timedelta(days=180)
        bookings_by_month = all_bookings.filter(
            created_at__gte=six_months_ago
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # Bookings by status
        bookings_by_status = all_bookings.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Bookings by venue
        bookings_by_venue = all_bookings.values('venue__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Revenue by venue
        revenue_by_venue = all_bookings.filter(
            payment_status='paid'
        ).values('venue__name').annotate(
            total=Sum('amount_paid')
        ).order_by('-total')
        
        # Popular event types
        popular_events = all_bookings.values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Recent 30 days trend
        thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        daily_bookings = all_bookings.filter(
            created_at__gte=thirty_days_ago
        ).annotate(
            day=TruncDay('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Convert DateTime objects to formatted strings for template
        # This avoids errors when dealing with the datetime objects directly in templates
        formatted_bookings_by_month = []
        for item in bookings_by_month:
            formatted_bookings_by_month.append({
                'month': item['month'].strftime('%b %Y'),
                'count': item['count']
            })
        
        formatted_daily_bookings = []
        for item in daily_bookings:
            formatted_daily_bookings.append({
                'day': item['day'].strftime('%d %b'),
                'count': item['count']
            })
        
        # Calculate success rate
        total_booking_count = all_bookings.count()
        confirmed_count = all_bookings.filter(status='confirmed').count()
        pending_count = all_bookings.filter(status='pending').count()
        cancelled_count = all_bookings.filter(status='cancelled').count()
        success_rate = (confirmed_count / total_booking_count * 100) if total_booking_count > 0 else 0
        
        context.update({
            'venues': venues,
            'venues_count': venues.count(),
            'total_bookings': total_booking_count,
            'booking_success_rate': success_rate,  # Success rate as percentage
            'confirmed_bookings': confirmed_count,  # Actual count for chart
            'pending_bookings': pending_count,
            'cancelled_bookings': cancelled_count,
            'total_revenue': total_revenue,
            'bookings_by_month': formatted_bookings_by_month,
            'bookings_by_status': list(bookings_by_status),
            'bookings_by_venue': list(bookings_by_venue),
            'revenue_by_venue': list(revenue_by_venue),
            'popular_events': list(popular_events),
            'daily_bookings': formatted_daily_bookings,
            'active_tab': 'analytics',
            'has_bookings': total_booking_count > 0,  # Add flag for empty state handling
            'has_venues': venues.exists(),
        })
        return context
