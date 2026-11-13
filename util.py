"""Small shared helpers used by both the app and the PDF report."""
import os
import re
from datetime import datetime, date, timedelta

# ICD storage (demurrage) rule — D-SERVICES:
#   anchor = Discharge Result Report Approved (B12) date when the container is
#   carried in to the ICD within STORAGE_GRACE days of it; otherwise (carried in
#   late, 3+ days after discharge) anchor = Carry In End (C04) date. Then
#   STORAGE_FREE_DAYS free days from the anchor before storage starts accruing —
#   and only while the container has NOT yet gated out.
STORAGE_FREE_DAYS = int(os.environ.get("STORAGE_FREE_DAYS", "7") or "7")
STORAGE_GRACE = int(os.environ.get("STORAGE_GRACE", "2") or "2")

# Free-day exception: public ports / government terminals give only 5 free days,
# while private ICDs keep the usual 7. The facility is matched (case-insensitive
# substring) against the BL's ICD name/code. Extend the list without code changes
# via STORAGE_PORT_KEYWORDS (comma-separated).
STORAGE_PORT_FREE_DAYS = int(os.environ.get("STORAGE_PORT_FREE_DAYS", "5") or "5")
_DEFAULT_PORT_KEYWORDS = ("DP WORLD", "DPWORLD", "SALSALA", "SALISLA",
                          "TANGA PORT", "MTWARA", "TEAGTL",
                          "EAST AFRICA GATEWAY", "GATEWAY TERMINAL")
STORAGE_PORT_KEYWORDS = tuple(
    k.strip().upper() for k in
    (os.environ.get("STORAGE_PORT_KEYWORDS") or ",".join(_DEFAULT_PORT_KEYWORDS)).split(",")
    if k.strip()
)


def free_days_for(icd):
    """Free days before storage starts for this facility: 5 for public ports /
    terminals (DP World, SALSALA, Tanga/Mtwara port, TEAGTL, ...), else 7."""
    s = (icd or "").upper()
    for kw in STORAGE_PORT_KEYWORDS:
        if kw and kw in s:
            return STORAGE_PORT_FREE_DAYS
    return STORAGE_FREE_DAYS


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def storage_info(bl, today=None):
    """Return storage state for a BL dict, or {} when it doesn't apply (no
    anchor yet, or already gated out). Keys: anchor, kind ('discharge' or
    'carry_in'), free_until, free_days, days (storage days; <=0 while still
    within free days), free_left, active (True while storage is accruing)."""
    if bl.get("category") == "completed" or (bl.get("gate_out_date") or "").strip():
        return {}
    disch = _parse_date(bl.get("discharge_date"))
    carry = _parse_date(bl.get("carry_in_date"))
    if disch and carry:
        if (carry - disch).days <= STORAGE_GRACE:
            anchor, kind = disch, "discharge"    # carried in promptly
        else:
            anchor, kind = carry, "carry_in"      # carried in late (3+ days)
    elif disch:
        anchor, kind = disch, "discharge"
    elif carry:
        anchor, kind = carry, "carry_in"
    else:
        return {}
    today = today or date.today()
    free_days = free_days_for(bl.get("icd"))
    free_until = anchor + timedelta(days=free_days)
    days = (today - free_until).days              # >=1 => accruing storage
    return {
        "anchor": anchor.isoformat(),
        "kind": kind,
        "free_until": free_until.isoformat(),
        "free_days": free_days,
        "days": days,
        "free_left": max(0, -days),
        "active": days >= 1,
    }


def storage_days(bl, today=None):
    """Chargeable storage days (>=1) or 0 when not currently accruing."""
    info = storage_info(bl, today)
    return info.get("days", 0) if info.get("active") else 0

# words that don't help identify an ICD/depot, dropped when abbreviating
_STOP = {"LIMITED", "LTD", "COMPANY", "CO", "AND", "THE", "ICD", "CFS",
         "GROUP", "PLC", "T", "TZ", "LOGISTICS", "TERMINAL", "DEPOT",
         "CONTAINER", "CARGO", "FREIGHT", "INLAND", "CLEARING", "FORWARDING"}

# too-generic leading words — if an ICD name starts with one of these we keep
# the next word too, so 'TANZANIA ROYAL HORIZON' -> 'TANZANIA ROYAL', not just
# 'TANZANIA'. Distinctive place names (KILIMANJARO, SALSALA, TANGA) are single.
_GENERIC = {"TANZANIA", "DAR", "EAST", "AFRICA", "AFRICAN", "CENTRAL",
            "NEW", "GREAT", "GENERAL"}


def icd_short(name, maxlen=16):
    """Short ICD label: the FIRST real name word(s) of the depot, e.g.
    'KILIMANJARO ICD' -> 'KILIMANJARO', 'SALSALA' -> 'SALSALA',
    'TANGA ...' -> 'TANGA', 'GALCO LIMITED' -> 'GALCO'. If the first word is
    too generic we also keep the second: 'TANZANIA ROYAL HORIZON' -> 'TANZANIA ROYAL'."""
    s = (name or "").strip()
    if not s:
        return ""
    if s.startswith("[") and "]" in s:          # drop a '[CODE]' prefix
        s = s.split("]", 1)[1].strip()
    words = [re.sub(r"[^A-Za-z0-9]", "", w) for w in s.split()]
    words = [w for w in words if w and w.upper() not in _STOP]
    if not words:
        return s[:maxlen].upper()
    first = words[0]
    # keep a second word only when the first is a generic prefix
    if first.upper() in _GENERIC and len(words) >= 2:
        return (first + " " + words[1]).upper()[:maxlen]
    return first.upper()[:maxlen]
