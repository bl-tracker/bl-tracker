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

CAT_COLORS = {
    "completed":   ((22, 101, 52),  (220, 252, 231)),
    "in_progress": ((30, 64, 175),  (219, 234, 254)),
    "problem":     ((153, 27, 27),  (254, 226, 226)),
    "other":       ((71, 85, 105),  (241, 245, 249)),
}

# column key -> (label i18n key, width mm)
COLS = [
    ("client", "client", 50),
    ("bl_no", "bl_no", 34),
    ("status", "status", 40),
    ("icd", "icd", 26),
    ("manifest_date", "manifest_date", 24),
    ("carry_in_date", "carry_in_date", 24),
    ("release_date", "release_date", 24),
    ("gate_out_date", "gate_out_date", 24),
    ("category", "category", 22),
]


def _s(text):
    return (str(text) if text is not None else "").encode("latin-1", "replace").decode("latin-1")


def _fit(text, w, size=8):
    text = _s(text)
    maxlen = int(w / (size * 0.17))  # rough chars that fit
    return text if len(text) <= maxlen else text[: max(1, maxlen - 1)] + "."


class _PDF(FPDF):
    def footer(self):
        self.set_y(-10)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, f"D-SERVICES OPERATION  -  {self.page_no()}", align="C")


def build_report_pdf(agent_filter=None, lang="sw"):
    records = db.list_bls(None, agent_filter)
    counts = db.summary_counts()
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
    sub = now if not agent_filter else f"{now}   |   {_s(agent_filter)}"
    pdf.cell(0, 6, sub, ln=1)

    pdf.ln(1)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 40, 50)
    pdf.cell(0, 6, _s(f"{t('total', lang)}: {counts['total']}    "
                      f"{t('completed', lang)}: {counts['completed']}    "
                      f"{t('in_progress', lang)}: {counts['in_progress']}    "
                      f"{t('problem', lang)}: {counts['problem']}    "
                      f"{t('other', lang)}: {counts['other']}"), ln=1)
    pdf.ln(1)

    def header_row():
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(90, 100, 110)
        pdf.set_fill_color(248, 250, 252)
        for key, lbl, w in COLS:
            pdf.cell(w, 7, _s(t(lbl, lang)), border="B", fill=True)
        pdf.ln(7)

    for agent in sorted(by_agent, key=lambda k: (k == no_agent, k.lower())):
        items = sorted(by_agent[agent], key=lambda b: b["category"])
        pdf.ln(1.5)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(11, 37, 69)
        pdf.set_fill_color(235, 240, 245)
        pdf.cell(0, 8, f"  {_fit(agent, 120, 11)}  ({len(items)})", fill=True, ln=1)
        header_row()
        for b in items:
            cat = b["category"] if b["category"] in CAT_COLORS else "other"
            text_rgb, bg_rgb = CAT_COLORS[cat]
            for key, lbl, w in COLS:
                if key == "category":
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.set_text_color(*text_rgb)
                    pdf.set_fill_color(*bg_rgb)
                    pdf.cell(w, 6.5, _fit(t(cat, lang), w), border="B", fill=True)
                else:
                    pdf.set_font("Helvetica", "", 8)
                    pdf.set_text_color(30, 40, 50)
                    val = b.get(key) or ("-" if key in ("client", "bl_no") else "")
                    pdf.cell(w, 6.5, _fit(val, w), border="B")
            pdf.ln(6.5)

    return bytes(pdf.output())
