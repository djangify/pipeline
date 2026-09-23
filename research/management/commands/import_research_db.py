# research/management/commands/import_research_db.py
"""
Copy research rows (competitor ads, keywords, pain themes) and search profiles
from another Pipeline database file into this one.

Written for the case where two installs drifted apart -- e.g. research Claude
saved through the connector landed in Claude Desktop's virtualized AppData
copy instead of the app's real database. Rows already present are skipped:
keywords and pain themes by (business, term/theme), search profiles by
business, competitor ads by identical content. The source file is only read.

    python manage.py import_research_db "C:/path/to/other/db.sqlite3"
"""
import sqlite3

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from crm.models import SearchProfile
from research.models import CompetitorAd, Keyword, PainTheme

# model -> fields that identify an existing row (None = every copied field)
MODELS = [
    (CompetitorAd, None),
    (Keyword, ["business", "term"]),
    (PainTheme, ["business", "theme"]),
    (SearchProfile, ["business"]),
]


class Command(BaseCommand):
    help = "Copy research rows and search profiles from another Pipeline database."

    def add_arguments(self, parser):
        parser.add_argument("source", help="Path to the other db.sqlite3")

    def handle(self, source, **options):
        try:
            src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
        except sqlite3.Error as exc:
            raise CommandError(f"Can't open {source}: {exc}")
        src.row_factory = sqlite3.Row

        with transaction.atomic():
            for model, key_fields in MODELS:
                fields = [
                    f.name
                    for f in model._meta.concrete_fields
                    if f.name not in ("id", "created_at", "updated_at")
                ]
                rows = src.execute(
                    f"SELECT {', '.join(fields)} FROM {model._meta.db_table}"
                ).fetchall()
                added = skipped = 0
                for row in rows:
                    data = {f: row[f] for f in fields}
                    lookup = {f: data[f] for f in (key_fields or fields)}
                    if model.objects.filter(**lookup).exists():
                        skipped += 1
                        continue
                    model.objects.create(**data)
                    added += 1
                self.stdout.write(
                    f"{model._meta.verbose_name_plural}: {added} added, {skipped} already there"
                )
        src.close()
