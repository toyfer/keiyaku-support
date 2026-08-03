"""手続チェックリスト"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QAbstractItemView,
)

from ..case_service import ensure_checklist, list_cases
from ..checklist_data import checklist_for
from ..db import db_session

STATUSES = ["未着手", "作成中", "提出済", "承認済", "不要"]
STATUS_TO_DB = {"未着手": "pending", "作成中": "draft", "提出済": "submitted", "承認済": "approved", "不要": "na"}
DB_TO_STATUS = {v: k for k, v in STATUS_TO_DB.items()}


class ChecklistPage(QWidget):
    def __init__(self, db_path=None):
        super().__init__()
        self.db_path = db_path
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("案件:"))
        self.case_combo = QComboBox()
        self.case_combo.setMinimumWidth(420)
        self.case_combo.currentIndexChanged.connect(self.reload_docs)
        top.addWidget(self.case_combo, 1)
        for text, fn in [
            ("案件一覧を更新", self.reload_cases),
            ("チェックリスト再マージ", self._init_list),
            ("進捗を保存", self.save_progress),
        ]:
            b = QPushButton(text)
            b.clicked.connect(fn)
            top.addWidget(b)
        layout.addLayout(top)
        self.hint = QLabel("方法・期間パターン・変更回数に応じて項目が分岐します（done はマージで消えません）。")
        layout.addWidget(self.hint)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["順", "工程", "書類", "ステータス", "備考"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        self.summary = QLabel("")
        layout.addWidget(self.summary)
        self.reload_cases()

    def reload_cases(self):
        self.case_combo.blockSignals(True)
        cur = self.case_combo.currentData()
        cur_id = cur.get("id") if isinstance(cur, dict) else None
        self.case_combo.clear()
        self.case_combo.addItem("（案件を選択）", None)
        sel = 0
        try:
            cases = list_cases(self.db_path)
        except Exception:
            cases = []
        for i, c in enumerate(cases, start=1):
            label = f"{c.get('case_no')} | {c.get('case_type')} | {c.get('period_pattern') or '単年度'} | {c.get('title')}"
            self.case_combo.addItem(label, c)
            if cur_id and c.get("id") == cur_id:
                sel = i
        if sel == 0 and self.case_combo.count() > 1:
            sel = 1
        self.case_combo.setCurrentIndex(sel)
        self.case_combo.blockSignals(False)
        self.reload_docs()

    def reload_docs(self):
        case = self.case_combo.currentData()
        self.table.setRowCount(0)
        self.summary.setText("")
        if not case:
            return
        ctype = case.get("case_type") or "工事"
        pat = case.get("period_pattern") or "単年度契約"
        ensure_checklist(
            case["id"], ctype, self.db_path, pat,
            contract_method=case.get("contract_method"),
            design_amount=int(case.get("design_amount") or 0),
            change_no=int(case.get("change_no") or 0),
            start_date=case.get("start_date"),
            force_merge=True,
        )
        with db_session(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM case_documents WHERE case_id=? ORDER BY order_no, id", (case["id"],)
            ).fetchall()
        self.table.setRowCount(len(rows))
        done = 0
        for r, row in enumerate(rows):
            st = DB_TO_STATUS.get(row["status"], row["status"] or "未着手")
            if st in ("提出済", "承認済", "不要"):
                done += 1
            self.table.setItem(r, 0, QTableWidgetItem(str(row["order_no"] or "")))
            self.table.setItem(r, 1, QTableWidgetItem(row["recipient"] or ""))
            self.table.setItem(r, 2, QTableWidgetItem(row["doc_name"] or ""))
            combo = QComboBox()
            combo.addItems(STATUSES)
            i = combo.findText(st)
            if i >= 0:
                combo.setCurrentIndex(i)
            self.table.setCellWidget(r, 3, combo)
            self.table.setItem(r, 4, QTableWidgetItem(""))
            self.table.item(r, 0).setData(256, row["id"])  # UserRole
        self.summary.setText(f"進捗: {done}/{len(rows)}")

    def _init_list(self):
        self.reload_docs()
        QMessageBox.information(self, "CL", "チェックリストを再マージしました")

    def save_progress(self):
        case = self.case_combo.currentData()
        if not case:
            return
        with db_session(self.db_path) as conn:
            for r in range(self.table.rowCount()):
                doc_id = self.table.item(r, 0).data(256)
                combo = self.table.cellWidget(r, 3)
                st = STATUS_TO_DB.get(combo.currentText(), "pending") if combo else "pending"
                conn.execute("UPDATE case_documents SET status=? WHERE id=?", (st, doc_id))
        QMessageBox.information(self, "保存", "進捗を保存しました")
        self.reload_docs()
