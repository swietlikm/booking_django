import datetime

from django.contrib.auth.models import User
from django.db import models


class CategoryQuerySet(models.QuerySet):
    def with_hotel_count(self):
        return self.annotate(hotel_count=models.Count('hotels'))


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    photo = models.ImageField(null=True, blank=True)
    objects = CategoryQuerySet.as_manager()

    def __str__(self):
        return self.name

    @property
    def total(self):
        return self.hotels.count()

    @property
    def photo_url(self):
        try:
            photo = self.photo.url
        except:
            photo = ''
        return photo


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Province(models.Model):
    name = models.CharField(max_length=100, unique=True)
    country = models.ForeignKey(Country, related_name='provinces', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} - {self.country.name}"


class City(models.Model):
    name = models.CharField(max_length=100)
    province = models.ForeignKey(Province, related_name='cities', on_delete=models.CASCADE)
    photo = models.ImageField(null=True, blank=True)

    objects = CategoryQuerySet.as_manager()

    def __str__(self):
        return f"{self.name} - {self.province.name} - {self.province.country.name}"

    @property
    def total(self):
        return self.hotels.count()

    @property
    def photo_url(self):
        try:
            photo = self.photo.url
        except:
            photo = ''
        return photo


class Hotel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    address = models.CharField(max_length=100)
    city = models.ForeignKey(City, related_name='hotels', on_delete=models.RESTRICT)
    stars = models.PositiveIntegerField()
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    category = models.ForeignKey(Category, related_name='hotels', on_delete=models.RESTRICT)

    objects = models.Manager()

    def __str__(self):
        return f"{self.name} ({self.city.name}, {self.city.province.country.name})"

    @property
    def average_rating(self):
        rating = self.hotelratings.aggregate(avg_rating=models.Avg('value')).get('avg_rating', 0)
        if rating:
            return round(rating, 1)
        else:
            return "No votes yet"

    @property
    def total_rating_votes(self):
        return self.hotelratings.count()

    @property
    def draw_stars(self):
        if self.stars:
            return int(self.stars) * '★'
        else:
            return ''

    @property
    def total_comments(self):
        return self.hotelreviews.count()

    def get_first_photo(self):
        photo = HotelPhoto.objects.filter(hotel=self).first()
        if photo:
            return photo.photo_url
        else:
            return ''


class HotelPhoto(models.Model):
    description = models.CharField(max_length=100)
    photo = models.ImageField(null=True, blank=True)
    hotel = models.ForeignKey(Hotel, related_name='hotelphotos', on_delete=models.CASCADE)

    objects = models.Manager()

    def __str__(self):
        return f"{self.description} | {self.hotel}"

    @property
    def photo_url(self):
        try:
            photo = self.photo.url
        except:
            photo = ''
        return photo

    @classmethod
    def get_first_photo_url(cls, hotel):
        first_photo = cls.objects.filter(hotel=hotel).first()
        if first_photo:
            return first_photo.photo_url
        return ''


class Room(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    capacity = models.PositiveIntegerField()
    hotel = models.ForeignKey(Hotel, related_name='rooms', on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    objects = models.Manager()

    def __str__(self):
        return f"{self.name} | {self.capacity} | {self.hotel.name}"


class Feature(models.Model):
    description = models.CharField(max_length=100)
    objects = models.Manager()

    def __str__(self):
        return self.description


class HotelFeature(models.Model):
    feature = models.ForeignKey(Feature, related_name='hotelfeatures', on_delete=models.CASCADE)
    hotel = models.ForeignKey(Hotel, related_name='hotelfeatures', on_delete=models.CASCADE)
    objects = models.Manager()


class RoomFeature(models.Model):
    feature = models.ForeignKey(Feature, related_name='roomfeatures', on_delete=models.CASCADE)
    room = models.ForeignKey(Room, related_name='roomfeatures', on_delete=models.CASCADE)
    objects = models.Manager()


class HotelReview(models.Model):
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    hotel = models.ForeignKey(Hotel, related_name='hotelreviews', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='hotelreviews', on_delete=models.SET_DEFAULT, default=2)
    objects = models.Manager()

    def __str__(self):
        return f"@{self.author.username} | {self.comment} | {self.hotel.name}"

    class Meta:
        ordering = ['-created_at']


class HotelRating(models.Model):
    value = models.IntegerField()
    created_at = models.DateField(auto_now_add=True)
    hotel = models.ForeignKey(Hotel, related_name='hotelratings', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='hotelratings', on_delete=models.SET_DEFAULT, default=2)
    objects = models.Manager()

    def __str__(self):
        return f"@{self.author.username} | {self.value} | {self.hotel.name}"


class BookingStatus(models.Model):
    name = models.CharField(max_length=50, unique=True)
    objects = models.Manager()

    def __str__(self):
        return self.name


class Booking(models.Model):
    check_in = models.DateField()
    check_out = models.DateField()
    num_guests = models.PositiveIntegerField()
    special_request = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    room = models.ForeignKey(Room, related_name='bookings', on_delete=models.RESTRICT)
    author = models.ForeignKey(User, related_name='bookings', on_delete=models.RESTRICT)
    status = models.ForeignKey(BookingStatus, related_name='bookingstatuses', on_delete=models.RESTRICT, default=1)

    objects = models.Manager()

    def __str__(self):
        return f"{self.author.username} | {self.room.hotel.name} | From: {self.check_in} | To: {self.check_out}"


class UserFavourite(models.Model):
    user = models.ForeignKey(User, related_name='userfavourites', on_delete=models.CASCADE)
    hotel = models.ForeignKey(Hotel, related_name='userfavourites', on_delete=models.CASCADE)
    objects = models.Manager()

    def __str__(self):
        return f"{self.user.username} | {self.hotel.name}"