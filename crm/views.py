# crm/views.py
import csv
import io
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from rest_framework import viewsets

from .models import Activity, Contact, FollowUpTemplate, Interaction, Purchase, log_activity
from .serializers import (
    ActivitySerializer,
    ContactSerializer,
    InteractionSerializer,
    PurchaseSerializer,
)

# Days to wait before the next follow-up stage
FOLLOW_UP_GAP_DAYS = 2


def _status_label(value):
    return dict(Contact.STATUS_CHOICES).get(value, value)


def _require_dead_reason(form):
    """Dead is a decision, not a shrug — make the reason part of the record."""
    if form.cleaned_data.get("status") == "dead" and not form.cleaned_data.get("dead_reason"):
        form.add_error("dead_reason", "Say why before marking this contact Dead.")
        return False
    return True


# ---------------------------------------------------------------------------
# Frontend views
# ---------------------------------------------------------------------------
class ContactListView(LoginRequiredMixin, ListView):
    model = Contact
    template_name = "crm/contact_list.html"
    context_object_name = "contacts"

    def get_queryset(self):
        qs = Contact.objects.all()
        status = self.request.GET.get("status")
        platform = self.request.GET.get("platform")
        search = self.request.GET.get("q")

        if status and status != "all":
            qs = qs.filter(status=status)
        if platform and platform != "all":
            qs = qs.filter(platform=platform)
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(social_handle__icontains=search)
                | Q(email__icontains=search)
                | Q(tags__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Contact.STATUS_CHOICES
        context["platform_choices"] = Contact.PLATFORM_CHOICES
        context["current_status"] = self.request.GET.get("status", "all")
        context["current_platform"] = self.request.GET.get("platform", "all")
        context["search"] = self.request.GET.get("q", "")

        # Dashboard totals (always across ALL contacts, ignoring filters)
        messages_sent = Interaction.objects.filter(direction="outbound").count()
        responses = Interaction.objects.filter(direction="inbound").count()
        context["stats"] = {
            "messages_sent": messages_sent,
            "responses": responses,
            "response_rate": round(responses / messages_sent * 100) if messages_sent else 0,
            "list_signups": Contact.objects.filter(joined_email_list=True).count(),
            "sales": Contact.objects.filter(made_purchase=True).count(),
            "revenue": Contact.objects.filter(made_purchase=True).aggregate(
                total=Sum("revenue")
            )["total"] or 0,
        }
        return context


class ContactDetailView(LoginRequiredMixin, DetailView):
    model = Contact
    template_name = "crm/contact_detail.html"
    context_object_name = "contact"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.object
        context["today"] = timezone.localdate()
        # Build the three stages with their done-state for the template
        context["stages"] = [
            {"num": 1, "done": contact.follow_up_1_done},
            {"num": 2, "done": contact.follow_up_2_done},
            {"num": 3, "done": contact.follow_up_3_done},
        ]
        # Suggested message template for the next incomplete stage
        if contact.current_stage:
            context["suggested_template"] = FollowUpTemplate.objects.filter(
                stage=contact.current_stage
            ).first()

        # Merge interactions, purchases, and system activities into one
        # reverse-chronological feed, sorted by the date each thing happened
        # (falling back to created_at as a same-day tiebreak).
        timeline = []
        for interaction in contact.interactions.all():
            timeline.append({
                "kind": "interaction",
                "sort_key": (interaction.date, interaction.created_at),
                "obj": interaction,
            })
        for purchase in contact.purchases.all():
            timeline.append({
                "kind": "purchase",
                "sort_key": (purchase.date, purchase.created_at),
                "obj": purchase,
            })
        for activity in contact.activities.all():
            timeline.append({
                "kind": "activity",
                "sort_key": (activity.created_at.date(), activity.created_at),
                "obj": activity,
            })
        timeline.sort(key=lambda row: row["sort_key"], reverse=True)
        context["timeline"] = timeline
        return context


CONTACT_FIELDS = [
    "name",
    "platform",
    "social_handle",
    "profile_url",
    "email",
    "status",
    "business",
    "tags",
    "follow_up_date",
    "joined_email_list",
    "made_purchase",
    "revenue",
    "next_touch_date",
    "next_touch_note",
    "dead_reason",
    "notes",
]

STAGE_FIELDS = ["follow_up_1_done", "follow_up_2_done", "follow_up_3_done"]


class ContactCreateView(LoginRequiredMixin, CreateView):
    model = Contact
    fields = CONTACT_FIELDS
    template_name = "crm/contact_form.html"

    def form_valid(self, form):
        if not _require_dead_reason(form):
            return self.form_invalid(form)
        response = super().form_valid(form)
        log_activity(self.object, "contact_created", "Contact created")
        return response

    def get_success_url(self):
        return reverse("crm:contact_detail", kwargs={"pk": self.object.pk})


class ContactUpdateView(LoginRequiredMixin, UpdateView):
    model = Contact
    fields = CONTACT_FIELDS + STAGE_FIELDS
    template_name = "crm/contact_form.html"

    def form_valid(self, form):
        if not _require_dead_reason(form):
            return self.form_invalid(form)
        # self.object already carries the form's new values at this point
        # (Django assigns them during is_valid()), so read the pre-save
        # status from the database rather than from self.object.
        previous_status = Contact.objects.get(pk=self.object.pk).status
        new_status = form.cleaned_data["status"]
        response = super().form_valid(form)
        if new_status != previous_status:
            content = f"{_status_label(previous_status)} → {_status_label(new_status)}"
            if new_status == "dead" and form.cleaned_data.get("dead_reason"):
                content += f" ({form.cleaned_data['dead_reason']})"
            log_activity(self.object, "status_changed", content)
        return response

    def get_success_url(self):
        return reverse("crm:contact_detail", kwargs={"pk": self.object.pk})


class InteractionCreateView(LoginRequiredMixin, CreateView):
    model = Interaction
    fields = ["date", "direction", "channel", "message", "image"]
    template_name = "crm/interaction_form.html"

    def form_valid(self, form):
        contact = get_object_or_404(Contact, pk=self.kwargs["contact_pk"])
        form.instance.contact = contact
        # Logging a touch nudges the contact forward from "new"
        if contact.status == "new":
            contact.status = "contacted"
            contact.save(update_fields=["status"])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("crm:contact_detail", kwargs={"pk": self.kwargs["contact_pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact"] = get_object_or_404(Contact, pk=self.kwargs["contact_pk"])
        return context


class FollowUpListView(LoginRequiredMixin, ListView):
    template_name = "crm/followups.html"
    context_object_name = "rows"

    def get_queryset(self):
        rows = []
        # Pre-sale: anyone with a follow-up date who still has an incomplete stage
        pre_sale = Contact.objects.filter(
            follow_up_date__isnull=False,
            follow_up_3_done=False,
        )
        for c in pre_sale:
            rows.append({
                "contact": c,
                "due_date": c.follow_up_date,
                "kind": "follow_up",
                "label": f"Follow-up {c.current_stage}" if c.current_stage else "Follow-up",
            })
        # Post-sale: a check-in nudge, no fixed stages
        check_ins = Contact.objects.filter(next_touch_date__isnull=False)
        for c in check_ins:
            rows.append({
                "contact": c,
                "due_date": c.next_touch_date,
                "kind": "check_in",
                "label": c.next_touch_note or "Check in",
            })
        rows.sort(key=lambda r: r["due_date"])
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["today"] = timezone.localdate()
        return context


class PurchaseCreateView(LoginRequiredMixin, CreateView):
    model = Purchase
    fields = ["product", "amount", "date", "notes"]
    template_name = "crm/purchase_form.html"

    def form_valid(self, form):
        contact = get_object_or_404(Contact, pk=self.kwargs["contact_pk"])
        form.instance.contact = contact
        form.instance.source = "manual"
        # Logging a purchase confirms the contact converted
        previous_status = contact.status
        if previous_status != "converted":
            contact.status = "converted"
            contact.save(update_fields=["status"])
            log_activity(
                contact, "status_changed",
                f"{_status_label(previous_status)} → {_status_label('converted')}",
            )
        response = super().form_valid(form)
        log_activity(
            contact, "purchase_logged",
            f"{form.instance.product} – £{form.instance.amount}",
        )
        return response

    def get_success_url(self):
        return reverse("crm:contact_detail", kwargs={"pk": self.kwargs["contact_pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact"] = get_object_or_404(Contact, pk=self.kwargs["contact_pk"])
        return context


class CheckInDoneView(LoginRequiredMixin, View):
    """Clear a contact's post-sale check-in reminder once it's been done."""

    def post(self, request, *args, **kwargs):
        contact = get_object_or_404(Contact, pk=kwargs["pk"])
        note = contact.next_touch_note
        contact.next_touch_date = None
        contact.next_touch_note = ""
        contact.save(update_fields=["next_touch_date", "next_touch_note"])
        log_activity(contact, "check_in_done", note or "Check-in done")
        next_url = request.POST.get("next") or reverse(
            "crm:contact_detail", kwargs={"pk": contact.pk}
        )
        return HttpResponseRedirect(next_url)


class StageToggleView(LoginRequiredMixin, View):
    """
    Toggle a follow-up stage (1, 2 or 3) done/undone for a contact.
    When a stage is marked done, auto-schedule the next follow-up
    FOLLOW_UP_GAP_DAYS out (unless it was the final stage).
    """

    STAGE_FIELD = {1: "follow_up_1_done", 2: "follow_up_2_done", 3: "follow_up_3_done"}

    def post(self, request, *args, **kwargs):
        contact = get_object_or_404(Contact, pk=kwargs["pk"])
        stage = int(kwargs["stage"])
        field = self.STAGE_FIELD.get(stage)
        if field:
            new_value = not getattr(contact, field)
            setattr(contact, field, new_value)
            if new_value:
                # Just completed this stage — schedule the next one
                if not contact.follow_ups_complete:
                    contact.follow_up_date = timezone.localdate() + timedelta(
                        days=FOLLOW_UP_GAP_DAYS
                    )
                else:
                    contact.follow_up_date = None
            contact.save()
            log_activity(
                contact, "stage_completed",
                f"Follow-up {stage} marked {'done' if new_value else 'not done'}",
            )
        next_url = request.POST.get("next") or reverse(
            "crm:contact_detail", kwargs={"pk": contact.pk}
        )
        return HttpResponseRedirect(next_url)


CSV_EXPORT_FIELDS = [
    "name", "platform", "social_handle", "profile_url", "email", "status",
    "business", "tags", "follow_up_date", "joined_email_list", "made_purchase",
    "revenue", "next_touch_date", "next_touch_note", "dead_reason", "notes",
    "created_at",
]


class ContactExportView(LoginRequiredMixin, View):
    """Dump every contact to CSV — a portability/backup path independent of
    the server's own daily backup job."""

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="pipeline_contacts.csv"'
        writer = csv.writer(response)
        writer.writerow(CSV_EXPORT_FIELDS)
        for contact in Contact.objects.all():
            writer.writerow([getattr(contact, field) for field in CSV_EXPORT_FIELDS])
        return response


class ContactImportView(LoginRequiredMixin, View):
    """Bulk-add contacts from a CSV. Headers are matched to Contact fields
    by exact name (case/spacing-insensitive) — no fuzzy matching, so an
    unrecognized column is just ignored rather than guessed at."""

    template_name = "crm/contact_import.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {"fields": CONTACT_FIELDS})

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            messages.error(request, "Choose a CSV file first.")
            return redirect("crm:contact_import")

        try:
            decoded = csv_file.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            messages.error(request, "That file doesn't look like a text CSV.")
            return redirect("crm:contact_import")

        reader = csv.DictReader(io.StringIO(decoded))
        field_by_normalized_name = {f.replace("_", " "): f for f in CONTACT_FIELDS}
        field_by_normalized_name.update({f: f for f in CONTACT_FIELDS})

        created, skipped = 0, 0
        for row_num, row in enumerate(reader, start=2):
            data = {}
            for header, value in row.items():
                if not header or value in (None, ""):
                    continue
                key = header.strip().lower().replace("-", " ")
                field = field_by_normalized_name.get(key) or field_by_normalized_name.get(
                    key.replace(" ", "_")
                )
                if field:
                    data[field] = value.strip()

            if not data.get("name"):
                skipped += 1
                continue

            # Same rule as the form: dead is a decision, not a shrug.
            if data.get("status") == "dead" and not data.get("dead_reason"):
                skipped += 1
                continue

            for bool_field in ("joined_email_list", "made_purchase"):
                if bool_field in data:
                    data[bool_field] = data[bool_field].lower() in ("true", "1", "yes", "y")

            contact = Contact.objects.create(**data)
            log_activity(contact, "contact_created", "Imported from CSV")
            created += 1

        messages.success(request, f"Imported {created} contact(s), skipped {skipped}.")
        return redirect("crm:contact_list")


CHART_HEIGHT = 100
BAR_WIDTH = 48
BAR_GAP = 16

PLATFORM_COLORS = {
    "instagram": "#e1306c", "linkedin": "#0a66c2", "x": "#111827",
    "facebook": "#1877f2", "tiktok": "#14b8a6", "youtube": "#ff0000",
    "threads": "#4b5563", "reddit": "#ff4500", "email": "#6366f1",
    "referral": "#10b981", "other": "#9ca3af", "": "#9ca3af",
}


def _month_start(d):
    return d.replace(day=1)


def _next_month(d):
    return (d.replace(day=28) + timedelta(days=4)).replace(day=1)


class ReportsView(LoginRequiredMixin, TemplateView):
    """Date-ranged KPIs plus two hand-rolled inline-SVG charts — no charting
    dependency, matching the rest of this codebase's plain-Django style."""

    template_name = "crm/reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        start = parse_date(self.request.GET.get("start", "")) or today - timedelta(days=90)
        end = parse_date(self.request.GET.get("end", "")) or today
        context["start"] = start
        context["end"] = end

        contacts_in_range = Contact.objects.filter(
            created_at__date__gte=start, created_at__date__lte=end
        )
        interactions_in_range = Interaction.objects.filter(date__gte=start, date__lte=end)
        purchases_in_range = Purchase.objects.filter(date__gte=start, date__lte=end)

        messages_sent = interactions_in_range.filter(direction="outbound").count()
        responses = interactions_in_range.filter(direction="inbound").count()

        context["kpis"] = {
            "new_contacts": contacts_in_range.count(),
            "messages_sent": messages_sent,
            "responses": responses,
            "response_rate": round(responses / messages_sent * 100) if messages_sent else 0,
            "purchases": purchases_in_range.count(),
            "revenue": purchases_in_range.aggregate(total=Sum("amount"))["total"] or 0,
        }

        # Revenue by month — bar chart
        months = []
        cursor = _month_start(start)
        while cursor <= end:
            months.append(cursor)
            cursor = _next_month(cursor)

        month_rows = []
        for month in months:
            month_end = min(_next_month(month) - timedelta(days=1), end)
            total = purchases_in_range.filter(
                date__gte=month, date__lte=month_end
            ).aggregate(total=Sum("amount"))["total"] or 0
            month_rows.append({"label": month.strftime("%b %y"), "value": float(total)})

        max_month = max((row["value"] for row in month_rows), default=0) or 1
        for idx, row in enumerate(month_rows):
            row["bar_height"] = round(row["value"] / max_month * CHART_HEIGHT)
            row["y"] = CHART_HEIGHT - row["bar_height"]
            row["x"] = idx * (BAR_WIDTH + BAR_GAP)
        context["revenue_by_month"] = month_rows
        context["chart_width"] = max(len(month_rows), 1) * (BAR_WIDTH + BAR_GAP)
        context["chart_height"] = CHART_HEIGHT
        context["bar_width"] = BAR_WIDTH

        # Leads by platform — donut chart (stacked-arc technique, r chosen
        # so the circumference is 100 units and each segment is just a
        # percentage of it)
        platform_counts = list(
            contacts_in_range.values("platform")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        total_leads = sum(row["count"] for row in platform_counts)
        segments = []
        offset = 0
        for row in platform_counts:
            pct = (row["count"] / total_leads * 100) if total_leads else 0
            segments.append({
                "label": dict(Contact.PLATFORM_CHOICES).get(row["platform"], "Unknown"),
                "count": row["count"],
                "pct": round(pct, 1),
                "color": PLATFORM_COLORS.get(row["platform"], "#9ca3af"),
                "dasharray": f"{pct:.2f} {max(100 - pct, 0):.2f}",
                "dashoffset": -offset,
            })
            offset += pct
        context["platform_segments"] = segments
        context["total_leads"] = total_leads

        return context


# ---------------------------------------------------------------------------
# API views
# ---------------------------------------------------------------------------
class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def perform_create(self, serializer):
        contact = serializer.save()
        log_activity(contact, "contact_created", "Created via API")


class InteractionViewSet(viewsets.ModelViewSet):
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer


class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer


class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only: activities are system-written, never created via the API."""

    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
