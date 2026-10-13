# 📦 BL Tracker — Mfumo wa Kufuatilia Bill of Lading

Web app ya kuhifadhi rekodi za BL na kutuma **muhtasari (summary) kwa Telegram kila baada ya saa 3**.
Inafanya kazi kwenye **simu na kompyuta**, na ina lugha mbili: **Kiswahili + English** (kitufe cha kubadilisha juu kulia).

*A bilingual web app to track Bill of Lading records and send a Telegram summary every 3 hours.*

---

## Awamu hii inafanya nini (Awamu ya 1)

- ➕ Kuongeza, kuhariri, kufuta rekodi za BL (namba, mteja, shipping line, status, kundi, tarehe, maelezo).
- 📊 Muhtasari wa papo hapo: zimekamilika / zinaendelea / zina tatizo / nyingine.
- ✈️ Kutuma muhtasari kwa Telegram — kwa kitufe, au kiotomatiki kila saa 3.

> **Awamu ya 2 (baadaye):** kujaza status kiotomatiki kutoka **TeSWS**.
> Mlango wa API umethibitishwa tayari (tazama `tesws.py`). Tutaukamilisha baada ya kuona data halisi.

---

## Sehemu ya 1 — Tengeneza bot ya Telegram (dakika 5)

1. Fungua Telegram, tafuta **@BotFather**, anza mazungumzo.
2. Andika `/newbot`, fuata maelekezo (chagua jina na username). Utapewa **TOKEN** ndefu — ihifadhi.
3. Tafuta bot yako mpya kwa jina ulilochagua, bonyeza **Start** (ili iweze kukutumia ujumbe).
4. Pata **Chat ID** yako: tafuta **@userinfobot**, bonyeza Start — itakuambia namba yako (hiyo ndiyo `TELEGRAM_CHAT_ID`).

> Kutuma kwenye **group**? Mwongeze bot kwenye group, kisha tumia chat id ya group (huanza na `-100...`). Rahisi zaidi: anza na chat yako binafsi.

---

## Sehemu ya 2 — Weka app mtandaoni (Render, bure)

1. Tengeneza akaunti bure kwenye **https://render.com** (unaweza kutumia GitHub).
2. Weka project hii kwenye **GitHub** (repo mpya), kisha kwenye Render bonyeza **New + → Web Service** na uchague repo hiyo.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
3. Kwenye **Environment** (Environment Variables), ongeza:

   | Key | Value |
   |-----|-------|
   | `TELEGRAM_BOT_TOKEN` | token kutoka BotFather |
   | `TELEGRAM_CHAT_ID` | chat id yako |
   | `NOTIFY_TOKEN` | neno la siri lolote refu (mf. `xk9f2mq7`) |
   | `SECRET_KEY` | neno lingine la siri |
   | `NOTIFY_LANG` | `sw` au `en` |
   | `RUN_SCHEDULER` | `0` |

4. Bonyeza **Deploy**. Baada ya dakika chache utapata link kama `https://bl-tracker-xxxx.onrender.com`.

> **Muhimu kuhusu tier ya bure:** disk ya Render ya bure hujifuta app ikipya-deploy, na app hulala baada ya dakika 15 bila matumizi. Kwa data isipotee kabisa, baadaye tunaweza kuunganisha **database ya bure ya Postgres** (nitakuelekeza). Kwa kuanzia, hii inatosha kujaribu.

---

## Sehemu ya 3 — Panga summary ya kila saa 3 (cron, bure)

App ina mlango maalum: `/tasks/notify?token=NOTIFY_TOKEN`. Tunatumia huduma ya bure kuupiga kila saa 3.

1. Nenda **https://cron-job.org**, tengeneza akaunti bure.
2. **Create cronjob**:
   - **URL:** `https://bl-tracker-xxxx.onrender.com/tasks/notify?token=NENO_LAKO_LA_SIRI`
     *(weka link yako halisi na `NOTIFY_TOKEN` uliyoiweka)*
   - **Schedule:** Every **3 hours** (au chagua masaa unayopenda).
3. Save. Sasa utapokea summary ya Telegram kila saa 3 — hata usipofungua app.

> Njia mbadala: kwenye seva isiyolala, weka `RUN_SCHEDULER=1` badala ya kutumia cron ya nje.

---

## Kuendesha kwenye kompyuta yako (hiari, kwa majaribio)

```bash
pip install -r requirements.txt
cp .env.example .env          # jaza token zako
python app.py                 # fungua http://127.0.0.1:5000
```

---

## Vigezo vya mazingira (Environment variables)

| Jina | Maana |
|------|-------|
| `TELEGRAM_BOT_TOKEN` | Token ya bot (BotFather). |
| `TELEGRAM_CHAT_ID` | Namba ya chat ya kupokea summary. |
| `NOTIFY_TOKEN` | Siri inayolinda `/tasks/notify`. |
| `NOTIFY_LANG` | `sw` au `en` — lugha ya ujumbe. |
| `SECRET_KEY` | Siri ya Flask. |
| `RUN_SCHEDULER` | `1` = scheduler ndani ya app; `0` = tumia cron ya nje. |
| `DB_PATH` | (hiari) mahali pa faili ya SQLite. |

---

## Faili zilizomo

- `app.py` — app kuu (routes, Telegram, scheduler).
- `db.py` — database (SQLite).
- `i18n.py` — maneno ya Kiswahili + English.
- `tesws.py` — kiunzi cha Awamu ya 2 (ufuatiliaji wa kiotomatiki).
- `templates/`, `static/` — mwonekano.
- `render.yaml`, `Procfile` — usanidi wa ku-deploy.
