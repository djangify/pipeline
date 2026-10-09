# crm/management/commands/create_default_user.py
"""
Creates the first login with a random password.

The packaged app runs this on first launch. There is no built-in password: a
random one is generated and saved to first_login.txt in the data folder, which
the app opens in Notepad. Log in, change the password under "Change password",
then delete that file (Pipeline deletes it for you when the password changes).

    python manage.py create_default_user            # first login (does nothing if one exists)
    python manage.py create_default_user --reset    # forgotten password: new random password

Optional settings (see .env.example): DEFAULT_USER_EMAIL chooses the login name;
DEFAULT_USER_PASSWORD uses a password you choose instead of a random one.
"""
import secrets
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

# No look-alike characters (0/O, 1/l/I) so the password is easy to read and type.
_ALPHABET = "".join(c for c in string.ascii_letters + string.digits if c not in "0O1lI")

FIRST_LOGIN_FILE = "first_login.txt"


def generate_password(length=16):
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


class Command(BaseCommand):
    help = (
        "Create the first login (random password) if no user exists. "
        "Use --reset to give the owner's login a new random password."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Set a NEW random password for the owner's login (forgotten password).",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        email = settings.DEFAULT_USER_EMAIL
        configured_password = settings.DEFAULT_USER_PASSWORD
        reset = options["reset"]

        if User.objects.exists() and not reset:
            self.stdout.write("A login already exists -- nothing to do.")
            return

        password = configured_password or generate_password()

        if reset:
            # Single-owner tool: the login to reset is the default one, or else the
            # oldest account.
            user = (
                User.objects.filter(username=email).first()
                or User.objects.order_by("date_joined", "pk").first()
            )
            if user is None:
                raise CommandError("There is no login to reset yet. Run this without --reset first.")
            user.set_password(password)
            user.save(update_fields=["password"])
            action = "Password reset"
            email = user.get_username()
        else:
            # Pipeline is a single-owner tool: every login is a superuser.
            User.objects.create_superuser(username=email, email=email, password=password)
            action = "Created login"

        # Only write the password to disk when we generated it. If the owner chose
        # one (DEFAULT_USER_PASSWORD) there is nothing to hand back.
        if configured_password:
            self.stdout.write(self.style.SUCCESS(f"{action}: {email} (password from DEFAULT_USER_PASSWORD)"))
            return

        note = settings.DATA_DIR / FIRST_LOGIN_FILE
        note.write_text(
            "Pipeline login\n"
            f"Email:    {email}\n"
            f"Password: {password}\n\n"
            "Log in, click Change password, choose your own password.\n"
            "Pipeline then deletes this file. If it is still here, delete it yourself.\n",
            encoding="utf-8",
        )
        self.stdout.write(self.style.SUCCESS(f"{action}: {email}"))
        self.stdout.write(f"Password: {password}")
        self.stdout.write(f"(also saved in {note} - it is deleted when you change your password)")
