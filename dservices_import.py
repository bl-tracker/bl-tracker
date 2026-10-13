"""
Smart importer for the "D-SERVICES OPERATION Daily" workbook.

The file has one sheet per company for containers and vehicles, named like
"ASKARI CNT", "ASKARI VEHICLE", "BYANGU CNT" ... Each sheet has a 2-row header
then data rows. Different sheets can have their columns in slightly different
positions, so instead of fixed indexes we locate each column by reading the
header labels of that specific sheet.

We pull only the essentials:
  agent  <- company name in the sheet title
  client, bl_no (Number/Ref/UCR), status, shipping_line (Vessel),
  icd (ICD/Port), manifest_date, carry_in_date, release_date, gate_out_date,
  bl_date (Received), notes (type + items), category (inferred from status).

Other sheets (DASHBOARD, SUMMARY, MASTER LIST, archives) are ignored. If the
uploaded file is not this workbook, the caller falls back to a flat import.
"""
import io
import re

from openpyxl import load_workbook

from carriers import detect_shipping_line

AGENT_SHEET_RE = re.compile(r"^(?P<agent>.+?)\s+(?P<kind>CNT|VEHICLE)$", re.I)

# field -> list of matcher functions on a lowercased combined header label
MATCHERS = {
    "status":        lambda s: s == "status",
    "client":        lambda s: s == "client",
    "bl_no":         lambda s: s == "number",
    "ref":           lambda s: "ref no" in s,
    "ucr":           lambda s: "ucr no" in s,
    "vessel":        lambda s: "vessel" in s,
    "items":         lambda s: s == "items",
    "received":      lambda s: "bl details" in s and "received" in s,
    "manifest_date": lambda s: "manifest" in s,
    "icd":           lambda s: s == "icd" or s.endswith(" icd"),
    "carry_in_date": lambda s: "carry in" in s,
    "release_date":  lambda s: "release" in s,
    "gate_out_date": lambda s: "get out" in s,
}


def is_dservices_workbook(sheetnames):
    return any(AGENT_SHEET_RE.match(n or "") for n in sheetnames)


def _infer_category(status):
    s = (status or "").lower()
    if any(k in s for k in ("release", "get out", "gate out", "handover report en",
                            "delivered", "delivery done", "completed")):
        return "completed"
    if any(k in s for k in ("suspect", "target", "overstay", "query", "hold",
                            "problem", "rejected", "blocked")):
        return "problem"
    return "in_progress"


def _as_date(v):
    try:
        return v.strftime("%Y-%m-%d")
    except Exception:
        s = str(v).strip() if v is not None else ""
        return s.split(" ")[0] if s else ""


def _find_header(rows):
    """Return (header_row_index, column_map) by locating the 'Status' sub-header."""
    for hi in range(min(6, len(rows))):
        if any(str(c).strip().lower() == "status" for c in rows[hi] if c is not None):
            hdr = rows[max(0, hi - 1): hi + 1]
            ncols = max((len(r) for r in hdr), default=0)

            def label(i):
                return " ".join(
                    str(r[i]).strip().lower()
                    for r in hdr if i < len(r) and r[i] is not None
                ).strip()

            cols = {}
            for i in range(ncols):
                lab = label(i)
                if not lab:
                    continue
                for field, match in MATCHERS.items():
                    if field not in cols and match(lab):
                        cols[field] = i
            return hi, cols
    return None, {}


def parse(file_bytes):
    wb = load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    out = []
    for name in wb.sheetnames:
        m = AGENT_SHEET_RE.match(name or "")
        if not m:
            continue
        agent = m.group("agent").strip()
        ktype = "Container" if m.group("kind").upper() == "CNT" else "Vehicle"
        rows = list(wb[name].iter_rows(values_only=True))
        hi, cols = _find_header(rows)
        if hi is None or "client" not in cols:
            continue

        def cell(r, field):
            i = cols.get(field)
            if i is None or i >= len(r) or r[i] is None:
                return ""
            return r[i]

        for r in rows[hi + 1:]:
            client = str(cell(r, "client")).strip()
            if not client or client.lower() == "select":
                continue
            bl = (str(cell(r, "bl_no")).strip() or str(cell(r, "ref")).strip()
                  or str(cell(r, "ucr")).strip() or "-")
            status = str(cell(r, "status")).strip()
            if status.lower() == "select":
                status = ""
            items = str(cell(r, "items")).strip()
            icd = str(cell(r, "icd")).strip().replace("Select", "")
            vessel = str(cell(r, "vessel")).strip()
            out.append({
                "bl_no": bl,
                "client": client,
                "agent": agent,
                "vessel": vessel,
                # auto-detected from vessel name / BL prefix; blank if unknown
                "shipping_line": detect_shipping_line(vessel, bl),
                "status": status,
                "category": _infer_category(status),
                "bl_date": _as_date(cell(r, "received")),
                "notes": " | ".join(x for x in (ktype, items) if x),
                "icd": icd,
                "manifest_date": _as_date(cell(r, "manifest_date")),
                "carry_in_date": _as_date(cell(r, "carry_in_date")),
                "release_date": _as_date(cell(r, "release_date")),
                "gate_out_date": _as_date(cell(r, "gate_out_date")),
            })
    return out
