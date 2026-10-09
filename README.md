# Pipeline

A small, standalone leads CRM. Log who you've talked to on LinkedIn (or any
other channel), track them through a status pipeline, and never lose track of
a follow-up.

Everything stays on your own computer: one SQLite database, no account, no
cloud service. Free and open source under the MIT license (see `LICENSE.txt`).

## Start here: the guides

Plain-language guides for people who just want to use Pipeline. Each is in
`docs/` as a PDF and as a plain text file:

| Guide | What it covers |
|---|---|
| `docs/Pipeline-Setup-Guide` | Full guide: download, install, first login, everyday use, Claude connector, backups, password reset, troubleshooting |
| `docs/HOW-TO-OPEN-PIPELINE` | One page: unzip it, double-click it, log in |
| `docs/LICENSE.pdf`, `LICENSE.txt` | The MIT license |
| `docs/THIRD_PARTY_NOTICES` | Licenses of the open source packages the app bundles |

This README is the short version for developers and for the repository front page.

## What it does

- **Contacts**: name, platform found on, social handle/profile link, email,
  a status pipeline (new, contacted, replied, in conversation, converted,
  dead), which of your businesses or projects they relate to (free text), tags, notes.
- **Follow-ups**: 3 dated follow-up stages per contact; ticking a stage
  auto-schedules the next one 2 days out. A dedicated Follow-ups view lists
  everything due or overdue.
- **Interactions**: a timestamped log of every DM/comment/email/call per
  contact, with an optional screenshot.
- **Purchases and check-ins**: log what a contact bought and schedule a
  post-sale check-in.
- **Dashboard and reports**: messages sent, reply rate, email-list signups,
  sales and revenue, plus date-ranged reports and charts.
- **Research**: pain themes, competitor ads and keywords per business.
- **CSV import and export**, with every imported row validated.
- **Follow-up email reminders**: `python manage.py followup_reminders` emails
  whatever's due today. Set `FOLLOWUP_REMINDER_TO` and the `EMAIL_` settings in
  `.env` (see `.env.example`), and point Task Scheduler or cron at it.
- A small REST API (Django REST Framework) at `/api/contacts/` and
  `/api/interactions/`, for automation.

## Claude Desktop connector (MCP)

`mcp_server/` exposes Pipeline to Claude Desktop over stdio (optional). Tools:
`list_contacts`, `find_contact` (dedup lookup by name / website / email /
handle), `get_contact`, `create_contact` (refuses exact duplicates),
`update_contact`, `list_followups_due`, search profiles, purchases,
interactions and research tools.

A **SearchProfile** (one per business name, edit in the admin or via Claude) holds
who to look for and comma-separated signal phrases, including complaint/intent
phrases for Reddit-style searches ("sick of spreadsheets", "alternative to X").
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

- **Python 3.10 or newer** (3.13 is what it is developed on) and `git`, to run
  from source.
- **Windows 10/11** for the desktop app (`Pipeline.exe`), which also needs the
  Microsoft WebView2 runtime (already present on current Windows 11 and most
  Windows 10 machines). `build_exe.bat` builds it and is Windows-only.
- **Windows, macOS or Linux** for running from source in a browser.
- No internet connection is needed to run Pipeline. The page styling is a
  compiled file shipped in the repo (`static/css/output.css`).

## Running it from source

Windows (PowerShell or Command Prompt):

```bat
git clone <the repository URL>
cd <the folder git created>
python -m venv pipelinevenv
pipelinevenv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py create_default_user
python manage.py runserver
```

macOS / Linux:

```bash
git clone <the repository URL>
cd <the folder git created>
python3 -m venv pipelinevenv
source pipelinevenv/bin/activate
pip install -r requirements.txt   # pywin32 and the Windows-only parts are skipped automatically
cp .env.example .env
python manage.py migrate
python manage.py create_default_user
python manage.py runserver
```

`create_default_user` prints your login and a random password (and saves them in
`first_login.txt` in the data folder). Open `http://127.0.0.1:8000/`, log in,
then click **Change password**; the file is deleted when you do. If you skip
that command, the first visit shows a setup page where you choose your own
email and password instead. There is no built-in default password.

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
database (research saved by Claude would never appear in the app).

Running from source uses a separate database in `data\db\db.sqlite3` inside the
project. A user added in one does not exist in the other. To point source
commands at the desktop app's database, set `PIPELINE_DATA_DIR` first
(PowerShell): `$env:PIPELINE_DATA_DIR = "$env:USERPROFILE\Pipeline Data"`.

## Logins and passwords

- **First login:** created with a random password (see above). Change it under
  **Change password**.
- **Forgotten password:** close the app and run `Pipeline-Reset-Password.bat`
  (next to `Pipeline.exe`), or `python manage.py create_default_user --reset` from
  source. It sets a new random password and leaves your data alone.
- **Every user must be a superuser.** Pipeline is a single-owner tool and Django
  admin only lets in staff users. A normal user gets bounced to the admin login
  page, which looks exactly like being logged out. Add more users with
  `python manage.py createsuperuser`, or in Admin after saving tick both
  **Staff status** and **Superuser status**.

## Building the Windows app

```bat
build_exe.bat
```

Installs the pinned requirements and PyInstaller, compiles the stylesheet when
Node.js is installed, builds `dist\Pipeline\` and copies the guides, the license
and `Pipeline-Reset-Password.bat` next to `Pipeline.exe`. Ship the whole folder.

## Changing the guides

The wording is in `tools/docs_content.py`. Run `python tools/build_docs.py`
(needs `pip install reportlab==4.4.4`) to rebuild the PDF and text files in `docs/`.

## Notes

- Styling uses Tailwind CSS 4, compiled into `static/css/output.css`, which is
  committed, so running Pipeline needs no Node.js. After adding or changing
  classes in a template, run `npm install` once and then `npm run build:css`.
  `build_exe.bat` does this for you when Node.js is installed.
- `Contact.business` and the research `business` fields are plain free text, so
  Pipeline has no built-in list of businesses. Type whatever you call yours;
  the Research page lists the businesses that have research saved.
- Uploaded screenshots are served only to a logged-in user.
- CSV import checks every row like the Add Contact form does. Rows that fail
  are skipped and the first few problems are shown by row number.

## License

MIT. See `LICENSE.txt`.
