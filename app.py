"""
BL Tracker - Awamu ya 1.5
Web app (bilingual SW/EN) ya kuongeza/kuhariri/kufuta rekodi za BL,
kutuma muhtasari wa kina kwa Telegram, ku-import Excel/CSV, na
kuambatanisha PDF/picha ya BL. Data huhifadhiwa kwenye database ya kudumu
(Neon Postgres) kupitia DATABASE_URL.
"""
import os
import io
import csv
import html
from datetime import datetime, timezone, date, timedelta
from functools import wraps

import requests
from flask import (
    Flask, request, redirect, url_for, render_template, make_response, flash,
    send_file, Response, session,
)

import db
from carriers import detect_shipping_line

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024  # 15 MB upload cap
app.permanent_session_lifetime = timedelta(days=14)

# ----- Config -----
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
NOTIFY_TOKEN = os.environ.get("NOTIFY_TOKEN", "")
NOTIFY_LANG = os.environ.get("NOTIFY_LANG", "sw")
RUN_SCHEDULER = os.environ.get("RUN_SCHEDULER", "0") == "1"
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")       # set this to enable login
OVERSTAY_DAYS = int(os.environ.get("OVERSTAY_DAYS", "21") or "21")

ALLOWED_DOC_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}

from i18n import t  # noqa: E402

db.init_db()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if APP_PASSWORD and not session.get("auth"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


def _days_since(s):
    try:
        d = datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
        return (date.today() - d).days
    except Exception:
        return None


def current_lang():
    lang = request.args.get("lang") or request.cookies.get("lang") or "sw"
    return "en" if lang == "en" else "sw"


@app.context_processor
def inject_helpers():
    lang = current_lang()
    return {
        "lang": lang,
        "t": lambda key: t(key, lang),
        "cat_label": lambda c: t(c if c in db.CATEGORIES else "other", lang),
        "days_since": _days_since,
        "overstay_days": OVERSTAY_DAYS,
        "auth_on": bool(APP_PASSWORD),
        "logged_in": (not APP_PASSWORD) or bool(session.get("auth")),
    }


# ----- Auth -----
@app.route("/login", methods=["GET", "POST"])
def login():
    lang = current_lang()
    if not APP_PASSWORD:
        return redirect(url_for("bl"))
    if request.method == "POST":
        if request.form.get("password") == APP_PASSWORD:
            session["auth"] = True
            session.permanent = True
            return redirect(request.args.get("next") or url_for("bl"))
        flash(t("login_wrong", lang), "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("auth", None)
    return redirect(url_for("welcome"))


# ----- Telegram -----
def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False, "missing_config"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=20,
        )
        if resp.status_code == 200 and resp.json().get("ok"):
            return True, "ok"
        return False, f"{resp.status_code}: {resp.text[:200]}"
    except requests.RequestException as e:
        return False, str(e)


def send_telegram_document(data_bytes, filename, caption=""):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False, "missing_config"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        resp = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1000], "parse_mode": "HTML"},
            files={"document": (filename, data_bytes, "application/pdf")},
            timeout=40,
        )
        if resp.status_code == 200 and resp.json().get("ok"):
            return True, "ok"
        return False, f"{resp.status_code}: {resp.text[:200]}"
    except requests.RequestException as e:
        return False, str(e)


def notify_telegram():
    """Send the grouped text summary, then attach the PDF report."""
    from report import build_report_pdf
    ok, detail = send_telegram(build_summary_text())
    try:
        pdf = build_report_pdf(lang=NOTIFY_LANG)
        fname = "BL_Report_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M") + ".pdf"
        ok2, detail2 = send_telegram_document(pdf, fname, caption=_pdf_caption())
    except Exception as e:  # PDF failure must not block the text summary
        ok2, detail2 = False, f"pdf_error: {e}"
    return (ok or ok2), f"text={detail}; pdf={detail2}"


def _pdf_caption():
    c = db.summary_counts()
    lang = NOTIFY_LANG
    return (f"\U0001F4C4 {t('tg_header', lang)} — {t('total', lang)}: {c['total']} | "
            f"✅ {c['completed']} | \U0001F6A2 {c['in_progress']} | "
            f"⚠️ {c['problem']} | ℹ️ {c['other']}")


CAT_EMOJI = {"completed": "✅", "in_progress": "\U0001F6A2",
             "problem": "⚠️", "other": "ℹ️"}
CAT_SORT = {"problem": 0, "in_progress": 1, "completed": 2, "other": 3}


def build_summary_text(lang=None):
    """Summary grouped by agent (clearing company); under each company,
    every BL is listed as: <status emoji> client - number (status).
    HTML-escaped and capped for Telegram's 4096 limit."""
    lang = lang or NOTIFY_LANG
    records = db.list_bls()
    counts = db.summary_counts()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    no_agent = t("no_agent", lang)
    by_agent = {}
    for b in records:
        key = (b.get("agent") or "").strip() or no_agent
        by_agent.setdefault(key, []).append(b)

    def agent_sort(k):
        return (k == no_agent, k.lower())

    lines = [f"<b>{t('tg_header', lang)}</b>", "",
             f"{t('total', lang)}: <b>{counts['total']}</b>", ""]

    for agent in sorted(by_agent, key=agent_sort):
        items = sorted(by_agent[agent],
                       key=lambda b: CAT_SORT.get(b["category"], 3))
        lines.append(f"\U0001F3E2 <b>{html.escape(agent)} ({len(items)})</b>")
        for b in items:
            emoji = CAT_EMOJI.get(b["category"], "ℹ️")
            client = html.escape(b["client"] or "-")
            bl_no = html.escape(b["bl_no"] or "")
            st = f" ({html.escape(b['status'])})" if b["status"] else ""
            lines.append(f"  {emoji} {client} — {bl_no}{st}")
        lines.append("")

    lines.append(f"{t('tg_time', lang)}: {now}")
    text = "\n".join(lines)
    if len(text) > 3800:
        text = text[:3800].rsplit("\n", 1)[0] + "\n…"
    return text


# ----- Welcome / landing -----
@app.route("/")
def welcome():
    return render_template("welcome.html")


# ----- Dashboard -----
@app.route("/dashboard")
@login_required
def dashboard():
    counts = db.summary_counts()
    by_agent = db.counts_by_agent()
    by_icd = db.counts_by_icd(limit=10)
    cat_counts = [(c, counts[c]) for c in db.CATEGORIES]
    return render_template("dashboard.html", counts=counts,
                           by_agent=by_agent, by_icd=by_icd, cat_counts=cat_counts)


# ----- BL tracker list / summary -----
@app.route("/bl")
@login_required
def bl():
    lang = current_lang()
    search = request.args.get("q", "").strip()
    agent = request.args.get("agent", "").strip()
    records = db.list_bls(search or None, agent or None)
    counts = db.summary_counts()
    doc_ids = db.bls_with_documents()
    agents = db.agents_list()

    # Group by company (agent) for the collapsible accordion.
    no_agent = t("no_agent", lang)
    groups = []
    for r in records:
        key = (r.get("agent") or "").strip() or no_agent
        if not groups or groups[-1]["agent"] != key:
            groups.append({"agent": key, "items": []})
        groups[-1]["items"].append(r)

    return render_template("index.html", groups=groups, counts=counts,
                           search=search, doc_ids=doc_ids,
                           agents=agents, agent=agent)


@app.route("/set-lang/<lang>")
def set_lang(lang):
    resp = make_response(redirect(request.referrer or url_for("welcome")))
    resp.set_cookie("lang", "en" if lang == "en" else "sw", max_age=60 * 60 * 24 * 365)
    return resp


# ----- Document helpers -----
def _save_uploaded_doc(bl_id):
    f = request.files.get("document")
    if not f or not f.filename:
        return
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED_DOC_EXT:
        return
    data = f.read()
    if not data:
        return
    db.save_document(bl_id, f.filename, f.mimetype or "application/octet-stream", data)


# ----- Add / edit / delete -----
def _form_with_carrier():
    """Form data as a dict; if Shipping Line is blank, auto-detect it from the
    Vessel name / BL number so the user doesn't have to type it."""
    data = request.form.to_dict()
    if not (data.get("shipping_line") or "").strip():
        guess = detect_shipping_line(data.get("vessel", ""), data.get("bl_no", ""))
        if guess:
            data["shipping_line"] = guess
    return data


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    lang = current_lang()
    if request.method == "POST":
        if not request.form.get("bl_no", "").strip():
            flash(t("required", lang), "error")
            return render_template("form.html", bl=request.form, mode="add", agents=db.agents_list())
        bl_id = db.create_bl(_form_with_carrier())
        _save_uploaded_doc(bl_id)
        flash(t("created_ok", lang), "ok")
        return redirect(url_for("bl"))
    return render_template("form.html", bl={}, mode="add", agents=db.agents_list())


@app.route("/edit/<int:bl_id>", methods=["GET", "POST"])
@login_required
def edit(bl_id):
    lang = current_lang()
    bl = db.get_bl(bl_id)
    if not bl:
        return redirect(url_for("bl"))
    if request.method == "POST":
        if not request.form.get("bl_no", "").strip():
            flash(t("required", lang), "error")
            return render_template("form.html", bl=request.form, mode="edit", bl_id=bl_id, agents=db.agents_list())
        db.update_bl(bl_id, _form_with_carrier())
        _save_uploaded_doc(bl_id)
        flash(t("updated_ok", lang), "ok")
        return redirect(url_for("bl"))
    has_doc = db.get_document(bl_id) is not None
    return render_template("form.html", bl=bl, mode="edit", bl_id=bl_id, has_doc=has_doc, agents=db.agents_list())


@app.route("/delete/<int:bl_id>", methods=["POST"])
@login_required
def delete(bl_id):
    lang = current_lang()
    db.delete_bl(bl_id)
    flash(t("deleted_ok", lang), "ok")
    return redirect(url_for("bl"))


# ----- View / download a BL document -----
@app.route("/document/<int:bl_id>")
@login_required
def document(bl_id):
    doc = db.get_document(bl_id)
    if not doc:
        return redirect(url_for("bl"))
    return send_file(
        io.BytesIO(doc["data"]),
        mimetype=doc["content_type"] or "application/octet-stream",
        download_name=doc["filename"] or f"bl-{bl_id}",
        as_attachment=False,
    )


# ----- Import Excel / CSV -----
IMPORT_FIELDS = ["bl_no", "client", "agent", "vessel", "shipping_line", "status", "category", "bl_date", "notes"]
HEADER_ALIASES = {
    "bl": "bl_no", "bl no": "bl_no", "bl_no": "bl_no", "bl number": "bl_no", "namba ya bl": "bl_no",
    "client": "client", "mteja": "client", "customer": "client",
    "agent": "agent", "kampuni": "agent", "company": "agent", "clearing agent": "agent", "clearing company": "agent",
    "vessel": "vessel", "vessel name": "vessel", "meli": "vessel", "ship": "vessel",
    "shipping_line": "shipping_line", "shipping line": "shipping_line", "s/line": "shipping_line", "carrier": "shipping_line", "line": "shipping_line",
    "status": "status", "hali": "status",
    "category": "category", "kundi": "category",
    "bl_date": "bl_date", "date": "bl_date", "tarehe": "bl_date",
    "notes": "notes", "maelezo": "notes",
}
CATEGORY_ALIASES = {
    "completed": "completed", "imekamilika": "completed", "zimekamilika": "completed", "done": "completed",
    "in_progress": "in_progress", "in progress": "in_progress", "inaendelea": "in_progress", "zinaendelea": "in_progress",
    "problem": "problem", "tatizo": "problem", "ina tatizo": "problem", "zina tatizo": "problem",
    "other": "other", "nyingine": "other",
}


def _norm_header(h):
    return HEADER_ALIASES.get((h or "").strip().lower(), (h or "").strip().lower())


def _norm_cat(v):
    return CATEGORY_ALIASES.get((v or "").strip().lower(), "in_progress")


def _parse_rows(headers, data_rows):
    idx = {}
    for i, h in enumerate(headers):
        key = _norm_header(h)
        if key in IMPORT_FIELDS and key not in idx:
            idx[key] = i
    rows = []
    for raw in data_rows:
        if not any((str(c).strip() if c is not None else "") for c in raw):
            continue
        rec = {}
        for field, i in idx.items():
            val = raw[i] if i < len(raw) else ""
            rec[field] = "" if val is None else str(val).strip()
        if rec.get("category"):
            rec["category"] = _norm_cat(rec["category"])
        rows.append(rec)
    return rows


@app.route("/import", methods=["GET", "POST"])
@login_required
def import_bls():
    lang = current_lang()
    if request.method == "POST":
        f = request.files.get("file")
        if not f or not f.filename:
            flash(t("import_nofile", lang), "error")
            return render_template("import.html")
        name = f.filename.lower()
        data = f.read()
        dservices = False
        try:
            if name.endswith(".csv"):
                text_content = data.decode("utf-8-sig", errors="replace")
                reader = list(csv.reader(io.StringIO(text_content)))
                if not reader:
                    raise ValueError("empty")
                rows = _parse_rows(reader[0], reader[1:])
            elif name.endswith(".xlsx"):
                from openpyxl import load_workbook
                import dservices_import
                wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
                if dservices_import.is_dservices_workbook(wb.sheetnames):
                    dservices = True
                    rows = dservices_import.parse(data)
                else:
                    ws = wb.active
                    all_rows = [[c for c in r] for r in ws.iter_rows(values_only=True)]
                    if not all_rows:
                        raise ValueError("empty")
                    rows = _parse_rows(all_rows[0], all_rows[1:])
            else:
                flash(t("import_badtype", lang), "error")
                return render_template("import.html")
        except Exception:
            flash(t("import_error", lang), "error")
            return render_template("import.html")

        if request.form.get("replace"):
            db.clear_all_bls()
        n = db.bulk_create(rows)
        flash(t("import_ds_ok" if dservices else "import_ok", lang).format(n=n), "ok")
        return redirect(url_for("bl"))
    return render_template("import.html")


@app.route("/template.csv")
@login_required
def template_csv():
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(IMPORT_FIELDS)
    w.writerow(["YSPQINMTW201", "ABC Traders Ltd", "Clearing Co A", "MAERSK NADI", "Maersk",
                "Cargo at port", "in_progress", "2026-10-10", "Inasubiri assessment"])
    w.writerow(["GOSUNGB20807248", "Juma Imports", "Clearing Co B", "CALANDRA", "MSC",
                "Released", "completed", "2026-10-05", ""])
    resp = Response(out.getvalue(), mimetype="text/csv")
    resp.headers["Content-Disposition"] = "attachment; filename=bl_template.csv"
    return resp


# ----- Send summary now (UI button) -----
@app.route("/send-summary", methods=["POST"])
@login_required
def send_summary():
    lang = current_lang()
    ok, _ = notify_telegram()
    flash(t("summary_sent" if ok else "summary_fail", lang), "ok" if ok else "error")
    return redirect(url_for("bl"))


# ----- PDF report (download / print) -----
@app.route("/report.pdf")
@login_required
def report_pdf():
    from report import build_report_pdf
    agent = request.args.get("agent", "").strip() or None
    lang = current_lang()
    pdf = build_report_pdf(agent_filter=agent, lang=lang)
    resp = make_response(pdf)
    resp.headers["Content-Type"] = "application/pdf"
    fname = "BL_Report_" + datetime.now(timezone.utc).strftime("%Y%m%d") + ".pdf"
    resp.headers["Content-Disposition"] = f'inline; filename="{fname}"'
    return resp


# ----- Notify endpoint for external cron (every 3 hours) -----
@app.route("/tasks/notify")
def tasks_notify():
    if NOTIFY_TOKEN and request.args.get("token") != NOTIFY_TOKEN:
        return {"ok": False, "error": "unauthorized"}, 401
    ok, detail = notify_telegram()
    return {"ok": ok, "detail": detail}


@app.route("/summary.json")
def summary_json():
    if NOTIFY_TOKEN and request.args.get("token") != NOTIFY_TOKEN:
        return {"ok": False, "error": "unauthorized"}, 401
    return {"ok": True, "counts": db.summary_counts()}


@app.route("/health")
def health():
    return {"ok": True}


def _start_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler(daemon=True, timezone="UTC")
    scheduler.add_job(notify_telegram, "interval", hours=3)
    scheduler.start()


if RUN_SCHEDULER:
    _start_scheduler()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
