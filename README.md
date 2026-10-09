# Pipeline

A small, standalone leads CRM. Log who you've talked to on LinkedIn (or any
other channel), track them through a status pipeline, and never lose track of
a follow-up.

Everything stays on your own computer: one SQLite database, no account, no
cloud service. Pipeline is free software under the [MIT licence](LICENSE).

## What it does

- **Contacts** — name, platform found on, social handle/profile link, email,
  a status pipeline (new → contacted → replied → in conversation → converted
  / dead), which of your businesses or projects they relate to (free text), tags, notes.
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

`mcp_server/` exposes Pipeline to Claude Desktop over stdio (optional). Tools: `list_contacts`, `find_contact`
(dedup lookup by name / website / email / handle), `get_contact`,
`create_contact` (refuses exact duplicates), `update_contact`,
`list_followups_due`, and `list/get/create/update_search_profile`.

A **SearchProfile** (one per business name, edit in the admin or via Claude) holds
who to look for and comma-separated signal phrases, including complaint/intent
phrases for Reddit-style searches ("sick of paying fees", "alternative to X").
The server instructions tell Claude to read the profile first, search only
public pages (never log into or automate LinkedIn/Facebook), check for
duplicates, then add candidates as `status=new`, tagged `ai-sourced`, with notes
saying why they fit. Outreach is left to you.

- **Packaged:** launching `Pipeline.exe` registers `Pipeline-mcp.exe` (built
  alongside it) in Claude Desktop's config as `pipeline`. Restart Claude
  Desktop once afterwards. Outcome is recorded in
  `%USERPROFILE%\Pipeline Data\claude_connect_state.json` / `claude_connect.log`.
- **From source:** `python manage.py runmcp` (or `python mcp_launcher.py`)
  runs the server against the dev database in `data/`.

## What you need

- **Python 3.10 or newer** (3.13 is what it is developed on) and `git`.
- **Windows 10/11** for the desktop app (`Pipeline.exe`), which also needs the
  Microsoft WebView2 runtime (already present on current Windows 11 and most
  Windows 10 machines). `build_exe.bat` builds it and is Windows-only.
- **Windows, macOS or Linux** for running from source in a browser.
- An internet connection when you open the app: the page styling (Tailwind) is
  loaded from `cdn.tailwindcss.com`. Your data never leaves your computer, but
  without a connection the pages appear unstyled.

## Running it from source

Windows (PowerShell or Command Prompt):

```bat
git clone https://github.com/djangify/pipeline.git
cd pipeline
python -m venv pipelinevenv
pipelinevenv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

macOS / Linux:

```bash
git clone https://github.com/djangify/pipeline.git
cd pipeline
python3 -m venv pipelinevenv
source pipelinevenv/bin/activate
pip install -r requirements.txt   # pywin32 and the Windows-only parts are skipped automatically
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Then visit `http://127.0.0.1:8000/`. The first time, Pipeline shows a setup
page where you choose your own email and password. There is no default login.

If port 8000 is already in use, run `python manage.py runserver 8001` and visit
that port instead.

You do not need to edit `.env` to get going. `SECRET_KEY` can stay blank:
Pipeline generates a random one on first run and keeps it in the data folder
(`data/secret_key.txt` from source). Leave `DEBUG=True` for local use.

## Where the desktop app keeps its data

`Pipeline.exe` stores its database, uploads and secret key in
`%USERPROFILE%\Pipeline Data`, **not** AppData. Claude Desktop is a packaged
Windows app and silently redirects AppData for anything it launches, so the
app window and the Claude connector would otherwise each get their own
database (research saved by Claude would never appear in the app). If an old
`%LOCALAPPDATA%\Pipeline` install drifted apart from it, merge its research in
with `python manage.py import_research_db <path to its db.sqlite3>`.

## Logins: every user must be a superuser

**Whenever you set up a new user, give them superuser access.** Pipeline is a
single-owner tool and Django admin (the Admin link, search profiles, raw
research data) only lets in staff users. A normal user gets bounced to the
admin login page, which looks exactly like being logged out.

- **First login:** the setup page creates it for you, already a superuser.
- **More users from the command line:** always use
  `python manage.py createsuperuser`, never `create_user`.
- **In the admin (Admin → Users → Add user):** after saving, tick both
  **Staff status** and **Superuser status** on the next screen, then save again.

There is no built-in default account. Full steps, including how to upgrade an
existing login and how to run these commands against the packaged app's
database, are in [docs/USERS.md](docs/USERS.md).

## Notes

- Tailwind is loaded from the CDN in `templates/base.html` — no node/npm
  build step, deliberately kept simple for a single-user internal tool.
- `Contact.business` and the research `business` fields are plain free text, so
  Pipeline has no built-in list of businesses. Type whatever you call yours;
  the Research page lists the businesses that have research saved.
- Uploaded screenshots are served only to a logged-in user.
- CSV import checks every row like the Add Contact form does. Rows that fail
  are skipped and the first few problems are shown by row number.

## Licence

MIT. See [LICENSE](LICENSE).
