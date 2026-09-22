import os
import sys
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# Where user data (database, uploaded files) is stored. When running as a
# packaged desktop app (PyInstaller .exe), the program files live in a
# temporary, read-only folder, so user data must be written to a persistent,
# writable location instead. A normal dev run keeps using the project's own
# "data" folder exactly as before.
if os.environ.get("PIPELINE_DATA_DIR"):
    # Explicit override, e.g. for running from source against the same data
    # folder a packaged build uses.
    DATA_DIR = Path(os.environ["PIPELINE_DATA_DIR"])
elif getattr(sys, "frozen", False):
    DATA_DIR = (
        Path(
            os.environ.get("LOCALAPPDATA")
            or os.environ.get("APPDATA")
            or Path.home()
        )
        / "Pipeline"
    )
else:
    DATA_DIR = BASE_DIR / "data"

(DATA_DIR / "db").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "media").mkdir(parents=True, exist_ok=True)

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-key-change-in-production")
DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

INSTALLED_APPS = [
    "adminita",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "crm",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db" / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Desktop (PyWebView) mode: let WhiteNoise serve admin/DRF's static files
# straight from the installed packages via the staticfiles finders, so the
# packaged app works without having run collectstatic.
if os.environ.get("PIPELINE_DESKTOP") == "1":
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_AUTOREFRESH = True

MEDIA_URL = "/media/"
MEDIA_ROOT = DATA_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "crm:contact_list"
LOGOUT_REDIRECT_URL = "login"

# Used by crm.management.commands.followup_reminders to build links in the
# reminder email, and as DEFAULT_FROM_EMAIL's domain when nothing else is set.
PRIMARY_DOMAIN = env("PRIMARY_DOMAIN", default="http://127.0.0.1:8000")
FOLLOWUP_REMINDER_TO = env("FOLLOWUP_REMINDER_TO", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="pipeline@example.com")

EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
