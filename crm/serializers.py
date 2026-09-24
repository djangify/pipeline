# crm/serializers.py
from rest_framework import serializers

from .models import Activity, Contact, Interaction, Purchase


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ["id", "contact", "activity_type", "content", "created_at"]


class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = [
            "id",
            "contact",
            "date",
            "channel",
            "direction",
            "message",
            "image",
            "created_at",
        ]


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = [
            "id",
            "contact",
            "product",
            "amount",
            "date",
            "source",
            "external_order_id",
            "notes",
            "created_at",
        ]


class ContactSerializer(serializers.ModelSerializer):
    interactions = InteractionSerializer(many=True, read_only=True)
    purchases = PurchaseSerializer(many=True, read_only=True)
    activities = ActivitySerializer(many=True, read_only=True)

    class Meta:
        model = Contact
        fields = [
            "id",
            "name",
            "platform",
            "social_handle",
            "profile_url",
            "email",
            "status",
            "business",
            "tags",
            "notes",
            "follow_up_date",
            "follow_up_1_done",
            "follow_up_2_done",
            "follow_up_3_done",
            "joined_email_list",
            "made_purchase",
            "revenue",
            "next_touch_date",
            "next_touch_note",
            "dead_reason",
            "created_at",
            "updated_at",
            "interactions",
            "purchases",
            "activities",
        ]
