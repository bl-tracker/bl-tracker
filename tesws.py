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
# Code -> name table for shipping agents (and more). The tracking response only
# gives the agent CODE (shagCd, e.g. "BFL"); this table resolves it to the full
# name ("BLUE FUNNEL TANZANIA LIMITED"). coTpCd == "SL" are shipping lines/agents.
CO_DCLA_URL = "https://tanesw.tra.go.tz/api/ptl/api/v1/ptle/extptl/comnppup/co-dcla-cd"

# in-memory cache of {agent_code: agent_name}; refreshed at most once a day
_AGENT_CACHE = {"map": None, "ts": 0.0}

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


def _is_complete(status):
    """A BL is complete when gated out, OR when it is a released overstayed
    cargo (that cargo has already left the ICD/Port)."""
    s = (status or "").lower()
    return "gate out" in s or "get out" in s or "released overstayed" in s


def _infer_category(status):
    s = (status or "").lower()
    if _is_complete(status):
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


def shipping_agents(session=None, timeout=20, force=False):
    """Return {code: name} for shipping agents (coTpCd 'SL'), cached for a day.
    On any error returns whatever is cached (possibly empty)."""
    now = time.time()
    if (not force and _AGENT_CACHE["map"] is not None
            and now - _AGENT_CACHE["ts"] < 86400):
        return _AGENT_CACHE["map"]
    getter = session or requests
    params = {"coCd": "", "coNm": "", "coTin": "", "coTpCd": "SL",
              "spcdlWrhsYn": "", "coCds": "", "size": "999999"}
    try:
        resp = getter.get(CO_DCLA_URL, params=params, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        lst = data.get("coDclaCdList")
        if isinstance(lst, dict):
            lst = lst.get("content") or []
        elif not isinstance(lst, list):
            lst = []
        m = {}
        for x in lst:
            if x.get("coTpCd") == "SL" and x.get("coCd"):
                m[str(x["coCd"]).strip().upper()] = (x.get("coNm") or "").strip()
        if m:
            _AGENT_CACHE["map"] = m
            _AGENT_CACHE["ts"] = now
        return m or (_AGENT_CACHE["map"] or {})
    except Exception:
        return _AGENT_CACHE["map"] or {}


def map_fields(content, agent_map=None):
    """Geuza trkngDtl.content kuwa sehemu za database tunazosasisha."""
    if agent_map is None:
        agent_map = _AGENT_CACHE.get("map") or {}
    plist = content.get("blPrcssLst") or []
    status = content.get("cagTrkngPrcssCdNm") or ""
    icd = (content.get("dlvrPlcCdNm")
           or _strip_code(content.get("lastGodsLoctCdNm"))
           or "")
    # s/line = Shipping Agent (shagCd -> name); fall back to carrier, then code.
    shag = str(content.get("shagCd") or "").strip().upper()
    shipping_line = agent_map.get(shag, "") or content.get("carrNm") or shag or ""
    # Complete ONLY when the CURRENT status is Gate Out. An earlier gate-out at
    # the port (on the way to the ICD) is NOT completion, so we only record the
    # gate-out date when the BL has truly finished.
    done = _is_complete(status)
    return {
        "status": status,
        "category": _infer_category(status),
        "vessel": content.get("vsslNm") or "",
        "shipping_line": shipping_line,
        "icd": icd,
        "manifest_date": _milestone(plist, MANIFEST_CODES),
        "carry_in_date": _milestone(plist, CARRY_IN_CODES),
        "release_date": _milestone(plist, RELEASE_CODES),
        "gate_out_date": _milestone(plist, GATE_OUT_CODES) if done else "",
    }


def fetch_bl(bl_no, session=None, timeout=12, agent_map=None):
    """
    Rudisha dict ya sehemu zilizo-map kwa BL moja, au None ikiwa TANeSW
    haina rekodi (content:0) au kuna hitilafu.
    """
    bl = (bl_no or "").strip()
    if not bl or bl == "-":
        return None
    getter = session or requests
    if agent_map is None:
        agent_map = shipping_agents(session)
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
    return map_fields(content, agent_map)


def sync_rows(rows, delay=0.2, only_open=True):
    """
    Pokea rekodi (dict zenye 'id','bl_no','category', n.k.), piga TANeSW kwa kila
    moja, na rudisha orodha ya mabadiliko:
      [{"id","bl_no","client","changes":{field:(old,new)}, "new": {...}}]
    Hairuki (skip) zilizokamilika ikiwa only_open=True.
    """
    out = []
    sess = requests.Session()
    amap = shipping_agents(sess)  # load the agent code->name table once
    TRACK = ("status", "category", "vessel", "shipping_line", "icd",
             "manifest_date", "carry_in_date", "release_date", "gate_out_date")
    for r in rows:
        if only_open and r.get("category") == "completed":
            continue
        fields = fetch_bl(r.get("bl_no"), session=sess, agent_map=amap)
        if not fields:
            continue
        changes = {}
        for k in TRACK:
            new = str(fields.get(k, "") or "")
            old = str(r.get(k) or "")
            if new != old:  # record real changes AND clears (TANeSW is authoritative)
                changes[k] = (old, new)
        if changes:
            out.append({
                "id": r.get("id"),
                "bl_no": r.get("bl_no"),
                "client": r.get("client"),
                "agent": r.get("agent"),
                "changes": changes,
                # newly manifested = manifest date appeared where there was none
                "new_manifest": ("manifest_date" in changes
                                 and not changes["manifest_date"][0]
                                 and changes["manifest_date"][1]),
                "fields": fields,  # full authoritative field set to apply
            })
        if delay:
            time.sleep(delay)
    return out


if __name__ == "__main__":
    import sys, json
    bl = sys.argv[1] if len(sys.argv) > 1 else "EMIVCHNNIN041349"
    print(json.dumps(fetch_bl(bl), indent=2))
