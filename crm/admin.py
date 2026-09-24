# crm/admin.py
from django.contrib import admin

from .models import (
    Activity,
    Contact,
    FollowUpTemplate,
    Interaction,
    Purchase,
    SearchProfile,
    log_activity,
)


class InteractionInline(admin.TabularInline):
    model = Interaction
    extra = 1
    fields = ("date", "direction", "channel", "message", "image")
    ordering = ("-date",)


class PurchaseInline(admin.TabularInline):
    model = Purchase
    extra = 1
    fields = ("date", "product", "amount", "source", "external_order_id", "notes")
    ordering = ("-date",)


class ActivityInline(admin.TabularInline):
    """Read-only — activities are system-written, never edited by hand."""

    model = Activity
    extra = 0
    fields = ("activity_type", "content", "created_at")
    readonly_fields = ("activity_type", "content", "created_at")
    ordering = ("-created_at",)
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "platform",
        "social_handle",
        "status",
        "business",
        "follow_up_1_done",
        "follow_up_2_done",
        "follow_up_3_done",
        "joined_email_list",
        "made_purchase",
        "revenue",
        "follow_up_date",
        "next_touch_date",
    )
    list_filter = (
        "platform",
        "status",
        "business",
        "joined_email_list",
        "made_purchase",
        "follow_up_1_done",
        "follow_up_2_done",
        "follow_up_3_done",
    )
    list_editable = ("joined_email_list", "made_purchase")
    search_fields = ("name", "social_handle", "email", "tags", "notes")
    date_hierarchy = "created_at"
    inlines = [InteractionInline, PurchaseInline, ActivityInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            log_activity(obj, "contact_created", "Created via admin")


@admin.register(FollowUpTemplate)
class FollowUpTemplateAdmin(admin.ModelAdmin):
    list_display = ("stage", "message")


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ("contact", "date", "direction", "channel")
    list_filter = ("direction", "channel", "date")
    search_fields = ("contact__name", "message")
    date_hierarchy = "date"


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("contact", "product", "amount", "date", "source", "external_order_id")
    list_filter = ("source", "date")
    search_fields = ("contact__name", "product", "external_order_id")
    date_hierarchy = "date"


@admin.register(SearchProfile)
class SearchProfileAdmin(admin.ModelAdmin):
    list_display = ("business", "website", "updated_at")
    search_fields = ("audience_description", "keywords")
