"""
PDF report for BL Tracker (landscape, grouped by agent/company).

Under each company its clients are listed with BL number, status, ICD/Port
and the key milestone dates (Manifest, Carry-in, Release, Gate-out).
Used by the in-app "Download/Print PDF" button and the PDF sent to Telegram.
"""
from datetime import datetime, timezone
from fpdf import FPDF

import db
from i18n import t
from util import icd_short

CAT_COLORS = {
    "completed":   ((22, 101, 52),  (220, 252, 231)),
    "in_progress": ((30, 64, 175),  (219, 234, 254)),
    "problem":     ((153, 27, 27),  (254, 226, 226)),
    "other":       ((71, 85, 105),  (241, 245, 249)),
}

# One professional layout for every PDF: key milestones + TANSAD + category.
COLS = [
    ("client", "client", 42),
    ("bl_no", "bl_no", 30),
    ("status", "status", 32),
    ("icd", "icd", 18),
    ("manifest_date", "manifest_date", 20),
    ("carry_in_date", "carry_in_date", 20),
    ("release_date", "release_date", 20),
    ("gate_out_date", "gate_out_date", 20),
    ("tansad_no", "tansad_no", 34),
    ("category", "category", 19),
]


def _s(text):
    return (str(text) if text is not None else "").encode("latin-1", "replace").decode("latin-1")


def _is_done(b):
    # Completion = Gate Out only (same rule as the app).
    return b.get("category") == "completed"


class _PDF(FPDF):
    def fit(self, text, w):
        """Truncate text to actually fit inside width w (prevents columns from
        overlapping each other)."""
        text = _s(text)
        avail = w - 2  # cell padding
        if self.get_string_width(text) <= avail:
            return text
        while text and self.get_string_width(text + ".") > avail:
            text = text[:-1]
        return text + "." if text else ""

    def footer(self):
        self.set_y(-10)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, f"D-SERVICES GROUP  -  {self.page_no()}", align="C")


SCOPE_TITLE = {
    "active": {"sw": "Zinazoendelea (hazijatoka ICD/Port)",
               "en": "Ongoing (not yet gated out)"},
    "done": {"sw": "Zimekamilika (Gate Out)", "en": "Completed (Gated out)"},
}

ROW_H = 7.2  # row height / line spacing (mm) — balanced, no overlap


def build_report_pdf(agent_filter=None, lang="sw", scope=None, allowed=None):
    records = db.list_bls(None, agent_filter)
    if allowed is not None:  # restrict to a user's permitted companies
        records = [b for b in records if (b.get("agent") or "").strip() in allowed]
    if scope == "active":
        records = [b for b in records if not _is_done(b)]
    elif scope == "done":
        records = [b for b in records if _is_done(b)]
    cols = COLS
    # counts reflect exactly what's shown (so a one-company report shows that
    # company's numbers, not the global totals)
    counts = {"total": len(records), "completed": 0, "in_progress": 0,
              "problem": 0, "other": 0}
    for b in records:
        c = b.get("category") if b.get("category") in counts else "other"
        counts[c if c in ("completed", "in_progress", "problem") else "other"] += 1
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    no_agent = t("no_agent", lang)
    by_agent = {}
    for b in records:
        key = (b.get("agent") or "").strip() or no_agent
        by_agent.setdefault(key, []).append(b)

    pdf = _PDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(11, 37, 69)
    pdf.cell(0, 9, _s(t("brand", lang)), ln=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(90, 100, 110)
    sub = now
    if scope in SCOPE_TITLE:
        sub += "   |   " + _s(SCOPE_TITLE[scope][lang if lang in ("sw", "en") else "sw"])
    if agent_filter:
        sub += "   |   " + _s(agent_filter)
    pdf.cell(0, 6, sub, ln=1)

    pdf.ln(1)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 40, 50)
    shown = sum(len(v) for v in by_agent.values())
    pdf.cell(0, 6, _s(f"{t('total', lang)}: {counts['total']}    "
                      f"{t('completed', lang)}: {counts['completed']}    "
                      f"{t('in_progress', lang)}: {counts['in_progress']}    "
                      f"{t('problem', lang)}: {counts['problem']}    "
                      f"{t('other', lang)}: {counts['other']}    "
                      f"[{shown}]"), ln=1)
    pdf.ln(1)

    def header_row():
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(90, 100, 110)
        pdf.set_fill_color(248, 250, 252)
        for key, lbl, w in cols:
            pdf.cell(w, ROW_H, pdf.fit(t(lbl, lang), w), border="B", fill=True)
        pdf.ln(ROW_H)

    for agent in sorted(by_agent, key=lambda k: (k == no_agent, k.lower())):
        items = sorted(by_agent[agent], key=lambda b: b["category"])
        pdf.ln(1.5)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(11, 37, 69)
        pdf.set_fill_color(235, 240, 245)
        pdf.cell(0, 8, "  " + pdf.fit(f"{agent}  ({len(items)})", 150), fill=True, ln=1)
        header_row()
        for b in items:
            cat = b["category"] if b["category"] in CAT_COLORS else "other"
            text_rgb, bg_rgb = CAT_COLORS[cat]
            for key, lbl, w in cols:
                if key == "category":
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.set_text_color(*text_rgb)
                    pdf.set_fill_color(*bg_rgb)
                    pdf.cell(w, ROW_H, pdf.fit(t(cat, lang), w), border="B", fill=True)
                else:
                    pdf.set_font("Helvetica", "", 8)
                    pdf.set_text_color(30, 40, 50)
                    val = b.get(key) or ("-" if key in ("client", "bl_no") else "")
                    if key == "icd":
                        val = icd_short(val)
                    pdf.cell(w, ROW_H, pdf.fit(val, w), border="B")
            pdf.ln(ROW_H)

    return bytes(pdf.output())
