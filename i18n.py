"""Bilingual strings (Kiswahili + English). Default language: Kiswahili."""

STRINGS = {
    "app_title": {"sw": "Mfumo wa Kufuatilia BL", "en": "BL Tracker"},
    "brand": {"sw": "D-SERVICES OPERATION", "en": "D-SERVICES OPERATION"},
    "slogan": {"sw": "Fast. Accurate. Trusted.", "en": "Fast. Accurate. Trusted."},
    "tagline": {"sw": "Clearing & Forwarding, Dar es Salaam", "en": "Clearing & Forwarding, Dar es Salaam"},
    "nav_home": {"sw": "Mwanzo", "en": "Home"},
    "nav_tracker": {"sw": "BL Tracker", "en": "BL Tracker"},
    "nav_dashboard": {"sw": "Dashboard", "en": "Dashboard"},
    "nav_login": {"sw": "Ingia", "en": "Login"},
    "nav_logout": {"sw": "Toka", "en": "Logout"},

    # Login
    "login_title": {"sw": "Ingia kwenye mfumo", "en": "Sign in"},
    "password": {"sw": "Nenosiri", "en": "Password"},
    "login_btn": {"sw": "Ingia", "en": "Sign in"},
    "login_wrong": {"sw": "Nenosiri si sahihi.", "en": "Wrong password."},
    "login_note": {"sw": "Ukurasa huu ni wa wafanyakazi wa D-SERVICES pekee.", "en": "This area is for D-SERVICES staff only."},

    # Overstay / days / stages
    "days": {"sw": "siku", "en": "days"},
    "at_port": {"sw": "bandarini", "en": "at port"},
    "overstay": {"sw": "OVERSTAY", "en": "OVERSTAY"},
    "progress": {"sw": "Hatua", "en": "Progress"},

    # Dashboard
    "dash_title": {"sw": "Dashboard ya Takwimu", "en": "Statistics Dashboard"},
    "dash_by_company": {"sw": "BL kwa Kampuni", "en": "BL by Company"},
    "dash_by_status": {"sw": "BL kwa Hali (Kundi)", "en": "BL by Status"},
    "dash_by_icd": {"sw": "BL kwa ICD/Port (10 za juu)", "en": "BL by ICD/Port (top 10)"},
    "nav_list": {"sw": "Orodha ya BL", "en": "BL List"},
    "nav_add": {"sw": "Ongeza BL", "en": "Add BL"},
    "lang_switch": {"sw": "English", "en": "Kiswahili"},

    # Welcome / landing page
    "w_welcome": {"sw": "Karibu", "en": "Welcome to"},
    "w_intro": {
        "sw": "Wataalam wa clearing & forwarding Dar es Salaam. Tunakuondoshea mizigo yako bandarini na uwanja wa ndege kwa haraka, usahihi na uaminifu — magari, makontena na mizigo ya aina zote.",
        "en": "Clearing & forwarding experts in Dar es Salaam. We clear your cargo at the port and airport with speed, accuracy and trust — vehicles, containers and all cargo types.",
    },
    "w_track_btn": {"sw": "Fuatilia BL", "en": "Track your BL"},
    "w_contact_btn": {"sw": "Wasiliana nasi", "en": "Contact us"},
    "w_video": {"sw": "Tazama kazi zetu", "en": "See our work"},
    "w_services": {"sw": "Huduma Zetu", "en": "Our Services"},
    "svc_import": {"sw": "Import", "en": "Import"},
    "svc_import_d": {"sw": "Uondoshaji wa mizigo inayoingia nchini.", "en": "Clearing cargo coming into the country."},
    "svc_export": {"sw": "Export", "en": "Export"},
    "svc_export_d": {"sw": "Usafirishaji wa mizigo kwenda nje ya nchi.", "en": "Handling cargo going out of the country."},
    "svc_transit": {"sw": "Transit", "en": "Transit"},
    "svc_transit_d": {"sw": "Mizigo inayopita kwenda nchi jirani.", "en": "Cargo in transit to neighbouring countries."},
    "svc_bond": {"sw": "Bond", "en": "Bond"},
    "svc_bond_d": {"sw": "Uhifadhi wa mizigo kwenye ghala la forodha (bonded).", "en": "Storage of goods in a customs bonded warehouse."},
    "svc_exbond": {"sw": "EX-Bond", "en": "EX-Bond"},
    "svc_exbond_d": {"sw": "Uondoshaji wa mizigo kutoka ghala la bond.", "en": "Clearing goods out of the bonded warehouse."},
    "svc_vehicles": {"sw": "Magari & Makontena", "en": "Vehicles & Containers"},
    "svc_vehicles_d": {"sw": "Clearing ya magari na makontena ya aina zote.", "en": "Clearing of vehicles and all container types."},

    # Contact
    "w_contact": {"sw": "Wasiliana Nasi", "en": "Contact Us"},
    "c_address": {"sw": "Anuani", "en": "Address"},
    "c_phone": {"sw": "Simu / WhatsApp", "en": "Phone / WhatsApp"},
    "c_email": {"sw": "Barua pepe", "en": "Email"},
    "c_hours": {"sw": "Saa za Kazi", "en": "Working Hours"},
    "c_hours_val": {"sw": "Jumatatu – Jumapili: 08:30 – 18:00", "en": "Monday – Sunday: 08:30 – 18:00"},
    "c_whatsapp_btn": {"sw": "Tuandikie WhatsApp", "en": "Message us on WhatsApp"},

    # Summary
    "summary_title": {"sw": "Muhtasari", "en": "Summary"},
    "total": {"sw": "Jumla", "en": "Total"},
    "completed": {"sw": "Zimekamilika", "en": "Completed"},
    "in_progress": {"sw": "Zinaendelea", "en": "In progress"},
    "problem": {"sw": "Zina tatizo", "en": "With problem"},
    "other": {"sw": "Nyingine", "en": "Other"},
    "send_summary_now": {"sw": "Tuma summary sasa (Telegram)", "en": "Send summary now (Telegram)"},
    "print_pdf": {"sw": "Chapisha / Pakua PDF", "en": "Print / Download PDF"},

    # Table headers
    "bl_no": {"sw": "Namba ya BL", "en": "BL Number"},
    "client": {"sw": "Mteja", "en": "Client"},
    "agent": {"sw": "Agent / Kampuni", "en": "Agent / Company"},
    "vessel": {"sw": "Vessel (Meli)", "en": "Vessel"},
    "all_agents": {"sw": "Kampuni zote", "en": "All companies"},
    "no_agent": {"sw": "(Bila kampuni)", "en": "(No company)"},
    "shipping_line": {"sw": "Shipping Line", "en": "Shipping Line"},
    "sl_auto_hint": {"sw": "Acha wazi — itajazwa yenyewe kutoka BL/Vessel ikiwezekana.",
                     "en": "Leave blank — auto-filled from the BL number / vessel when possible."},
    "status": {"sw": "Hali (Status)", "en": "Status"},
    "category": {"sw": "Kundi", "en": "Category"},
    "bl_date": {"sw": "Tarehe", "en": "Date"},
    "icd": {"sw": "ICD/Port", "en": "ICD/Port"},
    "manifest_date": {"sw": "Manifest", "en": "Manifest"},
    "carry_in_date": {"sw": "Carry-in", "en": "Carry-in"},
    "release_date": {"sw": "Release", "en": "Release"},
    "gate_out_date": {"sw": "Gate-out", "en": "Gate-out"},
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
    "tg_active": {"sw": "Zinazoendelea", "en": "Ongoing"},
    "tg_all_done": {"sw": "Hakuna BL inayoendelea — zote zimetoka gate out. ✅",
                    "en": "No active BLs — all have gated out. ✅"},
    "section_active": {"sw": "Zinazoendelea (hazijatoka ICD/Port)",
                       "en": "Ongoing (not yet gated out)"},
    "section_done": {"sw": "Zimekamilika (Gate Out)", "en": "Completed (Gated out)"},
    "tg_sync_header": {"sw": "\U0001F504 Mabadiliko mapya kutoka TANeSW",
                       "en": "\U0001F504 New updates from TANeSW"},
    "tg_sync_none": {"sw": "Hakuna mabadiliko mapya kwa sasa.",
                     "en": "No new changes right now."},
    "sync_now": {"sw": "\U0001F504 Sasisha kutoka TANeSW", "en": "\U0001F504 Sync from TANeSW"},
    "sync_done": {"sw": "Imesasishwa: {updated} kati ya {checked} zilizoangaliwa.",
                  "en": "Updated {updated} of {checked} checked."},

    # Documents / upload
    "nav_import": {"sw": "Upload Excel", "en": "Upload Excel"},
    "document": {"sw": "Hati (PDF/picha)", "en": "Document (PDF/image)"},
    "view_doc": {"sw": "Ona hati", "en": "View document"},
    "has_doc": {"sw": "Hati imeambatanishwa", "en": "Document attached"},
    "doc_hint": {"sw": "PDF, PNG au JPG. Ukiacha wazi, hati ya zamani inabaki.",
                  "en": "PDF, PNG or JPG. Leave empty to keep the current one."},

    # Import page
    "import_title": {"sw": "Upload faili ya wateja (Excel/CSV)", "en": "Upload clients file (Excel/CSV)"},
    "import_intro": {"sw": "Pakia faili ya .xlsx au .csv yenye rekodi zote za BL kwa mara moja.",
                      "en": "Upload a .xlsx or .csv file to add all BL records at once."},
    "import_columns": {"sw": "Safu zinazotakiwa (mstari wa kwanza):",
                        "en": "Required columns (first row):"},
    "import_cat_note": {"sw": "Kundi (category) liwe moja ya: completed, in_progress, problem, other (au Kiswahili: zimekamilika, zinaendelea, zina tatizo, nyingine).",
                         "en": "Category must be one of: completed, in_progress, problem, other."},
    "download_template": {"sw": "Pakua kiolezo (template)", "en": "Download template"},
    "choose_file": {"sw": "Chagua faili", "en": "Choose file"},
    "upload": {"sw": "Pakia", "en": "Upload"},
    "import_ok": {"sw": "Rekodi {n} zimeongezwa.", "en": "{n} records imported."},
    "import_ds_ok": {"sw": "Faili ya D-SERVICES imetambuliwa — rekodi {n} zimeingizwa.", "en": "D-SERVICES file recognised — {n} records imported."},
    "import_ds_note": {"sw": "Ukipakia faili yako ya “D-SERVICES OPERATION Daily”, mfumo utaitambua wenyewe na kuchukua taarifa za msingi (kampuni, mteja, BL, status, ICD na tarehe) kutoka sheets za CNT na VEHICLE.", "en": "If you upload your “D-SERVICES OPERATION Daily” file, the system recognises it and pulls the essentials (company, client, BL, status, ICD and dates) from the CNT and VEHICLE sheets."},
    "replace_label": {"sw": "Futa zote kwanza (badilisha na hizi mpya)", "en": "Clear all first (replace with these)"},
    "replace_hint": {"sw": "Tumia hii kila siku ukipakia faili mpya ili kuepuka marudio.", "en": "Use this for a daily refresh to avoid duplicates."},
    "import_nofile": {"sw": "Tafadhali chagua faili kwanza.", "en": "Please choose a file first."},
    "import_badtype": {"sw": "Aina ya faili si sahihi. Tumia .xlsx au .csv.", "en": "Unsupported file type. Use .xlsx or .csv."},
    "import_error": {"sw": "Imeshindwa kusoma faili. Hakikisha muundo ni sahihi.", "en": "Could not read the file. Check its format."},
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
