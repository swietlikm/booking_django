import datetime

from bootstrap_datepicker_plus.widgets import DatePickerInput
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import HotelReview, Booking


class CustomRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.IntegerField(required=True)

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if len(str(phone_number)) != 9:
            self._update_errors(
                forms.ValidationError(
                    {
                        "phone_number": "Phone number must contain 9 digits"
                    }
                )
            )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if (
            email
            and self._meta.model.objects.filter(email__iexact=email).exists()
        ):
            self._update_errors(
                forms.ValidationError(
                    {
                        "email": "This email already exists in database"
                    }
                )
            )
        else:
            return email

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name', 'phone_number', 'email']


class CustomProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    phone_number = forms.IntegerField(required=True)

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if len(str(phone_number)) != 9:
            self._update_errors(
                forms.ValidationError(
                    {
                        "phone_number": "Phone number must contain 9 digits"
                    }
                )
            )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        user = self.instance

        if email and email.lower() != user.email.lower():
            if self._meta.model.objects.filter(email__iexact=email).exists():
                self._update_errors(
                    forms.ValidationError(
                        {
                            "email": "This email already exists in the database"
                        }
                    )
                )
        return email

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone_number', 'email']


class HotelReviewForm(forms.ModelForm):
    class Meta:
        model = HotelReview
        fields = ['comment']


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['special_request']


class BookingDatesForm(forms.ModelForm):
    def clean(self, *args, **kwargs):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        num_guests = cleaned_data.get('num_guests')

        if not isinstance(check_in, datetime.date):
            raise forms.ValidationError("Check-in has got an incorrect date format. Must be: yyyy-mm-dd")
        if not isinstance(check_out, datetime.date):
            raise forms.ValidationError("Check-out has got an incorrect date format. Must be: yyyy-mm-dd")

        errors = []
        if check_in < datetime.date.today():
            errors.append(forms.ValidationError("Check-in can not be in the past date"))
        if check_in == check_out:
            errors.append(forms.ValidationError("Check out must be minimum 1 day after check-in"))
        if check_in > check_out:
            errors.append(forms.ValidationError("Check-out must be after check-in"))
        if num_guests < 1:
            errors.append(forms.ValidationError("There must be minimum 1 guest"))
        if errors:
            raise forms.ValidationError(errors)
        return cleaned_data

    class Meta:
        model = Booking
        fields = ['check_in', 'check_out', 'num_guests']
        widgets = {
            'check_in': DatePickerInput(),
            'check_out': DatePickerInput(range_from='check_in'),
        }
        labels = {
            'check_in': "Check-in",
            'check_out': "Check-out",
            'num_guests': 'Number of guests',
        }


RATING_CHOICES = (
    (10, '10'),
    (9, '9'),
    (8, '8'),
    (7, '7'),
    (6, '6'),
    (5, '5'),
    (4, '4'),
    (3, '3'),
    (2, '2'),
    (1, '1'),
)


class HotelRatingForm(forms.Form):
    rating = forms.ChoiceField(
        label='Rate the hotel (1-10)',
        choices=RATING_CHOICES,
        widget=forms.Select(),
    )