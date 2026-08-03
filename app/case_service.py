"""案件の保存・読込・帳票用値・変更契約・チェックリスト"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .checklist_data import checklist_for
from .dates import is_april_first, to_excel_value
from .db import db_session, log_action
from .fields import CHANGE_MAX, DB_COLUMNS, FIELD_DEFS
from .rule_engine import evaluate_case, gikai, saitei_genka
from .shikkou_text import build_amount_display, build_design_amount_label, build_shikkou_title, unit_total
from .validation import validate_generate, validate_judge, validate_save


def _num(n: Any) -> int | None:
    if n is None or n == "":
        return None
    try:
        return int(float(str(n).replace(",", "")))
    except (TypeError, ValueError):
        return None


def _float(n: Any) -> float | None:
    if n is None or n == "":
        return None
    try:
        return float(str(n).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _bool_label(v: Any, yes="有", no="無") -> str:
    if v in (1, True, "1", "true", "True", "あり", "行う", "有"):
        return yes
    return no


def to_exclusive(amount_in, amount_ex, rate: float = 0.10):
    if amount_ex is not None:
        return int(amount_ex)
    if amount_in is None:
        return None
    if rate <= 0:
        return int(amount_in)
    return round(int(amount_in) / (1 + rate))


def split_title(title, line2=None):
    t = (title or "").strip()
    l2 = (line2 or "").strip()
    if l2:
        return t, l2
    if "\n" in t:
        a, b = t.split("\n", 1)
        return a.strip(), b.strip()
    return ("", t) if t else ("", "")


def build_export_values(case: dict, changes: list | None = None) -> dict:
    rate = float(case.get("tax_rate") or 0.10)
    design_in = _num(case.get("design_amount"))
    design_ex = to_exclusive(design_in, _num(case.get("design_amount_ex")), rate)
    estimated_in = _num(case.get("estimated_price")) or design_in
    estimated_ex = to_exclusive(estimated_in, _num(case.get("estimated_price_ex")), rate)
    contract_in = _num(case.get("contract_amount"))
    contract_ex = to_exclusive(contract_in, _num(case.get("contract_amount_ex")), rate)
    change_in = _num(case.get("change_amount")) or 0
    change_ex = to_exclusive(abs(change_in) if change_in else None, _num(case.get("change_amount_ex")), rate)
    ctype = case.get("case_type") or "工事"
    price = int(estimated_in or design_in or 0)
    start, end = case.get("start_date") or "", case.get("end_date") or ""
    case = dict(case)
    ut = unit_total(case)
    if ut and not case.get("unit_price_total"):
        case["unit_price_total"] = ut
    adv_amt = _num(case.get("advance_payment_amount"))
    if adv_amt is None and case.get("advance_payment") in (1, True, "1"):
        base_c = contract_in or design_in or 0
        if base_c:
            adv_amt = int(round(base_c * float(case.get("advance_payment_rate") or 0.4)))
    if is_april_first(start):
        case["starts_on_april1"] = 1
    if not case.get("shikkou_title"):
        case["shikkou_title"] = build_shikkou_title(case)
    if not case.get("amount_display"):
        case["amount_display"] = build_amount_display(case)
    pat = case.get("period_pattern") or "単年度契約"
    long_suffix = "（長期継続契約）" if pat == "長期継続契約" else ("（債務負担行為）" if pat == "債務負担行為" else "")
    vals = dict(case)
    fy = case.get("fiscal_year")
    try:
        q1_default = f"令和{int(fy)-2018}年度" if fy else ""
    except Exception:
        q1_default = str(fy or "")
    raw_title = (case.get("title") or "").strip()
    q1, q2 = split_title(raw_title, case.get("title_line2"))
    if not q1:
        if raw_title.startswith("令和"):
            q1, q2 = "", raw_title
        else:
            q1 = q1_default
    if not q2:
        q2 = raw_title
    if long_suffix and long_suffix not in q2:
        q2 = f"{q2}{long_suffix}" if q2 else long_suffix

    def _dv(v):
        return to_excel_value(v) if v not in (None, "") else None

    vals.update({
        "title_q1": q1, "title_q2": q2,
        "design_ex": design_ex, "estimated_ex": estimated_ex, "contract_ex": contract_ex,
        "design_amount_label": build_design_amount_label(case),
        "start_date": _dv(start), "end_date": _dv(end),
        "period_start": _dv(start) or start or None, "period_end": _dv(end) or end or None,
        "request_date": _dv(case.get("request_date")), "contract_date": _dv(case.get("contract_date")),
        "bid_date": _dv(case.get("bid_date")), "notice_date": _dv(case.get("notice_date")),
        "view_start": _dv(case.get("view_start")), "view_end": _dv(case.get("view_end")),
        "completion_date": _dv(case.get("completion_date")),
        "inspect_notice": _dv(case.get("inspect_notice")), "inspect_date": _dv(case.get("inspect_date")),
        "inspect_result_dt": _dv(case.get("inspect_result_dt")),
        "delivery_date": _dv(case.get("delivery_date")), "accept_date": _dv(case.get("accept_date")),
        "shimei_shinsei_date": _dv(case.get("shimei_shinsei_date")),
        "shinsa_kaigi_date": _dv(case.get("shinsa_kaigi_date")),
        "question_deadline": _dv(case.get("question_deadline")),
        "staff_change_date": _dv(case.get("staff_change_date")),
        "advance_payment_label": _bool_label(case.get("advance_payment"), "有", "無"),
        "advance_payment_label2": _bool_label(case.get("advance_payment"), "行う", "行わない"),
        "advance_payment_amount": adv_amt,
        "chuukan_label": "あり" if case.get("chuukan_maebarai") else "なし",
        "dekidaka_label": _bool_label(case.get("dekidaka"), "有", "無"),
        "recycle_label": _bool_label(case.get("recycle"), "有", "無"),
        "gikai_label": "有" if "議決" in gikai(price, ctype) else "無",
        "saitei_label": "設定する" if saitei_genka(int(design_in or 0), ctype) else "設定しない",
        "soukatsu2": case.get("soukatsu") or case.get("supervisor"),
        "soukatsu": case.get("soukatsu") or case.get("supervisor"),
        "shunin": case.get("shunin") or "",
        "kantoku": case.get("kantoku") or case.get("supervisor") or "",
        "budget_allocated": _num(case.get("budget_allocated")),
        "budget_executed": _num(case.get("budget_executed")) or 0,
        "change_amount_ex": change_ex,
        "change_dir": case.get("change_dir") or ("増" if change_in > 0 else ("減" if change_in < 0 else "")),
        "change_end_date": _dv(case.get("change_end_date")) or end or None,
        "change_notice": _dv(case.get("change_notice")),
        "change_kessai_date": _dv(case.get("change_kessai_date")),
        "change_date": _dv(case.get("change_date")),
        "inspect_result": case.get("inspect_result") or "",
        "inspect_staff": case.get("inspect_staff") or "",
        "notice_no_q": case.get("notice_no"),
        "view_time_start": case.get("view_time_start"),
        "view_time_end": case.get("view_time_end"),
        "view_place": case.get("view_place"),
        "staff_change_notice_no": case.get("staff_change_notice_no"),
        "soukatsu_after": case.get("soukatsu_after"),
        "shunin_after": case.get("shunin_after"),
        "kantoku_after": case.get("kantoku_after"),
        "title": case.get("title"),
    })
    chs = changes if changes is not None else (list_changes(case["id"]) if case.get("id") else [])
    norm = []
    for ch in chs or []:
        nc = dict(ch)
        delta = _num(ch.get("amount_delta"))
        delta_ex = _num(ch.get("amount_delta_ex"))
        if delta_ex is None and delta is not None:
            sign = 1 if delta >= 0 else -1
            delta_ex = sign * (to_exclusive(abs(delta), None, rate) or 0)
        nc["amount_delta_ex"] = delta_ex
        nc["change_amount_ex"] = abs(delta_ex) if delta_ex is not None else None
        for dk in ("change_notice", "change_kessai_date", "change_date", "new_end_date", "change_end_date"):
            if nc.get(dk):
                nc[dk] = to_excel_value(nc[dk])
        if not nc.get("change_end_date") and nc.get("new_end_date"):
            nc["change_end_date"] = nc["new_end_date"]
        if not nc.get("change_dir") and delta is not None:
            nc["change_dir"] = "増" if delta > 0 else ("減" if delta < 0 else "増減")
        norm.append(nc)
    vals["_changes"] = norm
    return vals


def list_cases(db_path=None, q: str = "") -> list[dict]:
    with db_session(db_path) as conn:
        if q:
            rows = conn.execute(
                "SELECT * FROM cases WHERE title LIKE ? OR case_no LIKE ? OR supplier_name LIKE ? "
                "OR IFNULL(department,'') LIKE ? ORDER BY id DESC LIMIT 500",
                (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM cases ORDER BY id DESC LIMIT 500").fetchall()
        return [dict(r) for r in rows]


def get_case(case_id: int, db_path=None) -> dict | None:
    with db_session(db_path) as conn:
        row = conn.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
        return dict(row) if row else None


def save_case(vals: dict, case_id: int | None = None, db_path=None) -> int:
    data = {k: vals.get(k) for k, *_ in FIELD_DEFS}
    for k, _, kind, _ in FIELD_DEFS:
        if kind == "bool":
            data[k] = 1 if data.get(k) in (1, True, "1", "true", "True", "あり", "行う") else 0
        if kind == "money" and data.get(k) in ("", None):
            data[k] = None
        if kind == "float":
            data[k] = _float(data.get(k))
        if kind == "int" and data.get(k) in ("", None):
            data[k] = 0 if k in ("fiscal_year", "mitsu_count", "change_no", "rating", "supplier_id") else None
    ut = unit_total(data)
    if ut:
        data["unit_price_total"] = ut
    if not data.get("shikkou_title"):
        data["shikkou_title"] = build_shikkou_title(data)
    if not data.get("amount_display"):
        data["amount_display"] = build_amount_display(data)
    if is_april_first(data.get("start_date")):
        data["starts_on_april1"] = 1
    if not data.get("case_no"):
        data["case_no"] = f"{datetime.now().year}-{datetime.now().strftime('%m%d%H%M%S')}"
    if not data.get("fiscal_year"):
        data["fiscal_year"] = datetime.now().year
    if not data.get("title"):
        raise ValueError("工事名・業務名は必須です")
    if not data.get("status"):
        data["status"] = "draft"
    if not data.get("period_pattern"):
        data["period_pattern"] = "単年度契約"
    if data.get("tax_rate") is None:
        data["tax_rate"] = 0.10
    if data.get("advance_payment_rate") is None:
        data["advance_payment_rate"] = 0.4
    if not data.get("supplier_id"):
        data["supplier_id"] = None
    cols = [k for k in DB_COLUMNS if k in data]
    new_id = case_id
    with db_session(db_path) as conn:
        existing = {r[1] for r in conn.execute("PRAGMA table_info(cases)")}
        cols = [c for c in cols if c in existing]
        if case_id:
            sets = ", ".join(f"{c}=?" for c in cols)
            conn.execute(
                f"UPDATE cases SET {sets}, updated_at=datetime('now','localtime') WHERE id=?",
                [data[c] for c in cols] + [case_id],
            )
            log_action(conn, "update", "case", case_id, data.get("title"))
        else:
            conn.execute(
                f"INSERT INTO cases ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                [data[c] for c in cols],
            )
            new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            log_action(conn, "create", "case", new_id, data.get("title"))
    ensure_checklist(
        new_id, data.get("case_type") or "工事", db_path,
        data.get("period_pattern") or "単年度契約",
        contract_method=data.get("contract_method"),
        design_amount=_num(data.get("design_amount")) or 0,
        change_no=int(data.get("change_no") or 0),
        start_date=data.get("start_date"),
        force_merge=True,
    )
    return new_id


def delete_case(case_id: int, db_path=None) -> None:
    with db_session(db_path) as conn:
        conn.execute("DELETE FROM case_changes WHERE case_id=?", (case_id,))
        conn.execute("DELETE FROM case_documents WHERE case_id=?", (case_id,))
        conn.execute("DELETE FROM cases WHERE id=?", (case_id,))
        log_action(conn, "delete", "case", case_id, None)


def list_changes(case_id: int, db_path=None) -> list[dict]:
    with db_session(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM case_changes WHERE case_id=? ORDER BY change_no", (case_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def save_change(case_id: int, ch: dict, db_path=None) -> int:
    n = int(ch.get("change_no") or 0)
    if not (1 <= n <= CHANGE_MAX):
        raise ValueError(f"変更回数は1〜{CHANGE_MAX}です")
    fields = {
        "change_date": ch.get("change_date"), "change_notice": ch.get("change_notice"),
        "change_explain": ch.get("change_explain"), "change_kessai_date": ch.get("change_kessai_date"),
        "change_dir": ch.get("change_dir"), "amount_delta": _num(ch.get("amount_delta")),
        "amount_delta_ex": _num(ch.get("amount_delta_ex")),
        "new_contract_amount": _num(ch.get("new_contract_amount")),
        "new_end_date": ch.get("new_end_date") or ch.get("change_end_date"),
        "budget_allocated": _num(ch.get("budget_allocated")),
        "budget_executed": _num(ch.get("budget_executed")),
        "design_delta_ex": _num(ch.get("design_delta_ex")),
        "reason": ch.get("reason"), "note": ch.get("note"),
        "status": ch.get("status") or "applied",
    }
    with db_session(db_path) as conn:
        existing_cols = {r[1] for r in conn.execute("PRAGMA table_info(case_changes)")}
        row = conn.execute(
            "SELECT id FROM case_changes WHERE case_id=? AND change_no=?", (case_id, n)
        ).fetchone()
        use = {k: v for k, v in fields.items() if k in existing_cols}
        if row:
            sets = ", ".join(f"{k}=?" for k in use)
            conn.execute(f"UPDATE case_changes SET {sets} WHERE id=?", list(use.values()) + [row["id"]])
            cid = row["id"]
        else:
            cols = ["case_id", "change_no"] + list(use.keys())
            conn.execute(
                f"INSERT INTO case_changes ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                [case_id, n] + list(use.values()),
            )
            cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        log_action(conn, "upsert", "case_change", cid, f"case={case_id} no={n}")
        latest = conn.execute(
            "SELECT * FROM case_changes WHERE case_id=? AND IFNULL(status,'')!='cancelled' "
            "ORDER BY change_no DESC LIMIT 1", (case_id,)
        ).fetchone()
        if latest:
            conn.execute(
                "UPDATE cases SET change_no=?, change_notice=?, change_explain=?, "
                "change_kessai_date=?, change_date=?, change_dir=?, change_amount=?, "
                "change_end_date=?, updated_at=datetime('now','localtime') WHERE id=?",
                (
                    latest["change_no"],
                    latest["change_notice"] if "change_notice" in latest.keys() else None,
                    latest["change_explain"] if "change_explain" in latest.keys() else None,
                    latest["change_kessai_date"] if "change_kessai_date" in latest.keys() else None,
                    latest["change_date"],
                    latest["change_dir"] if "change_dir" in latest.keys() else None,
                    latest["amount_delta"], latest["new_end_date"], case_id,
                ),
            )
    case = get_case(case_id, db_path)
    if case:
        ensure_checklist(
            case_id, case.get("case_type") or "工事", db_path,
            case.get("period_pattern") or "単年度契約",
            contract_method=case.get("contract_method"),
            design_amount=_num(case.get("design_amount")) or 0,
            change_no=int(case.get("change_no") or n), force_merge=True,
        )
    return cid


def delete_change(case_id: int, change_no: int, db_path=None) -> None:
    with db_session(db_path) as conn:
        conn.execute("DELETE FROM case_changes WHERE case_id=? AND change_no=?", (case_id, change_no))
        latest = conn.execute(
            "SELECT * FROM case_changes WHERE case_id=? ORDER BY change_no DESC LIMIT 1", (case_id,)
        ).fetchone()
        if latest:
            conn.execute(
                "UPDATE cases SET change_no=?, change_amount=?, change_date=?, change_end_date=? WHERE id=?",
                (latest["change_no"], latest["amount_delta"], latest["change_date"], latest["new_end_date"], case_id),
            )
        else:
            conn.execute(
                "UPDATE cases SET change_no=0, change_amount=0, change_notice=NULL, change_explain=NULL, "
                "change_kessai_date=NULL, change_date=NULL, change_dir=NULL, change_end_date=NULL WHERE id=?",
                (case_id,),
            )


def ensure_checklist(
    case_id, case_type, db_path=None, period_pattern="単年度契約",
    contract_method=None, design_amount=0, change_no=0, start_date=None,
    prep_in_prior_year=None, force_merge=False,
) -> int:
    items = checklist_for(
        case_type or "工事", period_pattern or "単年度契約",
        contract_method=contract_method, design_amount=design_amount or 0,
        change_no=change_no or 0, start_date=start_date,
        prep_in_prior_year=prep_in_prior_year,
    )
    with db_session(db_path) as conn:
        rows = conn.execute(
            "SELECT id, doc_name, status FROM case_documents WHERE case_id=?", (case_id,)
        ).fetchall()
        existing = {r["doc_name"]: dict(r) for r in rows}
        if existing and not force_merge:
            return len(existing)
        for order, stage, doc in items:
            if doc not in existing:
                conn.execute(
                    "INSERT INTO case_documents (case_id, doc_name, order_no, status, recipient) VALUES (?,?,?,?,?)",
                    (case_id, doc, order, "pending", stage),
                )
            else:
                conn.execute(
                    "UPDATE case_documents SET order_no=?, recipient=? WHERE id=?",
                    (order, stage, existing[doc]["id"]),
                )
        return conn.execute(
            "SELECT COUNT(*) c FROM case_documents WHERE case_id=?", (case_id,)
        ).fetchone()["c"]


def judge(case: dict) -> dict:
    result = evaluate_case(case)
    errors, warnings = validate_judge(case)
    result["バリデーションエラー"] = errors
    result["バリデーション警告"] = warnings
    alerts = list(result.get("警告") or [])
    alerts += [f"[error] {e}" for e in errors] + list(warnings)
    result["警告"] = alerts
    return result


def prepare_generate(case: dict, db_path=None):
    errors, warnings = validate_generate(case)
    changes = list_changes(case["id"], db_path) if case.get("id") else []
    values = build_export_values(case, changes)
    return values, changes, errors, warnings


def list_suppliers(db_path=None, q: str = "") -> list[dict]:
    with db_session(db_path) as conn:
        if q:
            rows = conn.execute(
                "SELECT * FROM suppliers WHERE name LIKE ? OR kana LIKE ? OR IFNULL(address1,'') LIKE ? "
                "ORDER BY supplier_code LIMIT 500", (f"%{q}%", f"%{q}%", f"%{q}%"),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM suppliers ORDER BY supplier_code LIMIT 500").fetchall()
        return [dict(r) for r in rows]


def get_supplier(supplier_id=None, code=None, db_path=None):
    with db_session(db_path) as conn:
        if supplier_id:
            row = conn.execute("SELECT * FROM suppliers WHERE id=?", (supplier_id,)).fetchone()
        elif code:
            row = conn.execute("SELECT * FROM suppliers WHERE supplier_code=?", (code,)).fetchone()
        else:
            return None
        return dict(row) if row else None
