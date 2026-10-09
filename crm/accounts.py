# crm/accounts.py
"""First-run account creation, so no install ever ships with a default login.

Until the first user exists, the login page sends visitors to /accounts/setup/,
where they choose their own email and password. Once any user exists the setup
page redirects away for good (it can never be used to add a second account).
"""
import threading

from django import forms
from django.contrib.auth import get_user_model, login
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.conf import settings
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.views.generic import FormView


# Waitress serves requests on several threads in one process; without this two
# simultaneous setup posts could both pass the "no users yet" check.
_setup_lock = threading.Lock()


class FirstUserForm(forms.Form):
    email = forms.EmailField(label="Email (this is your username)")
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "The two passwords don't match.")
        elif p1:
            try:
                validate_password(p1)
            except ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned


class PipelineLoginView(LoginView):
    template_name = "registration/login.html"

    def dispatch(self, request, *args, **kwargs):
        if not get_user_model().objects.exists():
            return redirect("setup")
        return super().dispatch(request, *args, **kwargs)


class FirstUserSetupView(FormView):
    template_name = "registration/setup.html"
    form_class = FirstUserForm

    def dispatch(self, request, *args, **kwargs):
        if get_user_model().objects.exists():
            return redirect("login")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        User = get_user_model()
        email = form.cleaned_data["email"]
        # Pipeline is a single-owner tool: every login is a superuser (see
        # docs/USERS.md). Check and create under one lock so simultaneous
        # submits can't create two owners.
        with _setup_lock:
            if User.objects.exists():
                return redirect("login")
            user = User.objects.create_superuser(
                username=email, email=email, password=form.cleaned_data["password1"]
            )
        login(self.request, user)
        return redirect("crm:contact_list")


class PipelinePasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    template_name = "registration/password_change.html"
    success_url = reverse_lazy("crm:contact_list")
    success_message = "Your password has been changed."

    def form_valid(self, form):
        response = super().form_valid(form)
        # The random first password is no longer valid; remove the file that holds it.
        try:
            (settings.DATA_DIR / "first_login.txt").unlink(missing_ok=True)
        except OSError:
            pass
        return response
