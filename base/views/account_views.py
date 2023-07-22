from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import View, TemplateView, UpdateView, FormView

from base.forms import CustomRegistrationForm


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
                str(user.is_active) + str(user.pk) + str(timestamp)
        )


email_verification_token = EmailVerificationTokenGenerator()


class RegistrationView(FormView):
    template_name = 'account/register.html'
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
    template_name = 'account/login.html'
    fields = '__all__'
    redirect_authenticated_user = True
    success_url = reverse_lazy('homePage')


class CustomPasswordResetView(PasswordResetView):
    template_name = 'account/password_reset.html'
    form_class = PasswordResetForm
    html_email_template_name = "emails/password_reset.html"
    title = "BookingApp - Password reset"

    def get_context_data(self, **kwargs):
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
    template_name = 'account/password_change.html'
    form_class = PasswordChangeForm

    def get_success_url(self):
        return reverse('profile', kwargs={'pk': self.request.user.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Password changed successfully')
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'account/profile.html'
    model = User
    fields = ['username', 'first_name', 'last_name']

    def get_success_url(self):
        return reverse('profile', kwargs={'pk': self.request.user.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully')
        return super().form_valid(form)