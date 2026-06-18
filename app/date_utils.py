"""date_utils.py — shared smart date parsing used across all screens."""
from __future__ import annotations
import re
from datetime import date


def parse_date(raw: str) -> str:
    """
    Convert user-typed short dates to YYYY-MM-DD.

    Accepted inputs (examples):
        26-10-05  → 2026-10-05
        05-10-26  → ambiguous — treated as DD-MM-YY → 2026-10-05
        26/10/05  → 2026-10-05
        05/10/2026→ 2026-10-05
        20261005  → 2026-10-05
        2026-10-05→ 2026-10-05  (pass-through)
    """
    s = raw.strip()
    if not s:
        return ""
    
    # Ignore placeholder text
    if s.upper() in ("YYYY-MM-DD", "DD-MM-YYYY", "MM-DD-YYYY"):
        return ""

    # already YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s

    # normalise separators
    s2 = re.sub(r"[/.]", "-", s)

    # DD-MM-YY  or  YY-MM-DD  (6-digit pieces)
    m = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{2})$", s2)
    if m:
        p1, p2, p3 = int(m.group(1)), int(m.group(2)), int(m.group(3))
        year = 2000 + p3
        # heuristic: if p1 > 31 treat as YY-MM-DD
        if p1 > 31:
            year = 2000 + p1
            return f"{year}-{p2:02d}-{p3:02d}"
        return f"{year}-{p2:02d}-{p1:02d}"

    # DD-MM-YYYY
    m = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{4})$", s2)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"

    # YYYYMMDD
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # YYYY-MM-DD with 4-digit year first (already handled above, but catch YY-MM-YYYY)
    return ""  # return empty string if unrecognised instead of raw input


def today_iso() -> str:
    return date.today().isoformat()


def month_start_iso() -> str:
    d = date.today()
    return d.replace(day=1).isoformat()
