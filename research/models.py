# research/models.py
from django.db import models
from django.utils import timezone

# Deliberately duplicated from crm.models.Contact.BUSINESS_CHOICES rather than
# imported, so research stays dependency-free of crm the same way crm has no
# FK into other apps. Keep the two lists in sync by hand.
BUSINESS_CHOICES = [
    ("djangify", "Djangify"),
    ("inspirational_guidance", "Inspirational Guidance"),
    ("self_talk_effect", "The Self-Talk Effect"),
    ("todiane", "todiane.com"),
    ("other", "Other"),
]


class CompetitorAd(models.Model):
    """A competitor ad pulled from an ad library (Meta/Google/LinkedIn), for
    studying angles and messaging. No one to contact here -- this is market
    research, not a lead."""

    PLATFORM_CHOICES = [
        ("meta", "Meta (Facebook/Instagram)"),
        ("google", "Google"),
        ("linkedin", "LinkedIn"),
        ("other", "Other"),
    ]

    business = models.CharField(
        max_length=30,
        choices=BUSINESS_CHOICES,
        help_text="Which of our businesses this competitor overlaps with",
    )
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default="meta")
    competitor_name = models.CharField(max_length=150)
    headline = models.CharField(max_length=255, blank=True)
    angle = models.TextField(help_text="The messaging angle/positioning this ad uses")
    ad_copy = models.TextField(blank=True, help_text="Full ad copy, if captured")
    link = models.URLField(blank=True, help_text="Link to the ad or a screenshot")
    date_pulled = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_pulled", "-created_at"]

    def __str__(self):
        return f"{self.competitor_name} - {self.headline or self.angle[:40]}"


class Keyword(models.Model):
    """A search term surfaced by keyword/SERP research: how hard it is to
    rank for, and who currently owns that ranking."""

    business = models.CharField(
        max_length=30,
        choices=BUSINESS_CHOICES,
        help_text="Which of our businesses this keyword research is for",
    )
    term = models.CharField(max_length=255)
    difficulty_score = models.PositiveIntegerField(
        null=True, blank=True, help_text="Keyword difficulty, 0-100"
    )
    search_volume = models.PositiveIntegerField(null=True, blank=True)
    top_ranking_domain = models.CharField(
        max_length=255, blank=True, help_text="Who currently ranks for this term"
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["business", "term"]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "term"], name="unique_keyword_per_business"
            )
        ]

    def __str__(self):
        return f"{self.term} ({self.get_business_display()})"


class PainTheme(models.Model):
    """An aggregated complaint/pain theme synthesized from reviews and forum
    threads (Trustpilot, G2, Reddit, app stores, ...). Represents a pattern
    across many people, not one person to contact."""

    business = models.CharField(
        max_length=30,
        choices=BUSINESS_CHOICES,
        help_text="Which of our businesses this pain theme is relevant to",
    )
    theme = models.CharField(max_length=255, help_text="Short label for the theme")
    description = models.TextField(blank=True, help_text="Synthesized summary of the theme")
    quote_count = models.PositiveIntegerField(
        default=0, help_text="How many supporting quotes were found"
    )
    source_breakdown = models.CharField(
        max_length=255,
        blank=True,
        help_text="e.g. 'Reddit: 5, Trustpilot: 3, G2: 2'",
    )
    example_quotes = models.TextField(
        blank=True, help_text="Representative quotes, with source links"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["business", "-quote_count"]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "theme"], name="unique_pain_theme_per_business"
            )
        ]

    def __str__(self):
        return f"{self.theme} ({self.get_business_display()})"
