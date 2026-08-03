"""保存・判定・生成前のバリデーション"""
from __future__ import annotations

from typing import Any

from .dates import is_april_first, parse_date


def _num(v: Any) -> int:
    if v is None or v == "":
        return 0
    try:
        return int(float(str(v).replace(",", "")))
    except (TypeError, ValueError):
        return 0


def validate_save(case: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not (case.get("title") or "").strip():
        errors.append("工事名・業務名は必須です")
    if not case.get("case_no"):
        warnings.append("案件番号が空です（自動採番されます）")
    if _num(case.get("design_amount")) <= 0 and _num(case.get("unit_price_total")) <= 0:
        warnings.append("設計金額（または単価総合計）が未入力です")
    if not case.get("supplier_name") and not case.get("supplier_id"):
        warnings.append("業者が未選択です")
    pat = case.get("period_pattern") or "単年度契約"
    if pat == "長期継続契約":
        years = _num(case.get("contract_years"))
        if years and years > 5:
            warnings.append("契約年数が5年を超えています（要確認）")
        if not (
            _num(case.get("total_budget"))
            or _num(case.get("annual_amount"))
            or _num(case.get("monthly_amount"))
        ):
            warnings.append("長期継続: 全体額・年額・月額のいずれかが望ましいです")
    if pat == "債務負担行為":
        total = _num(case.get("total_budget"))
        debt = _num(case.get("debt_limit"))
        current = _num(case.get("current_year_amount"))
        if total and debt and current and total > debt + current:
            errors.append(
                f"債務負担: 期間全体額({total:,})が限度額+当年度({debt + current:,})を超えています"
            )
        elif total and debt and not current and total > debt:
            warnings.append("債務負担: 当年度執行額が未入力で、全体額が限度額を超えている可能性があります")
    if pat == "単価契約" or case.get("contract_method") == "単価契約":
        if _num(case.get("unit_price")) and not case.get("planned_quantity"):
            warnings.append("単価契約: 予定数量が未入力です")
        if not _num(case.get("unit_price")) and not _num(case.get("unit_price_total")):
            warnings.append("単価契約: 単価または総合計を入力してください")
    return errors, warnings


def validate_judge(case: dict) -> tuple[list[str], list[str]]:
    errors, warnings = validate_save(case)
    method = case.get("contract_method") or ""
    mitsu = _num(case.get("mitsu_count"))
    if "指名競争" in method and 0 < mitsu < 5:
        warnings.append(f"指名人数が{mitsu}者です（原則5者以上）")
    if method in ("随意契約", "見積り合せ") and mitsu == 1:
        warnings.append("1者見積です。1者随契の理由書・根拠が必要です")
    if is_april_first(case.get("start_date")):
        pat = case.get("period_pattern") or ""
        if pat == "長期継続契約":
            warnings.append(
                "4/1開始の長期継続: 予定価格決定・入札・契約は4/1以降。準備は前年度に実施すること。"
            )
        if pat == "債務負担行為":
            warnings.append(
                "4/1開始の債務負担: 前年度に債務負担行為で契約すること（初年度未執行は失効）。"
            )
        if not case.get("prep_in_prior_year"):
            warnings.append("前年度準備完了フラグが未チェックです")
    start = parse_date(case.get("start_date"))
    end = parse_date(case.get("end_date"))
    if start and end and end < start:
        errors.append("工期・履行終了が開始より前です")
    return errors, warnings


def validate_generate(case: dict) -> tuple[list[str], list[str]]:
    errors, warnings = validate_judge(case)
    if not case.get("case_type"):
        errors.append("案件種別が未設定です")
    if not case.get("contract_date"):
        warnings.append("契約日が未入力です（帳票の契約日欄が空になります）")
    return errors, warnings
