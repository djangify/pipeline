# research/serializers.py
from rest_framework import serializers

from .models import CompetitorAd, Keyword, PainTheme


class CompetitorAdSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitorAd
        fields = [
            "id",
            "business",
            "platform",
            "competitor_name",
            "headline",
            "angle",
            "ad_copy",
            "link",
            "date_pulled",
            "notes",
            "created_at",
            "updated_at",
        ]


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = [
            "id",
            "business",
            "term",
            "difficulty_score",
            "search_volume",
            "top_ranking_domain",
            "notes",
            "created_at",
            "updated_at",
        ]


class PainThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PainTheme
        fields = [
            "id",
            "business",
            "theme",
            "description",
            "quote_count",
            "source_breakdown",
            "example_quotes",
            "created_at",
            "updated_at",
        ]
