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

## Claude Desktop connector (MCP)

`mcp_server/` exposes Pipeline to Claude Desktop over stdio, same architecture
as Lead Generation Studio's connector. Tools: `list_contacts`, `find_contact`
(dedup lookup by name / website / email / handle), `get_contact`,
`create_contact` (refuses exact duplicates), `update_contact`,
`list_followups_due`, and `list/get/create/update_search_profile`.

A **SearchProfile** (one per business, edit in the admin or via Claude) holds
who to look for and comma-separated signal phrases, including complaint/intent
phrases for Reddit-style searches ("sick of paying fees", "alternative to X").
The server instructions tell Claude to read the profile first, search only
public pages (never log into or automate LinkedIn/Facebook), check for
duplicates, then add candidates as `status=new`, tagged `ai-sourced`, with notes
saying why they fit. Outreach is left to you.

- **Packaged:** launching `Pipeline.exe` registers `Pipeline-mcp.exe` (built
  alongside it) in Claude Desktop's config as `pipeline`. Restart Claude
  Desktop once afterwards. Outcome is recorded in
  `%LOCALAPPDATA%\Pipeline\claude_connect_state.json` / `claude_connect.log`.
- **From source:** `python manage.py runmcp` (or `python mcp_launcher.py`)
  runs the server against the dev database in `data/`.

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
