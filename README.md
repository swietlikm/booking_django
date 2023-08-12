# Hotel Booking System Documentation

This documentation provides an overview of the Hotel Booking System, which is built using Django.

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Features](#features)
- [Usage](#usage)
- [Views](#views)
- [Templates](#templates)
- [Models](#models)
- [Forms](#forms)
- [Email Notifications](#email-notifications)
- [Screenshots](#screenshots)

## Introduction

The Hotel Booking System is a web application that allows users to search for available rooms, view hotel details, make bookings, and manage their bookings. The application is built using Django and provides a range of views to handle user interactions. For a complete features list see **Features**

## Features

- Register/log-in and manage account (email token activation)
- Password reset using email token
- Set check-in + check-out + numer of guests to display only available hotels and rooms
- Write review of a hotel
- Rate hotel 1-10
- See all reviews in user panel with ratings
- Add hotel to favourites
- See list of favourites in hotel in user panel
- Book hotel
- Cancel booking
- See list of all bookings including canceled
- Change status of booking (by staff) and send email notification

## Installation

1. Clone the repository to your local machine.
2. Install the required dependencies using `pip install -r requirements.txt`.
3. Configure your database settings in `settings.py`.
4. Run migrations using `python manage.py migrate`.
5. Create a superuser account using `python manage.py createsuperuser`.
6. Start the development server using `python manage.py runserver`.

## Usage

- Access the application by navigating to `http://localhost:8000` in your web browser.
- Log in using your superuser account to access admin functionalities.
- Users can browse available rooms, view hotel details, make bookings, and manage their bookings.

## Views

The application provides the following views:

- `HomePageView`: Displays available rooms and hotel categories on the home page.
- `CategoryListingView`: Displays a paginated list of hotels in a specific category.
- `CityListingView`: Displays hotels within a specific city.
- `HotelDetailedView`: Displays detailed information about a hotel.
- `RoomBookingView`: Allows users to book a room in a hotel.
- `BookingHistoryView`: Shows the booking history of a logged-in user.
- `ReviewHistoryView`: Displays the review history of a user.
- `UserFavouriteView`: Displays a user's favorite hotels and allows adding/removing favorites.
- `BookingsView`: Shows a list of bookings (Permission required).
- `BookingUpdateView`: Allows updating booking status (Permission required).

## Templates

The application uses various HTML templates to render different views. Templates are organized into the `templates` directory. Templates are using Bootstrap5. 

## Models

The application defines the following models:

- `Category`: Represents hotel categories.
- `Hotel`: Represents hotels, with related information.
- `HotelPhoto`: Stores hotel photos.
- `City`: Represents cities where hotels are located.
- `Room`: Represents hotel rooms.
- `HotelFeature`: Represents features of a hotel.
- `HotelReview`: Stores hotel reviews by users.
- `HotelRating`: Stores hotel ratings by users.
- `Booking`: Represents bookings made by users.
- `BookingStatus`: Represents different booking statuses.
- `UserFavourite`: Stores favorite hotels of users.

## Forms

The application defines several forms:

- `BookingDatesForm`: Form for entering booking dates.
- `BookingForm`: Form for booking a room in a hotel.
- `HotelReviewForm`: Form for submitting hotel reviews.
- `HotelRatingForm`: Form for rating hotels.

## Email Notifications

The application sends email notifications for various actions, such as booking confirmation and booking status changes. Email templates are located in the `emails` directory. Moreover application using email system for account activation and password reset.

---

For detailed implementation details, refer to the codebase and comments within the source files.