from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

class Province(models.Model):
    name = models.CharField(max_length=100, unique=True)
    country = models.ForeignKey(Country, related_name='provinces', on_delete=models.DO_NOTHING)

    def __str__(self):
        return f"{self.name}" - {self.province.name} - {self.province.country.name}


class City(models.Model):
    name = models.CharField(max_length=100)
    province = models.ForeignKey(Province, related_name='cities', on_delete=models.DO_NOTHING)

    def __str__(self):
        return f"{self.name} - {self.province.name} - {self.province.country.name}"


class Hotel(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    city = models.ForeignKey(City, related_name='hotels', on_delete=models.RESTRICT)
    #province =
    #country =
    stars = models.PositiveIntegerField()
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    category = models.ForeignKey(Category, related_name='hotels', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.city.name}, {self.city.province.country.name})"

    # @property
    # def overall_rating(self):
    #     return self.likes.count()

    @property
    def total_rating_votes(self):
        return self.hotelratings.count()

    @property
    def total_comments(self):
        return self.hotelreviews.count()


class HotelPhoto(models.Model):
    description = models.CharField(max_length=100)
    photo = models.ImageField(null=True, blank=True)
    hotel = models.ForeignKey(Hotel, related_name='hotelphotos', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.description}"

    @property
    def image_url(self):
        try:
            photo = self.photo.url
        except:
            photo = ''
        return photo


class Room(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    capacity = models.PositiveIntegerField()
    hotel = models.ForeignKey(Hotel, related_name='rooms', on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.name} | {self.capacity} | {self.hotel.name}"


class Feature(models.Model):
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.description


class HotelFeature(models.Model):
    feature = models.ForeignKey(Feature, related_name='hotelfeatures', on_delete=models.DO_NOTHING)
    hotel = models.ForeignKey(Hotel, related_name='hotelfeatures', on_delete=models.DO_NOTHING)


class RoomFeature(models.Model):
    feature = models.ForeignKey(Feature, related_name='roomfeatures', on_delete=models.DO_NOTHING)
    hotel = models.ForeignKey(Room, related_name='roomfeatures', on_delete=models.DO_NOTHING)


class HotelReview(models.Model):
    comment = models.TextField()
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    hotel = models.ForeignKey(Hotel, related_name='hotelreviews', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='hotelreviews', on_delete=models.DO_NOTHING)

    def __str__(self):
        return f"@{self.author.username} | {self.comment} | {self.hotel.name}"


class HotelRating(models.Model):
    value = models.IntegerField()
    created_at = models.DateField(auto_now_add=True)
    hotel = models.ForeignKey(Hotel, related_name='hotelratings', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='hotelratings', on_delete=models.DO_NOTHING)

    def __str__(self):
        return f"@{self.author.username} | {self.value} | {self.hotel.name}"


class Booking(models.Model):
    check_in = models.DateField()
    check_out = models.DateField()
    num_guests = models.PositiveIntegerField()
    special_request = models.TextField()
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    room = models.ForeignKey(Room, related_name='bookings', on_delete=models.RESTRICT)
    author = models.ForeignKey(User, related_name='bookings', on_delete=models.RESTRICT)
    # status?

    def __str__(self):
        return f"{self.user.username} | {self.room.hotel.name} | {self.check_in}-{self.check_out}"

    @property
    def total_days(self):
        return self.check_out-self.check_in
