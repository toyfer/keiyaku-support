"""和暦・ISO日付のパースとExcel向け値変換"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

_WAREKI = re.compile(
    r"(令和|平成|昭和)\s*(\d+|元)\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日"
)
_ISO = re.compile(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})")
_ERA_START = {"令和": 2018, "平成": 1988, "昭和": 1925}


def parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    if not s:
        return None
    m = _WAREKI.search(s)
    if m:
        era, yraw, mo, d = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
        y = 1 if yraw == "元" else int(yraw)
        year = _ERA_START[era] + y
        try:
            return date(year, mo, d)
        except ValueError:
            return None
    m = _ISO.fullmatch(s) or _ISO.search(s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    for fmt in ("%Y年%m月%d日", "%Y.%m.%d", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def to_excel_value(value: Any):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    d = parse_date(value)
    if d:
        return datetime(d.year, d.month, d.day)
    return str(value).strip()


def is_april_first(value: Any) -> bool:
    d = parse_date(value)
    return bool(d and d.month == 4 and d.day == 1)


def fiscal_wareki(year: int | None) -> str:
    if not year:
        return ""
    try:
        y = int(year)
    except (TypeError, ValueError):
        return str(year)
    reiwa = y - 2018
    if reiwa >= 1:
        return f"令和{reiwa}年度"
    return f"{y}年度"


def format_yen(n: int | float | None) -> str:
    if n is None or n == "":
        return ""
    try:
        return f"{int(n):,}円"
    except (TypeError, ValueError):
        return str(n)
