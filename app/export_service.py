"""CSV/Excelエクスポート・ダッシュボード集計"""
from __future__ import annotations

import csv
from pathlib import Path

from .config import OUTPUT_DIR
from .db import db_session


def export_cases_csv(db_path=None, out: Path | None = None) -> Path:
    out = Path(out or (OUTPUT_DIR / "案件一覧.csv"))
    out.parent.mkdir(parents=True, exist_ok=True)
    with db_session(db_path) as conn:
        rows = conn.execute("SELECT * FROM cases ORDER BY id DESC").fetchall()
        cols = [d[0] for d in conn.execute("SELECT * FROM cases LIMIT 0").description] if False else (
            list(rows[0].keys()) if rows else ["case_no", "title"]
        )
        if rows:
            cols = list(dict(rows[0]).keys())
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(dict(r))
    return out


def export_suppliers_csv(db_path=None, out: Path | None = None) -> Path:
    out = Path(out or (OUTPUT_DIR / "業者一覧.csv"))
    out.parent.mkdir(parents=True, exist_ok=True)
    with db_session(db_path) as conn:
        rows = conn.execute("SELECT * FROM suppliers ORDER BY supplier_code").fetchall()
        cols = list(dict(rows[0]).keys()) if rows else ["supplier_code", "name"]
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(dict(r))
    return out


def dashboard_stats(db_path=None) -> dict:
    with db_session(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) c FROM cases").fetchone()["c"]
        by_status = conn.execute(
            "SELECT status, COUNT(*) c FROM cases GROUP BY status"
        ).fetchall()
        by_type = conn.execute(
            "SELECT case_type, COUNT(*) c FROM cases GROUP BY case_type"
        ).fetchall()
        amt = conn.execute(
            "SELECT COALESCE(SUM(contract_amount),0) a, COALESCE(SUM(design_amount),0) d FROM cases"
        ).fetchone()
        return {
            "件数": total,
            "ステータス別": {r["status"]: r["c"] for r in by_status},
            "種別別": {r["case_type"]: r["c"] for r in by_type},
            "契約額合計": int(amt["a"] or 0),
            "設計額合計": int(amt["d"] or 0),
        }
