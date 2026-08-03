"""起動エントリポイント"""
import sys
import traceback

from app.config import DATA_DIR, OUTPUT_DIR, TEMPLATES_DIR
from app.db import init_db


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    init_db()

    from PySide6.QtWidgets import QApplication, QMessageBox
    from app.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("契約手続き支援システム")
    app.setStyle("Fusion")
    try:
        win = MainWindow()
        win.show()
        sys.exit(app.exec())
    except Exception as e:
        QMessageBox.critical(None, "起動エラー", f"{e}\n\n{traceback.format_exc()}")
        raise


if __name__ == "__main__":
    main()
