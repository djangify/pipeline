"""Text of the Pipeline guides. tools/build_docs.py turns this into PDF and TXT.

Edit the words here, run `python tools/build_docs.py`, and both formats update.
Block types: h1, h2, h3, p, steps, bullets, box (kind, title, text), table.
Keep to plain ASCII (plus the pound sign) so every PDF font can print it.
"""

UPDATED = "October 9, 2026"

# ---------------------------------------------------------------------------
# Full guide
# ---------------------------------------------------------------------------
GUIDE_FILE = "Pipeline-Setup-Guide"
GUIDE_TITLE = "Pipeline: Download, Setup and User Guide"
GUIDE_META = f"Last updated {UPDATED}. About a 12 minute read. Beginner level."

GUIDE = [
    ("box", "Key takeaways", "Key takeaways",
     "Pipeline is a free, open source leads CRM for one person. It keeps your contacts, "
     "follow-ups, conversations, purchases and market research on your own computer, "
     "with no cloud account and no subscription.\n"
     "The Windows app is the easy route. You unzip a folder and double-click Pipeline.exe.\n"
     "The first time you open it, a Notepad window shows your email and a random password. "
     "Log in, click Change password, and choose your own.\n"
     "Pipeline does not send messages for you. You do the reaching out, and Pipeline "
     "remembers who is due a follow-up.\n"
     "Your data lives in one folder. Copy it somewhere safe every week."),

    ("h2", "What Pipeline does and does not do"),
    ("p", "Pipeline is a small leads CRM. You add people you have found or spoken to, "
          "log each conversation, and tick off follow-ups as you do them. A contact "
          "moves through six statuses: New, Contacted, Replied, In conversation, "
          "Converted and Dead."),
    ("bullets", [
        "Contacts: name, where you found them, their handle and profile link, email, "
        "which of your businesses or projects they relate to, tags and notes.",
        "Follow-ups: three dated stages per contact. Ticking one done schedules the "
        "next two days later. The Follow-ups page lists everything due or overdue.",
        "Conversations: a dated log of every message, comment, email or call, with an "
        "optional screenshot.",
        "Purchases and check-ins: log what a contact bought and set a reminder to get "
        "in touch after the sale.",
        "Reports: new contacts, messages sent, replies, sales and revenue for any date "
        "range, plus revenue by month and leads by platform.",
        "Research: pain themes, competitor ads and keywords for each of your "
        "businesses.",
        "Import and export: bring contacts in from a CSV file, or export them all.",
    ]),
    ("box", "Good to know", "Good to know",
     "Pipeline never contacts anyone. It does not send messages, connect to social "
     "networks or scrape websites. The optional Claude connector (see below) can add "
     "prospects for you to review, but you decide who to contact and you send every "
     "message yourself."),

    ("h2", "Before you start"),
    ("bullets", [
        "A Windows 10 or Windows 11 computer for the Windows app.",
        "About 200 MB of free space for the app and room for your data.",
        "The Microsoft WebView2 runtime. It is already on current Windows 11 and most "
        "Windows 10 machines. If the window opens blank, see Troubleshooting.",
        "Python 3.10 or newer, only if you choose to run Pipeline from the source code. "
        "The Windows app does not need Python.",
    ]),

    ("h2", "Download and start Pipeline"),
    ("p", "Use the Windows app unless you want to work with the code. It is the same "
          "program, already packaged."),
    ("h3", "Option 1: The Windows app (no Python needed)"),
    ("steps", [
        "Download the Pipeline zip file from the project's download page. It is "
        "saved to your Downloads folder.",
        "Right-click the zip file, choose Extract All, then click Extract. You get a "
        "normal folder called Pipeline. Move the whole folder somewhere permanent, for "
        "example your Documents folder. Do not pull Pipeline.exe out on its own, it "
        "needs the files beside it.",
        "Open the folder and double-click Pipeline.exe.",
        "The first start takes a few seconds while Pipeline sets up its database. "
        "Wait for the window to open.",
    ]),
    ("box", "Watch out", "Windows says it protected your PC",
     "The first time, Windows may show a blue box saying \"Windows protected your PC\". "
     "This happens because the app is not code signed, which is common for free "
     "software. Click More info, then click Run anyway. You only do this once."),
    ("h3", "Option 2: Run it from the source code"),
    ("steps", [
        "Install Python 3.10 or newer from python.org. On the first screen of the "
        "installer, tick Add Python to PATH.",
        "Download the project (the green Code button, then Download ZIP, or use git) "
        "and extract it to a folder.",
        "Open a terminal in that folder and create a private Python environment: "
        "python -m venv pipelinevenv",
        "Switch it on: pipelinevenv\\Scripts\\activate (on Mac or Linux: source "
        "pipelinevenv/bin/activate).",
        "Install what Pipeline needs: pip install -r requirements.txt",
        "Copy the settings template: copy .env.example .env (on Mac or Linux: cp "
        ".env.example .env). You can leave every value as it is.",
        "Create the database: python manage.py migrate",
        "Create your login: python manage.py create_default_user. It prints a random "
        "password. Copy it.",
        "Start Pipeline: python manage.py runserver",
        "Open your browser at http://127.0.0.1:8000/ and log in.",
    ]),
    ("p", "To open Pipeline in its own window instead of a browser tab, run "
          "python desktop.py after step 5. Source data is kept in the data folder inside "
          "the project."),
    ("box", "Tip", "Port 8000 already in use?",
     "Run python manage.py runserver 8001 and open http://127.0.0.1:8001/ instead."),

    ("h2", "Your first login and password"),
    ("p", "Pipeline has no built-in password. The first time it starts, it creates your "
          "login with a random 16 character password and saves it in a small text file "
          "called first_login.txt. The Windows app opens that file in Notepad for you."),
    ("steps", [
        "Read the email and password in the Notepad window. The email looks like an "
        "address but it is only your user name.",
        "Type them into the Pipeline login page and click Log in.",
        "Click Change password in the top right. Enter the random password, then choose "
        "a new one twice.",
        "Pipeline deletes first_login.txt for you as soon as the password is changed. "
        "If you ever see the file again, delete it.",
    ]),
    ("table", ["Version", "Where first_login.txt is"], [
        ["Windows app", "C:\\Users\\<you>\\Pipeline Data (paste %USERPROFILE%\\Pipeline Data into the File Explorer address bar)"],
        ["Source code", "The data folder inside the project folder"],
    ]),
    ("box", "Tip", "Choose a passphrase",
     "Four or five random words, such as tractor lemon river cupboard, is easier to "
     "remember than symbols and much harder to guess. Pipeline rejects very short, "
     "very common or all number passwords."),
    ("box", "Watch out", "Nobody can recover your account for you",
     "Everything is stored on this computer only. There is no email reset. If you forget "
     "the password, use the reset steps further down. Your contacts are not touched."),

    ("h2", "Set up your pipeline: first session checklist"),
    ("bullets", [
        "Change the first password and check that first_login.txt is gone.",
        "Click Add Contact and enter one real person to see how it works.",
        "Open the contact and click Log Interaction to record a message you sent.",
        "Look at the Follow-ups page to see the reminder appear.",
        "Open Reports to see your numbers update.",
        "Copy your data folder to a USB drive or another safe place (see Backups).",
    ]),

    ("h2", "Everyday use"),
    ("h3", "Adding a contact"),
    ("p", "Click Add Contact. Only the name is needed. The useful extras are the "
          "platform you found them on, their profile link, a status, which of your "
          "businesses or projects they relate to, tags separated by commas, and a "
          "follow-up date. The business is plain text, so type whatever name you use."),
    ("h3", "Statuses"),
    ("table", ["Status", "Meaning"], [
        ["New", "You have found them but not yet reached out."],
        ["Contacted", "You have sent a first message. Logging an interaction moves a New contact here for you."],
        ["Replied", "They answered."],
        ["In conversation", "You are talking."],
        ["Converted", "They became a customer. Logging a purchase sets this for you."],
        ["Dead", "No interest. Pipeline asks for a reason so you remember why."],
    ]),
    ("h3", "Follow-ups"),
    ("p", "Set a follow-up date on a contact. The contact page shows Follow-up 1, 2 and "
          "3. Tick one when you have done it and Pipeline sets the next date two days "
          "ahead. When the third is ticked, the reminder clears. The Follow-ups page "
          "lists every follow-up and check-in, oldest first, with a Mark done button."),
    ("h3", "Logging conversations"),
    ("p", "On a contact, click Log Interaction. Choose the date, whether you reached "
          "out or they did, the channel, and paste in what was said. You can attach a "
          "screenshot. Everything appears on the contact's timeline, together with "
          "status changes and purchases."),
    ("h3", "Purchases and check-ins"),
    ("p", "When someone buys, click Add Purchase on their page and enter the product and "
          "amount. Their total revenue updates and their status becomes Converted. To "
          "remember a thank-you or a re-offer, edit the contact and fill in Next "
          "check-in and the note. It shows on the Follow-ups page when it is due. "
          "Amounts are shown in pounds."),
    ("h3", "Importing and exporting contacts"),
    ("p", "Click Import CSV and choose a file with a header row. Columns are matched by "
          "name, for example name, email, platform, status, business, tags and notes. "
          "Anything unrecognized is ignored. Every row is checked the same way as the "
          "Add Contact form. Rows with a problem are skipped and the first few "
          "problems are listed by row number, so you can fix the file and import again. "
          "Export CSV downloads every contact."),
    ("h3", "Reports"),
    ("p", "Pick a start and end date. You see new contacts, messages sent, replies, the "
          "reply rate, sales and revenue, a revenue by month chart and a chart of leads "
          "by platform."),
    ("h3", "Research"),
    ("p", "The Research page shows pain themes (what your audience complains about), "
          "competitor ads and keywords, grouped by business. A business appears there "
          "once research has been saved for it. You can add research by hand in the Admin "
          "area, or through the optional Claude connector."),
    ("h3", "Where to find things"),
    ("table", ["To do this", "Go here"], [
        ["See and search contacts", "Contacts (home page)"],
        ["See what is due", "Follow-ups"],
        ["Check your numbers", "Reports"],
        ["Look at market research", "Research"],
        ["Edit search profiles, follow-up message templates, raw data", "Admin"],
        ["Bring contacts in or out", "Import CSV, Export CSV (home page)"],
        ["Change your password", "Change password (top right)"],
    ]),
    ("box", "Good to know", "Follow-up message templates",
     "In Admin, under Follow up templates, you can save a reusable message for each "
     "follow-up stage. The contact page shows the template for the stage you are on."),
    ("box", "Watch out", "Every login must be a superuser",
     "The Admin area only lets in staff users. If you add another login in Admin, tick "
     "both Staff status and Superuser status and save again. Otherwise it looks like you "
     "have been logged out when you click Admin. The first login is set up correctly."),

    ("h2", "Connect Claude Desktop (optional)"),
    ("p", "If you use Claude Desktop, Pipeline can connect to it so Claude can look up "
          "your contacts, check what is due, and add new prospects for you to review. "
          "This is optional. Pipeline works fully without it."),
    ("steps", [
        "Open Pipeline.exe. It adds itself to Claude Desktop's list of connectors "
        "automatically.",
        "Restart Claude Desktop once.",
        "Ask Claude something like: who is due a follow-up this week?",
    ]),
    ("p", "To find prospects, save a search profile first (in Admin, under Search "
          "profiles) describing who you want to reach and the phrases that signal them. "
          "Claude reads the profile, searches public pages only, checks for duplicates "
          "and adds people as New contacts tagged ai-sourced, with a note on why each "
          "one fits. You review them and do all the outreach."),
    ("box", "Watch out", "Claude can change your data",
     "The connector can add, edit and delete contacts, purchases and research. Deletes "
     "ask Claude to confirm first, but keep a recent backup and read what Claude "
     "adds before you act on it."),
    ("p", "If the connection does not appear, open the Pipeline Data folder and read "
          "claude_connect.log. The connector uses the same database as the app, so "
          "anything Claude saves shows up in Pipeline."),

    ("h2", "Email reminders (optional)"),
    ("p", "Pipeline can email you a list of what is due. It is a command, not a button, "
          "so it suits people running from source. In the .env file, set "
          "FOLLOWUP_REMINDER_TO to your address and fill in the EMAIL_ lines for your "
          "mail provider. Then run python manage.py followup_reminders. To run it every "
          "morning, use Windows Task Scheduler. With no mail settings the reminder is "
          "printed in the terminal instead."),

    ("h2", "Backups and keeping your data safe"),
    ("p", "Pipeline keeps everything in one folder. Copy that folder to keep a backup."),
    ("table", ["Version", "Your data folder"], [
        ["Windows app", "%USERPROFILE%\\Pipeline Data"],
        ["Source code", "The data folder inside the project folder"],
    ]),
    ("p", "Inside are db (your database), media (uploaded screenshots) and "
          "secret_key.txt. Close Pipeline, then copy the whole folder. To restore, close "
          "Pipeline and copy it back. Export CSV is a second, readable copy of your "
          "contacts."),
    ("box", "Watch out", "Pipeline does not back up for you",
     "Copy your data folder to a USB drive or an encrypted cloud folder every week. A "
     "copy on the same disk does not help if the computer is lost or fails. Your "
     "database holds names, emails and private conversations, so also use a Windows "
     "login password, lock the screen when you leave, and consider turning on BitLocker."),

    ("h2", "If you forget your password"),
    ("steps", [
        "Close Pipeline.",
        "Double-click Pipeline-Reset-Password.bat in the same folder as Pipeline.exe, "
        "then press any key when it asks.",
        "A Notepad window opens with a new random password.",
        "Log in, click Change password and choose your own. Pipeline deletes the file.",
    ]),
    ("p", "Your contacts and research are not touched. From source, run python "
          "manage.py create_default_user --reset instead."),
    ("box", "Watch out", "Anyone who can open your files can reset it",
     "The reset works for anyone using your Windows account. That is why the Windows "
     "login password and screen lock matter."),

    ("h2", "Updating to a new version"),
    ("steps", [
        "Close Pipeline and make a backup of your data folder.",
        "Extract the new zip into a new folder.",
        "Open Pipeline.exe from the new folder. It finds your existing data and updates "
        "the database itself.",
        "When you are happy, delete the old folder. The data folder is separate, so "
        "deleting the old program folder does not delete your data.",
    ]),
    ("p", "If you use the Claude connector, opening the new Pipeline.exe points Claude "
          "Desktop at the new folder. Restart Claude Desktop afterwards."),

    ("h2", "Troubleshooting"),
    ("table", ["Problem", "What to do"], [
        ["The window is blank or white",
         "Install the Microsoft WebView2 runtime from Microsoft, then open Pipeline again."],
        ["Windows blocks Pipeline.exe",
         "Click More info, then Run anyway. If the zip was downloaded from the internet, right-click it, choose Properties and tick Unblock before extracting."],
        ["The page looks plain with no styling (source code)",
         "Hold Ctrl and press F5 to refresh without the cached page."],
        ["Admin sends me to a login page",
         "The login is not a superuser. See the box under Where to find things."],
        ["I cannot find first_login.txt",
         "It is deleted when you change your password. If you have not and you lost it, use the reset steps."],
        ["Port 8000 is already in use (source code)",
         "Run python manage.py runserver 8001."],
        ["Python is not recognized (source code)",
         "Reinstall Python and tick Add Python to PATH, then open a new terminal."],
        ["Claude cannot see Pipeline",
         "Open Pipeline.exe once, restart Claude Desktop, and read claude_connect.log in your data folder."],
        ["Where is my data?",
         "See the Backups section."],
        ["Can I use it on Mac or Linux?",
         "Run it from source in a browser. The packaged app and the automatic Claude connection are for Windows."],
        ["Can two people share it?",
         "No. Pipeline is for one owner on one computer."],
    ]),

    ("box", "Watch out", "Use at your own risk",
     "Pipeline is provided as is, with no warranty. It is a tool for keeping notes, "
     "not legal or data protection advice. If you store other people's personal details, "
     "you are responsible for handling them lawfully and for keeping backups. See "
     "LICENSE.txt for the full terms."),

    ("h2", "Summary"),
    ("bullets", [
        "Pipeline keeps your leads on your own computer, with no account and no cloud.",
        "Open Pipeline.exe, read the password in Notepad, then change it.",
        "Add contacts, log conversations, and tick follow-ups as you go.",
        "Check Reports to see your replies, sales and revenue.",
        "Copy your data folder somewhere safe every week.",
        "If you forget the password, run Pipeline-Reset-Password.bat.",
    ]),
]

# ---------------------------------------------------------------------------
# Short how-to-open sheet (goes next to Pipeline.exe)
# ---------------------------------------------------------------------------
HOWTO_FILE = "HOW-TO-OPEN-PIPELINE"
HOWTO_TITLE = "How to Open Pipeline"
HOWTO_META = "Follow these steps one at a time. It is easy."

HOWTO = [
    ("h2", "1. Download it"),
    ("p", "Click the download link. You get a file called Pipeline.zip. It usually goes "
          "into your Downloads folder. Wait for it to finish."),
    ("h2", "2. Unzip it"),
    ("p", "Right-click Pipeline.zip and choose Extract All, then click Extract. This "
          "makes a normal folder called Pipeline. Move the whole folder somewhere "
          "permanent, such as your Documents folder."),
    ("h2", "3. Open the app"),
    ("p", "Open the Pipeline folder, find Pipeline.exe and double-click it."),
    ("h2", "4. If Windows shows a blue warning"),
    ("p", "The first time, Windows may say \"Windows protected your PC\". This is normal "
          "for free apps that are not code signed."),
    ("bullets", ["Click More info", "Then click Run anyway"]),
    ("p", "You only do this once."),
    ("h2", "5. The app opens"),
    ("p", "A window opens. The first time it may take a few seconds to get ready."),
    ("h2", "6. Log in"),
    ("p", "The first time, a small Notepad window opens by itself. It shows your email "
          "and a random password made just for you."),
    ("bullets", [
        "Type them into Pipeline and click Log in.",
        "Click Change password in the top right and choose a password of your own.",
        "Pipeline then deletes the first_login.txt file for you. If you still see it, "
        "delete it. It is in the folder %USERPROFILE%\\Pipeline Data (paste that into "
        "the File Explorer address bar).",
    ]),
    ("p", "Forgot your password? Close Pipeline, then double-click "
          "Pipeline-Reset-Password.bat in the same folder as Pipeline.exe. A new random "
          "password opens in Notepad. Log in, change it, and your contacts are not touched."),
    ("p", "Keep your password somewhere safe, for example a password manager or a "
          "notebook that stays at home. Your contacts are stored on this computer only, "
          "so nobody else can recover them for you."),
    ("h2", "7. Pin it so it is easy to find next time"),
    ("p", "While Pipeline is open, look at the bar along the bottom of your screen. "
          "Right-click the Pipeline icon and choose Pin to taskbar. To add it to the "
          "Start menu, right-click Pipeline.exe, choose Show more options if you see "
          "it, then Pin to Start."),
    ("p", "Now you can open Pipeline any time with one click. Done!"),
    ("p", "For the full guide, open Pipeline-Setup-Guide.pdf in this folder."),
]
