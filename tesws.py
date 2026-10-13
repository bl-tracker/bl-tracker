"""
Awamu ya 2 (kiunzi / stub) - Kufuatilia status kiotomatiki kutoka TeSWS.

Mlango wa API uliothibitishwa:
  GET https://tanesw.tra.go.tz/api/cgm/api/v1/cgme/trkng/srch
      ?srchBlNo=<BL>&srchCntrNo=&srchCrn=
  Hurudisha JSON: {"totalCnt": {"content": N}, "trkngDtl": {...}}

Tutakapoanza Awamu ya 2, tutaendesha hii dhidi ya BL "hai" ili kuona
majina kamili ya sehemu ndani ya `trkngDtl`, kisha tutayaunganisha na
safu za `status` na `category` kwenye database.

Faili hii HAITUMIKI bado kwenye Awamu ya 1 - ipo tayari kwa ajili ya baadaye.
"""
import requests

TESWS_URL = "https://tanesw.tra.go.tz/api/cgm/api/v1/cgme/trkng/srch"


def fetch_status(bl_no):
    """Fetch raw tracking JSON for a single BL number."""
    params = {"srchBlNo": bl_no, "srchCntrNo": "", "srchCrn": ""}
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "EN",
        "User-Agent": "Mozilla/5.0 (compatible; BLTracker/1.0)",
        "Referer": "https://tanesw.tra.go.tz/cgme/trkng/cgme0910001q",
    }
    resp = requests.get(TESWS_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def map_to_category(raw_json):
    """
    TODO (Awamu ya 2): tafsiri status halisi ya TeSWS kuwa moja ya:
    'completed' / 'in_progress' / 'problem' / 'other'.
    Tutakamilisha baada ya kuona muundo wa `trkngDtl` wenye data halisi.
    """
    total = (raw_json or {}).get("totalCnt", {}).get("content", 0)
    if not total:
        return "other", ""
    # Placeholder - itaboreshwa kwa data halisi.
    return "in_progress", ""


if __name__ == "__main__":
    import sys
    bl = sys.argv[1] if len(sys.argv) > 1 else "YSPQINMTW201"
    print(fetch_status(bl))
