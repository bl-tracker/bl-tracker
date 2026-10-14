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
import re
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
GATE_OUT_CODES = ("C62", "C60")   # Gate Out Confirm End / Start
TANSAD_CODES   = ("T03", "T04")   # TANSAD Declaration Receipt / Release


def _is_released_overstay(status):
    return "released overstayed" in (status or "").lower()


def _final_gate_out(plist, dlvr_code):
    """Return the date of the gate-out that happened AT the delivery place (the
    ICD), i.e. the real completion — not the earlier gate-out at the port while
    the cargo was only moving to the ICD. Returns '' if none."""
    best = ""
    for s in plist or []:
        if (s.get("cagTrkngPrcssCd") in GATE_OUT_CODES
                and dlvr_code and s.get("wrhsCd") == dlvr_code):
            dt = str(s.get("prcssDt") or "")
            if dt > best:
                best = dt
    return _d(best)


def _infer_category(status, done):
    if done:
        return "completed"
    s = (status or "").lower()
    if any(k in s for k in ("suspect", "target", "query", "hold",
                            "problem", "rejected", "blocked", "cancel")):
        return "problem"
    if "overstay" in s and "released overstay" not in s:
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

    # Completion = a gate-out that happened AT the delivery place (the ICD). The
    # earlier gate-out at the port (while only moving to the ICD) does NOT count.
    # Once that ICD gate-out exists the BL stays complete, even if TANeSW later
    # shows another step (amended TANSAD etc.). "Released Overstayed" also counts.
    dlvr_code = content.get("dlvrPlcCd")
    gate_out = _final_gate_out(plist, dlvr_code)
    done = bool(gate_out) or _is_released_overstay(status)

    # TANSAD / declaration number (shown once duty has been declared)
    tansad = ""
    for s in plist:
        if s.get("cagTrkngPrcssCd") in TANSAD_CODES:
            t = (s.get("dclrNo") or "").strip()
            if not t:
                t = (s.get("sctDclrNo") or "").split("(")[0].strip()
            if t:
                tansad = t
                break

    # containers: numbers + how many
    cntrs = [str(c.get("cntrNo")).strip() for c in (content.get("blCntrLst") or [])
             if c.get("cntrNo")]
    count = content.get("blCntrNo") or len(cntrs)

    return {
        "status": status,
        "category": _infer_category(status, done),
        "vessel": content.get("vsslNm") or "",
        "shipping_line": shipping_line,
        "icd": icd,
        "manifest_date": _milestone(plist, MANIFEST_CODES),
        "carry_in_date": _milestone(plist, CARRY_IN_CODES),
        "release_date": _milestone(plist, RELEASE_CODES),
        "gate_out_date": gate_out,
        "tansad_no": tansad,
        "containers": ", ".join(cntrs),
        "container_count": str(count) if count else "",
    }


def _bl_variants(bl):
    """BL search variants. A consolidated/groupage master BL is often split in
    the sheet as 'PLLD20845634-001', '-002'... but TANeSW only knows the master
    'PLLD20845634', so we also try with a trailing '-NNN' / '/NNN' removed."""
    bl = (bl or "").strip()
    out = [bl]
    base = re.sub(r"[-/ ]\d{1,4}$", "", bl)
    if base and base != bl:
        out.append(base)
    return out


def _probe(bl, getter, timeout):
    """Return (state, content): state is 'ok' (has data), 'empty' (clean
    content:0 — not in active tracking), or 'error' (couldn't reach TANeSW)."""
    params = {"srchCrn": "", "srchBlNo": bl, "srchCntrNo": ""}
    try:
        resp = getter.get(TESWS_URL, params=params, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return "error", None
    if (data.get("totalCnt") or {}).get("content", 0) < 1:
        return "empty", None
    content = (data.get("trkngDtl") or {}).get("content")
    return ("ok", content) if content else ("empty", None)


def _fetch_raw(bl, getter, timeout):
    state, content = _probe(bl, getter, timeout)
    return content if state == "ok" else None


# A BL whose status shows it already progressed past manifest — if TANeSW no
# longer has it (archived), it has gated out and is complete.
PROGRESS_KEYS = ("carry in", "carry out", "release", "tansad", "gate out",
                 "get out", "discharge", "handover", "css", "delivery",
                 "overstay")


def fetch_with_state(bl_no, getter, timeout, agent_map):
    """Return (fields_or_None, state). state: 'found' / 'empty' / 'error'."""
    any_empty = False
    for v in _bl_variants(bl_no):
        state, content = _probe(v, getter, timeout)
        if state == "ok" and content:
            return map_fields(content, agent_map), "found"
        if state == "empty":
            any_empty = True
    return None, ("empty" if any_empty else "error")


def diagnose(bl_no, session=None, timeout=12):
    """Diagnostic view: which variant matched, current status, delivery place,
    and every gate-out event with its location — to debug completion."""
    getter = session or requests
    tried = {}
    content = None
    matched = None
    for variant in _bl_variants(bl_no):
        c = _fetch_raw(variant, getter, timeout)
        tried[variant] = bool(c)
        if c and content is None:
            content, matched = c, variant
    out = {"input": bl_no, "tried": tried, "matched": matched, "found": bool(content)}
    if content:
        out["current_status"] = content.get("cagTrkngPrcssCdNm")
        out["dlvrPlcCd"] = content.get("dlvrPlcCd")
        out["dlvrPlcCdNm"] = content.get("dlvrPlcCdNm")
        out["gate_events"] = [
            {"code": s.get("cagTrkngPrcssCd"), "name": s.get("cagTrkngPrcssCdNm"),
             "date": s.get("prcssDt"), "wrhsCd": s.get("wrhsCd"),
             "wrhsCdNm": s.get("wrhsCdNm")}
            for s in (content.get("blPrcssLst") or [])
            if s.get("cagTrkngPrcssCd") in GATE_OUT_CODES]
        out["mapped"] = map_fields(content, {})
    return out


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
    fields, _ = fetch_with_state(bl, getter, timeout, agent_map)
    return fields


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
             "manifest_date", "carry_in_date", "release_date", "gate_out_date",
             "tansad_no", "containers", "container_count")
    fill_only = ("tansad_no", "containers", "container_count")
    found_count = 0
    archived = []  # deferred: only trust these if TANeSW is actually responding
    for r in rows:
        if only_open and r.get("category") == "completed":
            continue
        fields, state = fetch_with_state(r.get("bl_no"), sess, 12, amap)

        if not fields:
            # TANeSW has no active record. If the BL already progressed past
            # manifest, it has gated out and been archived -> mark completed.
            if state == "empty":
                st = (r.get("status") or "").lower()
                if r.get("category") != "completed" and any(k in st for k in PROGRESS_KEYS):
                    archived.append({
                        "id": r.get("id"), "bl_no": r.get("bl_no"),
                        "client": r.get("client"), "agent": r.get("agent"),
                        "changes": {"category": (r.get("category") or "", "completed")},
                        "new_manifest": False, "archived_done": True,
                        "fields": {"category": "completed"},
                    })
            if delay:
                time.sleep(delay)
            continue

        found_count += 1

        changes = {}
        for k in TRACK:
            new = str(fields.get(k, "") or "")
            old = str(r.get(k) or "")
            if new == old:
                continue
            if k in fill_only and not new:  # never report/clear a fill-only field
                continue
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

    # Only trust the "archived = gated out" calls if TANeSW actually returned
    # data this run (guards against a TANeSW outage completing everything).
    if found_count > 0:
        out.extend(archived)
    return out


if __name__ == "__main__":
    import sys, json
    bl = sys.argv[1] if len(sys.argv) > 1 else "EMIVCHNNIN041349"
    print(json.dumps(fetch_bl(bl), indent=2))
