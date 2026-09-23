# mcp_server/server.py
"""MCP server exposing Pipeline's contacts and search profiles over stdio.

Point Claude Desktop / Cowork / Claude Code at it (desktop.py registers it in
Claude Desktop's config automatically on launch) so an external Claude can look
up contacts, add AI-sourced prospects for review, and check follow-ups due.

Run it with:  python manage.py runmcp   (stdio transport)
"""
import datetime
import os
import re
from decimal import Decimal, InvalidOperation

import django
from django.apps import apps

# FastMCP invokes sync tools inside its asyncio loop, which trips Django's
# "cannot call this from an async context" ORM guard. This is a single-user,
# local stdio server that handles one request at a time, so briefly running a
# SQLite query on the loop thread is safe -- opt out of the guard rather than
# thread every ORM call. Must be set before any ORM use.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "1")

# Works both as a standalone script (`python -m mcp_server.server`) and when
# imported after Django is already configured (the runmcp management command).
if not apps.ready:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()

from django.db.models import Q
from django.utils import timezone
from mcp.server.fastmcp import FastMCP

from crm.models import Contact, SearchProfile

# The server-level instructions Claude Desktop / Cowork reads at connect time.
# The job of this connector ends at getting well-researched candidates INTO
# Pipeline for the owner to review. Outreach stays with the owner, and the
# connecting Claude must never log into or automate LinkedIn/Facebook.
INSTRUCTIONS = (
    "Pipeline is the owner's personal leads CRM. Use it to look up contacts, "
    "check follow-ups due, and add new prospects for the owner to review. "
    "Dates are ISO strings (YYYY-MM-DD).\n\n"
    "FINDING PROSPECTS. When the owner asks you to find prospects, leads or "
    "potential customers for a business, work in this order:\n"
    "1. Call get_search_profile for that business FIRST (list_search_profiles "
    "shows which exist). Its audience_description says who the ideal prospect "
    "is and its keywords are the signal phrases to search for, including "
    "complaint and intent phrases such as 'sick of paying fees', "
    "'alternative to X' or 'account suspended'. Search against the owner's "
    "profile, not your own idea of the audience. If no profile exists, ask the "
    "owner to describe the audience (and offer to save it with "
    "create_search_profile) before searching.\n"
    "2. Use your own web search to find PUBLIC candidates: personal websites, "
    "Gumroad / Stan Store / Payhip storefronts, public LinkedIn profile pages "
    "that Google has indexed, and Reddit posts or comments matching the "
    "keywords. NEVER log into LinkedIn or Facebook, and never attempt any "
    "in-app browsing, scraping or automation of them. Only use what a search "
    "engine shows publicly.\n"
    "3. Before adding anyone, call find_contact with their name plus any "
    "website/profile URL, email and handle you found, to check they are not "
    "already in Pipeline. Skip anyone who is.\n"
    "4. Add each new candidate with create_contact: status='new', the "
    "business being prospected for, the tag 'ai-sourced', the most relevant "
    "platform and profile_url, and a notes field explaining WHY this person "
    "is a plausible fit: which keyword or signal matched, where you found "
    "them (include the source URL), and what they sell or say that fits the "
    "audience description. Only record what you actually saw; never guess an "
    "email address or invent details.\n"
    "5. Finish with a short summary of who you added (and who you skipped as "
    "duplicates) so the owner can review them in Pipeline.\n\n"
    "OUTREACH IS THE OWNER'S JOB. Do not message, email, follow, connect with, "
    "comment on or otherwise contact anyone, and do not draft outreach unless "
    "the owner explicitly asks. Your job ends at getting candidates into "
    "Pipeline for review. Only change a contact's status past 'new' when the "
    "owner tells you what happened."
)

mcp = FastMCP("pipeline", instructions=INSTRUCTIONS)

AI_SOURCED_TAG = "ai-sourced"


# --- helpers ----------------------------------------------------------------

def _resolve_choice(value: str, choices, field: str) -> str:
    """Accept either a choice key ('self_talk_effect') or its label ('The
    Self-Talk Effect'), case-insensitively. Raises ValueError listing the valid
    keys otherwise, so the caller can correct itself in one step."""
    v = (value or "").strip()
    if not v:
        return ""
    low = v.lower()
    for key, label in choices:
        if low == str(key).lower() or low == str(label).lower():
            return key
    valid = ", ".join(str(k) for k, _ in choices)
    raise ValueError(f"Unknown {field} '{value}'. Use one of: {valid}")


def _parse_date(value: str, field: str):
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(f"{field} must be YYYY-MM-DD, got '{value}'") from exc


def _split_tags(value) -> list[str]:
    if isinstance(value, (list, tuple)):
        parts = value
    else:
        parts = (value or "").split(",")
    return [t.strip() for t in parts if t and t.strip()]


def _merge_tags(existing: str, extra) -> str:
    """Comma-joined union of two tag lists, keeping order, case-insensitive."""
    out, seen = [], set()
    for tag in _split_tags(existing) + _split_tags(extra):
        if tag.lower() not in seen:
            seen.add(tag.lower())
            out.append(tag)
    return ", ".join(out)


def _normalize_url(url: str) -> str:
    """Scheme-less, www-less, lowercase host + path without trailing slash, so
    'https://www.Jane.com/' and 'jane.com' compare equal."""
    u = (url or "").strip().lower()
    u = re.sub(r"^[a-z][a-z0-9+.-]*://", "", u)
    u = re.sub(r"^www\.", "", u)
    u = u.split("#", 1)[0].split("?", 1)[0]
    return u.rstrip("/")


def _normalize_handle(handle: str) -> str:
    return (handle or "").strip().lstrip("@").lower()


def _contact_dict(c: Contact, *, full: bool = False) -> dict:
    out = {
        "id": c.id,
        "name": c.name,
        "business": c.business,
        "status": c.status,
        "platform": c.platform,
        "social_handle": c.social_handle,
        "profile_url": c.profile_url,
        "email": c.email,
        "tags": c.tag_list,
        "follow_up_date": c.follow_up_date.isoformat() if c.follow_up_date else None,
        "updated_at": c.updated_at.isoformat(timespec="seconds"),
    }
    if full:
        out.update({
            "notes": c.notes,
            "follow_up_1_done": c.follow_up_1_done,
            "follow_up_2_done": c.follow_up_2_done,
            "follow_up_3_done": c.follow_up_3_done,
            "follow_up_overdue": c.follow_up_overdue,
            "joined_email_list": c.joined_email_list,
            "made_purchase": c.made_purchase,
            "revenue": str(c.revenue) if c.revenue is not None else None,
            "created_at": c.created_at.isoformat(timespec="seconds"),
        })
    else:
        # A short preview is enough to recognise someone in a list.
        out["notes_preview"] = (c.notes[:160] + "...") if len(c.notes) > 160 else c.notes
    return out


def _profile_dict(p: SearchProfile) -> dict:
    return {
        "id": p.id,
        "business": p.business,
        "business_label": p.get_business_display(),
        "website": p.website,
        "audience_description": p.audience_description,
        "keywords": p.keyword_list,
        "updated_at": p.updated_at.isoformat(timespec="seconds"),
    }


def _find_matches(name="", website="", email="", social_handle="", profile_url=""):
    """Duplicate check shared by find_contact and create_contact.

    'exact' = a strong identifier matches (email, handle, same URL, or the
    exact same name). 'possible' = a weaker signal (partial name, or the URL
    only appearing in someone's notes) worth a human glance."""
    exact: dict[int, tuple[Contact, list[str]]] = {}
    possible: dict[int, tuple[Contact, list[str]]] = {}

    def add(bucket, contact, reason):
        bucket.setdefault(contact.id, (contact, []))[1].append(reason)

    email = (email or "").strip()
    if email:
        for c in Contact.objects.filter(email__iexact=email):
            add(exact, c, "same email")

    handle = _normalize_handle(social_handle)
    if handle:
        for c in Contact.objects.filter(
            Q(social_handle__iexact=handle) | Q(social_handle__iexact="@" + handle)
        ):
            add(exact, c, "same social handle")

    for raw in (website, profile_url):
        url = _normalize_url(raw)
        if not url:
            continue
        # Filter coarsely in SQL, then compare normalised forms in Python so
        # scheme/www/trailing-slash differences don't hide a duplicate.
        for c in Contact.objects.filter(profile_url__icontains=url.split("/", 1)[0]):
            if _normalize_url(c.profile_url) == url:
                add(exact, c, f"same URL ({url})")
        for c in Contact.objects.filter(notes__icontains=url):
            add(possible, c, f"URL {url} mentioned in notes")

    name = (name or "").strip()
    if name:
        for c in Contact.objects.filter(name__iexact=name):
            add(exact, c, "same name")
        # Word overlap, in either direction, catches "Jane Smith" vs
        # "Jane Smith Coaching" or "J. Smith". Pull candidates sharing any
        # longer word in SQL, then compare word sets in Python.
        def tokens(s):
            return {w for w in re.findall(r"[a-z0-9']+", s.lower()) if len(w) >= 3}

        wanted = tokens(name)
        q = Q(name__icontains=name)
        for w in wanted:
            q |= Q(name__icontains=w)
        for c in Contact.objects.filter(q):
            have = tokens(c.name)
            shared = wanted & have
            if (name.lower() in c.name.lower() or c.name.lower() in name.lower()
                    or (shared and (shared == wanted or shared == have or len(shared) >= 2))):
                add(possible, c, "similar name")

    for cid in exact:
        possible.pop(cid, None)

    def rows(bucket):
        return [
            {**_contact_dict(c), "match_reasons": sorted(set(reasons))}
            for c, reasons in bucket.values()
        ]

    return rows(exact), rows(possible)


# --- contacts -----------------------------------------------------------------

@mcp.tool()
def list_contacts(
    query: str = "",
    business: str = "",
    status: str = "",
    tag: str = "",
    platform: str = "",
    limit: int = 50,
) -> dict:
    """List/search contacts, newest-updated first. `query` searches name,
    handle, email, profile URL, tags and notes. Filter by business
    (djangify / inspirational_guidance / self_talk_effect / todiane / other),
    status (new / contacted / replied / in_conversation / converted / dead),
    tag (e.g. 'ai-sourced') and platform. For a duplicate check before adding
    someone, use find_contact instead."""
    qs = Contact.objects.all()
    if query.strip():
        q = query.strip()
        qs = qs.filter(
            Q(name__icontains=q) | Q(social_handle__icontains=q)
            | Q(email__icontains=q) | Q(profile_url__icontains=q)
            | Q(tags__icontains=q) | Q(notes__icontains=q)
        )
    if business:
        qs = qs.filter(business=_resolve_choice(business, Contact.BUSINESS_CHOICES, "business"))
    if status:
        qs = qs.filter(status=_resolve_choice(status, Contact.STATUS_CHOICES, "status"))
    if platform:
        qs = qs.filter(platform=_resolve_choice(platform, Contact.PLATFORM_CHOICES, "platform"))
    if tag.strip():
        # tags is a free-text comma list; filter coarsely then exactly.
        wanted = tag.strip().lower()
        qs = [c for c in qs.filter(tags__icontains=wanted)
              if wanted in (t.lower() for t in c.tag_list)]
    total = len(qs) if isinstance(qs, list) else qs.count()
    limit = max(1, min(int(limit or 50), 200))
    return {
        "total": total,
        "returned": min(total, limit),
        "contacts": [_contact_dict(c) for c in list(qs)[:limit]],
    }


@mcp.tool()
def find_contact(
    name: str = "",
    website: str = "",
    email: str = "",
    social_handle: str = "",
    profile_url: str = "",
) -> dict:
    """Duplicate-safe lookup: call this BEFORE create_contact with everything
    you know about the person (name, their website or storefront URL, email,
    @handle, profile URL). Returns exact_matches (same email, handle, URL or
    exact name: treat as already in Pipeline, do not add again) and
    possible_matches (similar name, or the URL mentioned in someone's notes:
    check them with get_contact before deciding)."""
    if not any(v.strip() for v in (name, website, email, social_handle, profile_url)):
        return {"error": "Pass at least one of name, website, email, social_handle, profile_url."}
    exact, possible = _find_matches(name, website, email, social_handle, profile_url)
    return {
        "already_exists": bool(exact),
        "exact_matches": exact,
        "possible_matches": possible,
    }


@mcp.tool()
def get_contact(contact_id: int) -> dict:
    """Full details of one contact, including notes, follow-up stages and the
    logged interactions (most recent first)."""
    try:
        c = Contact.objects.get(pk=contact_id)
    except Contact.DoesNotExist:
        return {"error": f"No contact with id {contact_id}."}
    out = _contact_dict(c, full=True)
    out["interactions"] = [
        {
            "date": i.date.isoformat(),
            "direction": i.direction,
            "channel": i.channel,
            "message": i.message,
        }
        for i in c.interactions.all()[:25]
    ]
    return out


@mcp.tool()
def create_contact(
    name: str,
    business: str,
    notes: str,
    platform: str = "other",
    social_handle: str = "",
    profile_url: str = "",
    email: str = "",
    status: str = "new",
    tags: str = AI_SOURCED_TAG,
    follow_up_date: str = "",
    follow_up_1_done: bool = False,
    follow_up_2_done: bool = False,
    follow_up_3_done: bool = False,
    joined_email_list: bool = False,
    made_purchase: bool = False,
    revenue: str = "",
    allow_duplicate: bool = False,
) -> dict:
    """Add a contact to Pipeline. For prospects you found yourself: status='new',
    keep 'ai-sourced' in tags (the default; add others alongside it, e.g.
    'ai-sourced, gumroad'), and use `notes` to explain WHY they are a
    plausible fit: the matched keyword/signal, the source URL where you found
    them, and what they sell or said. Only record what you actually saw. For a
    contact the owner gives you themselves, set tags to whatever they want.

    business: djangify / inspirational_guidance / self_talk_effect / todiane /
    other. platform: where you found them (instagram, linkedin, x, facebook,
    tiktok, youtube, threads, reddit, email, referral, other). profile_url: the
    public page you found them on (personal site, storefront, profile).
    tags: comma-separated. follow_up_date: YYYY-MM-DD. revenue: e.g. '49.00'.

    Runs the same check as find_contact first and refuses to save if an exact
    match already exists (returning the match). Pass allow_duplicate=True only
    if the owner confirms it really is a different person."""
    name = (name or "").strip()
    if not name:
        return {"error": "name is required."}
    try:
        business_key = _resolve_choice(business, Contact.BUSINESS_CHOICES, "business")
        status_key = _resolve_choice(status or "new", Contact.STATUS_CHOICES, "status")
        platform_key = _resolve_choice(platform or "other", Contact.PLATFORM_CHOICES, "platform")
        fu_date = _parse_date(follow_up_date, "follow_up_date")
        rev = None
        if str(revenue).strip():
            try:
                rev = Decimal(str(revenue).strip())
            except InvalidOperation:
                raise ValueError(f"revenue must be a number, got '{revenue}'")
    except ValueError as exc:
        return {"error": str(exc)}

    if not allow_duplicate:
        exact, possible = _find_matches(name, "", email, social_handle, profile_url)
        if exact:
            return {
                "error": (
                    "Not saved: this looks like someone already in Pipeline. "
                    "Review the match below; if it really is a different person, "
                    "call create_contact again with allow_duplicate=True."
                ),
                "exact_matches": exact,
            }
    else:
        possible = []

    contact = Contact(
        name=name,
        business=business_key,
        status=status_key,
        platform=platform_key,
        social_handle=(social_handle or "").strip(),
        profile_url=(profile_url or "").strip(),
        email=(email or "").strip(),
        tags=_merge_tags("", tags),
        notes=(notes or "").strip(),
        follow_up_date=fu_date,
        follow_up_1_done=follow_up_1_done,
        follow_up_2_done=follow_up_2_done,
        follow_up_3_done=follow_up_3_done,
        joined_email_list=joined_email_list,
        made_purchase=made_purchase,
        revenue=rev,
    )
    try:
        contact.full_clean()
    except Exception as exc:  # ValidationError: bad URL/email, too long, etc.
        return {"error": f"Not saved: {exc}"}
    contact.save()
    out = {"created": _contact_dict(contact, full=True)}
    if possible:
        out["note"] = "Saved. Some similar contacts exist; mention them to the owner."
        out["possible_matches"] = possible
    return out


@mcp.tool()
def update_contact(
    contact_id: int,
    status: str = "",
    notes: str | None = None,
    append_note: str = "",
    add_tags: str = "",
    follow_up_date: str = "",
    business: str = "",
) -> dict:
    """Update a contact's status and/or notes (plus a few small extras).
    status: new / contacted / replied / in_conversation / converted / dead;
    only move a contact past 'new' when the owner tells you what happened.
    notes REPLACES the whole notes field; append_note adds a dated line to the
    end instead (prefer this). add_tags merges comma-separated tags in.
    follow_up_date: YYYY-MM-DD, or 'none' to clear it."""
    try:
        c = Contact.objects.get(pk=contact_id)
    except Contact.DoesNotExist:
        return {"error": f"No contact with id {contact_id}."}
    changed = []
    try:
        if status:
            c.status = _resolve_choice(status, Contact.STATUS_CHOICES, "status")
            changed.append("status")
        if business:
            c.business = _resolve_choice(business, Contact.BUSINESS_CHOICES, "business")
            changed.append("business")
        if follow_up_date:
            c.follow_up_date = (
                None if follow_up_date.strip().lower() == "none"
                else _parse_date(follow_up_date, "follow_up_date")
            )
            changed.append("follow_up_date")
    except ValueError as exc:
        return {"error": str(exc)}
    if notes is not None:
        c.notes = notes.strip()
        changed.append("notes")
    if append_note.strip():
        line = f"[{timezone.localdate().isoformat()}] {append_note.strip()}"
        c.notes = f"{c.notes.rstrip()}\n{line}" if c.notes.strip() else line
        changed.append("notes")
    if add_tags.strip():
        c.tags = _merge_tags(c.tags, add_tags)
        changed.append("tags")
    if not changed:
        return {"error": "Nothing to update: pass status, notes, append_note, add_tags, follow_up_date or business."}
    c.save()
    return {"updated_fields": sorted(set(changed)), "contact": _contact_dict(c, full=True)}


@mcp.tool()
def list_followups_due(days_ahead: int = 0, business: str = "", include_upcoming: bool = False) -> dict:
    """Contacts whose next follow-up is due: follow_up_date on or before today
    + days_ahead (0 = due today or overdue), with at least one follow-up stage
    still open. include_upcoming=True returns every scheduled follow-up
    regardless of date. Sorted by date, oldest first."""
    today = timezone.localdate()
    qs = Contact.objects.filter(follow_up_date__isnull=False, follow_up_3_done=False)
    if not include_upcoming:
        qs = qs.filter(follow_up_date__lte=today + datetime.timedelta(days=max(0, int(days_ahead or 0))))
    if business:
        try:
            qs = qs.filter(business=_resolve_choice(business, Contact.BUSINESS_CHOICES, "business"))
        except ValueError as exc:
            return {"error": str(exc)}
    rows = []
    for c in qs.order_by("follow_up_date"):
        row = _contact_dict(c)
        row["next_stage"] = c.current_stage
        row["overdue"] = c.follow_up_overdue
        row["days_overdue"] = max(0, (today - c.follow_up_date).days)
        rows.append(row)
    return {"today": today.isoformat(), "count": len(rows), "followups": rows}


# --- search profiles ------------------------------------------------------------

def _get_profile(business: str) -> SearchProfile | None:
    key = _resolve_choice(business, Contact.BUSINESS_CHOICES, "business")
    return SearchProfile.objects.filter(business=key).first()


@mcp.tool()
def list_search_profiles() -> dict:
    """All saved search profiles (one per business): who the ideal prospect is
    and which signal phrases to search for."""
    return {"profiles": [_profile_dict(p) for p in SearchProfile.objects.all()]}


@mcp.tool()
def get_search_profile(business: str) -> dict:
    """Call this FIRST whenever the owner asks you to find prospects. Returns
    the business's audience_description (who to look for) and keywords (the
    signal phrases to search for, including complaint/intent phrases like
    'sick of paying fees' or 'alternative to X' for Reddit-style searches).
    business: djangify / inspirational_guidance / self_talk_effect / todiane /
    other (or its display name)."""
    try:
        p = _get_profile(business)
    except ValueError as exc:
        return {"error": str(exc)}
    if p is None:
        return {
            "error": (
                f"No search profile saved for '{business}'. Ask the owner who "
                "the ideal prospect is and which phrases signal them, then save "
                "it with create_search_profile before searching."
            ),
            "existing_profiles": [p.business for p in SearchProfile.objects.all()],
        }
    return _profile_dict(p)


@mcp.tool()
def create_search_profile(
    business: str,
    audience_description: str,
    keywords: str,
    website: str = "",
) -> dict:
    """Save a new search profile for a business (one per business; use
    update_search_profile to change an existing one). keywords is a
    comma-separated list of signal phrases, e.g. 'life coach, Gumroad, Stan
    Store, download my guide, sick of paying fees, alternative to Kajabi'."""
    try:
        key = _resolve_choice(business, Contact.BUSINESS_CHOICES, "business")
    except ValueError as exc:
        return {"error": str(exc)}
    if not key:
        return {"error": "business is required."}
    if SearchProfile.objects.filter(business=key).exists():
        return {"error": f"A search profile for '{key}' already exists; use update_search_profile."}
    p = SearchProfile(
        business=key,
        website=(website or "").strip(),
        audience_description=(audience_description or "").strip(),
        keywords=_merge_tags("", keywords),
    )
    try:
        p.full_clean()
    except Exception as exc:
        return {"error": f"Not saved: {exc}"}
    p.save()
    return {"created": _profile_dict(p)}


@mcp.tool()
def update_search_profile(
    business: str,
    website: str | None = None,
    audience_description: str | None = None,
    keywords: str | None = None,
    add_keywords: str = "",
    remove_keywords: str = "",
) -> dict:
    """Change a business's search profile. Any argument left out is kept.
    keywords REPLACES the whole list; add_keywords / remove_keywords edit it
    (comma-separated, case-insensitive)."""
    try:
        p = _get_profile(business)
    except ValueError as exc:
        return {"error": str(exc)}
    if p is None:
        return {"error": f"No search profile for '{business}'; use create_search_profile."}
    if website is not None:
        p.website = website.strip()
    if audience_description is not None:
        p.audience_description = audience_description.strip()
    if keywords is not None:
        p.keywords = _merge_tags("", keywords)
    if add_keywords.strip():
        p.keywords = _merge_tags(p.keywords, add_keywords)
    if remove_keywords.strip():
        drop = {k.lower() for k in _split_tags(remove_keywords)}
        p.keywords = ", ".join(k for k in _split_tags(p.keywords) if k.lower() not in drop)
    try:
        p.full_clean()
    except Exception as exc:
        return {"error": f"Not saved: {exc}"}
    p.save()
    return {"updated": _profile_dict(p)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
