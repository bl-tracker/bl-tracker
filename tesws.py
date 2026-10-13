"""
Awamu ya 2 - Kufuatilia status kiotomatiki kutoka TANeSW (TeSWS).

Mlango wa umma (HAKUNA login, HAKUNA cookie - umethibitishwa kwa HAR):
  GET https://tanesw.tra.go.tz/api/cgm/api/v1/cgme/trkng/srch
      ?srchCrn=&srchBlNo=<BL>&srchCntrNo=
  Hurudisha JSON: {"totalCnt":{"content":N}, "trkngDtl":{"content":{...}}}

Lazima tutume headers za "kibrowser" (Referer + Accept-Language: EN + User-Agent
halisi), vinginevyo seva hurudisha content:0.

Tunachochukua kwa kila BL:
  status, vessel, shipping_line (carrier), icd (depot/delivery place),
  tarehe: manifest / carry-in / release / gate-out (kutoka blPrcssLst),
  pamoja na category iliyokisiwa kutoka status.
"""
import time
import requests

TESWS_URL = "https://tanesw.tra.go.tz/api/cgm/api/v1/cgme/trkng/srch"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "EN",
    "Referer": "https://tanesw.tra.go.tz/cgme/trkng/cgme0910001q?menuId=menu_cgme0711",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36"),
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

# process-code -> which milestone date it fills. Tunachukua tarehe ya HIVI
# KARIBUNI zaidi (max) kwa kila msimbo.
MANIFEST_CODES = ("A02", "A01")   # Import Manifest Approved / Submitted
CARRY_IN_CODES = ("C04", "C01")   # Carry In End / Start
RELEASE_CODES  = ("T04",)         # TANSAD Declaration Release
GATE_OUT_CODES = ("C62", "C60")   # Gate Out Confirm End / Start (ya mwisho = kutoka ICD)


def _infer_category(status):
    s = (status or "").lower()
    if any(k in s for k in ("gate out", "get out", "carry out", "delivered",
                            "handover report end", "completed")):
        return "completed"
    if any(k in s for k in ("suspect", "target", "overstay", "query", "hold",
                            "problem", "rejected", "blocked", "cancel")):
        return "problem"
    return "in_progress"


def _d(s):
    """'2026-10-13 21:29:11' -> '2026-10-13'."""
    if not s:
        return ""
    return str(s)[:10]


def _milestone(prcss_list, codes):
    """Tarehe ya hivi karibuni zaidi (prcssDt) kati ya hatua zenye misimbo hii."""
    best = ""
    for st in prcss_list or []:
        if st.get("cagTrkngPrcssCd") in codes:
            dt = str(st.get("prcssDt") or "")
            if dt > best:
                best = dt
    return _d(best)


def _strip_code(name):
    """'[WITZDL046] GALCO LIMITED' -> 'GALCO LIMITED'."""
    s = (name or "").strip()
    if s.startswith("[") and "]" in s:
        s = s.split("]", 1)[1].strip()
    return s


def map_fields(content):
    """Geuza trkngDtl.content kuwa sehemu za database tunazosasisha."""
    plist = content.get("blPrcssLst") or []
    status = content.get("cagTrkngPrcssCdNm") or ""
    icd = (content.get("dlvrPlcCdNm")
           or _strip_code(content.get("lastGodsLoctCdNm"))
           or "")
    return {
        "status": status,
        "category": _infer_category(status),
        "vessel": content.get("vsslNm") or "",
        "shipping_line": content.get("carrNm") or "",
        "icd": icd,
        "manifest_date": _milestone(plist, MANIFEST_CODES),
        "carry_in_date": _milestone(plist, CARRY_IN_CODES),
        "release_date": _milestone(plist, RELEASE_CODES),
        "gate_out_date": _milestone(plist, GATE_OUT_CODES),
    }


def fetch_bl(bl_no, session=None, timeout=12):
    """
    Rudisha dict ya sehemu zilizo-map kwa BL moja, au None ikiwa TANeSW
    haina rekodi (content:0) au kuna hitilafu.
    """
    bl = (bl_no or "").strip()
    if not bl or bl == "-":
        return None
    getter = session or requests
    params = {"srchCrn": "", "srchBlNo": bl, "srchCntrNo": ""}
    try:
        resp = getter.get(TESWS_URL, params=params, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None
    if (data.get("totalCnt") or {}).get("content", 0) < 1:
        return None
    content = (data.get("trkngDtl") or {}).get("content")
    if not content:
        return None
    return map_fields(content)


def sync_rows(rows, delay=0.2, only_open=True):
    """
    Pokea rekodi (dict zenye 'id','bl_no','category', n.k.), piga TANeSW kwa kila
    moja, na rudisha orodha ya mabadiliko:
      [{"id","bl_no","client","changes":{field:(old,new)}, "new": {...}}]
    Hairuki (skip) zilizokamilika ikiwa only_open=True.
    """
    out = []
    sess = requests.Session()
    TRACK = ("status", "category", "vessel", "shipping_line", "icd",
             "manifest_date", "carry_in_date", "release_date", "gate_out_date")
    for r in rows:
        if only_open and (r.get("category") == "completed" or r.get("gate_out_date")):
            continue
        fields = fetch_bl(r.get("bl_no"), session=sess)
        if not fields:
            continue
        changes = {}
        for k in TRACK:
            new = fields.get(k, "")
            old = r.get(k) or ""
            # usifute thamani iliyopo kwa tupu kutoka TANeSW
            if new and str(new) != str(old):
                changes[k] = (old, new)
        if changes:
            out.append({
                "id": r.get("id"),
                "bl_no": r.get("bl_no"),
                "client": r.get("client"),
                "agent": r.get("agent"),
                "changes": changes,
                "new": {k: fields.get(k, "") for k in TRACK if fields.get(k)},
            })
        if delay:
            time.sleep(delay)
    return out


if __name__ == "__main__":
    import sys, json
    bl = sys.argv[1] if len(sys.argv) > 1 else "EMIVCHNNIN041349"
    print(json.dumps(fetch_bl(bl), indent=2))
