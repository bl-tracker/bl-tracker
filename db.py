"""
Database layer for BL Tracker (SQLAlchemy Core).

- If DATABASE_URL is set (e.g. a Neon Postgres connection string), data is
  stored there and PERSISTS forever.
- Otherwise it falls back to a local SQLite file (handy for local testing).

Tables:
  bls           - one row per Bill of Lading record
  bl_documents  - optional uploaded file (PDF/image) attached to a BL,
                  stored directly in the database so it survives restarts.
"""
import os
from datetime import datetime, timezone

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Text,
    LargeBinary, ForeignKey, select, func, or_, insert, update as sa_update,
    delete as sa_delete,
)

CATEGORIES = ["completed", "in_progress", "problem", "other"]


def _db_url():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        path = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "bl_tracker.db"))
        return f"sqlite:///{path}"
    # Some providers give the old-style prefix; SQLAlchemy wants postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


engine = create_engine(_db_url(), pool_pre_ping=True, future=True)
metadata = MetaData()

bls = Table(
    "bls", metadata,
    Column("id", Integer, primary_key=True),
    Column("bl_no", String(255), nullable=False),
    Column("client", String(255), default=""),
    Column("agent", String(255), default=""),
    Column("shipping_line", String(255), default=""),
    Column("status", Text, default=""),
    Column("category", String(32), default="in_progress"),
    Column("bl_date", String(32), default=""),
    Column("notes", Text, default=""),
    Column("icd", String(255), default=""),             # ICD / Port location
    Column("manifest_date", String(64), default=""),
    Column("carry_in_date", String(64), default=""),
    Column("release_date", String(64), default=""),
    Column("gate_out_date", String(64), default=""),
    Column("last_checked", String(64), default=""),
    Column("created_at", String(64)),
    Column("updated_at", String(64)),
)

bl_documents = Table(
    "bl_documents", metadata,
    Column("id", Integer, primary_key=True),
    Column("bl_id", Integer, ForeignKey("bls.id"), nullable=False),
    Column("filename", String(255)),
    Column("content_type", String(128)),
    Column("data", LargeBinary),
    Column("uploaded_at", String(64)),
)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _norm_category(value):
    return value if value in CATEGORIES else "in_progress"


EXTRA_COLS = {
    "icd": "VARCHAR(255)",
    "manifest_date": "VARCHAR(64)",
    "carry_in_date": "VARCHAR(64)",
    "release_date": "VARCHAR(64)",
    "gate_out_date": "VARCHAR(64)",
}


def init_db():
    metadata.create_all(engine)
    _migrate()


def _migrate():
    """Add any newer columns to an existing table (Neon/SQLite safe)."""
    from sqlalchemy import inspect as sa_inspect, text
    insp = sa_inspect(engine)
    existing = {c["name"] for c in insp.get_columns("bls")}
    with engine.begin() as conn:
        for col, typ in EXTRA_COLS.items():
            if col not in existing:
                conn.execute(text(f"ALTER TABLE bls ADD COLUMN {col} {typ} DEFAULT ''"))


def _row_to_dict(row):
    return dict(row._mapping) if row is not None else None


def list_bls(search=None, agent=None):
    stmt = select(bls)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(
            bls.c.bl_no.ilike(like),
            bls.c.client.ilike(like),
            bls.c.agent.ilike(like),
            bls.c.shipping_line.ilike(like),
        ))
    if agent:
        stmt = stmt.where(bls.c.agent == agent)
    # Alphabetical: by company (agent) A-Z, then client, then BL number.
    stmt = stmt.order_by(bls.c.agent.asc(), bls.c.client.asc(), bls.c.bl_no.asc())
    with engine.connect() as conn:
        return [dict(r._mapping) for r in conn.execute(stmt).fetchall()]


def agents_list():
    """Distinct non-empty agent/company names, sorted, for the filter."""
    with engine.connect() as conn:
        rows = conn.execute(
            select(bls.c.agent).where(bls.c.agent != "").distinct()
        ).fetchall()
    return sorted({r[0] for r in rows if r[0]})


def get_bl(bl_id):
    with engine.connect() as conn:
        row = conn.execute(select(bls).where(bls.c.id == bl_id)).fetchone()
    return _row_to_dict(row)


def _clean(data):
    now = _now()
    return {
        "bl_no": (data.get("bl_no") or "").strip(),
        "client": (data.get("client") or "").strip(),
        "agent": (data.get("agent") or "").strip(),
        "shipping_line": (data.get("shipping_line") or "").strip(),
        "status": (data.get("status") or "").strip(),
        "category": _norm_category(data.get("category")),
        "bl_date": (data.get("bl_date") or "").strip(),
        "notes": (data.get("notes") or "").strip(),
        "icd": (data.get("icd") or "").strip(),
        "manifest_date": (data.get("manifest_date") or "").strip(),
        "carry_in_date": (data.get("carry_in_date") or "").strip(),
        "release_date": (data.get("release_date") or "").strip(),
        "gate_out_date": (data.get("gate_out_date") or "").strip(),
        "updated_at": now,
    }


def create_bl(data):
    values = _clean(data)
    values["created_at"] = values["updated_at"]
    values["last_checked"] = ""
    with engine.begin() as conn:
        result = conn.execute(insert(bls).values(**values))
        return result.inserted_primary_key[0]


def update_bl(bl_id, data):
    values = _clean(data)
    with engine.begin() as conn:
        conn.execute(sa_update(bls).where(bls.c.id == bl_id).values(**values))


def delete_bl(bl_id):
    with engine.begin() as conn:
        conn.execute(sa_delete(bl_documents).where(bl_documents.c.bl_id == bl_id))
        conn.execute(sa_delete(bls).where(bls.c.id == bl_id))


def clear_all_bls():
    """Delete every BL record and its documents (used by 'replace' import)."""
    with engine.begin() as conn:
        conn.execute(sa_delete(bl_documents))
        conn.execute(sa_delete(bls))


def summary_counts():
    counts = {c: 0 for c in CATEGORIES}
    with engine.connect() as conn:
        rows = conn.execute(
            select(bls.c.category, func.count()).group_by(bls.c.category)
        ).fetchall()
    for cat, n in rows:
        key = cat if cat in CATEGORIES else "other"
        counts[key] += n
    counts["total"] = sum(counts[c] for c in CATEGORIES)
    return counts


def bulk_create(rows):
    """Insert many BL rows at once (used by Excel/CSV import). Returns count."""
    payload = []
    for data in rows:
        if not (data.get("bl_no") or "").strip():
            continue
        values = _clean(data)
        values["created_at"] = values["updated_at"]
        values["last_checked"] = ""
        payload.append(values)
    if not payload:
        return 0
    with engine.begin() as conn:
        conn.execute(insert(bls), payload)
    return len(payload)


# ----- Documents -----
def save_document(bl_id, filename, content_type, data):
    """Attach a file to a BL. Replaces any existing document for that BL."""
    with engine.begin() as conn:
        conn.execute(sa_delete(bl_documents).where(bl_documents.c.bl_id == bl_id))
        conn.execute(insert(bl_documents).values(
            bl_id=bl_id, filename=filename, content_type=content_type,
            data=data, uploaded_at=_now(),
        ))


def get_document(bl_id):
    with engine.connect() as conn:
        row = conn.execute(
            select(bl_documents).where(bl_documents.c.bl_id == bl_id)
        ).fetchone()
    return _row_to_dict(row)


def bls_with_documents():
    """Return a set of bl_id that have a document (for list display)."""
    with engine.connect() as conn:
        rows = conn.execute(select(bl_documents.c.bl_id)).fetchall()
    return {r[0] for r in rows}
