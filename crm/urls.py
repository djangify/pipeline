# crm/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "crm"

router = DefaultRouter()
router.register(r"contacts", views.ContactViewSet)
router.register(r"interactions", views.InteractionViewSet)
router.register(r"purchases", views.PurchaseViewSet)
router.register(r"activities", views.ActivityViewSet)

urlpatterns = [
    # Frontend URLs
    path("", views.ContactListView.as_view(), name="contact_list"),
    path("create/", views.ContactCreateView.as_view(), name="contact_create"),
    path("follow-ups/", views.FollowUpListView.as_view(), name="followups"),
    path("reports/", views.ReportsView.as_view(), name="reports"),
    path("export/", views.ContactExportView.as_view(), name="contact_export"),
    path("import/", views.ContactImportView.as_view(), name="contact_import"),
    path("contact/<int:pk>/", views.ContactDetailView.as_view(), name="contact_detail"),
    path("contact/<int:pk>/edit/", views.ContactUpdateView.as_view(), name="contact_edit"),
    path(
        "contact/<int:contact_pk>/add-interaction/",
        views.InteractionCreateView.as_view(),
        name="interaction_create",
    ),
    path(
        "contact/<int:contact_pk>/add-purchase/",
        views.PurchaseCreateView.as_view(),
        name="purchase_create",
    ),
    path(
        "contact/<int:pk>/stage/<int:stage>/toggle/",
        views.StageToggleView.as_view(),
        name="stage_toggle",
    ),
    path(
        "contact/<int:pk>/check-in/done/",
        views.CheckInDoneView.as_view(),
        name="check_in_done",
    ),
    # API URLs
    path("api/", include(router.urls)),
]
