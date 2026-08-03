"""業者マスタ"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QAbstractItemView,
)

from ..case_service import list_suppliers


class SupplierPage(QWidget):
    def __init__(self, db_path=None):
        super().__init__()
        self.db_path = db_path
        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("検索:"))
        self.search = QLineEdit()
        self.search.textChanged.connect(self.reload)
        top.addWidget(self.search, 1)
        lay.addLayout(top)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "CD", "業者名", "代表者", "住所", "電話"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        lay.addWidget(self.table)
        self.reload()

    def reload(self):
        try:
            rows = list_suppliers(self.db_path, self.search.text().strip())
        except Exception:
            rows = []
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            addr = " ".join(filter(None, [row.get("address1"), row.get("address2")]))
            for c, v in enumerate([
                row.get("id"), row.get("supplier_code"), row.get("name"),
                row.get("representative"), addr, row.get("phone"),
            ]):
                self.table.setItem(r, c, QTableWidgetItem("" if v is None else str(v)))
