from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path
from django.views.static import serve

from crm.accounts import FirstUserSetupView, PipelineLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", PipelineLoginView.as_view(), name="login"),
    path("accounts/setup/", FirstUserSetupView.as_view(), name="setup"),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(next_page="login"),
        name="logout",
    ),
    path("api/research/", include("research.api_urls")),
    path("research/", include("research.urls")),
    # Uploaded screenshots hold private conversations, so they are served only
    # to a logged-in user (and regardless of DEBUG, so they also work in the
    # packaged app).
    re_path(
        r"^media/(?P<path>.*)$",
        login_required(serve),
        {"document_root": settings.MEDIA_ROOT},
    ),
    path("", include("crm.urls")),
]
