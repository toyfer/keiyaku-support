"""様式検索"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QAbstractItemView,
)

from ..db import db_session


class FormSearchPage(QWidget):
    def __init__(self, db_path=None):
        super().__init__()
        self.db_path = db_path
        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("検索:"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("様式名・番号")
        self.search.textChanged.connect(self.reload)
        top.addWidget(self.search, 1)
        lay.addLayout(top)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "分類", "番号", "名称", "種別"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        lay.addWidget(self.table)
        self.hint = QLabel("様式メタは DB（分割パッケージD）。実ファイルは source_path を参照。")
        lay.addWidget(self.hint)
        self.reload()

    def reload(self):
        q = self.search.text().strip()
        try:
            with db_session(self.db_path) as conn:
                if q:
                    rows = conn.execute(
                        "SELECT f.id, c.name cat, f.seq_no, f.name, f.file_type "
                        "FROM forms f LEFT JOIN categories c ON c.id=f.category_id "
                        "WHERE f.name LIKE ? OR f.full_name LIKE ? OR f.seq_no LIKE ? "
                        "ORDER BY f.id LIMIT 300",
                        (f"%{q}%", f"%{q}%", f"%{q}%"),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT f.id, c.name cat, f.seq_no, f.name, f.file_type "
                        "FROM forms f LEFT JOIN categories c ON c.id=f.category_id "
                        "ORDER BY f.id LIMIT 300"
                    ).fetchall()
        except Exception:
            rows = []
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, v in enumerate([row["id"], row["cat"], row["seq_no"], row["name"], row["file_type"]]):
                self.table.setItem(r, c, QTableWidgetItem("" if v is None else str(v)))
