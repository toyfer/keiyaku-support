"""案件フィールド定義（GUI・DB・帳票マップの単一ソース）

I列=ラベル / Q列=値。変更契約はストライド17で動的生成。
工事 base=61 / 業務 base=67 / 物品は BUPPIN_MAP（Phase2）。
"""
from __future__ import annotations

CASE_TYPES = ["工事", "業務", "建設業務", "物品", "プロポーザル"]
METHODS = [
    "一般競争入札",
    "総合評価一般競争入札",
    "指名競争入札（委員会）",
    "指名競争入札（部長選定）",
    "随意契約",
    "見積り合せ",
    "プロポーザル",
    "単価契約",
    "長期継続契約",
]
STATUSES = [
    ("draft", "下書き"),
    ("executing", "執行中"),
    ("change", "変更中"),
    ("completed", "完了"),
    ("closed", "閉件"),
]
ZUII_CATEGORIES = ["工事請負", "財産買入", "物件借入", "財産売払", "物件貸付", "その他"]
PERIOD_PATTERNS = ["単年度契約", "長期継続契約", "債務負担行為", "単価契約"]

FIELD_DEFS = [
    ("case_no", "案件番号", "text", "基本"),
    ("fiscal_year", "年度", "int", "基本"),
    ("case_type", "案件種別", "combo_case", "基本"),
    ("contract_method", "契約方法", "combo_method", "基本"),
    ("period_pattern", "契約期間パターン", "combo_period", "基本"),
    ("contract_years", "契約年数（長期・債務）", "int", "基本"),
    ("shikkou_title", "執行伺表題（自動/編集可）", "text", "基本"),
    ("amount_display", "金額段書き（自動/編集可）", "text", "基本"),
    ("budget_display", "予算表示（自動/編集可）", "text", "基本"),
    ("starts_on_april1", "4月1日開始", "bool", "基本"),
    ("prep_in_prior_year", "前年度準備完了", "bool", "基本"),
    ("total_budget", "期間全体予定額（税込）", "money", "金額"),
    ("annual_amount", "年額（長期・単価）", "money", "金額"),
    ("monthly_amount", "月額（長期）", "money", "金額"),
    ("debt_limit", "債務負担行為限度額", "money", "金額"),
    ("current_year_amount", "当年度執行額（税込）", "money", "金額"),
    ("unit_price", "単価（税込）", "money", "金額"),
    ("planned_quantity", "予定数量", "float", "金額"),
    ("quantity_unit", "数量単位", "text", "金額"),
    ("unit_price_total", "単価×数量 総合計（税込）", "money", "金額"),
    ("title", "工事名・業務名", "text", "基本"),
    ("title_line2", "名称（2行目・任意）", "text", "基本"),
    ("location", "場所", "text", "基本"),
    ("department", "担当課", "text", "基本"),
    ("manager", "事務担当", "text", "基本"),
    ("request_date", "依頼日", "date", "基本"),
    ("view_method", "閲覧方法", "text", "基本"),
    ("designer", "設計者", "text", "基本"),
    ("design_amount", "設計金額（税込）", "money", "金額"),
    ("tax_rate", "消費税率", "rate", "金額"),
    ("estimated_price", "予定価格（税込）", "money", "金額"),
    ("contract_amount", "契約額（税込）", "money", "金額"),
    ("design_amount_text", "設計額（表示用・任意）", "text", "金額"),
    ("advance_payment_rate", "前払金率", "rate", "金額"),
    ("advance_payment_amount", "前払金額", "money", "金額"),
    ("contract_date", "契約日", "date", "契約"),
    ("start_date", "工期・履行開始", "date", "契約"),
    ("end_date", "工期・履行終了", "date", "契約"),
    ("period_text", "工期表示文言（任意）", "text", "契約"),
    ("advance_payment", "前払金あり", "bool", "契約"),
    ("chuukan_maebarai", "中間前払金あり", "bool", "契約"),
    ("guarantee_flag", "契約保証金あり", "bool", "契約"),
    ("dekidaka", "出来高払あり", "bool", "契約"),
    ("recycle", "リサイクル法対象", "bool", "契約"),
    ("supplier_id", "業者ID", "int", "業者"),
    ("supplier_name", "業者名", "text", "業者"),
    ("supplier_address", "業者住所", "text", "業者"),
    ("supplier_rep", "代表者名", "text", "業者"),
    ("mitsu_count", "見積・指名人数", "int", "業者"),
    ("zuii_category", "随契区分", "combo_zuii", "業者"),
    ("budget_kan", "款", "text", "予算"),
    ("budget_ko", "項", "text", "予算"),
    ("budget_moku", "目", "text", "予算"),
    ("budget_setsu", "節", "text", "予算"),
    ("budget_saisho", "細節", "text", "予算"),
    ("budget_allocated", "配当予算現額", "money", "予算"),
    ("budget_executed", "執行済額", "money", "予算"),
    ("notice_no", "職員通知文書番号", "text", "監督"),
    ("soukatsu", "統括監督員・統括調査職員", "text", "監督"),
    ("shunin", "主任監督員・主任調査職員", "text", "監督"),
    ("kantoku", "監督員・調査職員", "text", "監督"),
    ("supervisor", "監督員（表示用）", "text", "監督"),
    ("staff_change_date", "監督員変更通知日", "date", "監督"),
    ("staff_change_notice_no", "監督員変更文書番号", "text", "監督"),
    ("soukatsu_after", "変更後・統括", "text", "監督"),
    ("shunin_after", "変更後・主任", "text", "監督"),
    ("kantoku_after", "変更後・監督/調査", "text", "監督"),
    ("bid_date", "入札日", "date", "入札"),
    ("notice_date", "落札・決定通知日", "date", "入札"),
    ("view_period", "閲覧期間", "text", "入札"),
    ("view_start", "閲覧開始日", "date", "入札"),
    ("view_end", "閲覧終了日", "date", "入札"),
    ("view_time_start", "閲覧開始時間", "text", "入札"),
    ("view_time_end", "閲覧終了時間", "text", "入札"),
    ("view_place", "閲覧場所", "text", "入札"),
    ("question_deadline", "質問受付期限", "date", "入札"),
    ("shimei_shinsei_date", "指名審議 申出日", "date", "入札"),
    ("shinsa_kaigi_date", "契業審 開催日", "date", "入札"),
    ("bid_place", "入札場所", "text", "入札"),
    ("bid_time", "入札開始時間", "text", "入札"),
    ("bid_executor", "入札執行者", "text", "入札"),
    ("completion_date", "完了日", "date", "検査"),
    ("inspect_notice", "検査通知日", "date", "検査"),
    ("inspect_date", "検査日", "date", "検査"),
    ("inspect_staff", "検査員", "text", "検査"),
    ("inspect_result_dt", "検査結果通知日", "date", "検査"),
    ("inspect_result", "検査結果", "text", "検査"),
    ("delivery_date", "引渡日", "date", "検査"),
    ("accept_date", "引受日", "date", "検査"),
    ("rating", "評定点", "int", "検査"),
    ("change_no", "変更回数", "int", "変更"),
    ("change_notice", "変更協議通知日", "date", "変更"),
    ("change_explain", "変更等説明日時", "text", "変更"),
    ("change_kessai_date", "変更契約締結伺日", "date", "変更"),
    ("change_date", "変更契約日", "date", "変更"),
    ("change_dir", "増減区分（増/減/増減）", "text", "変更"),
    ("change_amount", "変更増減額（税込）", "money", "変更"),
    ("change_end_date", "変更後工期・履行終了", "date", "変更"),
    ("status", "ステータス", "combo_status", "基本"),
]

DB_COLUMNS = [k for k, *_ in FIELD_DEFS]

WORKS_MAP = {
    "title_q1": "Q1", "title_q2": "Q2", "location": "Q3", "request_date": "Q5",
    "design_amount_label": "Q6", "contract_method": "Q7", "view_method": "Q8",
    "soukatsu": "Q9", "manager": "Q10", "designer": "Q11",
    "advance_payment_label": "Q12", "gikai_label": "Q13", "dekidaka_label": "Q14",
    "recycle_label": "Q15", "design_ex": "Q16", "estimated_ex": "Q19",
    "contract_date": "Q22", "period_start": "Q23", "period_end": "Q24", "end_date": "Q24",
    "contract_ex": "Q25", "advance_payment_amount": "Q29", "chuukan_label": "Q30",
    "supplier_address": "Q31", "supplier_name": "Q32", "supplier_rep": "Q33",
    "budget_kan": "Q34", "budget_ko": "Q35", "budget_moku": "Q36",
    "budget_setsu": "Q37", "budget_saisho": "Q38",
    "budget_allocated": "Q39", "budget_executed": "Q40",
    "notice_no": "Q43", "notice_no_q": "Q43", "soukatsu2": "Q44",
    "shunin": "Q45", "kantoku": "Q46",
    "staff_change_date": "Q47", "staff_change_notice_no": "Q48",
    "soukatsu_after": "Q49", "shunin_after": "Q50", "kantoku_after": "Q51",
    "completion_date": "Q52", "inspect_notice": "Q53", "inspect_date": "Q54",
    "inspect_staff": "Q55", "inspect_result_dt": "Q56", "inspect_result": "Q57",
    "delivery_date": "Q58", "accept_date": "Q59",
    "change_notice": "Q61", "change_explain": "Q62", "change_kessai_date": "Q63",
    "change_date": "Q64", "change_dir": "Q65", "change_amount_ex": "Q66",
    "change_end_date": "Q72",
}

GYOMU_MAP = {
    "title_q1": "Q1", "title": "Q2", "location": "Q3", "bid_executor": "Q4",
    "shimei_shinsei_date": "Q5", "shinsa_kaigi_date": "Q6",
    "period_start": "Q7", "period_end": "Q8", "end_date": "Q8",
    "notice_date": "Q9", "view_start": "Q10", "view_end": "Q11",
    "view_time_start": "Q12", "view_time_end": "Q13", "view_place": "Q14",
    "question_deadline": "Q15", "bid_date": "Q16", "bid_time": "Q17", "bid_place": "Q18",
    "advance_payment_label2": "Q19", "saitei_label": "Q20",
    "design_ex": "Q21", "estimated_ex": "Q24", "contract_date": "Q27",
    "start_date": "Q28", "contract_ex": "Q30",
    "advance_payment_amount": "Q34", "chuukan_label": "Q35",
    "supplier_address": "Q36", "supplier_name": "Q37", "supplier_rep": "Q38",
    "budget_kan": "Q39", "budget_ko": "Q40", "budget_moku": "Q41",
    "budget_setsu": "Q42", "budget_saisho": "Q43",
    "budget_allocated": "Q44", "budget_executed": "Q45",
    "notice_no": "Q48", "soukatsu": "Q49", "shunin": "Q50", "kantoku": "Q51",
    "staff_change_date": "Q54", "staff_change_notice_no": "Q55",
    "soukatsu_after": "Q56", "shunin_after": "Q57", "kantoku_after": "Q58",
    "completion_date": "Q59", "inspect_notice": "Q60", "inspect_date": "Q61",
    "inspect_staff": "Q62", "inspect_result_dt": "Q63", "inspect_result": "Q64",
    "delivery_date": "Q65", "accept_date": "Q66",
    "change_notice": "Q67", "change_explain": "Q68", "change_kessai_date": "Q69",
    "change_date": "Q70", "change_dir": "Q71", "change_amount_ex": "Q72",
    "change_end_date": "Q78",
}

# Phase2: 物品ひな形 — 業務系に近い入力シートを想定。実機で inspect し差分調整。
BUPPIN_MAP = {
    "title_q1": "Q1", "title": "Q2", "location": "Q3",
    "bid_executor": "Q4", "period_start": "Q7", "period_end": "Q8",
    "notice_date": "Q9", "view_start": "Q10", "view_end": "Q11",
    "bid_date": "Q16", "bid_time": "Q17", "bid_place": "Q18",
    "design_ex": "Q21", "estimated_ex": "Q24",
    "contract_date": "Q27", "start_date": "Q28", "contract_ex": "Q30",
    "supplier_address": "Q36", "supplier_name": "Q37", "supplier_rep": "Q38",
    "budget_kan": "Q39", "budget_ko": "Q40", "budget_moku": "Q41",
    "budget_setsu": "Q42", "budget_saisho": "Q43",
    "budget_allocated": "Q44", "budget_executed": "Q45",
    "completion_date": "Q59", "delivery_date": "Q65", "accept_date": "Q66",
}

TEMPLATE_FILES = {
    "工事": "templates/hinagata_koji.xlsx",
    "業務": "templates/hinagata_gyomu.xlsx",
    "建設業務": "templates/hinagata_kensetsu_gyomu.xlsx",
    "物品": "templates/hinagata_buppin.xlsx",
}

WORKS_CHANGE_BASE, WORKS_CHANGE_STRIDE = 61, 17
GYOMU_CHANGE_BASE, GYOMU_CHANGE_STRIDE = 67, 17
CHANGE_MAX = 5

WORKS_CHANGE_OFFSETS = {
    "change_notice": 0, "change_explain": 1, "change_kessai_date": 2,
    "change_date": 3, "change_dir": 4, "change_amount_ex": 5,
    "change_end_date": 11, "budget_allocated": 12, "budget_executed": 13,
}
GYOMU_CHANGE_OFFSETS = {**WORKS_CHANGE_OFFSETS, "design_delta_ex": 14}
WORKS_FORMULA_REL = (6, 7, 8, 9, 10, 14, 15, 16)
GYOMU_FORMULA_REL = (6, 7, 8, 9, 10, 15, 16)


def _change_params(case_type: str) -> tuple[int, int, dict]:
    if case_type == "工事":
        return WORKS_CHANGE_BASE, WORKS_CHANGE_STRIDE, WORKS_CHANGE_OFFSETS
    return GYOMU_CHANGE_BASE, GYOMU_CHANGE_STRIDE, GYOMU_CHANGE_OFFSETS


def change_map(case_type: str, change_no: int) -> dict[str, str]:
    if not (1 <= int(change_no) <= CHANGE_MAX):
        raise ValueError(f"change_no must be 1..{CHANGE_MAX}")
    # 物品は変更ブロックが薄い → 業務オフセット流用
    ct = "工事" if case_type == "工事" else "業務"
    base, stride, offsets = _change_params(ct)
    start = base + (int(change_no) - 1) * stride
    return {k: f"Q{start + off}" for k, off in offsets.items()}


def change_write_cells(case_type: str, change_no: int) -> list[str]:
    return list(change_map(case_type, change_no).values())


def all_change_write_cells(case_type: str) -> list[str]:
    cells = []
    for n in range(1, CHANGE_MAX + 1):
        cells.extend(change_write_cells(case_type, n))
    return cells


def build_formula_cells(case_type: str) -> set[str]:
    if case_type == "工事":
        base_fixed = {"Q17", "Q18", "Q20", "Q21", "Q26", "Q27", "Q28", "Q41", "Q42", "Q60"}
        base, stride, rel = WORKS_CHANGE_BASE, WORKS_CHANGE_STRIDE, WORKS_FORMULA_REL
    else:
        base_fixed = {"Q22", "Q23", "Q25", "Q26", "Q29", "Q31", "Q32", "Q33", "Q46", "Q47"}
        base, stride, rel = GYOMU_CHANGE_BASE, GYOMU_CHANGE_STRIDE, GYOMU_FORMULA_REL
    cells = set(base_fixed)
    for n in range(CHANGE_MAX):
        start = base + n * stride
        for off in rel:
            cells.add(f"Q{start + off}")
    return cells


FORMULA_CELLS_WORKS = build_formula_cells("工事")
FORMULA_CELLS_GYOMU = build_formula_cells("業務")
FORMULA_CELLS_BUPPIN = build_formula_cells("業務")  # 近似


def map_type_for(case_type: str) -> str:
    if case_type == "工事":
        return "工事"
    if case_type == "物品":
        return "物品"
    return "業務"


def cell_map_for(case_type: str) -> dict:
    mt = map_type_for(case_type)
    if mt == "工事":
        return WORKS_MAP
    if mt == "物品":
        return BUPPIN_MAP
    return GYOMU_MAP


def formula_cells_for(case_type: str) -> set:
    mt = map_type_for(case_type)
    if mt == "工事":
        return FORMULA_CELLS_WORKS
    if mt == "物品":
        return FORMULA_CELLS_BUPPIN
    return FORMULA_CELLS_GYOMU
