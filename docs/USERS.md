# Users and logins

## The rule

**Every Pipeline login must be a superuser.** When you set up a new user, give
them superuser access (which also makes them staff).

Pipeline is a single-owner tool. Django admin only lets in staff users, so a
normal login can use Contacts, Follow-ups and Research but gets bounced to the
admin login page when it clicks Admin. That looks exactly like being logged
out, and it is easy to mistake for a bug.

## Which database?

Pipeline keeps two separate databases. Make sure you change the right one.

| How you run Pipeline | Database |
|---|---|
| `Pipeline.exe` (desktop app) | `%USERPROFILE%\Pipeline Data\db\db.sqlite3` |
| `python manage.py runserver` (from source) | `data\db\db.sqlite3` in the project folder |

A user added in one does not exist in the other.

The desktop app's data deliberately lives outside AppData. Claude Desktop
redirects AppData for everything it launches (including the Pipeline
connector), so data kept there splits into two databases. Older builds used
`%LOCALAPPDATA%\Pipeline`; the first launch of a newer Pipeline.exe copies it
across and leaves the old folder as a backup.

To run the commands below against the **desktop app's** database, set
`PIPELINE_DATA_DIR` first (PowerShell, from the project folder):

```powershell
$env:PIPELINE_DATA_DIR = "$env:USERPROFILE\Pipeline Data"
```

Leave it unset to work on the source/dev database.

## Add a new user

### Command line (recommended)

```powershell
pipelinevenv\Scripts\python manage.py createsuperuser
```

Enter the email address as the username. `createsuperuser` sets staff and
superuser automatically.

### In the admin

1. Log in as an existing superuser and go to **Admin → Users → Add user**.
2. Enter the username (their email) and password, then click **Save**.
3. On the next screen, tick **Staff status** and **Superuser status**.
4. Click **Save** again.

Step 3 is the one that gets missed. Without it the new login cannot open Admin.

## Upgrade an existing login to superuser

### In the admin

Log in as a superuser, open **Admin → Users → (their email)**, tick
**Staff status** and **Superuser status**, then save.

### Command line

```powershell
pipelinevenv\Scripts\python manage.py shell -c "from django.contrib.auth import get_user_model; u = get_user_model().objects.get(username='name@example.com'); u.is_staff = u.is_superuser = True; u.save(); print('done')"
```

Replace `name@example.com` with the login's username. Close Pipeline.exe first
if you are changing the desktop app's database.

## The default login

On first launch the desktop app creates `admin@example.com` / `admin123` as a
superuser, but only if the database has no users yet (see
`crm/management/commands/create_default_user.py`). Set `DEFAULT_USER_EMAIL`
and `DEFAULT_USER_PASSWORD` before first launch to change it. Change the
password once you are in.
