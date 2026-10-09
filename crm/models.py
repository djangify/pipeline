# crm/models.py
from django.db import models
from django.utils import timezone


class Contact(models.Model):
    PLATFORM_CHOICES = [
        ("instagram", "Instagram"),
        ("linkedin", "LinkedIn"),
        ("x", "X / Twitter"),
        ("facebook", "Facebook"),
        ("tiktok", "TikTok"),
        ("youtube", "YouTube"),
        ("threads", "Threads"),
        ("reddit", "Reddit"),
        ("email", "Email"),
        ("referral", "Referral"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("replied", "Replied"),
        ("in_conversation", "In conversation"),
        ("converted", "Converted"),
        ("dead", "Dead / No interest"),
    ]

    name = models.CharField(max_length=150)
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        default="linkedin",
        help_text="Where you found them",
    )
    social_handle = models.CharField(
        max_length=150, blank=True, help_text="Their @username on that platform"
    )
    profile_url = models.URLField(blank=True, help_text="Link to their profile")
    email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    business = models.CharField(
        max_length=100,
        blank=True,
        help_text="Which of your businesses or projects this contact relates to",
    )
    tags = models.CharField(
        max_length=255, blank=True, help_text="Comma-separated, e.g. coach, warm lead"
    )
    notes = models.TextField(blank=True)

    follow_up_date = models.DateField(
        null=True, blank=True, help_text="When to follow up next"
    )
    follow_up_1_done = models.BooleanField("Follow-up 1 done", default=False)
    follow_up_2_done = models.BooleanField("Follow-up 2 done", default=False)
    follow_up_3_done = models.BooleanField("Follow-up 3 done", default=False)

    joined_email_list = models.BooleanField(
        "Joined email list",
        default=False,
        help_text="Signed up for the email list",
    )
    made_purchase = models.BooleanField(
        default=False, help_text="This contact has bought something"
    )
    revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total amount this contact has paid",
    )

    next_touch_date = models.DateField(
        null=True,
        blank=True,
        help_text="Post-sale check-in reminder (thank-you, how's it going, re-offer)",
    )
    next_touch_note = models.CharField(
        max_length=255, blank=True, help_text="What the next check-in is for"
    )

    dead_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Why this went dead (required when status is Dead)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name

    @property
    def follow_ups_complete(self):
        return self.follow_up_1_done and self.follow_up_2_done and self.follow_up_3_done

    @property
    def current_stage(self):
        """Next incomplete follow-up stage (1, 2 or 3), or None if all done."""
        if not self.follow_up_1_done:
            return 1
        if not self.follow_up_2_done:
            return 2
        if not self.follow_up_3_done:
            return 3
        return None

    @property
    def follow_up_overdue(self):
        if self.follow_up_date and not self.follow_ups_complete:
            return self.follow_up_date < timezone.localdate()
        return False

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class FollowUpTemplate(models.Model):
    STAGE_CHOICES = [(1, "Follow-up 1"), (2, "Follow-up 2"), (3, "Follow-up 3")]

    stage = models.PositiveSmallIntegerField(choices=STAGE_CHOICES, unique=True)
    message = models.TextField(help_text="Reusable message for this follow-up stage")

    class Meta:
        ordering = ["stage"]

    def __str__(self):
        return self.get_stage_display()


class Interaction(models.Model):
    CHANNEL_CHOICES = [
        ("dm", "Direct message"),
        ("comment", "Comment"),
        ("email", "Email"),
        ("call", "Call"),
        ("meeting", "Meeting"),
        ("other", "Other"),
    ]

    DIRECTION_CHOICES = [
        ("outbound", "I reached out"),
        ("inbound", "They reached out"),
    ]

    contact = models.ForeignKey(
        Contact, on_delete=models.CASCADE, related_name="interactions"
    )
    date = models.DateField(default=timezone.localdate)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default="dm")
    direction = models.CharField(
        max_length=20, choices=DIRECTION_CHOICES, default="outbound"
    )
    message = models.TextField(help_text="What was said")
    image = models.ImageField(
        upload_to="crm/interactions/",
        blank=True,
        null=True,
        help_text="Optional screenshot (e.g. of a comment or DM)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.get_direction_display()} – {self.contact.name} ({self.date})"


def _recalc_contact_totals(contact):
    """Keep Contact.made_purchase/revenue as the sum of its logged purchases,
    so the dashboard totals stay correct whether a purchase was typed in
    manually or synced in from Djangify."""
    total = contact.purchases.aggregate(total=models.Sum("amount"))["total"] or 0
    contact.made_purchase = total > 0
    contact.revenue = total
    contact.save(update_fields=["made_purchase", "revenue"])


class Purchase(models.Model):
    SOURCE_CHOICES = [
        ("manual", "Manual entry"),
        ("djangify", "Djangify sync"),
    ]

    contact = models.ForeignKey(
        Contact, on_delete=models.CASCADE, related_name="purchases"
    )
    product = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="manual")
    external_order_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        unique=True,
        help_text="Djangify order id, used to avoid importing the same order twice",
    )
    notes = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.product} – {self.contact.name} ({self.date})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        _recalc_contact_totals(self.contact)

    def delete(self, *args, **kwargs):
        contact = self.contact
        super().delete(*args, **kwargs)
        _recalc_contact_totals(contact)


class Activity(models.Model):
    """System-written history for a contact.

    Unlike Interaction (what you said to them) and Purchase (what they
    bought), this exists purely so the contact timeline can show status
    changes, stage completions, and check-ins alongside those — one merged
    feed instead of three things you have to mentally stitch together.
    Never edited by a user; only ever created by the view that made the
    change, via log_activity() below.
    """

    TYPE_CHOICES = [
        ("contact_created", "Contact created"),
        ("status_changed", "Status changed"),
        ("stage_completed", "Follow-up stage updated"),
        ("check_in_done", "Check-in done"),
        ("purchase_logged", "Purchase logged"),
    ]

    contact = models.ForeignKey(
        Contact, on_delete=models.CASCADE, related_name="activities"
    )
    activity_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    content = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "activities"

    def __str__(self):
        return f"{self.get_activity_type_display()} – {self.contact.name}"


def log_activity(contact, activity_type, content=""):
    return Activity.objects.create(
        contact=contact, activity_type=activity_type, content=content
    )


class SearchProfile(models.Model):
    """Who to look for, per business, when prospecting for new contacts.

    Read by the MCP server's get_search_profile tool so a connected Claude
    searches for prospects against the owner's own description of the ideal
    customer instead of improvising one.
    """

    business = models.CharField(
        max_length=100,
        unique=True,
        help_text="Which of your businesses or projects this profile searches for",
    )
    website = models.URLField(blank=True)
    audience_description = models.TextField(
        blank=True, help_text="Who the ideal prospect is, in plain words"
    )
    keywords = models.TextField(
        blank=True,
        help_text=(
            "Comma-separated signal phrases, e.g. life coach, Gumroad, "
            "sick of paying fees, alternative to Kajabi"
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["business"]

    def __str__(self):
        return self.business

    @property
    def keyword_list(self):
        return [k.strip() for k in self.keywords.split(",") if k.strip()]
