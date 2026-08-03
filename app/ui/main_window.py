"""メインウィンドウ"""
from PySide6.QtWidgets import QMainWindow, QTabWidget

from .case_page import CaseListPage
from .checklist_page import ChecklistPage
from .dashboard_page import DashboardPage
from .form_page import FormSearchPage
from .supplier_page import SupplierPage
from .template_page import TemplatePage


class MainWindow(QMainWindow):
    def __init__(self, db_path=None):
        super().__init__()
        self.setWindowTitle("契約手続き支援システム")
        self.resize(1280, 820)
        tabs = QTabWidget()
        self.dashboard = DashboardPage(db_path)
        self.case_page = CaseListPage(db_path)
        self.checklist_page = ChecklistPage(db_path)
        self.form_page = FormSearchPage(db_path)
        self.supplier_page = SupplierPage(db_path)
        self.template_page = TemplatePage(db_path)
        tabs.addTab(self.dashboard, "ダッシュボード")
        tabs.addTab(self.case_page, "案件管理")
        tabs.addTab(self.checklist_page, "手続チェックリスト")
        tabs.addTab(self.form_page, "様式検索")
        tabs.addTab(self.supplier_page, "業者マスタ")
        tabs.addTab(self.template_page, "ひな形診断")
        tabs.currentChanged.connect(self._on_tab)
        self.setCentralWidget(tabs)
        self.statusBar().showMessage(
            "GUI入力 → 判定 → ひな形Q列へ投入 → JustOfficeで印刷（変更1–5・単価・段書き対応）"
        )

    def _on_tab(self, idx):
        w = self.centralWidget().widget(idx)
        if hasattr(w, "reload_cases"):
            w.reload_cases()
        elif hasattr(w, "reload"):
            w.reload()
