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
    # Deliberately NOT under AppData: Claude Desktop is an MSIX-packaged app,
    # and Windows silently redirects AppData writes from anything it launches
    # (including Pipeline-mcp.exe) into Claude's own private LocalCache. The
    # app window and the Claude connector then each get a separate database.
    # The user profile folder isn't virtualized, so both see the same file.
    # Keep in sync with desktop._writable_data_dir().
    DATA_DIR = Path.home() / "Pipeline Data"
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
    "rest_framework.authtoken",
    "crm",
    "research",
]

# The frontend (contact_list.html etc.) is server-rendered Django views, not
# API calls, so this only gates the REST endpoints (/api/contacts/,
# /api/research/...) themselves. SessionAuthentication covers a logged-in
# browser hitting the browsable API; TokenAuthentication covers scripts (see
# crm.management.commands.issue_api_token).
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

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

# Browsers share cookies across every port on 127.0.0.1, and the desktop app
# picks a random port each launch. Other local Django apps (e.g. Lead
# Generation Studio) also use the default "sessionid"/"csrftoken" names, so
# logging into one silently logged you out of the other. Unique names keep
# Pipeline's login separate.
SESSION_COOKIE_NAME = "pipeline_sessionid"
CSRF_COOKIE_NAME = "pipeline_csrftoken"

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
