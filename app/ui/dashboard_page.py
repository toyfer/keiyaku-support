"""ダッシュボード"""
from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget, QMessageBox

from ..export_service import dashboard_stats, export_cases_csv


class DashboardPage(QWidget):
    def __init__(self, db_path=None):
        super().__init__()
        self.db_path = db_path
        lay = QVBoxLayout(self)
        self.info = QLabel("")
        self.info.setWordWrap(True)
        lay.addWidget(self.info)
        row = QHBoxLayout()
        b1 = QPushButton("再集計")
        b1.clicked.connect(self.reload)
        b2 = QPushButton("案件CSV出力")
        b2.clicked.connect(self._csv)
        row.addWidget(b1)
        row.addWidget(b2)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addStretch(1)
        self.reload()

    def reload(self):
        try:
            s = dashboard_stats(self.db_path)
        except Exception as e:
            self.info.setText(f"DB未初期化またはエラー: {e}\n\ndata/keiyaku.db を配置するか、起動時に空DBが作成されます。")
            return
        lines = [
            f"案件件数: {s['件数']}",
            f"設計額合計: {s['設計額合計']:,} 円",
            f"契約額合計: {s['契約額合計']:,} 円",
            "",
            "【ステータス別】",
        ]
        for k, v in (s.get("ステータス別") or {}).items():
            lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append("【種別別】")
        for k, v in (s.get("種別別") or {}).items():
            lines.append(f"  {k}: {v}")
        self.info.setText("\n".join(lines))

    def _csv(self):
        try:
            p = export_cases_csv(self.db_path)
            QMessageBox.information(self, "CSV", f"出力しました:\n{p}")
        except Exception as e:
            QMessageBox.warning(self, "CSV", str(e))
