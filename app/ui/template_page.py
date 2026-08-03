"""ひな形診断"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget, QMessageBox,
)

from ..config import TEMPLATES_DIR, DATA_DIR
from ..document_engine import inspect_template, resolve_template
from ..fields import CASE_TYPES, change_map


class TemplatePage(QWidget):
    def __init__(self, db_path=None):
        super().__init__()
        self.db_path = db_path
        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("種別:"))
        self.ctype = QComboBox()
        self.ctype.addItems(CASE_TYPES)
        top.addWidget(self.ctype)
        b = QPushButton("診断実行")
        b.clicked.connect(self._run)
        top.addWidget(b)
        top.addStretch(1)
        lay.addLayout(top)
        self.out = QTextEdit()
        self.out.setReadOnly(True)
        lay.addWidget(self.out)
        self.out.setPlainText(
            "data/templates/ に hinagata_*.xlsx（分割パッケージB）を置き、診断実行してください。\n"
            f"探索パス: {TEMPLATES_DIR}\n"
            f"変更マップ例 工事#1: {change_map('工事', 1)}\n"
            f"変更マップ例 業務#2: {change_map('業務', 2)}"
        )

    def _run(self):
        ct = self.ctype.currentText()
        path = resolve_template(ct)
        if not path:
            # try any xlsx
            cands = list(TEMPLATES_DIR.glob("*.xlsx")) + list((DATA_DIR / "templates").glob("*.xlsx"))
            path = cands[0] if cands else None
        if not path or not Path(path).exists():
            QMessageBox.warning(self, "診断", "ひな形が見つかりません（パッケージBを data/templates/ へ）。")
            return
        try:
            info = inspect_template(path)
        except Exception as e:
            QMessageBox.warning(self, "診断", str(e))
            return
        lines = [
            f"file: {info['file']}",
            f"sheets ({len(info['sheets'])}): {', '.join(info['sheets'][:20])}...",
            f"has_input: {info['has_input']}",
            f"ref_columns: {info['ref_columns']}",
            f"broken_names: {len(info['broken_names'])}",
            "",
            "--- 入力シート I/Q (抜粋) ---",
        ]
        for row in info.get("input_labels", [])[:40]:
            lines.append(f"R{row['row']}: {row['label']} | Q={row['Q']}")
        self.out.setPlainText("\n".join(lines))
