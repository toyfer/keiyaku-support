"""契約方法別の推奨帳票シート・必須項目プロファイル"""
from __future__ import annotations

METHOD_PROFILES: dict[str, dict] = {
    "一般競争入札": {
        "preferred_sheets": {
            "工事": ["事業執行伺", "入札公告内容 担当課内申（一般競争）", "予定価格"],
            "業務": ["事業執行伺 (業務)", "予定価格", "閲覧調書", "入札調書"],
            "default": ["事業執行伺", "予定価格"],
        },
        "checklist_variant": "ippan",
    },
    "総合評価一般競争入札": {
        "preferred_sheets": {
            "工事": ["事業執行伺", "入札公告内容 担当課内申 (総合評価)", "予定価格"],
            "default": ["事業執行伺", "予定価格"],
        },
        "checklist_variant": "ippan",
    },
    "指名競争入札（委員会）": {
        "preferred_sheets": {
            "工事": ["事業執行伺", "指名調書", "予定価格", "監督員(主任入り)"],
            "業務": ["事業執行伺 (業務)", "指名調書", "予定価格"],
            "default": ["事業執行伺", "指名調書", "予定価格"],
        },
        "checklist_variant": "shimei",
    },
    "指名競争入札（部長選定）": {
        "preferred_sheets": {"default": ["事業執行伺", "指名調書", "予定価格"]},
        "checklist_variant": "shimei",
    },
    "随意契約": {
        "preferred_sheets": {"default": ["事業執行伺"]},
        "checklist_variant": "zuii",
        "city_forms": ["見積書"],
    },
    "見積り合せ": {
        "preferred_sheets": {"default": ["事業執行伺"]},
        "checklist_variant": "mitsumori",
        "city_forms": ["見積書", "見積り合せ辞退届"],
    },
    "プロポーザル": {
        "preferred_sheets": {"default": ["事業執行伺"]},
        "checklist_variant": "proposal",
    },
    "単価契約": {
        "preferred_sheets": {"default": ["事業執行伺", "予定価格"]},
        "checklist_variant": "tanka",
    },
    "長期継続契約": {
        "preferred_sheets": {"default": ["事業執行伺"]},
        "checklist_variant": "shimei",
    },
}


def profile_for(method: str | None) -> dict:
    return METHOD_PROFILES.get(method or "", {
        "preferred_sheets": {"default": ["事業執行伺"]},
        "checklist_variant": "shimei",
    })


def preferred_sheets(method: str | None, case_type: str | None) -> list[str]:
    prof = profile_for(method)
    sheets = prof.get("preferred_sheets") or {}
    return list(sheets.get(case_type or "", sheets.get("default", [])))


def checklist_variant(method: str | None) -> str:
    return profile_for(method).get("checklist_variant") or "shimei"


def recommended_city_forms(method: str | None, case_type: str | None) -> list[str]:
    """templates_excel 側の市様式キー（form_templates と対応）。"""
    prof = profile_for(method)
    keys = list(prof.get("city_forms") or [])
    if case_type == "物品":
        keys = [k + "_物品" if not k.endswith("物品") else k for k in keys] or ["見積書_物品", "入札書_物品"]
    elif case_type in ("業務", "建設業務"):
        keys = keys or ["見積書_業務", "入札書_業務"]
    return keys
