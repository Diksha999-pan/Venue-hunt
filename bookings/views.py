from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import get_template
import razorpay
import io
from xhtml2pdf import pisa
from datetime import datetime
from .models import Booking
from .forms import BookingForm
from venues.models import Venue

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class BookingDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Booking
    template_name = 'bookings/booking_detail.html'
    context_object_name = 'booking'

    def test_func(self):
        booking = self.get_object()
        return (self.request.user == booking.organizer or 
                self.request.user == booking.venue.owner)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = datetime.now().date()
        
        # Check if there's a review for this booking
        try:
            from reviews.models import Review
            booking = self.get_object()
            review = Review.objects.filter(booking=booking).first()
            context['review'] = review
        except:
            pass
            
        return context

@login_required
def create_booking(request, venue_id):
    venue = get_object_or_404(Venue, pk=venue_id)
    
    initial_data = {'venue': venue}
    if request.method == 'POST':
        form = BookingForm(request.POST, initial=initial_data)
        # Set the venue instance directly
        form.instance.venue = venue
        
        if form.is_valid():
            booking = form.save(commit=False)
            booking.organizer = request.user
            booking.status = 'pending'
            booking.payment_status = 'pending'
            
            # Calculate the total amount based on hours booked
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            hours = (end_time.hour - start_time.hour) + (end_time.minute - start_time.minute) / 60
            amount = int(float(venue.price_per_hour) * hours * 100)  # Amount in paisa
            
            try:
                # Create Razorpay Order
                razorpay_order = razorpay_client.order.create({
                    'amount': amount,
                    'currency': 'INR',
                    'payment_capture': 1,
                    'notes': {
                        'venue_name': venue.name,
                        'venue_id': str(venue.id),
                        'event_date': str(form.cleaned_data['event_date']),
                        'organizer_email': request.user.email
                    }
                })
                
                booking.amount_paid = amount / 100  # Store amount in rupees
                booking.payment_id = razorpay_order['id']  # Store the order ID
                booking.save()
                
                context = {
                    'booking': booking,
                    'razorpay_order_id': razorpay_order['id'],
                    'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                    'callback_url': request.build_absolute_uri(reverse('bookings:payment_callback')),
                    'amount': amount,
                    'currency': 'INR',
                    'form': form,
                    'venue': venue,
                    'customer_email': request.user.email,
                    'customer_name': f"{request.user.first_name} {request.user.last_name}".strip()
                }
                return render(request, 'bookings/payment.html', context)
                
            except razorpay.errors.BadRequestError as e:
                messages.error(request, f"Invalid payment request: {str(e)}")
                if booking.id:
                    booking.delete()
                return redirect('venues:venue_detail', pk=venue.id)
            except Exception as e:
                messages.error(request, f"Error creating payment: {str(e)}")
                if booking.id:
                    booking.delete()  # Clean up the booking if payment creation fails
                return redirect('venues:venue_detail', pk=venue.id)
    else:
        form = BookingForm()
        form.instance.venue = venue  # This is needed for capacity validation

    return render(request, 'bookings/booking_form.html', {
        'form': form,
        'venue': venue
    })

@csrf_exempt
def payment_callback(request):
    if request.method == "POST":
        try:
            # Get the payment details from POST data
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')
            
            # Create parameters dict for verification
            params_dict = {
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_signature': signature
            }
            
            try:
                # Verify the payment signature
                razorpay_client.utility.verify_payment_signature(params_dict)
                
                # Get the booking by order ID
                booking = Booking.objects.filter(payment_id=razorpay_order_id).first()
                if booking:
                    # Update booking status and payment details
                    booking.payment_status = 'paid'
                    booking.status = 'confirmed'  # Auto-confirm booking after payment
                    booking.transaction_id = payment_id  # Store the Razorpay payment ID
                    booking.save()
                    
                    messages.success(request, 'Payment successful! Your booking has been confirmed.')
                    return redirect('bookings:booking_detail', pk=booking.pk)
                else:
                    messages.error(request, 'Booking not found!')
                    return redirect('home')
            except Exception as e:
                messages.error(request, f'Payment verification failed! Error: {str(e)}')
                return redirect('home')
                
        except Exception as e:
            messages.error(request, f'Error processing payment callback: {str(e)}')
            return redirect('home')
    return redirect('home')

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse("Error generating PDF", status=400)

@login_required
def download_receipt(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    
    # Ensure only the organizer or venue owner can download the receipt
    if request.user != booking.organizer and request.user != booking.venue.owner:
        messages.error(request, "You don't have permission to access this receipt.")
        return redirect('home')
    
    # Check if payment is completed
    if booking.payment_status != 'paid':
        messages.error(request, "Receipt is only available for paid bookings.")
        return redirect('bookings:booking_detail', pk=booking.pk)
    
    # Prepare context data for the PDF
    context = {
        'booking': booking,
        'venue': booking.venue,
        'organizer': booking.organizer,
        'payment_date': booking.updated_at,
        'generation_date': datetime.now(),
        'receipt_number': f"REC-{booking.id}-{datetime.now().strftime('%Y%m%d')}"
    }
    
    # Generate the PDF
    pdf = render_to_pdf('bookings/receipt_pdf.html', context)
    
    # Set the filename for download
    filename = f"VenueHunt_Receipt_{booking.id}.pdf"
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
def my_bookings(request):
    """View for users to see their bookings as an organizer"""
    # Make sure the user is an organizer
    if request.user.user_type != 'organizer':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
        
    bookings = Booking.objects.filter(organizer=request.user).order_by('-created_at')
    
    return render(request, 'bookings/my_bookings.html', {
        'bookings': bookings,
        'user_type': request.user.user_type
    })

@login_required
def venue_bookings(request):
    """View for venue owners to see bookings for their venues"""
    if request.user.user_type != 'vendor':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Get all venues owned by the user
    venue_ids = Venue.objects.filter(owner=request.user).values_list('id', flat=True)
    # Get all bookings for those venues
    bookings = Booking.objects.filter(venue_id__in=venue_ids).order_by('-created_at')
    
    return render(request, 'bookings/venue_bookings.html', {
        'bookings': bookings,
        'user_type': 'vendor',
        'venues': Venue.objects.filter(owner=request.user)
    })

@login_required
def update_booking_status(request, pk, status):
    """View to update booking status"""
    booking = get_object_or_404(Booking, pk=pk)
    
    # Ensure only the venue owner can update the status
    if request.user != booking.venue.owner:
        messages.error(request, "You don't have permission to update this booking.")
        return redirect('bookings:venue_bookings')
    
    # Check if status is valid
    if status not in dict(Booking.STATUS_CHOICES):
        messages.error(request, "Invalid status.")
        return redirect('bookings:venue_bookings')
    
    # Update booking status
    booking.status = status
    booking.save()
    
    messages.success(request, f"Booking status updated to {booking.get_status_display()}")
    return redirect('bookings:venue_bookings')

@login_required
def cancel_booking(request, pk):
    """View for cancelling a booking"""
    booking = get_object_or_404(Booking, pk=pk)
    
    # Check if the user is either the organizer or the venue owner
    if request.user != booking.organizer and request.user != booking.venue.owner:
        messages.error(request, "You don't have permission to cancel this booking.")
        return redirect('home')
    
    # Only allow cancellation of pending or confirmed bookings
    if booking.status == 'cancelled':
        messages.warning(request, "This booking is already cancelled.")
        
    # Check for venue owner's 3-day restriction
    from datetime import datetime, timedelta
    today = datetime.now().date()
    event_date = booking.event_date
    days_until_event = (event_date - today).days

    if request.user == booking.venue.owner and days_until_event <= 3:
        messages.error(request, "Venue owners can only cancel bookings more than 3 days before the event date.")
        return redirect('bookings:venue_bookings')
        
        # Redirect based on user type
        if request.user == booking.organizer:
            return redirect('bookings:my_bookings')
        else:
            return redirect('bookings:venue_bookings')
    
    # Update booking status
    booking.status = 'cancelled'
    booking.save()
    
    # Send notification (can be expanded with email notification)
    canceller_type = "organizer" if request.user == booking.organizer else "venue owner"
    messages.success(request, f"Booking has been cancelled successfully.")
    
    # Redirect based on user type
    if request.user == booking.organizer:
        return redirect('bookings:my_bookings')
    else:
        return redirect('bookings:venue_bookings')
