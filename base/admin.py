from django.contrib import admin
from .models import *

# SIMPLE MODELS
admin.site.register(Category)
admin.site.register(City)
admin.site.register(Province)
admin.site.register(Country)
admin.site.register(Feature)

# MAIN
admin.site.register(Hotel)
admin.site.register(Room)
admin.site.register(BookingStatus)


@admin.register(Booking)
class NoteAdmin(admin.ModelAdmin):
    list_display = ["author", "room", "status", "check_in", "check_out", "num_guests", "created_at"]


# HOTEL ATTRIBUTES
admin.site.register(HotelPhoto)
admin.site.register(HotelReview)
admin.site.register(HotelRating)

# HOTEL RANKING/OPINIONS
admin.site.register(HotelFeature)
admin.site.register(RoomFeature)
admin.site.register(UserFavourite)



