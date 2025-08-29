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
try:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    print(f"PAYMENT DEBUG: Razorpay client initialized with key: {settings.RAZORPAY_KEY_ID[:6]}...")
except Exception as e:
    print(f"PAYMENT DEBUG: Error initializing Razorpay client: {str(e)}")

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
    
    # Set initial data based on venue
    initial_data = {
        'venue': venue,
        'event_category': venue.event_category,  # Pre-select venue's event category
        'event_type': venue.supported_events     # Pre-select venue's supported event type
    }
    
    if request.method == 'POST':
        form = BookingForm(request.POST, initial=initial_data)
        # Set the venue instance directly
        form.instance.venue = venue
        
        if form.is_valid():
            booking = form.save(commit=False)
            booking.organizer = request.user
            booking.status = 'pending'
            booking.payment_status = 'pending'
            
            # Calculate the total amount based on number of attendees
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            number_of_guests = form.cleaned_data.get('number_of_guests', 1)  # Get number of guests
            is_advance_payment = form.cleaned_data.get('is_advance_payment', False)
            
            # Calculate total amount first
            total_amount = float(venue.price_per_person) * number_of_guests
            
            # Determine payment amount (full or 20% advance)
            # Razorpay test mode has a lower limit than documented
            RAZORPAY_ACTUAL_LIMIT = 40000  # ₹40,000 - Configured limit for test mode
            
            # Calculate the payment amount based on user selection
            if is_advance_payment:
                payment_amount = total_amount * 0.2  # 20% of total
                payment_description = "20% Advance Payment"
            else:
                payment_amount = total_amount  # Full payment
                payment_description = "Full Payment"
            
            # Now enforce the payment limit regardless of which option was selected
            if payment_amount > RAZORPAY_ACTUAL_LIMIT:
                payment_amount = RAZORPAY_ACTUAL_LIMIT
                payment_description = f"Partial Payment (Capped at ₹{RAZORPAY_ACTUAL_LIMIT:,.2f})"
                
            # Convert to paisa for Razorpay
            amount = int(payment_amount * 100)  # Amount in paisa
            
            print(f"PAYMENT DEBUG: New booking payment - Amount in paisa: {amount}, Description: {payment_description}")
            print(f"PAYMENT DEBUG: Total amount: {total_amount}, Is advance: {is_advance_payment}")
            
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
                        'organizer_email': request.user.email,
                        'payment_type': 'advance' if is_advance_payment else 'full'
                    }
                })
                
                print(f"PAYMENT DEBUG: Razorpay order created successfully: {razorpay_order['id']}")
                
                booking.amount_paid = payment_amount  # Store amount in rupees
                booking.total_amount = total_amount  # Store total amount
                booking.is_advance_payment = is_advance_payment  # Store whether it's an advance payment
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
                    'customer_name': f"{request.user.first_name} {request.user.last_name}".strip(),
                    'is_advance_payment': is_advance_payment,
                    'total_amount': total_amount,
                    'payment_description': payment_description
                }
                return render(request, 'bookings/payment.html', context)
                
            except razorpay.errors.BadRequestError as e:
                error_message = str(e)
                if "amount exceeds maximum" in error_message.lower():
                    messages.error(
                        request,
                        "The total amount exceeds the maximum payment limit. Please reduce the number of guests or contact support for assistance with large bookings."
                    )
                else:
                    messages.error(request, f"Payment error: {error_message}")
                
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
            print("PAYMENT DEBUG: Payment callback received")
            print(f"PAYMENT DEBUG: POST data: {request.POST}")
            
            # Get the payment details from POST data
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')
            
            print(f"PAYMENT DEBUG: Payment ID: {payment_id}")
            print(f"PAYMENT DEBUG: Order ID: {razorpay_order_id}")
            print(f"PAYMENT DEBUG: Signature: {signature[:10]}...")
            
            # If we don't have all the required parameters, it might be a payment failure
            if not (payment_id and razorpay_order_id and signature):
                print("PAYMENT DEBUG: Missing payment details - likely a payment failure")
                booking = None
                error_code = request.POST.get('error[code]', '')
                error_message = request.POST.get('error[description]', 'Payment process was interrupted')
                
                print(f"PAYMENT DEBUG: Error code: {error_code}")
                print(f"PAYMENT DEBUG: Error message: {error_message}")
                
                # Common Razorpay error codes
                if error_code == 'BAD_REQUEST_ERROR' and 'amount' in error_message.lower():
                    error_message = "Payment failed: The transaction amount exceeds your card's limit. Try using a credit card or contact your bank to increase your limit."
                elif 'card declined' in error_message.lower() or 'payment authorization failed' in error_message.lower():
                    error_message = "Payment failed: Your card was declined. Please try a different payment method or contact your bank."
                
                # Try to get the booking from the order ID if available
                if razorpay_order_id:
                    booking = Booking.objects.filter(payment_id=razorpay_order_id).first()
                
                if booking:
                    messages.error(request, f"Payment failed: {error_message}")
                    return redirect('bookings:retry_payment', pk=booking.pk)
                else:
                    messages.error(request, f"Payment failed: {error_message}")
                    return redirect('home')
            
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
                    # Get the actual amount paid from Razorpay
                    try:
                        # Fetch payment details from Razorpay
                        payment_details = razorpay_client.payment.fetch(payment_id)
                        amount_paid = float(payment_details['amount']) / 100  # Convert from paisa to rupees
                        
                        # Update booking with actual amount paid
                        booking.amount_paid = amount_paid
                    except Exception as e:
                        # If we can't fetch the payment details, use the amount from the booking
                        pass
                    
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
                # Payment verification failed
                booking = Booking.objects.filter(payment_id=razorpay_order_id).first()
                if booking:
                    messages.error(request, f'Payment verification failed: {str(e)}')
                    return redirect('bookings:retry_payment', pk=booking.pk)
                else:
                    messages.error(request, f'Payment verification failed: {str(e)}')
                    return redirect('home')
        except Exception as e:
            messages.error(request, f'Error processing payment callback: {str(e)}')
            return redirect('home')
    return redirect('home')

@login_required
def retry_payment(request, pk):
    """View to retry a failed payment"""
    booking = get_object_or_404(Booking, pk=pk)
    
    # Make sure only the booking organizer can retry the payment
    if request.user != booking.organizer:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    # Make sure the booking is in pending state
    if booking.status != 'pending' or booking.payment_status == 'paid':
        messages.error(request, "This booking is already processed and cannot be retried.")
        return redirect('bookings:booking_detail', pk=booking.pk)
    
    try:
        # Calculate the payment amount
        if booking.is_advance_payment:
            payment_description = "20% Advance Payment"
        else:
            payment_description = "Full Payment"
        
        # Get the payment amount from the booking
        payment_amount = float(booking.amount_paid)
        
        # Debug print to see what's happening
        print(f"PAYMENT DEBUG: Retry payment for booking {booking.pk}")
        print(f"PAYMENT DEBUG: Original payment amount: {payment_amount}")
        
        # Razorpay test mode has a lower limit than documented
        RAZORPAY_ACTUAL_LIMIT = 40000  # ₹40,000 - Configured limit for test mode
        
        # If the amount is still too large, cap it
        if payment_amount > RAZORPAY_ACTUAL_LIMIT:
            payment_amount = RAZORPAY_ACTUAL_LIMIT
            payment_description = f"Partial Payment (Capped at ₹{RAZORPAY_ACTUAL_LIMIT:,.2f})"
            print(f"PAYMENT DEBUG: Amount capped at {RAZORPAY_ACTUAL_LIMIT}")
        
        # Amount should already be stored in the booking
        amount = int(payment_amount * 100)  # Convert to paisa
        print(f"PAYMENT DEBUG: Final amount in paisa: {amount}")
        
        # Create a new Razorpay order
        try:
            razorpay_order = razorpay_client.order.create({
                'amount': amount,
                'currency': 'INR',
                'payment_capture': 1,
                'notes': {
                    'venue_name': booking.venue.name,
                    'venue_id': str(booking.venue.id),
                    'event_date': str(booking.event_date),
                    'organizer_email': booking.organizer.email,
                    'payment_type': 'advance' if booking.is_advance_payment else 'full',
                    'retry': 'true'
                }
            })
            print(f"PAYMENT DEBUG: Razorpay order created: {razorpay_order['id']}")
        except Exception as e:
            print(f"PAYMENT DEBUG: Error creating Razorpay order: {str(e)}")
            raise
        
        # Update the booking with the new order ID
        booking.payment_id = razorpay_order['id']
        booking.save()
        
        context = {
            'booking': booking,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
            'callback_url': request.build_absolute_uri(reverse('bookings:payment_callback')),
            'amount': amount,
            'currency': 'INR',
            'venue': booking.venue,
            'customer_email': request.user.email,
            'customer_name': f"{request.user.first_name} {request.user.last_name}".strip(),
            'is_advance_payment': booking.is_advance_payment,
            'total_amount': booking.total_amount,
            'payment_description': payment_description,
            'is_retry': True
        }
        
        return render(request, 'bookings/payment.html', context)
        
    except razorpay.errors.BadRequestError as e:
        error_message = str(e)
        if "amount exceeds maximum" in error_message.lower():
            messages.error(
                request,
                "The payment amount exceeds the maximum payment limit. Please contact support for assistance."
            )
        else:
            messages.error(request, f"Payment error: {error_message}")
        return redirect('bookings:booking_detail', pk=booking.pk)
        
    except Exception as e:
        messages.error(request, f"Error retrying payment: {str(e)}")
        return redirect('bookings:booking_detail', pk=booking.pk)

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
    
    if pdf:
        # Set the filename for download
        filename = f"VenueHunt_Receipt_{booking.id}.pdf"
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        messages.error(request, "Error generating receipt. Please try again later.")
        return redirect('bookings:booking_detail', pk=booking.pk)

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
        return redirect('bookings:my_bookings' if request.user == booking.organizer else 'bookings:venue_bookings')
        
    # Check for cancellation restrictions based on proximity to event date
    from datetime import datetime, timedelta
    today = datetime.now().date()
    event_date = booking.event_date
    days_until_event = (event_date - today).days

    # Venue owners can't cancel 3 days before, organizers can't cancel 2 days before
    if (request.user == booking.venue.owner and days_until_event <= 3) or \
       (request.user == booking.organizer and days_until_event <= 2):
        
        if request.user == booking.venue.owner:
            messages.error(request, "Venue owners can only cancel bookings more than 3 days before the event date.")
        else:
            messages.error(request, "Bookings cannot be cancelled within 2 days of the event date.")
            
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
