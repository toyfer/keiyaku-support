"""パス設定（ポータブル・自己完結型）

配布時は exe と同じフォルダに data/ を置き、そこに DB・様式・生成物を
保存する。USBメモリやネットワークドライブにコピーしてそのまま使える。
"""
import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = APP_DIR

BASE_DIR = Path(os.environ.get("KEIYAKU_DATA", str(BASE_DIR)))

DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = DATA_DIR / "templates"
TEMPLATES_EXCEL_DIR = DATA_DIR / "templates_excel"
OUTPUT_DIR = DATA_DIR / "output"
DB_PATH = DATA_DIR / "keiyaku.db"

FORM_CATEGORIES = {
    "01工事関係": "01",
    "02業務関係": "02",
    "03プロポーザル関係": "03",
    "物品印刷": "04",
    "施行関係書類一式（R6～）": "05",
    "見積り合せ（R6～）": "06",
    "★★★ひな形形式": "99",
}
