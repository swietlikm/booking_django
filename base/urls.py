"""
Main urls for base of booking app
"""
from django.urls import path
from django.contrib.auth.views import LogoutView, PasswordResetConfirmView

from base.views import account_views, core_views

urlpatterns = [

    # ACCOUNT VIEWS
    path('register/', account_views.RegistrationView.as_view(), name='register'),
    path('login/', account_views.CustomLoginView.as_view(next_page='homePage'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/<int:pk>', account_views.ProfileView.as_view(), name='profile'),
    path('activate/<uidb64>/<token>', account_views.ActivateView.as_view(), name='activate'),
    path('activate/pending', account_views.ActivationPendingView.as_view(), name='activationPending'),
    path('activate/error', account_views.ActivationErrorView.as_view(), name='activationError'),
    path('activate/success', account_views.ActivationSuccessView.as_view(), name='activationSuccess'),
    path('profile/change-password', account_views.CustomPasswordChangeView.as_view(), name='change_password'),
    path('password-reset/', account_views.CustomPasswordResetView.as_view(), name='reset_password'),
    path('password-reset/done/', account_views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/', account_views.CustomPasswordComplete.as_view(), name='password_reset_complete'),

    # CORE VIEWS
    path("", core_views.HomePageView.as_view(), name='homePage'),
    path("category/<str:category_name>", core_views.CategoryListingView.as_view(), name='categoryListing'),
    path("city/<int:city_id>", core_views.CityListingView.as_view(), name='cityListing'),
    path("hotel/<str:hotel_name>", core_views.HotelDetailedView.as_view(), name='hotelDetails'),
    path("book/<str:hotel_name>/<int:room_id>", core_views.RoomBookingView.as_view(), name='roomBooking'),

    path("account/profile/", core_views.HomePageView.as_view(), name='accountDetails'),
    path("account/reviews/", core_views.ReviewHistoryView.as_view(), name='reviewHistory'),
    path("account/favourite/", core_views.UserFavouriteView.as_view(), name='userFavourite'),

    path("bookings/", core_views.BookingHistoryView.as_view(), name='bookingHistory'),
]
