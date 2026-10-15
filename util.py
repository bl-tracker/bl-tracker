"""Small shared helpers used by both the app and the PDF report."""
import re

# words that don't help identify an ICD/depot, dropped when abbreviating
_STOP = {"LIMITED", "LTD", "COMPANY", "CO", "AND", "THE", "ICD", "CFS",
         "GROUP", "PLC", "T", "TZ", "LOGISTICS", "TERMINAL", "DEPOT"}


def icd_short(name, maxlen=8):
    """Short ICD label: initials for multi-word names, the word itself for
    one-word names. 'TANZANIA ROYAL HORIZON LTD' -> 'TRH', 'GALCO' -> 'GALCO'."""
    s = (name or "").strip()
    if not s:
        return ""
    if s.startswith("[") and "]" in s:          # drop a '[CODE]' prefix
        s = s.split("]", 1)[1].strip()
    words = [re.sub(r"[^A-Za-z0-9]", "", w) for w in s.split()]
    words = [w for w in words if w and w.upper() not in _STOP]
    if not words:
        return s[:maxlen].upper()
    if len(words) >= 2:
        return "".join(w[0] for w in words).upper()[:maxlen]
    return words[0][:maxlen].upper()
