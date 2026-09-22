# Pipeline

A small, standalone leads CRM. Log who you've talked to on LinkedIn (or any
other channel), track them through a status pipeline, and never lose track of
a follow-up.

Built by pulling the `crm` app out of the original Tracker/LGS lineage — it
was deliberately removed from [Lead Generation Studio](../ProductTracker)
on 2026-08-09 to keep that tool focused on content, not contacts. Pipeline
gives that CRM its own home instead of bolting it back on.

## What it does

- **Contacts** — name, platform found on, social handle/profile link, email,
  a status pipeline (new → contacted → replied → in conversation → converted
  / dead), which business they relate to, tags, notes.
- **Follow-ups** — 3 dated follow-up stages per contact; ticking a stage
  auto-schedules the next one 2 days out. A dedicated Follow-ups view lists
  everything due or overdue.
- **Interactions** — a timestamped log of every DM/comment/email/call per
  contact, with an optional screenshot.
- **Dashboard totals** — messages sent, reply rate, email-list signups,
  sales and revenue, all on the contacts list.
- **Follow-up email reminders** — `python manage.py followup_reminders`
  emails whatever's due today. Point cron at it and set `FOLLOWUP_REMINDER_TO`
  in `.env`.
- A small REST API (Django REST Framework) at `/api/contacts/` and
  `/api/interactions/`, for future automation.

## Running it

```bash
python -m venv pipelinevenv
pipelinevenv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then visit `http://127.0.0.1:8000/` and log in.

## Notes

- Tailwind is loaded from the CDN in `templates/base.html` — no node/npm
  build step, deliberately kept simple for a single-user internal tool.
- `Contact.business` is a plain choice field (Djangify / Inspirational
  Guidance / The Self-Talk Effect / todiane.com / Other) rather than a
  foreign key, so this app has zero dependency on any other project.
