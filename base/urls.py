"""
Main urls for base of booking app
"""
from django.urls import path
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetCompleteView
)
from . import views

urlpatterns = [
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(next_page='homePage'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/<int:pk>', views.ProfileView.as_view(), name='profile'),
    path('activate/<uidb64>/<token>', views.ActivateView.as_view(), name='activate'),
    path('activate/pending', views.ActivationPendingView.as_view(), name='activationPending'),
    path('activate/error', views.ActivationErrorView.as_view(), name='activationError'),
    path('activate/success', views.ActivationSuccessView.as_view(), name='activationSuccess'),
    path('profile/change-password', views.CustomPasswordChangeView.as_view(), name='change_password'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='reset_password'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/', views.CustomPasswordComplete.as_view(), name='password_reset_complete'),

    path("", views.HomePageView.as_view(), name='homePage'),
    path("category/<str:category_name>",views.CategoryListingView.as_view(), name='categoryListing'),
    path("city/<int:city_id>", views.CityListingView.as_view(), name='cityListing'),
    path("hotel/<str:hotel_name>", views.HotelDetailedView.as_view(), name='hotelDetails'),
    path("hotel/add-to-favourite/<int:pk>", views.AddToFavouritesView.as_view(), name='addFavouriteHotel'),
    path("book/<str:hotel_name>/<int:room_id>", views.RoomBookingView.as_view(), name='roomBooking'),

    path("account/profile/", views.HomePageView.as_view(), name='accountDetails'),
    path("account/reviews/", views.ReviewHistoryView.as_view(), name='reviewHistory'),
    path("account/favourite/", views.UserFavouriteView.as_view(), name='userFavourite'),

    path("bookings/", views.BookingHistoryView.as_view(), name='bookingHistory'),
]

