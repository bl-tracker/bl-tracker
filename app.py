"""
BL Tracker - Awamu ya 1
Web app (bilingual SW/EN) ya kuongeza/kuhariri/kufuta rekodi za BL,
pamoja na kutuma muhtasari (summary) kwa Telegram.

Awamu ya 2 (baadaye): kufuatilia status kiotomatiki kutoka TeSWS.
Tazama teSWS.py kwa kiunzi (stub) kilichoandaliwa tayari.
"""
import os
from datetime import datetime, timezone

import requests
from flask import (
    Flask, request, redirect, url_for, render_template, make_response, flash
)

import db
from i18n import t, STRINGS

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

# ----- Config (via environment variables) -----
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
NOTIFY_TOKEN = os.environ.get("NOTIFY_TOKEN", "")          # secret for the cron endpoint
NOTIFY_LANG = os.environ.get("NOTIFY_LANG", "sw")          # language of the Telegram summary
RUN_SCHEDULER = os.environ.get("RUN_SCHEDULER", "0") == "1"  # in-process 3-hourly job

db.init_db()


# ----- Language helper -----
def current_lang():
    lang = request.args.get("lang") or request.cookies.get("lang") or "sw"
    return "en" if lang == "en" else "sw"


@app.context_processor
def inject_helpers():
    lang = current_lang()
    return {
        "lang": lang,
        "t": lambda key: t(key, lang),
        "cat_label": lambda c: t(c if c in ("completed", "in_progress", "problem", "other") else "other", lang),
    }


# ----- Telegram -----
def send_telegram(text):
    """Send a message to the configured Telegram chat. Returns (ok, detail)."""
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


def build_summary_text(lang=None):
    """Build the bilingual-aware summary message for Telegram."""
    lang = lang or NOTIFY_LANG
    c = db.summary_counts()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"<b>{t('tg_header', lang)}</b>",
        "",
        f"{t('total', lang)}: <b>{c['total']}</b>",
        f"✅ {t('completed', lang)}: {c['completed']}",
        f"\U0001F6A2 {t('in_progress', lang)}: {c['in_progress']}",
        f"⚠️ {t('problem', lang)}: {c['problem']}",
        f"ℹ️ {t('other', lang)}: {c['other']}",
        "",
        f"{t('tg_time', lang)}: {now}",
    ]
    return "\n".join(lines)


# ----- Routes: list / summary -----
@app.route("/")
def index():
    lang = current_lang()
    search = request.args.get("q", "").strip()
    bls = db.list_bls(search or None)
    counts = db.summary_counts()
    return render_template("index.html", bls=bls, counts=counts, search=search)


@app.route("/set-lang/<lang>")
def set_lang(lang):
    resp = make_response(redirect(request.referrer or url_for("index")))
    resp.set_cookie("lang", "en" if lang == "en" else "sw", max_age=60 * 60 * 24 * 365)
    return resp


# ----- Routes: add / edit / delete -----
@app.route("/add", methods=["GET", "POST"])
def add():
    lang = current_lang()
    if request.method == "POST":
        if not request.form.get("bl_no", "").strip():
            flash(t("required", lang), "error")
            return render_template("form.html", bl=request.form, mode="add")
        db.create_bl(request.form)
        flash(t("created_ok", lang), "ok")
        return redirect(url_for("index"))
    return render_template("form.html", bl={}, mode="add")


@app.route("/edit/<int:bl_id>", methods=["GET", "POST"])
def edit(bl_id):
    lang = current_lang()
    bl = db.get_bl(bl_id)
    if not bl:
        return redirect(url_for("index"))
    if request.method == "POST":
        if not request.form.get("bl_no", "").strip():
            flash(t("required", lang), "error")
            return render_template("form.html", bl=request.form, mode="edit", bl_id=bl_id)
        db.update_bl(bl_id, request.form)
        flash(t("updated_ok", lang), "ok")
        return redirect(url_for("index"))
    return render_template("form.html", bl=bl, mode="edit", bl_id=bl_id)


@app.route("/delete/<int:bl_id>", methods=["POST"])
def delete(bl_id):
    lang = current_lang()
    db.delete_bl(bl_id)
    flash(t("deleted_ok", lang), "ok")
    return redirect(url_for("index"))


# ----- Route: send summary now (button in the UI) -----
@app.route("/send-summary", methods=["POST"])
def send_summary():
    lang = current_lang()
    ok, _ = send_telegram(build_summary_text())
    flash(t("summary_sent" if ok else "summary_fail", lang), "ok" if ok else "error")
    return redirect(url_for("index"))


# ----- Route: notify endpoint for external cron (every 3 hours) -----
@app.route("/tasks/notify")
def tasks_notify():
    # Protect with a secret token so only your scheduler can trigger it.
    if NOTIFY_TOKEN and request.args.get("token") != NOTIFY_TOKEN:
        return {"ok": False, "error": "unauthorized"}, 401
    ok, detail = send_telegram(build_summary_text())
    return {"ok": ok, "detail": detail}


@app.route("/health")
def health():
    return {"ok": True}


# ----- Optional in-process scheduler (for always-on hosts) -----
def _start_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler(daemon=True, timezone="UTC")
    # Every 3 hours
    scheduler.add_job(lambda: send_telegram(build_summary_text()), "interval", hours=3)
    scheduler.start()
    app.logger.info("In-process scheduler started (every 3 hours).")


if RUN_SCHEDULER:
    _start_scheduler()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
