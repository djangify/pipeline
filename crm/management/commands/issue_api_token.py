# crm/management/commands/issue_api_token.py
"""
Prints the DRF API token for a user, creating one if it doesn't exist yet.

Use this to get a token for a script to call Pipeline's REST API with:
    Authorization: Token <token>

Usage:
    python manage.py issue_api_token                  # uses DEFAULT_USER_EMAIL
    python manage.py issue_api_token you@example.com
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = "Prints (creating if needed) the API token for a user."

    def add_arguments(self, parser):
        parser.add_argument("email", nargs="?", default=None)

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"] or os.environ.get("DEFAULT_USER_EMAIL", "admin@example.com")

        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            raise CommandError(
                f"No user '{email}'. Pass an existing user's email, or run "
                "create_default_user first."
            )

        token, _ = Token.objects.get_or_create(user=user)
        self.stdout.write(token.key)
