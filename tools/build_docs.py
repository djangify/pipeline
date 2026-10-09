"""Build Pipeline's guides as PDF and plain text.

    pip install reportlab==4.4.4
    python tools/build_docs.py

Writes into docs/:
    Pipeline-Setup-Guide.pdf / .txt     the full guide
    HOW-TO-OPEN-PIPELINE.pdf / .txt     the one-page "double-click it" sheet
    LICENSE.pdf                          a PDF copy of LICENSE.txt
    THIRD_PARTY_NOTICES.pdf / .txt      licences of the packages the app bundles

The wording lives in tools/docs_content.py. THIRD_PARTY_NOTICES is built from
whatever is installed, so run this from a virtual environment that holds only
requirements.txt (plus reportlab) if you want that file regenerated; pass
--skip-third-party to leave it as it is.
"""
import importlib.metadata as md
import sys
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import docs_content as C  # noqa: E402

WIDTH = 78

# ---------------------------------------------------------------------------
# Plain text
# ---------------------------------------------------------------------------


def _wrap(text, indent="", first=None):
    first = indent if first is None else first
    out = []
    for i, para in enumerate(text.split("\n")):
        out.append(textwrap.fill(para, WIDTH, initial_indent=first if i == 0 else indent,
                                 subsequent_indent=indent) or "")
    return "\n".join(out)


def to_txt(title, meta, blocks):
    lines = [title.upper(), "=" * min(len(title), WIDTH), "", _wrap(meta), ""]
    for blk in blocks:
        kind = blk[0]
        if kind == "h2":
            lines += ["", blk[1].upper(), "-" * min(len(blk[1]), WIDTH), ""]
        elif kind == "h3":
            lines += ["", blk[1], ""]
        elif kind == "p":
            lines += [_wrap(blk[1]), ""]
        elif kind == "steps":
            for n, step in enumerate(blk[1], 1):
                lines.append(_wrap(step, indent="    ", first=f"{n:>2}. "))
            lines.append("")
        elif kind == "bullets":
            for item in blk[1]:
                lines.append(_wrap(item, indent="    ", first="  - "))
            lines.append("")
        elif kind == "box":
            _, _k, heading, body = blk
            lines.append(f"[{heading.upper()}]")
            lines.append(_wrap(body, indent="    "))
            lines.append("")
        elif kind == "table":
            _, head, rows = blk
            for row in rows:
                lines.append(_wrap(f"{row[0]}: {row[1]}", indent="    ", first="  * "))
            lines.append("")
    text = "\n".join(lines)
    while "\n\n\n\n" in text:
        text = text.replace("\n\n\n\n", "\n\n\n")
    return text.rstrip() + "\n"


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
BOX_COLOURS = {  # fill, bar
    "Key takeaways": ("#eef2ff", "#4f46e5"),
    "Good to know": ("#eff6ff", "#2563eb"),
    "Tip": ("#ecfdf5", "#059669"),
    "Watch out": ("#fffbeb", "#d97706"),
}


def _styles():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.styles import ParagraphStyle

    base = dict(fontName="Helvetica", fontSize=10.5, leading=15, textColor=colors.HexColor("#1f2937"),
                alignment=TA_LEFT)
    return {
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=22, leading=27,
                                textColor=colors.HexColor("#111827"), spaceAfter=6),
        "meta": ParagraphStyle("meta", **{**base, "textColor": colors.HexColor("#6b7280"), "spaceAfter": 14}),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=15, leading=19, spaceBefore=16,
                             spaceAfter=6, textColor=colors.HexColor("#3730a3"), keepWithNext=1),
        "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=11.5, leading=15, spaceBefore=10,
                             spaceAfter=3, textColor=colors.HexColor("#111827"), keepWithNext=1),
        "p": ParagraphStyle("p", spaceAfter=7, **base),
        "li": ParagraphStyle("li", leftIndent=18, firstLineIndent=0, spaceAfter=4, **base),
        "cell": ParagraphStyle("cell", **{**base, "fontSize": 9.5, "leading": 13}),
        "cellb": ParagraphStyle("cellb", **{**base, "fontName": "Helvetica-Bold", "fontSize": 9.5, "leading": 13}),
        "boxh": ParagraphStyle("boxh", **{**base, "fontName": "Helvetica-Bold", "spaceAfter": 3}),
        "boxp": ParagraphStyle("boxp", **{**base, "fontSize": 10, "leading": 14, "spaceAfter": 3}),
    }


def build_pdf(path, title, meta, blocks):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                    TableStyle)

    st = _styles()
    story = [Paragraph(escape(title), st["title"]), Paragraph(escape(meta), st["meta"])]
    usable = A4[0] - 40 * mm

    def para(text, style):
        return Paragraph(escape(text).replace("\n", "<br/>"), st[style])

    for blk in blocks:
        kind = blk[0]
        if kind in ("h2", "h3"):
            story.append(para(blk[1], kind))
        elif kind == "p":
            story.append(para(blk[1], "p"))
        elif kind in ("steps", "bullets"):
            for n, item in enumerate(blk[1], 1):
                mark = f"{n}." if kind == "steps" else "•"
                story.append(Paragraph(
                    f'<para leftIndent="20" firstLineIndent="-16"><b>{mark}</b>&nbsp;&nbsp;{escape(item)}</para>',
                    st["li"]))
            story.append(Spacer(1, 4))
        elif kind == "box":
            _, key, heading, body = blk
            fill, bar = BOX_COLOURS.get(key, BOX_COLOURS["Good to know"])
            inner = [para(heading, "boxh")] + [para(chunk, "boxp") for chunk in body.split("\n")]
            t = Table([[inner]], colWidths=[usable])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fill)),
                ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor(bar)),
                ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story += [Spacer(1, 4), KeepTogether(t), Spacer(1, 8)]
        elif kind == "table":
            _, head, rows = blk
            data = [[Paragraph(escape(h), st["cellb"]) for h in head]]
            data += [[Paragraph(escape(c), st["cell"]) for c in r] for r in rows]
            t = Table(data, colWidths=[usable * 0.30, usable * 0.70], repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story += [t, Spacer(1, 10)]

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8.5)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        canvas.drawString(20 * mm, 12 * mm, title)
        canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f"Page {doc.page}")
        canvas.restoreState()

    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                      topMargin=18 * mm, bottomMargin=20 * mm, title=title, author="Pipeline").build(
        story, onFirstPage=footer, onLaterPages=footer)


def text_pdf(path, title, text):
    """A monospaced PDF of a plain text file (used for LICENSE and notices)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle(title)
    left, top, bottom, lead = 18 * mm, A4[1] - 18 * mm, 18 * mm, 11.2
    y = top
    c.setFont("Courier", 9)
    for raw in text.splitlines():
        for line in (textwrap.wrap(raw, 92, replace_whitespace=False, drop_whitespace=False) or [""]):
            if y < bottom:
                c.showPage()
                c.setFont("Courier", 9)
                y = top
            c.drawString(left, y, line.replace("\t", "    "))
            y -= lead
    c.save()


# ---------------------------------------------------------------------------
# Third-party notices
# ---------------------------------------------------------------------------
SKIP = {"pip", "setuptools", "wheel", "reportlab", "pyinstaller", "pyinstaller-hooks-contrib",
        "altgraph", "pefile", "pywin32-ctypes", "packaging", "charset-normalizer", "chardet"}


def third_party_text():
    out = [
        "PIPELINE: THIRD PARTY NOTICES", "=" * 29, "",
        "Pipeline is released under the MIT license (see LICENSE.txt). The Windows app",
        "bundles the open source packages listed below. Each one stays under its own",
        "license, reproduced here as those licenses require. Versions are the ones in",
        "requirements.txt and the packages they pull in.", "",
        "SUMMARY", "-------", "",
    ]
    dists = sorted({d.metadata["Name"]: d for d in md.distributions()
                    if d.metadata["Name"] and d.metadata["Name"].lower() not in SKIP}.values(),
                   key=lambda d: d.metadata["Name"].lower())
    for d in dists:
        name, ver = d.metadata["Name"], d.version
        lic = (d.metadata.get("License-Expression") or d.metadata.get("License") or "").strip()
        lic = lic.splitlines()[0][:60] if lic else ""
        if not lic or len(lic) > 55:
            cls = [c.split("::")[-1].strip() for c in (d.metadata.get_all("Classifier") or [])
                   if c.startswith("License ::")]
            lic = ", ".join(cls) or "see license text below"
        out.append(f"  {name} {ver}: {lic}")
    out += ["", "", "LICENSE TEXTS", "-------------", ""]
    for d in dists:
        texts = []
        for f in d.files or []:
            n = f.name.lower()
            if (n.startswith(("license", "licence", "copying", "notice")) and "/test" not in str(f).lower()):
                try:
                    texts.append((str(f), f.locate().read_text(encoding="utf-8", errors="replace")))
                except OSError:
                    pass
        out += [f"== {d.metadata['Name']} {d.version} ==", ""]
        if texts:
            seen = set()
            for _name, t in texts:
                if t.strip() not in seen:
                    seen.add(t.strip())
                    out += [t.strip(), ""]
        else:
            out += ["(no separate license file ships with this package; see its project page)", ""]
    return "\n".join(out).replace("\r\n", "\n") + "\n"


# ---------------------------------------------------------------------------
def main():
    DOCS.mkdir(exist_ok=True)
    for stem, title, meta, blocks in (
        (C.GUIDE_FILE, C.GUIDE_TITLE, C.GUIDE_META, C.GUIDE),
        (C.HOWTO_FILE, C.HOWTO_TITLE, C.HOWTO_META, C.HOWTO),
    ):
        (DOCS / f"{stem}.txt").write_text(to_txt(title, meta, blocks), encoding="utf-8", newline="\r\n")
        build_pdf(DOCS / f"{stem}.pdf", title, meta, blocks)
        print("wrote", stem)
    lic = (ROOT / "LICENSE.txt").read_text(encoding="utf-8")
    text_pdf(DOCS / "LICENSE.pdf", "Pipeline LICENSE", lic)
    print("wrote LICENSE.pdf")
    if "--skip-third-party" not in sys.argv:
        text = third_party_text()
        (DOCS / "THIRD_PARTY_NOTICES.txt").write_text(text, encoding="utf-8", newline="\r\n")
        text_pdf(DOCS / "THIRD_PARTY_NOTICES.pdf", "Pipeline third party notices", text)
        print("wrote THIRD_PARTY_NOTICES")


if __name__ == "__main__":
    main()
