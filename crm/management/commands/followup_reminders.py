# crm/management/commands/followup_reminders.py
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone

from crm.models import Contact


class Command(BaseCommand):
    help = "Email a reminder listing CRM follow-ups that are due or overdue."

    def add_arguments(self, parser):
        parser.add_argument(
            "--always",
            action="store_true",
            help="Send the email even when nothing is due (default: skip).",
        )

    def handle(self, *args, **options):
        today = timezone.localdate()
        due_follow_ups = (
            Contact.objects.filter(
                follow_up_date__isnull=False,
                follow_up_date__lte=today,
                follow_up_3_done=False,
            )
            .order_by("follow_up_date")
        )
        due_check_ins = (
            Contact.objects.filter(
                next_touch_date__isnull=False,
                next_touch_date__lte=today,
            )
            .order_by("next_touch_date")
        )
        count = due_follow_ups.count() + due_check_ins.count()
        domain = (getattr(settings, "PRIMARY_DOMAIN", "") or "").rstrip("/")

        if count == 0 and not options["always"]:
            self.stdout.write("Nothing due today — no email sent.")
            return

        if count == 0:
            subject = "Pipeline follow-ups: nothing due today"
            body = "Nothing is due today. Nice work staying on top of it!"
        else:
            lines = []
            for c in due_follow_ups:
                overdue = " (OVERDUE)" if c.follow_up_date < today else ""
                link = f"{domain}/contact/{c.pk}/" if domain else ""
                lines.append(
                    f"- {c.name} — Follow-up {c.current_stage} "
                    f"due {c.follow_up_date:%b %d}{overdue}  {link}"
                )
            for c in due_check_ins:
                overdue = " (OVERDUE)" if c.next_touch_date < today else ""
                link = f"{domain}/contact/{c.pk}/" if domain else ""
                note = f" — {c.next_touch_note}" if c.next_touch_note else ""
                lines.append(
                    f"- {c.name} — Check in{note} "
                    f"due {c.next_touch_date:%b %d}{overdue}  {link}"
                )
            plural = "" if count == 1 else "s"
            subject = f"Pipeline follow-ups: {count} due today"
            body = (
                f"You have {count} item{plural} due:\n\n"
                + "\n".join(lines)
                + (f"\n\nSee all: {domain}/follow-ups/" if domain else "")
            )

        recipient = getattr(settings, "FOLLOWUP_REMINDER_TO", None)
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
        if not recipient:
            self.stderr.write("FOLLOWUP_REMINDER_TO is not set; cannot send.")
            return

        send_mail(subject, body, from_email, [recipient], fail_silently=False)
        self.stdout.write(
            self.style.SUCCESS(f"Reminder sent to {recipient} ({count} due).")
        )
