"""SQLiteデータベース初期化・接続・マイグレーション"""
import sqlite3
from contextlib import contextmanager

from .config import DB_PATH

SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE, name TEXT NOT NULL, sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS forms (
    id INTEGER PRIMARY KEY, category_id INTEGER NOT NULL REFERENCES categories(id),
    seq_no TEXT NOT NULL, name TEXT NOT NULL, full_name TEXT NOT NULL, description TEXT,
    file_type TEXT NOT NULL, source_path TEXT NOT NULL, is_template INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1, notes TEXT, UNIQUE (category_id, seq_no, name)
);
CREATE TABLE IF NOT EXISTS form_versions (
    id INTEGER PRIMARY KEY, form_id INTEGER NOT NULL REFERENCES forms(id) ON DELETE CASCADE,
    version_label TEXT NOT NULL, revision_date TEXT, file_path TEXT NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE (form_id, version_label)
);
CREATE TABLE IF NOT EXISTS workflow_stages (
    id INTEGER PRIMARY KEY, case_type TEXT NOT NULL, stage_code TEXT NOT NULL,
    stage_name TEXT NOT NULL, sort_order INTEGER NOT NULL, UNIQUE (case_type, stage_code)
);
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY, supplier_code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, kana TEXT,
    representative TEXT, postal_code TEXT, address1 TEXT, address2 TEXT, area_code TEXT, city TEXT,
    phone TEXT, fax TEXT, license_no TEXT, license_date TEXT, is_active INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, employee_no TEXT UNIQUE, name TEXT NOT NULL, department TEXT,
    role TEXT NOT NULL DEFAULT 'user', is_active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY, case_no TEXT UNIQUE NOT NULL, fiscal_year INTEGER,
    case_type TEXT NOT NULL, contract_method TEXT, period_pattern TEXT DEFAULT '単年度契約',
    contract_years INTEGER, total_budget INTEGER, annual_amount INTEGER, monthly_amount INTEGER,
    debt_limit INTEGER, current_year_amount INTEGER, title TEXT NOT NULL, title_line2 TEXT,
    location TEXT, department TEXT, manager TEXT, request_date TEXT, view_method TEXT, designer TEXT,
    supplier_id INTEGER REFERENCES suppliers(id), supplier_name TEXT, supplier_address TEXT, supplier_rep TEXT,
    design_amount INTEGER, tax_rate REAL DEFAULT 0.10, estimated_price INTEGER, contract_amount INTEGER,
    contract_date TEXT, start_date TEXT, end_date TEXT, advance_payment INTEGER DEFAULT 0,
    chuukan_maebarai INTEGER DEFAULT 0, guarantee_flag INTEGER DEFAULT 0, dekidaka INTEGER DEFAULT 0,
    recycle INTEGER DEFAULT 0, budget_kan TEXT, budget_ko TEXT, budget_moku TEXT, budget_setsu TEXT,
    budget_saisho TEXT, budget_item TEXT, budget_allocated INTEGER, budget_executed INTEGER,
    notice_no TEXT, soukatsu TEXT, shunin TEXT, kantoku TEXT, supervisor TEXT, inspector TEXT,
    bid_date TEXT, notice_date TEXT, view_period TEXT, bid_place TEXT, completion_date TEXT,
    inspect_notice TEXT, inspect_date TEXT, inspect_staff TEXT, inspect_result_dt TEXT, inspect_result TEXT,
    rating INTEGER, delivery_date TEXT, accept_date TEXT, change_no INTEGER DEFAULT 0,
    change_notice TEXT, change_explain TEXT, change_kessai_date TEXT, change_date TEXT, change_dir TEXT,
    change_amount INTEGER DEFAULT 0, change_end_date TEXT, mitsu_count INTEGER DEFAULT 2,
    zuii_category TEXT DEFAULT 'その他', status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS case_documents (
    id INTEGER PRIMARY KEY, case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    form_id INTEGER REFERENCES forms(id), version_id INTEGER REFERENCES form_versions(id),
    doc_name TEXT NOT NULL, order_no INTEGER, file_path TEXT, status TEXT NOT NULL DEFAULT 'pending',
    submitted_at TEXT, recipient TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS case_stage_progress (
    id INTEGER PRIMARY KEY, case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    stage_id INTEGER NOT NULL REFERENCES workflow_stages(id), started_at TEXT, completed_at TEXT, note TEXT,
    UNIQUE (case_id, stage_id)
);
CREATE TABLE IF NOT EXISTS case_changes (
    id INTEGER PRIMARY KEY, case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    change_no INTEGER NOT NULL, change_date TEXT, amount_delta INTEGER, new_contract_amount INTEGER,
    new_end_date TEXT, reason TEXT, status TEXT NOT NULL DEFAULT 'pending',
    UNIQUE (case_id, change_no)
);
CREATE TABLE IF NOT EXISTS inspections (
    id INTEGER PRIMARY KEY, case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    inspect_type TEXT NOT NULL, requested_at TEXT, inspect_at TEXT, inspector TEXT,
    result TEXT, rating INTEGER, delivered_at TEXT, accepted_at TEXT
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), action TEXT NOT NULL,
    target_type TEXT, target_id INTEGER, detail TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_forms_category ON forms(category_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_docs_case ON case_documents(case_id);
"""

SEED_SQL = """
INSERT OR IGNORE INTO categories (code, name, sort_order) VALUES
    ('01', '工事関係', 1), ('02', '業務関係', 2), ('03', 'プロポーザル関係', 3),
    ('04', '物品印刷', 4), ('05', '施行関係書類一式（R6～）', 5), ('06', '見積り合せ（R6～）', 6),
    ('98', '例規・資料', 98), ('99', 'ひな形形式', 99);
INSERT OR IGNORE INTO workflow_stages (case_type, stage_code, stage_name, sort_order) VALUES
    ('工事', 'EXEC', '執行伺', 1), ('工事', 'SHIMEI', '指名', 2), ('工事', 'NYUSATSU', '入札', 3),
    ('工事', 'KEIYAKU', '契約', 4), ('工事', 'POST', '契約後提出', 5), ('工事', 'HENKO', '変更契約', 8),
    ('工事', 'KANSEI', '完成検査', 9), ('工事', 'SEIKYU', '請求・支払', 10),
    ('業務', 'EXEC', '執行伺', 1), ('業務', 'SHIMEI', '指名', 2), ('業務', 'NYUSATSU', '入札', 3),
    ('業務', 'KEIYAKU', '契約', 4), ('業務', 'POST', '契約後及び履行', 5), ('業務', 'HENKO', '変更契約', 6),
    ('業務', 'KANSEI', '完了検査', 7), ('業務', 'SEIKYU', '請求・支払', 8),
    ('物品', 'EXEC', '執行伺', 1), ('物品', 'KEIYAKU', '契約', 4), ('物品', 'KANSEI', '検収', 5), ('物品', 'SEIKYU', '請求・支払', 6);
"""

_MIGRATE_COLS = [
    ("request_date", "TEXT"), ("view_method", "TEXT"), ("designer", "TEXT"),
    ("supplier_address", "TEXT"), ("supplier_rep", "TEXT"),
    ("chuukan_maebarai", "INTEGER DEFAULT 0"), ("dekidaka", "INTEGER DEFAULT 0"), ("recycle", "INTEGER DEFAULT 0"),
    ("budget_kan", "TEXT"), ("budget_ko", "TEXT"), ("budget_moku", "TEXT"), ("budget_setsu", "TEXT"), ("budget_saisho", "TEXT"),
    ("notice_no", "TEXT"), ("soukatsu", "TEXT"), ("shunin", "TEXT"), ("kantoku", "TEXT"),
    ("view_period", "TEXT"), ("bid_place", "TEXT"), ("inspect_notice", "TEXT"), ("inspect_staff", "TEXT"),
    ("inspect_result_dt", "TEXT"), ("accept_date", "TEXT"),
    ("change_notice", "TEXT"), ("change_explain", "TEXT"), ("change_kessai_date", "TEXT"),
    ("change_date", "TEXT"), ("change_dir", "TEXT"), ("zuii_category", "TEXT DEFAULT 'その他'"),
    ("period_pattern", "TEXT DEFAULT '単年度契約'"), ("title_line2", "TEXT"),
    ("bid_executor", "TEXT"), ("bid_time", "TEXT"), ("view_end", "TEXT"), ("view_start", "TEXT"),
    ("period_text", "TEXT"), ("design_amount_text", "TEXT"),
    ("contract_years", "INTEGER"), ("total_budget", "INTEGER"), ("annual_amount", "INTEGER"),
    ("monthly_amount", "INTEGER"), ("debt_limit", "INTEGER"), ("current_year_amount", "INTEGER"),
    ("design_amount_ex", "INTEGER"), ("estimated_price_ex", "INTEGER"), ("contract_amount_ex", "INTEGER"),
    ("change_amount_ex", "INTEGER"),
    ("unit_price", "INTEGER"), ("planned_quantity", "REAL"), ("quantity_unit", "TEXT"), ("unit_price_total", "INTEGER"),
    ("shikkou_title", "TEXT"), ("budget_display", "TEXT"), ("amount_display", "TEXT"),
    ("starts_on_april1", "INTEGER DEFAULT 0"), ("prep_in_prior_year", "INTEGER DEFAULT 0"),
    ("shimei_shinsei_date", "TEXT"), ("shinsa_kaigi_date", "TEXT"),
    ("view_time_start", "TEXT"), ("view_time_end", "TEXT"), ("view_place", "TEXT"), ("question_deadline", "TEXT"),
    ("advance_payment_amount", "INTEGER"), ("advance_payment_rate", "REAL DEFAULT 0.4"),
    ("staff_change_date", "TEXT"), ("staff_change_notice_no", "TEXT"),
    ("soukatsu_after", "TEXT"), ("shunin_after", "TEXT"), ("kantoku_after", "TEXT"),
]

_CHANGE_MIGRATE_COLS = [
    ("change_notice", "TEXT"), ("change_explain", "TEXT"), ("change_kessai_date", "TEXT"),
    ("change_dir", "TEXT"), ("amount_delta_ex", "INTEGER"),
    ("budget_allocated", "INTEGER"), ("budget_executed", "INTEGER"),
    ("design_delta_ex", "INTEGER"), ("note", "TEXT"),
]


def get_conn(db_path=None):
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _migrate_changes(conn):
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(case_changes)")}
    except Exception:
        return
    if not cols:
        return
    for name, typedef in _CHANGE_MIGRATE_COLS:
        if name not in cols:
            try:
                conn.execute(f"ALTER TABLE case_changes ADD COLUMN {name} {typedef}")
            except Exception:
                pass


def _migrate(conn):
    cols = {r[1] for r in conn.execute("PRAGMA table_info(cases)")}
    for name, typedef in _MIGRATE_COLS:
        if name not in cols:
            try:
                conn.execute(f"ALTER TABLE cases ADD COLUMN {name} {typedef}")
            except sqlite3.OperationalError:
                pass
    _migrate_changes(conn)


def init_db(db_path=None):
    conn = get_conn(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.executescript(SEED_SQL)
        _migrate(conn)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def db_session(db_path=None):
    conn = get_conn(db_path)
    try:
        _migrate(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def log_action(conn, action, target_type=None, target_id=None, detail=None, user_id=None):
    conn.execute(
        "INSERT INTO audit_log (user_id, action, target_type, target_id, detail) VALUES (?,?,?,?,?)",
        (user_id, action, target_type, target_id, detail),
    )
