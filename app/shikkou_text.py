"""執行伺の表題・金額段書きテキスト生成"""
from __future__ import annotations

from typing import Any

from .dates import fiscal_wareki, format_yen


def _num(v: Any) -> int:
    if v is None or v == "":
        return 0
    try:
        return int(float(str(v).replace(",", "")))
    except (TypeError, ValueError):
        return 0


def unit_total(case: dict) -> int:
    up = _num(case.get("unit_price"))
    try:
        qty = float(case.get("planned_quantity") or 0)
    except (TypeError, ValueError):
        qty = 0.0
    if up and qty:
        return int(round(up * qty))
    return _num(case.get("unit_price_total") or case.get("total_budget") or case.get("design_amount"))


def build_shikkou_title(case: dict) -> str:
    title = (case.get("title") or "").strip()
    fy = fiscal_wareki(case.get("fiscal_year"))
    pat = case.get("period_pattern") or "単年度契約"
    base = title
    if fy and title and not title.startswith("令和") and not title.startswith(str(case.get("fiscal_year") or "")):
        base = f"{fy} {title}"
    elif not title:
        base = fy or "執行伺"
    if pat == "長期継続契約":
        if "長期継続" not in base:
            return f"{base} 執行伺（長期継続契約）" if "執行伺" not in base else f"{base}（長期継続契約）"
        return base if "執行伺" in base else f"{base} 執行伺"
    if pat == "債務負担行為":
        head = base if base.startswith("（債）") else f"（債）{base}"
        if "債務負担" not in head:
            return f"{head} 執行伺（債務負担行為）" if "執行伺" not in head else f"{head}（債務負担行為）"
        return head if "執行伺" in head else f"{head} 執行伺"
    if pat == "単価契約":
        return base if "執行伺" in base else f"{base} 執行伺"
    return base if "執行伺" in base else f"{base} 執行伺"


def build_amount_display(case: dict) -> str:
    pat = case.get("period_pattern") or "単年度契約"
    if pat == "長期継続契約":
        monthly, annual, total = _num(case.get("monthly_amount")), _num(case.get("annual_amount")), _num(case.get("total_budget"))
        years = _num(case.get("contract_years"))
        parts = []
        if monthly:
            parts.append(f"月額 {format_yen(monthly)}")
        if annual:
            parts.append(f"年額 {format_yen(annual)}")
        if total:
            parts.append(f"期間全体 {format_yen(total)}" + (f"（{years}年）" if years else ""))
        if not parts:
            d = _num(case.get("design_amount"))
            return f"設計金額 {format_yen(d)}" if d else ""
        return " ／ ".join(parts)
    if pat == "債務負担行為":
        current, total, debt = _num(case.get("current_year_amount")), _num(case.get("total_budget")), _num(case.get("debt_limit"))
        if not total and (debt or current):
            total = debt + current
        parts = []
        if current:
            parts.append(f"当年度 {format_yen(current)}")
        if total:
            parts.append(f"期間全体 {format_yen(total)}")
        if not parts:
            d = _num(case.get("design_amount"))
            return f"設計金額 {format_yen(d)}" if d else ""
        return " ／ ".join(parts)
    if pat == "単価契約" or case.get("contract_method") == "単価契約":
        up, qty, unit, total = _num(case.get("unit_price")), case.get("planned_quantity"), case.get("quantity_unit") or "", unit_total(case)
        bits = []
        if up:
            bits.append(f"単価 {format_yen(up)}")
        if qty not in (None, ""):
            bits.append(f"予定数量 {qty}{unit}")
        if total:
            bits.append(f"総合計 {format_yen(total)}")
        return " ／ ".join(bits)
    d = _num(case.get("design_amount"))
    return f"設計金額 {format_yen(d)}" if d else ""


def build_budget_display(case: dict) -> str:
    pat = case.get("period_pattern") or "単年度契約"
    if pat in ("債務負担行為", "長期継続契約"):
        return build_amount_display(case)
    parts = [p for p in (case.get("budget_kan"), case.get("budget_ko"), case.get("budget_moku"), case.get("budget_setsu")) if p]
    return " / ".join(parts)


def build_design_amount_label(case: dict) -> str | None:
    pat = case.get("period_pattern") or "単年度契約"
    if pat == "長期継続契約":
        monthly, annual, total = _num(case.get("monthly_amount")), _num(case.get("annual_amount")), _num(case.get("total_budget"))
        if monthly:
            return f"月額 {monthly // 10000:,}万円" if monthly >= 10000 else f"月額 {monthly:,}円"
        if annual:
            return f"年額 {annual // 10000:,}万円" if annual >= 10000 else f"年額 {annual:,}円"
        if total:
            return f"全体 {total // 10000:,}万円" if total >= 10000 else f"全体 {total:,}円"
    if pat == "債務負担行為":
        return build_amount_display(case) or None
    if pat == "単価契約" or case.get("contract_method") == "単価契約":
        t = unit_total(case)
        if t:
            return f"{t // 10000:,}万円" if t >= 10000 else f"{t:,}円"
    design = _num(case.get("design_amount"))
    if case.get("design_amount_text"):
        return str(case.get("design_amount_text"))
    if design and design >= 10000:
        return f"{design // 10000:,}万円"
    if design:
        return str(design)
    return None
