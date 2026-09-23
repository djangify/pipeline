# research/admin.py
from django.contrib import admin

from .models import CompetitorAd, Keyword, PainTheme


@admin.register(CompetitorAd)
class CompetitorAdAdmin(admin.ModelAdmin):
    list_display = ("competitor_name", "headline", "business", "platform", "date_pulled")
    list_filter = ("business", "platform")
    search_fields = ("competitor_name", "headline", "angle", "ad_copy")
    date_hierarchy = "date_pulled"


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = (
        "term",
        "business",
        "difficulty_score",
        "search_volume",
        "top_ranking_domain",
        "updated_at",
    )
    list_filter = ("business",)
    search_fields = ("term", "top_ranking_domain")


@admin.register(PainTheme)
class PainThemeAdmin(admin.ModelAdmin):
    list_display = ("theme", "business", "quote_count", "source_breakdown", "updated_at")
    list_filter = ("business",)
    search_fields = ("theme", "description", "example_quotes")
