import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Min, Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.html import strip_tags
from django.utils.http import urlencode
from django.views.generic import View, TemplateView, FormView, ListView, UpdateView

from base.forms import HotelReviewForm, BookingDatesForm, BookingForm, HotelRatingForm
from base.models import Category, Hotel, HotelPhoto, City, Room, HotelFeature, HotelReview, HotelRating, Booking, \
    BookingStatus, UserFavourite


# Constant queries
booking_status_confirmed = get_object_or_404(BookingStatus, name='Confirmed')
booking_status_pending = get_object_or_404(BookingStatus, name='Pending')
booking_status_rejected = get_object_or_404(BookingStatus, name='Rejected')
booking_status_canceled = get_object_or_404(BookingStatus, name='Canceled')


def get_request_query(request, *args):
    """
    Function to retrive all parameters from GET method and returning them
    """
    result = []
    for arg in args:
        result.append(request.GET.get(arg, ''))
    return result


class HomePageView(TemplateView):
    """
    View for the home page displaying available rooms and hotel categories.
    """
    template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        """
        Handles the GET request for the home page.
        This method retrieves the request parameters, checks for available rooms
        and hotel categories, and prepares the context for rendering the home page.
        """
        check_in, check_out, num_guests = get_request_query(request, 'check_in', 'check_out', 'num_guests')
        form = BookingDatesForm(request.GET)

        form_errors = None
        if form.errors and check_in and check_out and num_guests:
            form_errors = form.errors

        # Retrieve available rooms for the given check-in, check-out, and number of guests
        if form.is_valid():
            available_rooms = Room.objects.filter(
                ~Q(bookings__check_in__lt=check_out,
                   bookings__check_out__gt=check_in,
                   bookings__status=booking_status_confirmed),
                capacity__gte=num_guests
            )
            category_ids = available_rooms.values_list('hotel__category__id', flat=True)
            # Retrieve categories for available rooms
            categories = Category.objects.filter(id__in=category_ids)
            # Retrieve hotels with available rooms
            hotels = Hotel.objects.filter(rooms__in=available_rooms).distinct()
        else:
            form = BookingDatesForm()
            categories = Category.objects.all()
            hotels = Hotel.objects.all()

        category_data = []
        for category in categories:
            # Count the number of hotels in the category with available rooms
            hotels_filtered = hotels.filter(category=category)
            hotels_counter = len(hotels_filtered) if form.is_valid() else category.hotels.count()
            data = {
                'category': category,
                'hotels_counter': hotels_counter
            }
            category_data.append(data)

        category_data.sort(key=lambda x: x['hotels_counter'], reverse=True)

        # Retrieve all cities for display in the search form
        cities = City.objects.all()

        # Prepare context for rendering the template
        context = {
            'category_data': category_data,
            'cities': cities,

            'form': form,
            'form_errors': form_errors,

            'check_in': check_in,
            'check_out': check_out,
            'num_guests': num_guests,
        }

        return render(request, self.template_name, context)


class CategoryListingView(TemplateView):
    """
    View to display a paginated list of hotels in a particular category.
    """

    template_name = 'category.html'
    paginate_by = 3

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and renders the list of hotels in the specified category.
        """

        # Extract request parameters
        check_in, check_out, num_guests, page = get_request_query(
            request, 'check_in', 'check_out', 'num_guests', 'page'
        )
        category_name = kwargs.get('category_name', '')

        # Get the category object or return 404 if not found
        category = get_object_or_404(Category, name=category_name)

        # Create the booking dates form with the provided request GET data
        form = BookingDatesForm(request.GET)

        # Check for form errors and assign them to 'form_errors' if applicable
        form_errors = None
        if form.errors and check_in and check_out and num_guests:
            form_errors = form.errors

        if form.is_valid():
            # If the form is valid, fetch available rooms based on booking dates and capacity
            available_rooms = Room.objects.filter(
                ~Q(
                    bookings__check_in__lt=check_out,
                    bookings__check_out__gt=check_in,
                    bookings__status=booking_status_confirmed
                ),
                capacity__gte=num_guests
            )
            # Filter hotels that have available rooms in the specified category
            hotels = Hotel.objects.filter(rooms__in=available_rooms, category=category).distinct()
        else:
            # If the form is not valid, reset the form and get all hotels in the specified category
            form = BookingDatesForm()
            hotels = Hotel.objects.filter(category=category)
            available_rooms = Room.objects.all()

        # Prepare the data for rendering hotels with associated information
        hotel_data = [
            {
                'hotel': hotel,
                'hotel_favourite': UserFavourite.objects.filter(hotel=hotel, user=request.user),
                'min_price': hotel.rooms.aggregate(Min('price'))['price__min'] or 0,
                'first_photo_url': HotelPhoto.get_first_photo_url(hotel),
                'available_room_count': available_rooms.filter(hotel=hotel).count(),
            }
            for hotel in hotels
        ]

        # Paginate the hotel data based on the 'paginate_by' attribute
        paginator = Paginator(hotel_data, self.paginate_by)

        try:
            paginated_hotel_data = paginator.page(page)
        except PageNotAnInteger:
            paginated_hotel_data = paginator.page(1)
        except EmptyPage:
            paginated_hotel_data = paginator.page(paginator.num_pages)

        # Prepare the context data for rendering the template
        context = {
            'hotel_data': paginated_hotel_data,
            'form': form,
            'form_errors': form_errors,
            'check_in': check_in,
            'check_out': check_out,
            'num_guests': num_guests,
        }

        return render(request, template_name=self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for adding/removing a hotel from the user's favorites.
        """

        # Extract request parameters
        category_name = kwargs.get('category_name')
        hotel_id = request.POST.get('fav_hotel_id')
        user = self.request.user
        check_in, check_out, num_guests, page = get_request_query(
            request, 'check_in', 'check_out', 'num_guests', 'page'
        )

        # Get the hotel object or return 404 if not found
        hotel = get_object_or_404(Hotel, id=hotel_id)

        # Check if the hotel is already in the user's favorites
        user_favourite = UserFavourite.objects.filter(user=user, hotel=hotel).exists()

        # If not already in favorites, add it to favorites; otherwise, remove it from favorites
        if not user_favourite:
            user_favourite = UserFavourite(user=user, hotel=hotel)
            user_favourite.save()
        else:
            user_favourite = UserFavourite.objects.get(user=user, hotel=hotel)
            user_favourite.delete()

        # Constructing the query parameter string
        query_param = urlencode(
            {
                'check_in': check_in,
                'check_out': check_out,
                'num_guests': num_guests,
                'page': page
            }
        )

        # Using reverse to get the URL and then appending the query parameter
        redirect_url = reverse('categoryListing', kwargs={'category_name': category_name})
        redirect_url = f"{redirect_url}?{query_param}"
        return redirect(redirect_url)


class CityListingView(View):
    template_name = 'city.html'

    def get(self, request, *args, **kwargs):
        city_id = kwargs['city_id']
        city = City(pk=city_id)
        hotels = Hotel.objects.filter(city=city)
        context = {'hotels': hotels, 'city': city}
        return render(request,
                      template_name=self.template_name,
                      context=context)


class HotelDetailedView(TemplateView):
    template_name = 'hotel.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return render(request, template_name=self.template_name, context=context)

    def get_context_data(self, request, **kwargs):
        check_in, check_out, num_guests = get_request_query(request, 'check_in', 'check_out', 'num_guests')
        hotel_name = kwargs.get('hotel_name')
        hotel = get_object_or_404(Hotel, name=hotel_name)

        # Get the core form and handle validation
        core_form, core_form_errors = self.get_core_form(request)

        # Retrieve related objects using select_related/prefetch_related for optimization
        if core_form.is_valid():
            rooms = Room.objects.filter(
                ~Q(bookings__check_in__lt=check_out,
                   bookings__check_out__gt=check_in,
                   bookings__status=booking_status_confirmed),
                capacity__gte=num_guests,
                hotel=hotel
            ).select_related('hotel').prefetch_related('bookings')
        else:
            rooms = Room.objects.filter(hotel=hotel)

        hotel_features = HotelFeature.objects.filter(hotel=hotel)
        hotel_photos = HotelPhoto.objects.filter(hotel=hotel)
        hotel_reviews = HotelReview.objects.filter(hotel=hotel).select_related('author')
        hotel_rating = HotelRating.objects.filter(hotel=hotel)

        user_hotel_rating = ''
        if request.user.is_authenticated:
            user_hotel_rating = HotelRating.objects.filter(hotel=hotel, author=request.user).first()

        context = {
            'hotel': hotel,
            'rooms': rooms,
            'hotel_features': hotel_features,
            'hotel_photos': hotel_photos,
            'hotel_reviews': hotel_reviews,
            'hotel_rating': hotel_rating,
            'user_hotel_rating': user_hotel_rating,

            'core_form': core_form,
            'core_form_errors': core_form_errors,

            'comment_form': HotelReviewForm(),
            'rate_form': HotelRatingForm(),

            'check_in': check_in,
            'check_out': check_out,
            'num_guests': num_guests,
        }

        return context

    def get_core_form(self, request):
        check_in, check_out, num_guests = get_request_query(request, 'check_in', 'check_out', 'num_guests')

        core_form = BookingDatesForm(request.GET)

        core_form_errors = None
        if check_in and check_out and num_guests and core_form.errors:
            core_form_errors = core_form.errors

        if not core_form.is_valid():
            core_form = BookingDatesForm()

        return core_form, core_form_errors

    def post(self, request, *args, **kwargs):
        check_in, check_out, num_guests = get_request_query(request, 'check_in', 'check_out', 'num_guests')
        user = self.request.user
        hotel_name = kwargs.get('hotel_name')
        hotel = get_object_or_404(Hotel, name=hotel_name)

        rating_value = request.POST.get('rating')
        comment = request.POST.get('comment')
        delete_review_id = request.POST.get('delete-review-id')

        # Get or create rating of the hotel
        if rating_value:
            user_hotel_rating, created = HotelRating.objects.get_or_create(
                hotel=hotel,
                author=user,
                defaults={'value': rating_value}
            )
            if not created:
                user_hotel_rating.value = rating_value
                user_hotel_rating.save()

        # Remove hotel review if requested
        if delete_review_id:
            review = get_object_or_404(HotelReview, id=delete_review_id)
            if request.user == review.author or request.user.is_staff:
                review.delete()

        # Add comment
        if comment:
            hotel_review = HotelReview(hotel=hotel, author=user, comment=comment)
            hotel_review.save()
        query_param = urlencode(
            {
                'check_in': check_in,
                'check_out': check_out,
                'num_guests': num_guests
            }
        )

        # Using reverse to get the URL and then appending the query parameter
        redirect_url = reverse('hotelDetails', kwargs={'hotel_name': hotel_name})
        redirect_url = f"{redirect_url}?{query_param}"
        return redirect(redirect_url)


class RoomBookingView(LoginRequiredMixin, FormView):
    """
    View for booking a room in a hotel.
    This view handles the form for booking a room and checks for availability and other validations.
    """

    form_class = BookingForm
    template_name = 'room_booking.html'
    success_url = reverse_lazy('bookingHistory')

    def get_context_data(self, **kwargs):
        """
        Adds context data to the template for rendering.
        This method retrieves hotel and room information and calculates the total price for the booking.
        """

        context = super().get_context_data(**kwargs)
        hotel_name = self.kwargs.get('hotel_name')
        room_id = self.kwargs.get('room_id')
        hotel = get_object_or_404(Hotel, name=hotel_name)
        hotel_rating = HotelRating(hotel=hotel)
        room = get_object_or_404(Room, id=room_id)
        check_in = datetime.datetime.strptime(self.request.GET.get('check_in', ''), '%Y-%m-%d').date()
        check_out = datetime.datetime.strptime(self.request.GET.get('check_out', ''), '%Y-%m-%d').date()
        num_guests = self.request.GET.get('num_guests', '')
        total_nights = (check_out - check_in).days
        total_price = total_nights * room.price

        context['hotel'] = hotel
        context['hotel_rating'] = hotel_rating
        context['room'] = room
        context['num_guests'] = num_guests
        context['check_in'] = check_in.strftime("%Y-%m-%d")
        context['check_out'] = check_out.strftime("%Y-%m-%d")
        context['total_nights'] = total_nights
        context['total_price'] = total_price
        return context

    def form_valid(self, form):
        """
        Handles form submission when the form is valid.
        This method validates the form data and creates a booking if all conditions are met.
        """

        context = self.get_context_data()
        room = context.get('room')
        check_in = context.get('check_in')
        check_out = context.get('check_out')
        num_guests = context.get('num_guests')

        if check_in == check_out:
            messages.error(self.request, 'Date of check-in must be different than check-out')
            return self.form_invalid(form)

        status_confirmed = get_object_or_404(BookingStatus, name='Confirmed')
        room_booked = Booking.objects.filter(
            room=room,
            check_in__lt=check_out,
            check_out__gt=check_in,
            status=status_confirmed,
        )

        if room_booked:
            messages.error(self.request, 'The room is not available for the selected dates.')
            return self.form_invalid(form)

        if int(num_guests) > room.capacity:
            messages.error(self.request, 'Room capacity is lower than the number of guests requested')
            return self.form_invalid(form)

        booking = Booking(
            room=room,
            author=self.request.user,
            check_in=check_in,
            check_out=check_out,
            num_guests=num_guests
        )
        booking.save()
        messages.success(self.request, 'Booking registered successfully!')
        return super().form_valid(form)


class BookingHistoryView(LoginRequiredMixin, TemplateView):
    """
    A view to display the booking history of a logged-in user.
    This view shows two lists: confirmed_bookings and canceled_bookings
    for the authenticated user.
    """
    template_name = 'booking_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Fetch confirmed and canceled bookings for the current user and order them by creation date
        confirmed_bookings = Booking.objects.filter(author=user, status=booking_status_confirmed).order_by('-created_at')
        canceled_bookings = Booking.objects.filter(author=user, status=booking_status_canceled).order_by('-created_at')
        pending_bookings = Booking.objects.filter(author=user, status=booking_status_pending).order_by('-created_at')
        context['confirmed_bookings'] = confirmed_bookings
        context['canceled_bookings'] = canceled_bookings
        context['pending_bookings'] = pending_bookings
        return context

    def post(self, request, *args, **kwargs):
        """
        Handle the post request for canceling a booking.
        This method is invoked when the user tries to cancel a booking from the booking history page.
        It changes the status of the booking to 'Canceled' and displays a success message.
        """
        user = self.request.user
        cancel_booking_id = request.POST.get('cancel-booking-id')
        booking = get_object_or_404(Booking, id=cancel_booking_id)
        canceled_status = get_object_or_404(BookingStatus, name='Canceled')

        if booking and user == booking.author and canceled_status:
            booking.status = canceled_status
            booking.save()
            messages.success(self.request, 'Booking canceled successfully!')
        return redirect(reverse('bookingHistory'))


class ReviewHistoryView(LoginRequiredMixin, ListView):
    """View for displaying the review history of a user."""
    model = HotelReview
    template_name = 'review_history.html'
    context_object_name = 'reviews_data'
    ordering = '-created_at'

    def get_queryset(self):
        user = self.request.user
        return super().get_queryset().filter(author=user).select_related('hotel')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reviews_data = []
        for review in context['reviews_data']:
            data = {
                'comment': review.comment,
                'hotel_name': review.hotel.name,
                'hotel_photo': review.hotel.hotelphotos.first().photo_url,
                'hotel_stars': review.hotel.draw_stars,
                'created_at': review.created_at,
                'rating': None
            }
            rating = HotelRating.objects.filter(author=self.request.user, hotel=review.hotel).first()
            if rating:
                data['rating'] = rating.value
            reviews_data.append(data)
        context['reviews_data'] = reviews_data
        return context


class UserFavouriteView(LoginRequiredMixin, ListView):
    """View for displaying user's favorite hotels and allowing them to add/remove favorites."""
    model = UserFavourite
    template_name = 'favourites.html'
    context_object_name = 'favourites_data'

    def get_queryset(self):
        user = self.request.user
        return super().get_queryset().filter(user=user).select_related('hotel')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        favourites_data = []
        for favourite in context['favourites_data']:
            data = {
                'hotel': favourite.hotel,
                'hotel_name': favourite.hotel.name,
                'hotel_photo': favourite.hotel.hotelphotos.first().photo_url,
                'hotel_stars': favourite.hotel.draw_stars,
            }
            favourites_data.append(data)
        context['favourites_data'] = favourites_data
        return context

    def post(self, request, *args, **kwargs):
        hotel_id = request.POST.get('fav_hotel_id')
        try:
            user_favourite = UserFavourite.objects.get(user=self.request.user, hotel_id=hotel_id)
            user_favourite.delete()
        except UserFavourite.DoesNotExist:
            pass  # If the favorite doesn't exist, do nothing.
        return redirect(reverse('userFavourite'))


class BookingsView(PermissionRequiredMixin, ListView):
    permission_required = 'base.booking_add'
    template_name = 'booking_list.html'
    model = Booking
    context_object_name = 'bookings'


class BookingUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = 'base.booking_change'
    template_name = 'booking_update.html'
    model = Booking
    fields = ['status']
    success_url = reverse_lazy('bookingsList')

    def form_valid(self, form):
        status = form.instance.status
        self._send_email_booking_status_changed(status)
        return super().form_valid(form)

    def _send_email_booking_status_changed(self, status):
        current_site = get_current_site(self.request)
        context = self.get_context_data()
        booking = context.get('booking')
        user = booking.author
        hotel = booking.room.hotel.name
        check_in = booking.check_in
        check_out = booking.check_out

        subject = 'BookingApp - Booking status changed'
        from_email = 'mswbooking@gmail.com'
        to = [user.email]
        html_message = render_to_string(
            'emails/booking_status_changed.html',
            {
                'domain': current_site.domain,
                'hotel': hotel,
                'check_in': check_in,
                'check_out': check_out,
                'status': status
            }
        )
        plain_message = strip_tags(html_message)

        send_mail(subject=subject,
                  message=plain_message,
                  from_email=from_email,
                  recipient_list=to,
                  html_message=html_message)