# crm/management/commands/create_default_user.py
"""
Optionally creates the first login from environment variables, for hands-off
installs. There is no built-in default account: with nothing set, this does
nothing, and the first visit to Pipeline shows a setup page where the owner
chooses their own email and password.

Safe to run every time -- it does nothing once any user already exists.

Configure via environment variables (see .env.example), both required:
    DEFAULT_USER_EMAIL
    DEFAULT_USER_PASSWORD
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates the first superuser from DEFAULT_USER_EMAIL/PASSWORD, if set and no users exist."

    def handle(self, *args, **options):
        User = get_user_model()

        if User.objects.exists():
            self.stdout.write("A user already exists -- skipping default user creation.")
            return

        email = os.environ.get("DEFAULT_USER_EMAIL", "").strip()
        password = os.environ.get("DEFAULT_USER_PASSWORD", "")
        if not email or not password:
            self.stdout.write(
                "DEFAULT_USER_EMAIL/DEFAULT_USER_PASSWORD not set -- the owner "
                "creates their login on the setup page."
            )
            return

        User.objects.create_superuser(
            username=email,
            email=email,
            password=password,
        )
        self.stdout.write(
            self.style.SUCCESS(f"Created default login -- email: {email}")
        )
