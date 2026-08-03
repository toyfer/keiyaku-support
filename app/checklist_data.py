"""手続チェックリスト定義（工事・業務＋方法・パターン分岐）"""
from __future__ import annotations

from .dates import is_april_first
from .template_profile import checklist_variant

CHECKLIST = {
    "工事": [
        (1, "執行伺", "執行伺"),
        (2, "指名", "契約事務依頼書（200万円以上）"),
        (3, "指名", "業者の指名等について（通知）"),
        (4, "指名", "指名通知"),
        (5, "入札", "現場説明閲覧調書"),
        (6, "入札", "質問回答書"),
        (7, "入札", "予定価格調書"),
        (8, "入札", "入札調書"),
        (9, "入札", "落札決定通知書"),
        (10, "契約", "消費税に係る届出書"),
        (11, "契約", "契約保証に関する届出書・免除届出書"),
        (12, "契約", "契約締結伺"),
        (13, "契約", "契約書"),
        (14, "契約", "契約締結報告"),
        (15, "契約後提出", "現場代理人等通知書"),
        (16, "契約後提出", "着手届及び工事工程表"),
        (17, "契約後提出", "監督職員通知書"),
        (18, "契約後提出", "建設業退職金共済組合証紙購入状況報告書"),
        (19, "完成検査", "完成届"),
        (20, "完成検査", "工事完成検査依頼"),
        (21, "完成検査", "工事完成検査復命書"),
        (22, "完成検査", "検査結果通知書"),
        (23, "完成検査", "工事目的物引渡書"),
        (24, "完成検査", "請負工事成績評定通知書"),
        (25, "請求・支払", "請求書"),
    ],
    "業務": [
        (1, "執行伺", "予算執行伺"),
        (2, "指名", "指名通知・見積依頼通知"),
        (3, "入札", "見積書（2者以上）"),
        (4, "入札", "予定価格調書"),
        (5, "入札", "入札調書・見積り合せ調書"),
        (6, "契約", "契約締結伺"),
        (7, "契約", "契約書・請書"),
        (8, "契約後及び履行", "着手届及び業務工程表（10日以内）"),
        (9, "契約後及び履行", "管理技術者・照査技術者通知書"),
        (10, "契約後及び履行", "調査職員通知書"),
        (11, "完了検査", "業務完了報告書"),
        (12, "完了検査", "完了検査復命書"),
        (13, "完了検査", "完了検査結果通知書"),
        (14, "完了検査", "業務成果物引渡書"),
        (15, "請求・支払", "請求書"),
    ],
}

_IPPAN_KOJI = [
    (2, "公告", "入札公告内容_担当課内申"),
    (3, "公告", "入札公告"),
    (4, "入札", "現場説明閲覧調書"),
]
_MITSUMORI_KOJI = [
    (3, "見積", "見積り合せ通知"),
    (4, "見積", "見積参加者名簿"),
    (8, "見積", "見積り合せ調書"),
]
_MITSUMORI_GYOMU = [
    (2, "見積", "見積依頼通知"),
    (3, "見積", "見積書（2者以上）"),
    (5, "見積", "見積り合せ調書"),
]

PATTERN_EXTRA = {
    "単年度契約": [],
    "長期継続契約": [
        (901, "長期継続", "執行伺表題に（長期継続契約）表記"),
        (902, "長期継続", "全体額・年額/月額・当年度額の段書き"),
        (903, "長期継続", "予定価格を月額または年額で設定"),
        (904, "長期継続", "契約書に（長期継続契約）・予算減額削除時解除特約"),
        (905, "長期継続", "予定価格決定・入札・契約は4月1日以降"),
        (906, "長期継続", "契約期間5年以内の確認"),
    ],
    "債務負担行為": [
        (911, "債務負担", "執行伺表題に（債）…（債務負担行為）"),
        (912, "債務負担", "当年度執行額と期間全体額の併記"),
        (913, "債務負担", "全体額が限度額+現年度を超えないこと"),
        (914, "債務負担", "初年度内の契約執行（未執行は失効）"),
        (915, "債務負担", "4/1開始の場合は前年度に債務負担で契約"),
    ],
    "単価契約": [
        (921, "単価契約", "予定調達総額（量）を執行伺・仕様に明示"),
        (922, "単価契約", "決裁は単価×予定数量の総合計"),
        (923, "単価契約", "個々の発注時の数量制限・予算管理"),
        (924, "単価契約", "総額200万円以上は審査委員会"),
        (925, "単価契約", "分割納品の総価契約と誤用していないか確認"),
    ],
}

CHANGE_EXTRA = [
    (801, "変更契約", "変更協議書"),
    (802, "変更契約", "事業執行伺（変更）"),
    (803, "変更契約", "変更契約締結伺"),
    (804, "変更契約", "変更契約書"),
    (805, "変更契約", "工程表変更届（工事）"),
]

APRIL1_EXTRA = [
    (930, "年度跨ぎ", "4/1開始: 前年度準備の実施確認"),
    (931, "年度跨ぎ", "4/1以降の予定価格決定・入札・契約"),
]


def _replace_by_order(base: list, replacements: list) -> list:
    by_order = {o: (o, s, d) for o, s, d in base}
    for o, s, d in replacements:
        by_order[o] = (o, s, d)
    return [by_order[k] for k in sorted(by_order)]


def checklist_for(
    case_type: str,
    period_pattern: str = "単年度契約",
    contract_method: str | None = None,
    design_amount: int = 0,
    change_no: int = 0,
    start_date: str | None = None,
    prep_in_prior_year=None,
) -> list[tuple[int, str, str]]:
    if case_type == "工事":
        base = list(CHECKLIST["工事"])
    else:
        base = list(CHECKLIST["業務"])

    variant = checklist_variant(contract_method)
    if case_type == "工事":
        if variant == "ippan":
            base = _replace_by_order(base, _IPPAN_KOJI)
        elif variant in ("mitsumori", "zuii"):
            base = _replace_by_order(base, _MITSUMORI_KOJI)
        if design_amount and int(design_amount) < 2_000_000:
            base = [x for x in base if "契約事務依頼書" not in x[2]]
    else:
        if variant in ("mitsumori", "zuii"):
            base = _replace_by_order(base, _MITSUMORI_GYOMU)

    extra = list(PATTERN_EXTRA.get(period_pattern or "単年度契約") or [])
    if period_pattern != "単価契約" and contract_method == "単価契約":
        extra = list(PATTERN_EXTRA["単価契約"])

    if int(change_no or 0) >= 1:
        extra = extra + list(CHANGE_EXTRA)
        if case_type != "工事":
            extra = [x for x in extra if "工程表変更届" not in x[2]]

    if is_april_first(start_date):
        extra = extra + list(APRIL1_EXTRA)

    return base + extra
