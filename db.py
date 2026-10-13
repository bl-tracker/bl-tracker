"""
Database layer for BL Tracker.

Uses SQLite by default (zero-config, file-based) so the app runs instantly
anywhere. For persistent hosting on a free tier whose disk resets, set a
Postgres connection string in the DATABASE_URL environment variable and the
app will use that instead (see README).

Awamu ya 1: rekodi za BL zinaongezwa/huhaririwa kwa mkono.
Awamu ya 2: safu `status`, `category` na `last_checked` zitajazwa kiotomatiki
kutoka TeSWS.
"""
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "bl_tracker.db"))

# Status categories that drive the summary counts.
CATEGORIES = ["completed", "in_progress", "problem", "other"]


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the table if it does not exist."""
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bls (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                bl_no         TEXT NOT NULL,
                client        TEXT DEFAULT '',
                shipping_line TEXT DEFAULT '',
                status        TEXT DEFAULT '',
                category      TEXT DEFAULT 'in_progress',
                bl_date       TEXT DEFAULT '',
                notes         TEXT DEFAULT '',
                last_checked  TEXT DEFAULT '',
                created_at    TEXT NOT NULL,
                updated_at    TEXT NOT NULL
            )
            """
        )


def list_bls(search=None):
    sql = "SELECT * FROM bls"
    params = ()
    if search:
        sql += " WHERE bl_no LIKE ? OR client LIKE ? OR shipping_line LIKE ?"
        like = f"%{search}%"
        params = (like, like, like)
    sql += " ORDER BY updated_at DESC"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_bl(bl_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM bls WHERE id = ?", (bl_id,)).fetchone()
        return dict(row) if row else None


def create_bl(data):
    now = _now()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO bls (bl_no, client, shipping_line, status, category,
                             bl_date, notes, last_checked, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, '', ?, ?)
            """,
            (
                data.get("bl_no", "").strip(),
                data.get("client", "").strip(),
                data.get("shipping_line", "").strip(),
                data.get("status", "").strip(),
                _norm_category(data.get("category")),
                data.get("bl_date", "").strip(),
                data.get("notes", "").strip(),
                now,
                now,
            ),
        )
        return cur.lastrowid


def update_bl(bl_id, data):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE bls SET bl_no = ?, client = ?, shipping_line = ?, status = ?,
                           category = ?, bl_date = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                data.get("bl_no", "").strip(),
                data.get("client", "").strip(),
                data.get("shipping_line", "").strip(),
                data.get("status", "").strip(),
                _norm_category(data.get("category")),
                data.get("bl_date", "").strip(),
                data.get("notes", "").strip(),
                _now(),
                bl_id,
            ),
        )


def delete_bl(bl_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM bls WHERE id = ?", (bl_id,))


def summary_counts():
    """Return {total, completed, in_progress, problem, other} for the summary."""
    counts = {c: 0 for c in CATEGORIES}
    with get_conn() as conn:
        rows = conn.execute("SELECT category, COUNT(*) AS n FROM bls GROUP BY category").fetchall()
    for r in rows:
        cat = r["category"] if r["category"] in CATEGORIES else "other"
        counts[cat] += r["n"]
    counts["total"] = sum(counts[c] for c in CATEGORIES)
    return counts


def _norm_category(value):
    return value if value in CATEGORIES else "in_progress"
