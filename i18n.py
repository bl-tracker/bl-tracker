"""Bilingual strings (Kiswahili + English). Default language: Kiswahili."""

STRINGS = {
    "app_title": {"sw": "Mfumo wa Kufuatilia BL", "en": "BL Tracker"},
    "tagline": {"sw": "Fuatilia taarifa za Bill of Lading", "en": "Track your Bill of Lading records"},
    "nav_list": {"sw": "Orodha ya BL", "en": "BL List"},
    "nav_add": {"sw": "Ongeza BL", "en": "Add BL"},
    "lang_switch": {"sw": "English", "en": "Kiswahili"},

    # Summary
    "summary_title": {"sw": "Muhtasari", "en": "Summary"},
    "total": {"sw": "Jumla", "en": "Total"},
    "completed": {"sw": "Zimekamilika", "en": "Completed"},
    "in_progress": {"sw": "Zinaendelea", "en": "In progress"},
    "problem": {"sw": "Zina tatizo", "en": "With problem"},
    "other": {"sw": "Nyingine", "en": "Other"},
    "send_summary_now": {"sw": "Tuma summary sasa (Telegram)", "en": "Send summary now (Telegram)"},

    # Table headers
    "bl_no": {"sw": "Namba ya BL", "en": "BL Number"},
    "client": {"sw": "Mteja", "en": "Client"},
    "shipping_line": {"sw": "Shipping Line", "en": "Shipping Line"},
    "status": {"sw": "Hali (Status)", "en": "Status"},
    "category": {"sw": "Kundi", "en": "Category"},
    "bl_date": {"sw": "Tarehe", "en": "Date"},
    "notes": {"sw": "Maelezo", "en": "Notes"},
    "actions": {"sw": "Vitendo", "en": "Actions"},
    "edit": {"sw": "Hariri", "en": "Edit"},
    "delete": {"sw": "Futa", "en": "Delete"},
    "confirm_delete": {"sw": "Una uhakika unataka kufuta BL hii?", "en": "Are you sure you want to delete this BL?"},
    "no_records": {"sw": "Hakuna BL bado. Bonyeza “Ongeza BL” kuanza.", "en": "No BL records yet. Click “Add BL” to start."},
    "search_placeholder": {"sw": "Tafuta kwa namba, mteja au shipping line…", "en": "Search by number, client or shipping line…"},
    "search": {"sw": "Tafuta", "en": "Search"},

    # Form
    "add_title": {"sw": "Ongeza BL mpya", "en": "Add new BL"},
    "edit_title": {"sw": "Hariri BL", "en": "Edit BL"},
    "save": {"sw": "Hifadhi", "en": "Save"},
    "cancel": {"sw": "Ghairi", "en": "Cancel"},
    "required": {"sw": "Namba ya BL inahitajika", "en": "BL number is required"},

    # Flash messages
    "created_ok": {"sw": "BL imeongezwa.", "en": "BL added."},
    "updated_ok": {"sw": "BL imehaririwa.", "en": "BL updated."},
    "deleted_ok": {"sw": "BL imefutwa.", "en": "BL deleted."},
    "summary_sent": {"sw": "Summary imetumwa kwa Telegram.", "en": "Summary sent to Telegram."},
    "summary_fail": {"sw": "Imeshindwa kutuma. Hakikisha TELEGRAM_BOT_TOKEN na TELEGRAM_CHAT_ID zimewekwa.",
                      "en": "Send failed. Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."},

    # Telegram message
    "tg_header": {"sw": "\U0001F4E6 Muhtasari wa BL", "en": "\U0001F4E6 BL Summary"},
    "tg_time": {"sw": "Muda", "en": "Time"},
}

CATEGORY_KEYS = {
    "completed": "completed",
    "in_progress": "in_progress",
    "problem": "problem",
    "other": "other",
}


def t(key, lang="sw"):
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(lang, entry.get("sw", key))
