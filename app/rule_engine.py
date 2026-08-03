"""ルールエンジン: 決裁区分・随意契約・根拠条文・期間パターン・警告

根拠: 東松島市 契約事務ガイドブック(R7.4.1) / 決裁区分一覧(R7) / 財規114・115
"""
from __future__ import annotations

from datetime import date, timedelta

from .dates import is_april_first
from .shikkou_text import build_amount_display, build_shikkou_title, unit_total
from .template_profile import preferred_sheets

THRESHOLDS = {
    "kessai_mayor_koji": 30_000_000,
    "kessai_fuku_koji": 3_000_000,
    "kessai_bucho": 500_000,
    "kessai_mayor_other": 10_000_000,
    "kessai_fuku_other": 2_000_000,
    "shinsa_koji": 3_000_000,
    "shinsa_other": 2_000_000,
    "saitei_koji": 10_000_000,
    "saitei_gyomu": 5_000_000,
    "keiyakusho_koji": 2_000_000,
    "keiyakusho_other": 1_000_000,
    "ukesho_other": 300_000,
    "hoshokin": 2_000_000,
    "jimu_inin_koji": 2_000_000,
    "kaikei_goui": 1_000_000,
    "gikai_ketsugi_koji": 150_000_000,
    "gikai_hokoku_koji": 30_000_000,
    "gikai_buppin": 20_000_000,
    "kensa_koji": 2_000_000,
    "seiseki": 3_000_000,
    "ippan_koji": 10_000_000,
    "sogo_koji": 70_000_000,
    "yotei_chosho": 300_000,
    "tanka_shinsa": 2_000_000,
    "mitsumori_hi": 50_000_000,
    "mitsumori_mid": 5_000_000,
}

ZUII_RANGE = {
    "工事請負": 2_000_000, "財産買入": 1_500_000, "物件借入": 800_000,
    "財産売払": 500_000, "物件貸付": 300_000, "その他": 1_000_000,
}


def kessai_kubun(amount: int, case_type: str = "工事") -> str:
    amount = int(amount or 0)
    if case_type == "工事":
        if amount >= THRESHOLDS["kessai_mayor_koji"]:
            return "市長"
        if amount >= THRESHOLDS["kessai_fuku_koji"]:
            return "副市長"
        if amount >= THRESHOLDS["kessai_bucho"]:
            return "部長（教育次長、議会事務局長）"
        return "課長"
    if amount >= THRESHOLDS["kessai_mayor_other"]:
        return "市長"
    if amount >= THRESHOLDS["kessai_fuku_other"]:
        return "副市長"
    if amount >= THRESHOLDS["kessai_bucho"]:
        return "部長（教育次長、議会事務局長）"
    return "課長"


def henko_kessai_amount(design_amount: int, change_amount: int) -> int:
    d, c = int(design_amount or 0), int(change_amount or 0)
    return d + c if c > 0 else d


def shinsa_committee(amount: int, case_type: str = "工事") -> bool:
    amount = int(amount or 0)
    return amount >= (THRESHOLDS["shinsa_koji"] if case_type == "工事" else THRESHOLDS["shinsa_other"])


def zuii_range(category: str) -> int:
    return ZUII_RANGE.get(category, 1_000_000)


def zuii_judge(amount: int, category: str = "その他") -> dict:
    amount = int(amount or 0)
    limit = zuii_range(category)
    return {
        "範囲額": limit,
        "判定": "範囲内" if amount <= limit else "範囲外",
        "根拠": f"東松島市財務規則第114条（{category} {limit:,}円）",
    }


def mitsumori_period(amount: int) -> dict:
    amount = int(amount or 0)
    if amount >= THRESHOLDS["mitsumori_hi"]:
        return {"閲覧期間": "3日以上", "見積期間": "15日以上", "短縮": "5日以内に限り短縮可", "見積日数": 15, "閲覧日数": 3}
    if amount >= THRESHOLDS["mitsumori_mid"]:
        return {"閲覧期間": "2日以上", "見積期間": "10日以上", "短縮": "5日以内に限り短縮可", "見積日数": 10, "閲覧日数": 2}
    return {"閲覧期間": "1日以上", "見積期間": "1日以上", "短縮": "短縮可", "見積日数": 1, "閲覧日数": 1}


def add_business_days(start: date, days: int) -> date:
    if days <= 0:
        return start
    d, left = start, days
    while left > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            left -= 1
    return d


def saitei_genka(amount: int, case_type: str = "工事") -> bool:
    amount = int(amount or 0)
    if case_type == "工事":
        return amount >= THRESHOLDS["saitei_koji"]
    if case_type in ("建設業務", "業務"):
        return amount >= THRESHOLDS["saitei_gyomu"]
    return False


def keiyakusho_omission(amount: int, case_type: str = "工事") -> str:
    amount = int(amount or 0)
    if case_type == "工事":
        return "契約書の作成を要する" if amount >= THRESHOLDS["keiyakusho_koji"] else "契約書の作成を省略可（請書等に準じる書面を要する）"
    if amount >= THRESHOLDS["keiyakusho_other"]:
        return "契約書の作成を要する"
    if amount >= THRESHOLDS["ukesho_other"]:
        return "契約書の作成を省略可（請書等に準じる書面を要する）"
    return "契約書及び請書等の作成を省略可"


def yotei_kakaku_chosho(amount: int) -> str:
    if int(amount or 0) > THRESHOLDS["yotei_chosho"]:
        return "予定価格調書を作成（入札日当日の午前9時までに財政課へ提出）"
    return "予定価格調書の作成を省略可（執行伺に予定価格を記載）"


def gikai(estimated_price: int, case_type: str = "工事") -> str:
    p = int(estimated_price or 0)
    if case_type == "工事" and p >= THRESHOLDS["gikai_ketsugi_koji"]:
        return "議会の議決を要する（予定価格1億5,000万円以上）"
    if case_type == "工事" and p >= THRESHOLDS["gikai_hokoku_koji"]:
        return "契約締結後、直近の議会定例会で報告（予定価格3,000万円以上）"
    if case_type == "物品" and p >= THRESHOLDS["gikai_buppin"]:
        return "議会の議決を要する可能性（動産買入 予定価格2,000万円以上）"
    return "議会の議決・報告は不要"


def kensa_kubun(amount: int, case_type: str = "工事") -> str:
    amount = int(amount or 0)
    if case_type == "工事":
        return "工事検査監へ検査を依頼（契約金額200万円以上）" if amount >= THRESHOLDS["kensa_koji"] else "担当課で検査（課長補佐又は係長等）"
    return "担当課で検査（履行確認・完了検査復命書）"


def kensa_kigen(case_type: str = "工事") -> str:
    return "工事完成から14日以内" if case_type == "工事" else "業務完了の日から10日以内"


def seiseki_chosho(amount: int) -> bool:
    return int(amount or 0) >= THRESHOLDS["seiseki"]


def hoshokin(amount: int, case_type: str = "工事") -> str:
    amount = int(amount or 0)
    if amount >= THRESHOLDS["hoshokin"]:
        return "契約金額の10%以上（免除事由の確認要：財規第120条）"
    if amount <= 0:
        return "契約額未入力（200万円以上は10%、未満は免除）"
    return "契約保証金免除（200万円未満・免除届出書の提出要）"


def jimu_inin(amount: int, case_type: str = "工事") -> str:
    if case_type == "工事" and int(amount or 0) >= THRESHOLDS["jimu_inin_koji"]:
        return "財政課（管財契約係）へ契約事務依頼（設計金額200万円以上の建設工事）"
    return "担当課で契約事務を執行"


def kaikei_goui(contract_amount: int, case_type: str = "工事") -> str:
    if int(contract_amount or 0) >= THRESHOLDS["kaikei_goui"] and case_type in ("工事", "業務", "建設業務", "物品"):
        return "要（契約金額100万円以上：会計管理者合議）"
    return "不要"


def henko_judge(change_amount: int, contract_amount: int) -> dict:
    c, a = int(change_amount or 0), int(contract_amount or 0)
    if a <= 0:
        return {"30%判定": "契約額未入力", "50%判定": "契約額未入力", "変更率": "-"}
    ratio = abs(c) / a
    return {
        "30%判定": "30%超：新たな設計が必要（別契約）。分離困難時は理由書添付" if ratio > 0.3 else "30%以内：変更契約で対応可",
        "50%判定": "50%超：契約保証金の再徴収・保証書の提出要" if ratio > 0.5 else "50%以内：通常の変更手続",
        "変更率": f"{ratio:.1%}",
    }


def shimei_check(method: str, mitsu_count: int) -> str:
    m = int(mitsu_count or 0)
    if "指名競争" in (method or ""):
        if m >= 5:
            return f"OK（指名{m}者・原則5者以上）"
        if m > 0:
            return f"注意：指名{m}者（原則5者以上。登録業者が5者未満の場合を除く）"
        return "未設定（原則5者以上）"
    if method in ("随意契約", "見積り合せ"):
        if m >= 2:
            return f"OK（見積{m}者）"
        if m == 1:
            return "1者見積（1者随契の理由書・根拠が必要）"
        return "見積人数未設定"
    return "—"


def ippan_kyoso_target(amount: int, case_type: str) -> str:
    """7,000万を先に判定（バグ修正済み）。"""
    amount = int(amount or 0)
    if case_type == "工事":
        if amount >= THRESHOLDS["sogo_koji"]:
            return "総合評価一般競争の検討対象（設計金額7,000万円以上の土木等）"
        if amount >= THRESHOLDS["ippan_koji"]:
            return "一般競争入札の対象（設計金額1,000万円以上の建設工事）"
    return "—"


KONKYO_TEXTS = {
    "一般競争入札": (
        "契約締結については、地方自治法第２３４条第１項の規定により、一般競争入札にて執行したい。"
        "なお、入札参加資格等の決定については、東松島市契約業者審査委員会の審議結果により執行する。"
    ),
    "総合評価一般競争入札": (
        "契約締結については、地方自治法第２３４条第１項及び同法施行令第１６７条の１０の２第１項の規定により"
        "総合評価一般競争入札にて執行したい。なお、入札参加資格等の決定については東松島市契約業者審査委員会の"
        "審議結果によるものとし、落札者決定基準については同法施行令第１６７条の１０の２第３項及び東松島市"
        "総合評価落札方式実施要綱第５条第２項の規定により別に定め執行する。"
    ),
    "指名競争入札（委員会）": (
        "契約締結については、地方自治法第２３４条第２項、同法施行令第１６７条第（１～３）号の規定により、"
        "指名競争入札にて執行したい。また、業者の選定については、東松島市契約業者審査委員会の審議結果により執行する。"
    ),
    "指名競争入札（部長選定）": (
        "契約締結については、地方自治法第２３４条第２項、同法施行令第１６７条第（１～３）号の規定により、"
        "指名競争入札にて執行したい。なお、業者の選定については、別紙のとおり執行する。"
    ),
    "随意契約（範囲内・2者以上）": (
        "契約締結については、地方自治法第２３４条第２項、同法施行令第１６７条の２第１項第１号及び"
        "東松島市財務規則第１１４条第（１～６）号の規定による随意契約とし、同規則第１１５条の規定により"
        "（業者名（２者以上））から見積りを徴して執行する。"
    ),
    "随意契約（範囲内・1者）": (
        "契約締結については、地方自治法第２３４条第２項、同法施行令第１６７条の２第１項第１号及び"
        "東松島市財務規則第１１４条第（１～６）号の規定による随意契約とし、同規則第１１５条第１号キの規定により"
        "（業者名（１者））から見積りを徴して執行する。"
    ),
    "随意契約（範囲外・2者以上）": (
        "契約締結については、地方自治法第２３４条第２項、同法施行令第１６７条の２第１項第（２～９）号の規定により"
        "随意契約とし、東松島市財務規則第１１５条の規定により見積を徴して執行したい。"
        "なお、業者の選定については、別紙のとおり執行する。"
    ),
    "随意契約（範囲外・1者）": (
        "契約締結については、地方自治法第２３４条第２項、同法施行令第１６７条の２第１項第（２～９）号の規定による"
        "随意契約とし、東松島市財務規則第１１５条第１号（ア～カ）の規定により（業者名（１者））から見積を徴して執行する。"
    ),
    "随意契約（範囲外・見積なし）": (
        "契約締結については、地方自治法第２３４条第２項、同法施行令第１６７条の２第１項第１号及び"
        "東松島市財務規則第１１４条第（１～６）号の規定による随意契約とし、同規則第１１５条第２号（ア～エ）の規定により"
        "（業者名（１者））と契約締結して執行する。"
    ),
    "プロポーザル": (
        "本業務は、金額のみの判断とせず、優れた企画提案を募るため、東松島市プロポーザルガイドライン"
        "（平成２５年東松島市訓令甲第１３号）第２条第２項第（１～３）号の規定による○○型プロポーザル方式により"
        "事業者を選定する。契約については、東松島市○○○○プロポーザル審査委員会において決定された候補者と"
        "地方自治法施行令第１６７条の２第１項第２号の規定による随意契約により執行する。"
    ),
    "前金払": (
        "…当該経費は地方自治法施行令第１６３条第（１～７号、又は８号及び東松島市財務規則第７５条第１～３号）に"
        "該当することから前金払いするもの。"
    ),
}


def konkyo_text(method: str, amount: int = 0, category: str = "その他", mitsu_count: int = 2) -> str:
    if method in KONKYO_TEXTS and method not in ("随意契約", "見積り合せ"):
        if method in ("一般競争入札", "総合評価一般競争入札", "指名競争入札（委員会）", "指名競争入札（部長選定）", "プロポーザル"):
            return KONKYO_TEXTS[method]
    if method in ("随意契約", "見積り合せ"):
        inside = zuii_judge(amount, category)["判定"] == "範囲内"
        if inside:
            return KONKYO_TEXTS["随意契約（範囲内・2者以上）"] if mitsu_count >= 2 else KONKYO_TEXTS["随意契約（範囲内・1者）"]
        if mitsu_count <= 0:
            return KONKYO_TEXTS["随意契約（範囲外・見積なし）"]
        return KONKYO_TEXTS["随意契約（範囲外・2者以上）"] if mitsu_count >= 2 else KONKYO_TEXTS["随意契約（範囲外・1者）"]
    return "（契約方法を選択してください）"


def period_pattern_rules(case: dict) -> dict:
    pat = case.get("period_pattern") or "単年度契約"
    years = int(case.get("contract_years") or 0)
    design = int(case.get("design_amount") or 0)
    total = int(case.get("total_budget") or 0)
    annual = int(case.get("annual_amount") or 0)
    monthly = int(case.get("monthly_amount") or 0)
    debt = int(case.get("debt_limit") or 0)
    current = int(case.get("current_year_amount") or 0)

    if pat == "長期継続契約":
        base = total or (annual * max(years, 1)) or (monthly * 12 * max(years, 1)) or design
        notes = {
            "決裁の考え方": "決裁・委員会は契約期間全体の金額で判断（長期継続マニュアル）",
            "執行伺表記": "執行伺表題に（長期継続契約）を表記",
            "予定価格": "予定価格は原則 月額 または 年額（性質により選択）",
            "契約保証金": "物品借上: 月額(税込)×12の10% / 維持管理: 年額の10%",
            "契約書・特約": "金額に関わらず契約書作成。履行期間の後ろに（長期継続契約）。予算減額・削除時の解除特約が必要",
            "スケジュール": "予定価格決定・入札・契約締結は4月1日以降。4/1開始は準備を前年度に",
            "期間・限度": "契約期間は5年以内" + (" ⚠ 5年超は要確認" if years > 5 else ""),
        }
    elif pat == "債務負担行為":
        base = total or (debt + current) or design
        notes = {
            "決裁の考え方": "決裁は設計金額（通常どおり）。執行伺に債務負担である旨を明記",
            "執行伺表記": "表題例: （債）令和○年度 … 執行伺（債務負担行為）",
            "予定価格": "予算執行額は上段=当年度、下段=期間全体",
            "契約保証金": "通常の契約保証金ルールを適用",
            "契約書・特約": "初年度内に契約行為を執行。未執行なら効力消滅",
            "スケジュール": "予算要求→議会議決→執行",
            "期間・限度": "期間全体額は原則 債務負担限度額+現年度事業予算",
        }
    elif pat == "単価契約" or case.get("contract_method") == "単価契約":
        base = unit_total(case) or total or design
        sched = "個々の発注時に数量制限し予算超過を防ぐ"
        if base >= THRESHOLDS["tanka_shinsa"]:
            sched += " → 200万円以上のため委員会選定"
        notes = {
            "決裁の考え方": "決裁区分は単価ではなく予定数量×単価の総合計金額",
            "執行伺表記": "執行伺・仕様で予定調達総額（量）を明示",
            "予定価格": "単価のみ / 総合計 など実態に応じて",
            "契約保証金": "落札単価×予定数量を基準",
            "契約書・特約": "総量が決められる分割納品は単価契約ではない",
            "スケジュール": sched,
            "期間・限度": "必要最小限に留める",
        }
    else:
        base = design
        notes = {
            "決裁の考え方": "決裁は設計金額（通常どおり）",
            "執行伺表記": "通常の執行伺",
            "予定価格": "総額で予定価格を設定（原則）",
            "契約保証金": "通常の契約保証金ルール",
            "契約書・特約": "会計年度内の履行が原則",
            "スケジュール": "—",
            "期間・限度": "—",
        }

    return {
        "パターン": pat,
        "判定基準額": base,
        **notes,
        "年額": annual or None,
        "月額": monthly or None,
        "全体額": total or None,
        "債務負担限度額": debt or None,
        "当年度執行額": current or None,
    }


def kessai_base_amount(case: dict) -> int:
    return int(period_pattern_rules(case).get("判定基準額") or case.get("design_amount") or 0)


def _collect_alerts(case: dict) -> list[str]:
    alerts: list[str] = []
    pat = case.get("period_pattern") or "単年度契約"
    if is_april_first(case.get("start_date")) or case.get("starts_on_april1") in (1, True, "1"):
        if pat == "長期継続契約":
            alerts.append("4/1開始の長期継続: 予定価格決定・入札・契約は4/1以降。準備は前年度に実施すること。")
        if pat == "債務負担行為":
            alerts.append("4/1開始の債務負担: 前年度に債務負担行為で契約すること（初年度未執行は失効）。")
        if not case.get("prep_in_prior_year"):
            alerts.append("前年度準備完了フラグが未チェックです。")
    if pat == "長期継続契約" and int(case.get("contract_years") or 0) > 5:
        alerts.append("契約年数が5年を超えています（要確認）。")
    if pat == "債務負担行為":
        total = int(case.get("total_budget") or 0)
        debt = int(case.get("debt_limit") or 0)
        current = int(case.get("current_year_amount") or 0)
        if total and debt and current and total > debt + current:
            alerts.append(f"⚠ 期間全体額({total:,})が限度額+当年度({debt + current:,})を超えています。")
    return alerts


def evaluate_case(case: dict) -> dict:
    amount = int(case.get("design_amount") or 0)
    price = int(case.get("estimated_price") or amount or 0)
    contract = int(case.get("contract_amount") or 0)
    ctype = case.get("case_type") or "工事"
    method = case.get("contract_method") or ""
    mitsu = int(case.get("mitsu_count") or 2)
    category = case.get("zuii_category") or "その他"
    change_amt = int(case.get("change_amount") or 0)
    pat_rules = period_pattern_rules(case)
    base = int(pat_rules.get("判定基準額") or amount)
    keiyaku_base = contract if contract > 0 else amount
    henko_base = henko_kessai_amount(amount, change_amt)
    alerts = _collect_alerts(case)
    sheets = preferred_sheets(method, ctype)

    result = {
        "契約期間パターン": pat_rules,
        "決裁区分": kessai_kubun(base, ctype),
        "決裁判定額": f"{base:,}円",
        "変更時決裁区分": kessai_kubun(henko_base, ctype) if change_amt else "—",
        "変更時判定額": f"{henko_base:,}円（増額=変更後/減額=当初）" if change_amt else "—",
        "審査委員会": "要（審議申出は開催4日前まで）" if shinsa_committee(base, ctype) else "不要",
        "随意契約範囲": zuii_judge(amount, category)["判定"] if method in ("随意契約", "見積り合せ") else "—",
        "見積期間": mitsumori_period(amount),
        "最低制限価格": "設定" if saitei_genka(amount, ctype) else "設定不要",
        "契約書": keiyakusho_omission(keiyaku_base, ctype),
        "予定価格調書": yotei_kakaku_chosho(amount),
        "議会": gikai(price, ctype),
        "検査者": kensa_kubun(contract if contract else amount, ctype),
        "検査期限": kensa_kigen(ctype),
        "成績調書": "作成要（契約金額300万円以上）" if seiseki_chosho(contract if contract else amount) else "不要",
        "契約保証金": hoshokin(contract if contract else amount, ctype),
        "事務委任": jimu_inin(amount, ctype),
        "会計管理者合議": kaikei_goui(contract if contract else amount, ctype),
        "指名・見積人数": shimei_check(method, mitsu),
        "入札方式の目安": ippan_kyoso_target(amount, ctype),
        "変更判定": henko_judge(change_amt, contract if contract else amount),
        "根拠条文": konkyo_text(method, amount, category, mitsu),
        "執行伺表題": case.get("shikkou_title") or build_shikkou_title(case),
        "金額表示": case.get("amount_display") or build_amount_display(case),
        "推奨帳票シート": sheets,
        "警告": alerts,
        "根拠資料": "ガイドブックR7.4 / 決裁区分一覧R7 / 財規114・115",
    }
    pat = case.get("period_pattern") or "単年度契約"
    if pat == "長期継続契約":
        result["執行伺追記"] = "表題に（長期継続契約）。根拠に各年度執行予定額を参考併記。"
    elif pat == "債務負担行為":
        result["執行伺追記"] = "表題に（債）…（債務負担行為）。予算欄は当年度/全体を段書き。"
    elif pat == "単価契約" or method == "単価契約":
        result["執行伺追記"] = "予定調達総額（量）を仕様・執行伺で明示。総額で決裁・公表。"
        result["単価総合計"] = f"{unit_total(case):,}円"
    else:
        result["執行伺追記"] = "—"
    if case.get("advance_payment") in (1, True, "1"):
        result["前金払記載"] = KONKYO_TEXTS["前金払"]
    return result
