"""
Auto-detect the Shipping Line (carrier) from the vessel name and/or the BL
number prefix. No OCR needed - uses data we already have.

- Vessel names often contain the carrier: "MSC LORENA" -> MSC,
  "CMA CGM TAORMINA" -> CMA CGM, "MAERSK NADI" -> Maersk.
- BL numbers often start with the carrier's prefix: MEDU -> MSC,
  COSU -> COSCO, HLCU -> Hapag-Lloyd, etc.

Returns "" when it cannot tell (then the user fills it manually).
"""
import re

# keyword found in a VESSEL name (or document text) -> carrier
VESSEL_KEYWORDS = [
    ("MSC", "MSC"),
    ("CMA CGM", "CMA CGM"), ("CMA", "CMA CGM"), ("ANL", "CMA CGM"), ("APL", "APL"),
    ("MAERSK", "Maersk"), ("SEALAND", "Maersk"),
    ("HAPAG", "Hapag-Lloyd"),
    ("COSCO", "COSCO"),
    ("OOCL", "OOCL"),
    ("EVERGREEN", "Evergreen"),
    ("HYUNDAI", "HMM"), ("HMM", "HMM"),
    ("YANG MING", "Yang Ming"),
    ("WAN HAI", "Wan Hai"),
    ("INTERASIA", "Interasia"),
    ("SITC", "SITC"),
    ("ZIM", "ZIM"),
    ("PIL", "PIL"), ("KOTA", "PIL"),
    ("ONE ", "ONE"), ("OCEAN NETWORK", "ONE"),
    ("KMTC", "KMTC"),
]

# first 4 letters of the BL number -> carrier
BL_PREFIX = {
    "MAEU": "Maersk", "MSKU": "Maersk", "MRKU": "Maersk", "MRSU": "Maersk", "SEAU": "Maersk",
    "MSCU": "MSC", "MEDU": "MSC", "MSDU": "MSC",
    "CMAU": "CMA CGM", "CMDU": "CMA CGM", "CGMU": "CMA CGM", "APLU": "APL", "APZU": "APL",
    "HLCU": "Hapag-Lloyd", "HLXU": "Hapag-Lloyd",
    "COSU": "COSCO", "CSNU": "COSCO", "CBHU": "COSCO", "CCLU": "COSCO",
    "OOLU": "OOCL", "OOCU": "OOCL",
    "EGLV": "Evergreen", "EISU": "Evergreen", "EGHU": "Evergreen",
    "ONEY": "ONE", "KKFU": "ONE",
    "HDMU": "HMM", "HMMU": "HMM",
    "KMTU": "KMTC", "KMTC": "KMTC",
    "SITC": "SITC", "SITU": "SITC",
    "WHLC": "Wan Hai", "WHSU": "Wan Hai",
    "YMLU": "Yang Ming",
    "ZIMU": "ZIM",
    "PABV": "PIL", "PCIU": "PIL",
}


def detect_shipping_line(vessel="", bl_no="", text=""):
    # The BL number prefix identifies who ISSUED the Bill of Lading - the most
    # reliable signal. The vessel name can belong to a slot-charter partner
    # (e.g. a COSU... BL carried on an "APL CHONGQING" ship is COSCO's), so we
    # try the BL prefix first and only fall back to the vessel/document name.
    code = re.sub(r"[^A-Z]", "", (bl_no or "").upper())[:4]
    if code in BL_PREFIX:
        return BL_PREFIX[code]
    hay = f"{vessel} {text}".upper()
    for kw, carrier in VESSEL_KEYWORDS:
        if kw in hay:
            return carrier
    return ""
