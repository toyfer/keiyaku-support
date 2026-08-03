"""ルールエンジン代表ケース（ひな形不要）"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.rule_engine import evaluate_case, ippan_kyoso_target, kessai_kubun
from app.shikkou_text import build_shikkou_title, unit_total
from app.fields import change_map


def main():
    assert "総合評価" in ippan_kyoso_target(70_000_000, "工事")
    assert "一般競争" in ippan_kyoso_target(10_000_000, "工事")
    assert ippan_kyoso_target(5_000_000, "工事") == "—"
    assert kessai_kubun(50_000_000, "工事") == "市長"
    assert kessai_kubun(5_000_000, "工事") == "副市長"

    case = {
        "title": "庁舎複合機賃貸借",
        "fiscal_year": 2025,
        "case_type": "業務",
        "period_pattern": "長期継続契約",
        "contract_years": 5,
        "monthly_amount": 100_000,
        "annual_amount": 1_200_000,
        "total_budget": 6_000_000,
        "design_amount": 1_200_000,
        "contract_method": "指名競争入札（委員会）",
        "start_date": "令和7年4月1日",
    }
    r = evaluate_case(case)
    assert r["決裁判定額"] == "6,000,000円"
    assert any("4/1" in a for a in r["警告"])
    assert "長期継続" in build_shikkou_title(case)

    tanka = {
        "period_pattern": "単価契約",
        "case_type": "物品",
        "unit_price": 1000,
        "planned_quantity": 2500,
        "design_amount": 0,
        "contract_method": "単価契約",
    }
    assert unit_total(tanka) == 2_500_000
    rt = evaluate_case(tanka)
    assert rt["決裁判定額"] == "2,500,000円"

    assert change_map("工事", 1)["change_notice"] == "Q61"
    assert change_map("工事", 2)["change_notice"] == "Q78"
    assert change_map("業務", 5)["change_notice"] == "Q135"

    print("rules OK")
    print("ippan 70M:", ippan_kyoso_target(70_000_000, "工事"))
    print("long:", r["決裁判定額"], r["決裁区分"])
    print("tanka:", rt["決裁判定額"])


if __name__ == "__main__":
    main()
