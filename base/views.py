import datetime

from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.contrib.sites.shortcuts import get_current_site
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.html import strip_tags
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import View, TemplateView, UpdateView, FormView

from .forms import CustomRegistrationForm, HotelReviewForm, BookingDatesForm, BookingForm, HotelRatingForm
from .models import Category, Hotel, HotelPhoto, City, Room, HotelFeature, HotelReview, HotelRating, Booking, \
    BookingStatus, UserFavourite


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
                str(user.is_active) + str(user.pk) + str(timestamp)
        )


email_verification_token = EmailVerificationTokenGenerator()


class RegistrationView(FormView):
    template_name = 'register.html'
    form_class = CustomRegistrationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('activationPending')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        # userprofile TODO
        user.save()
        self._send_email_verification(user)
        return super().form_valid(form)

    def _send_email_verification(self, user):
        current_site = get_current_site(self.request)
        subject = 'BookingApp - Activate Your Account'
        from_email = 'mswbooking@gmail.com'
        to = [user.email]
        html_message = render_to_string(
            'emails/email_verification.html',
            {
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': email_verification_token.make_token(user),
            }
        )
        plain_message = strip_tags(html_message)

        send_mail(subject=subject,
                  message=plain_message,
                  from_email=from_email,
                  recipient_list=to,
                  html_message=html_message)


class ActivateView(View):
    def get_user_from_email_verification_token(self, uidb64: str, token: str):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError,
                get_user_model().DoesNotExist):
            return None

        if user is not None and email_verification_token.check_token(user, token):
            return user

        return None

    def get(self, request, uidb64, token):
        user = self.get_user_from_email_verification_token(uidb64, token)
        if user is not None:
            user.is_active = True
            user.save()
            login(request, user)
            return redirect('activationSuccess')
        else:
            return redirect('activationError')


class ActivationErrorView(TemplateView):
    template_name = 'message.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = 'Something went wrong or your activation link expired.'
        return context


class ActivationPendingView(TemplateView):
    template_name = 'message.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = 'Activation link has been sent to your email address.'
        return context


class ActivationSuccessView(TemplateView):
    template_name = 'message.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = 'Account activated successfully, you are now logged in'
        return context


class CustomLoginView(LoginView):
    template_name = 'login.html'
    fields = '__all__'
    redirect_authenticated_user = True
    success_url = reverse_lazy('homePage')


class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset.html'
    form_class = PasswordResetForm
    html_email_template_name = "emails/password_reset.html"
    title = "BookingApp - Password reset"

    def get_context_data(self, **kwargs):
        print(kwargs)
        return super().get_context_data()


class CustomPasswordResetDoneView(TemplateView):
    template_name = 'message.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['message'] = 'Password reset link was sent to the given email'
        return context


class CustomPasswordComplete(TemplateView):
    template_name = 'message.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['message'] = 'Password changed successfully, you can now log in'
        return context


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'password_change.html'
    form_class = PasswordChangeForm

    def get_success_url(self):
        return reverse('profile', kwargs={'pk': self.request.user.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Password changed successfully')
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'profile.html'
    model = User
    fields = ['username', 'first_name', 'last_name']

    def get_success_url(self):
        return reverse('profile', kwargs={'pk': self.request.user.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully')
        return super().form_valid(form)


class HomePageView(FormView):
    template_name = 'index.html'
    form_class = BookingDatesForm

    def get(self, request, *args, **kwargs):
        check_in = request.GET.get('check_in', '')
        check_out = request.GET.get('check_out', '')
        num_guests = request.GET.get('num_guests', '')

        form_errors = None
        form = self.form_class(request.GET)
        if check_in and check_out and num_guests and form.errors:
            form_errors = form.errors
            check_in = ''
            check_out = ''
            num_guests = ''
        status_confirmed = get_object_or_404(BookingStatus, name='Confirmed')
        if form.is_valid():
            available_rooms = Room.objects.filter(
                ~Q(bookings__check_in__lt=check_out,
                   bookings__check_out__gt=check_in,
                   bookings__status=status_confirmed),
                capacity__gte=num_guests)

            category_ids = available_rooms.values_list('hotel__category__id', flat=True)
            categories = Category.objects.filter(id__in=category_ids)
            hotels = Hotel.objects.filter(rooms__in=available_rooms).distinct()
            category_data = []
            for category in categories:
                hotels_filtered = hotels.filter(category=category)
                hotels_counter = len([hotel for hotel in hotels_filtered])
                data = {
                    'category': category,
                    'hotels_counter': hotels_counter
                }
                category_data.append(data)
        else:
            form = self.form_class()
            categories = Category.objects.with_hotel_count().order_by('-hotel_count')
            category_data = []
            for category in categories:
                data = {
                    'category': category,
                    'hotels_counter': category.hotels.count()
                }
                category_data.append(data)

        cities = City.objects.all()
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


class CategoryListingView(FormView):
    template_name = 'category.html'
    form_class = BookingDatesForm
    paginate_by = 3

    def get(self, request, *args, **kwargs):
        check_in = request.GET.get('check_in', '')
        check_out = request.GET.get('check_out', '')
        num_guests = request.GET.get('num_guests', '')
        category_name = kwargs.get('category_name', '')

        category = Category.objects.get(name=category_name)
        form_errors = None
        hotel_data = []
        form = self.form_class(request.GET)

        if check_in and check_out and num_guests:
            form_errors = form.errors

        status_confirmed = get_object_or_404(BookingStatus, name='Confirmed')
        if form.is_valid():
            available_rooms = Room.objects.filter(
                ~Q(bookings__check_in__lt=check_out,
                   bookings__check_out__gt=check_in,
                   bookings__status=status_confirmed),
                capacity__gte=num_guests)

            hotels = Hotel.objects.filter(rooms__in=available_rooms, category=category).distinct()

            for hotel in hotels:
                first_photo_url = HotelPhoto.get_first_photo_url(hotel)
                available_hotel_rooms = available_rooms.filter(hotel=hotel)
                if available_hotel_rooms:
                    min_price = min(room.price for room in available_hotel_rooms)
                else:
                    min_price = 0
                available_room_count = available_rooms.filter(hotel=hotel).count()
                hotel_favourite = UserFavourite.objects.filter(hotel=hotel, user=self.request.user)
                hotel_data.append({
                    'hotel': hotel,
                    'hotel_favourite': hotel_favourite,
                    'min_price': min_price,
                    'first_photo_url': first_photo_url,
                    'available_room_count': available_room_count,
                })
        else:
            form = self.form_class()
            hotels = Hotel.objects.filter(category=category)
            for hotel in hotels:
                first_photo_url = HotelPhoto.get_first_photo_url(hotel)

                available_hotel_rooms = Room.objects.filter(hotel=hotel)
                if available_hotel_rooms:
                    min_price = min(room.price for room in available_hotel_rooms)
                else:
                    min_price = 0

                available_room_count = available_hotel_rooms.filter(hotel=hotel).count()
                hotel_favourite = UserFavourite.objects.filter(hotel=hotel, user=self.request.user)
                hotel_data.append({
                    'hotel': hotel,
                    'hotel_favourite': hotel_favourite,
                    'min_price': min_price,
                    'first_photo_url': first_photo_url,
                    'available_room_count': available_room_count,
                })

        paginator = Paginator(hotel_data, self.paginate_by)
        page = request.GET.get('page')

        try:
            paginated_hotel_data = paginator.page(page)
        except PageNotAnInteger:
            paginated_hotel_data = paginator.page(1)
        except EmptyPage:
            paginated_hotel_data = paginator.page(paginator.num_pages)

        context = {
            'hotel_data': paginated_hotel_data,
            'form_errors': form_errors,
            'check_in': check_in,
            'check_out': check_out,
            'num_guests': num_guests,
            'form': form,
        }

        return render(request, template_name=self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        category_name = kwargs.get('category_name')
        hotel_id = request.POST.get('fav_hotel_id')
        user = self.request.user
        hotel = Hotel.objects.get(id=hotel_id)
        user_favourite = UserFavourite.objects.filter(user=user, hotel=hotel)
        if not user_favourite:
            user_favourite = UserFavourite(user=user, hotel=hotel)
            user_favourite.save()
        else:
            user_favourite = UserFavourite.objects.get(user=user, hotel=hotel)
            user_favourite.delete()
        return redirect(reverse('categoryListing', kwargs={'category_name': category_name}))


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


class HotelDetailedView(FormView):
    template_name = 'hotel.html'

    def get(self, request, *args, **kwargs):
        core_form = BookingDatesForm
        comment_form = HotelReviewForm
        rate_form = HotelRatingForm

        check_in = request.GET.get('check_in', '')
        check_out = request.GET.get('check_out', '')
        num_guests = request.GET.get('num_guests', '')

        hotel_name = kwargs['hotel_name']
        hotel = Hotel.objects.get(name=hotel_name)
        rooms = Room.objects.filter(hotel=hotel)
        user = self.request.user

        core_form_errors = None
        core_form = core_form(request.GET)
        if check_in and check_out and num_guests:
            core_form_errors = core_form.errors

        if core_form.is_valid():
            core_form = BookingDatesForm(
                initial={
                    'check_in': check_in,
                    'check_out': check_out,
                    'num_guests': num_guests})

            status_confirmed = get_object_or_404(BookingStatus, name='Confirmed')
            rooms = Room.objects.filter(
                ~Q(bookings__check_in__lt=check_out,
                   bookings__check_out__gt=check_in,
                   bookings__status=status_confirmed), capacity__gte=num_guests
                ).filter(hotel=hotel)

        hotel_features = HotelFeature.objects.filter(hotel=hotel)
        hotel_photos = HotelPhoto.objects.filter(hotel=hotel)
        hotel_reviews = HotelReview.objects.filter(hotel=hotel)
        hotel_rating = HotelRating.objects.filter(hotel=hotel)

        user_hotel_rating = ''
        if user.is_authenticated:
            user_hotel_rating = HotelRating.objects.filter(hotel=hotel, author=user).first()

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
            'comment_form': comment_form,
            'rate_form': rate_form,
            'check_in': check_in,
            'check_out': check_out,
            'num_guests': num_guests,
                   }

        return render(request,
                      template_name=self.template_name,
                      context=context)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        hotel_name = kwargs['hotel_name']
        hotel = Hotel.objects.get(name=hotel_name)
        rating_value = request.POST.get('rating')
        comment = request.POST.get('comment')

        if rating_value:
            user_hotel_rating, created = HotelRating.objects.get_or_create(
                hotel=hotel,
                author=user,
                defaults={'value': rating_value}
            )

            if not created:
                user_hotel_rating.value = rating_value
                user_hotel_rating.save()

        # remove hotel Review
        review_id = request.POST.get('delete-review-id')
        if review_id:
            review = HotelReview.objects.get(id=review_id)
            if request.user == review.author or request.user.is_staff:
                review.delete()
                return redirect(reverse('hotelDetails', kwargs={'hotel_name': hotel_name}))

        if comment:
            hotel = Hotel.objects.get(name=hotel_name)
            hotel_review = HotelReview(hotel=hotel,
                                       author=user,
                                       comment=comment)
            hotel_review.save()

        return redirect(reverse('hotelDetails', kwargs={'hotel_name': hotel_name}))


class RoomBookingView(LoginRequiredMixin, FormView):
    form_class = BookingForm
    template_name = 'room_booking.html'
    success_url = reverse_lazy('bookingHistory')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hotel_name = self.kwargs.get('hotel_name')
        room_id = self.kwargs.get('room_id')
        hotel = Hotel.objects.get(name=hotel_name)
        hotel_rating = HotelRating(hotel=hotel)
        room = Room.objects.get(id=room_id)
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

        booking = Booking(room=room,
                          author=self.request.user,
                          check_in=check_in,
                          check_out=check_out,
                          num_guests=num_guests)
        booking.save()
        messages.success(self.request, 'Booking registered successfully!')
        return super().form_valid(form)


class BookingHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'booking_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        user = self.request.user
        status_confirmed = get_object_or_404(BookingStatus, name='Confirmed')
        status_canceled = get_object_or_404(BookingStatus, name='Canceled')
        confirmed_bookings = Booking.objects.filter(author=user, status=status_confirmed).order_by('-created_at')
        canceled_bookings = Booking.objects.filter(author=user, status=status_canceled).order_by('-created_at')
        context['confirmed_bookings'] = confirmed_bookings
        context['canceled_bookings'] = canceled_bookings
        return context

    def post(self, request, *args, **kwargs):
        user = self.request.user
        cancel_booking_id = request.POST.get('cancel-booking-id')
        booking = get_object_or_404(Booking, id=cancel_booking_id)
        canceled_status = get_object_or_404(BookingStatus, name='Canceled')

        if booking and user == booking.author and canceled_status:
            booking.status = canceled_status
            booking.save()
            messages.success(self.request, 'Booking canceled successfully!')
        return redirect(reverse('bookingHistory'))


class ReviewHistoryView(LoginRequiredMixin, View):
    template_name = 'review_history.html'

    def get(self, request, *args, **kwargs):
        user = self.request.user
        reviews = HotelReview.objects.filter(author=user).order_by('-created_at')

        reviews_data = []
        for review in reviews:
            data = {
                'comment': review.comment,
                'hotel_name': review.hotel.name,
                'hotel_photo': review.hotel.hotelphotos.first().photo_url,
                'hotel_stars': review.hotel.draw_stars,
                'created_at': review.created_at,
                'rating': None
            }
            rating = HotelRating.objects.filter(author=user, hotel=review.hotel).first()
            if rating:
                data['rating'] = rating.value
            reviews_data.append(data)

        context = {
            'reviews_data': reviews_data
        }
        return render(request, template_name=self.template_name, context=context)


class UserFavouriteView(LoginRequiredMixin, View):
    template_name = 'favourites.html'

    def get(self, request, *args, **kwargs):
        user = self.request.user

        favourites = UserFavourite.objects.filter(user=user)

        favourites_data = []
        for favourite in favourites:
            data = {
                'hotel': favourite.hotel,
                'hotel_name': favourite.hotel.name,
                'hotel_photo': favourite.hotel.hotelphotos.first().photo_url,
                'hotel_stars': favourite.hotel.draw_stars,
            }
            favourites_data.append(data)

        context = {
            'favourites_data': favourites_data
        }
        return render(request, template_name=self.template_name, context=context)


class AddToFavouritesView(View):

    def post(self, request, *args, **kwargs):
        hotel_id = request.POST.get('fav_hotel_id')
        user = request.user
        hotel = Hotel.objects.get(id=hotel_id)
        user_favourite = UserFavourite.objects.get(user=user, hotel=hotel)
        if not user_favourite:
            UserFavourite(user=user, hotel=hotel)
        return reverse_lazy('homePage')
