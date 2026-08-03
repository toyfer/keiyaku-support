"""案件管理: 入力・判定・変更契約・ひな形/市様式生成"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPushButton, QScrollArea, QSpinBox, QDoubleSpinBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget, QAbstractItemView,
)

from ..case_service import (
    build_export_values, delete_case, delete_change, get_case, judge,
    list_cases, list_changes, list_suppliers, prepare_generate, save_case, save_change,
)
from ..document_engine import generate_form, generate_from_case, resolve_template
from ..fields import (
    CASE_TYPES, CHANGE_MAX, FIELD_DEFS, METHODS, PERIOD_PATTERNS, STATUSES, ZUII_CATEGORIES,
)
from ..form_templates import generate_recommended_city_forms
from ..shikkou_text import build_amount_display, build_shikkou_title, unit_total
from ..validation import validate_save


class MoneySpin(QSpinBox):
    def __init__(self):
        super().__init__()
        self.setRange(0, 2_000_000_000)
        self.setGroupSeparatorShown(True)
        self.setSingleStep(10000)


class CaseDetailDialog(QDialog):
    def __init__(self, parent=None, db_path=None, case_id=None):
        super().__init__(parent)
        self.db_path = db_path
        self.case_id = case_id
        self.setWindowTitle("案件詳細" if case_id else "新規案件")
        self.resize(980, 820)
        self.widgets = {}
        self._last_judge = {}
        self._build()
        if case_id:
            self._load(case_id)
        else:
            self.widgets["fiscal_year"].setValue(datetime.now().year)
            self.widgets["tax_rate"].setValue(0.10)
            if "advance_payment_rate" in self.widgets:
                self.widgets["advance_payment_rate"].setValue(0.40)
            self.widgets["mitsu_count"].setValue(5)
            self.widgets["status"].setCurrentIndex(0)

    def _build(self):
        root = QVBoxLayout(self)
        tabs = QTabWidget()
        forms = {}
        for key, label, kind, group in FIELD_DEFS:
            if group not in forms:
                w = QWidget()
                f = QFormLayout(w)
                f.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
                forms[group] = f
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setWidget(w)
                tabs.addTab(scroll, group)
            f = forms[group]
            w = self._make_widget(kind)
            self.widgets[key] = w
            if key == "supplier_name":
                row = QHBoxLayout()
                row.addWidget(w, 1)
                btn = QPushButton("マスタから選択…")
                btn.clicked.connect(self._pick_supplier)
                row.addWidget(btn)
                wrap = QWidget()
                wrap.setLayout(row)
                f.addRow(label, wrap)
            elif key == "unit_price_total":
                row = QHBoxLayout()
                row.addWidget(w, 1)
                b1 = QPushButton("単価×数量")
                b1.clicked.connect(self._calc_unit_total)
                b2 = QPushButton("→設計金額")
                b2.clicked.connect(self._copy_unit_to_design)
                row.addWidget(b1)
                row.addWidget(b2)
                wrap = QWidget()
                wrap.setLayout(row)
                f.addRow(label, wrap)
            elif key == "shikkou_title":
                row = QHBoxLayout()
                row.addWidget(w, 1)
                btn = QPushButton("文言を再生成")
                btn.clicked.connect(self._regen_shikkou)
                row.addWidget(btn)
                wrap = QWidget()
                wrap.setLayout(row)
                f.addRow(label, wrap)
            else:
                f.addRow(label, w)

        change_tab = QWidget()
        cl = QVBoxLayout(change_tab)
        cl.addWidget(QLabel("変更契約（最大5回）→ ひな形①〜⑤。未使用回は生成時クリア。"))
        self.change_table = QTableWidget(0, 10)
        self.change_table.setHorizontalHeaderLabels([
            "回", "協議通知日", "説明日時", "締結伺日", "変更契約日",
            "増減", "増減額(税込)", "変更後工期", "配当予算", "執行済",
        ])
        self.change_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        cl.addWidget(self.change_table)
        crow = QHBoxLayout()
        for text, fn in [
            ("行追加", self._change_add_row),
            ("DB保存", self._change_save_row),
            ("削除", self._change_delete_row),
            ("再読込", self._reload_changes),
        ]:
            b = QPushButton(text)
            b.clicked.connect(fn)
            crow.addWidget(b)
        crow.addStretch(1)
        cl.addLayout(crow)
        tabs.addTab(change_tab, "変更契約")
        root.addWidget(tabs, 1)

        self.result_view = QTextEdit()
        self.result_view.setReadOnly(True)
        self.result_view.setMaximumHeight(220)
        root.addWidget(QLabel("◆ 判定結果"))
        root.addWidget(self.result_view)

        btns = QHBoxLayout()
        for text, fn in [
            ("判定実行", self._judge),
            ("根拠条文コピー", self._copy_konkyo),
            ("ひな形を生成", self._generate_hinagata),
            ("市様式も生成", self._generate_city),
            ("任意テンプレ…", self._generate_any),
            ("保存して閉じる", self._save_close),
            ("保存", self._save),
            ("閉じる", self.reject),
        ]:
            b = QPushButton(text)
            b.clicked.connect(fn)
            btns.addWidget(b)
        root.addLayout(btns)

    def _make_widget(self, kind):
        if kind == "combo_case":
            w = QComboBox(); w.addItems(CASE_TYPES); return w
        if kind == "combo_method":
            w = QComboBox(); w.addItems(METHODS); return w
        if kind == "combo_status":
            w = QComboBox()
            for code, label in STATUSES:
                w.addItem(label, code)
            return w
        if kind == "combo_zuii":
            w = QComboBox(); w.addItems(ZUII_CATEGORIES); return w
        if kind == "combo_period":
            w = QComboBox(); w.addItems(PERIOD_PATTERNS); return w
        if kind == "money":
            return MoneySpin()
        if kind == "int":
            w = QSpinBox(); w.setRange(0, 99_999_999); return w
        if kind == "float":
            w = QDoubleSpinBox(); w.setRange(0, 1e9); w.setDecimals(3); return w
        if kind == "rate":
            w = QDoubleSpinBox(); w.setRange(0, 0.5); w.setDecimals(2); w.setValue(0.10); return w
        if kind == "bool":
            return QCheckBox("はい")
        return QLineEdit()

    def _values(self) -> dict:
        vals = {}
        for key, label, kind, group in FIELD_DEFS:
            w = self.widgets[key]
            if kind in ("combo_case", "combo_method", "combo_zuii", "combo_period"):
                vals[key] = w.currentText()
            elif kind == "combo_status":
                vals[key] = w.currentData() or "draft"
            elif kind == "money":
                vals[key] = w.value() if w.value() else None
            elif kind == "int":
                vals[key] = w.value()
            elif kind in ("rate", "float"):
                vals[key] = w.value()
            elif kind == "bool":
                vals[key] = 1 if w.isChecked() else 0
            else:
                vals[key] = w.text().strip()
        if self.case_id:
            vals["id"] = self.case_id
        return vals

    def _set_widget(self, key, kind, val):
        w = self.widgets[key]
        if val is None:
            return
        if kind in ("combo_case", "combo_method", "combo_zuii", "combo_period"):
            i = w.findText(str(val))
            if i >= 0:
                w.setCurrentIndex(i)
        elif kind == "combo_status":
            for i in range(w.count()):
                if w.itemData(i) == val or w.itemText(i) == val:
                    w.setCurrentIndex(i); break
        elif kind in ("money", "int"):
            try:
                w.setValue(int(val))
            except (TypeError, ValueError):
                pass
        elif kind in ("rate", "float"):
            try:
                w.setValue(float(val))
            except (TypeError, ValueError):
                pass
        elif kind == "bool":
            w.setChecked(bool(val) and val not in (0, "0"))
        else:
            w.setText(str(val))

    def _load(self, case_id):
        row = get_case(case_id, self.db_path)
        if not row:
            return
        for key, label, kind, group in FIELD_DEFS:
            if key in row:
                self._set_widget(key, kind, row[key])
        self._reload_changes()

    def _pick_supplier(self):
        dlg = SupplierPickDialog(self, self.db_path)
        if dlg.exec() and dlg.selected:
            s = dlg.selected
            self.widgets["supplier_id"].setValue(int(s.get("id") or 0))
            self.widgets["supplier_name"].setText(s.get("name") or "")
            addr = " ".join(filter(None, [s.get("address1"), s.get("address2")]))
            self.widgets["supplier_address"].setText(addr)
            self.widgets["supplier_rep"].setText(s.get("representative") or "")

    def _calc_unit_total(self):
        t = unit_total(self._values())
        if t and "unit_price_total" in self.widgets:
            self.widgets["unit_price_total"].setValue(t)

    def _copy_unit_to_design(self):
        self._calc_unit_total()
        t = self.widgets["unit_price_total"].value()
        if t:
            self.widgets["design_amount"].setValue(t)

    def _regen_shikkou(self):
        vals = self._values()
        self.widgets["shikkou_title"].setText(build_shikkou_title(vals))
        self.widgets["amount_display"].setText(build_amount_display(vals))

    def _reload_changes(self):
        self.change_table.setRowCount(0)
        if not self.case_id:
            return
        rows = list_changes(self.case_id, self.db_path)
        self.change_table.setRowCount(len(rows))
        for r, ch in enumerate(rows):
            vals = [
                ch.get("change_no"), ch.get("change_notice") or "", ch.get("change_explain") or "",
                ch.get("change_kessai_date") or "", ch.get("change_date") or "",
                ch.get("change_dir") or "",
                ch.get("amount_delta") if ch.get("amount_delta") is not None else "",
                ch.get("new_end_date") or "",
                ch.get("budget_allocated") if ch.get("budget_allocated") is not None else "",
                ch.get("budget_executed") if ch.get("budget_executed") is not None else "",
            ]
            for c, v in enumerate(vals):
                self.change_table.setItem(r, c, QTableWidgetItem("" if v is None else str(v)))

    def _change_add_row(self):
        if not self.case_id:
            QMessageBox.information(self, "変更", "先に案件を保存してください"); return
        n = self.change_table.rowCount() + 1
        if n > CHANGE_MAX:
            QMessageBox.warning(self, "変更", f"最大{CHANGE_MAX}回"); return
        r = self.change_table.rowCount()
        self.change_table.insertRow(r)
        self.change_table.setItem(r, 0, QTableWidgetItem(str(n)))
        for c in range(1, 10):
            self.change_table.setItem(r, c, QTableWidgetItem(""))

    def _change_row_dict(self, r: int) -> dict:
        def cell(c):
            it = self.change_table.item(r, c)
            return it.text().strip() if it else ""
        def num(c):
            s = cell(c)
            if not s:
                return None
            try:
                return int(float(s.replace(",", "")))
            except ValueError:
                return None
        return {
            "change_no": int(cell(0) or 0), "change_notice": cell(1), "change_explain": cell(2),
            "change_kessai_date": cell(3), "change_date": cell(4), "change_dir": cell(5),
            "amount_delta": num(6), "new_end_date": cell(7),
            "budget_allocated": num(8), "budget_executed": num(9), "status": "applied",
        }

    def _change_save_row(self):
        if not self.case_id:
            QMessageBox.information(self, "変更", "先に案件を保存"); return
        r = self.change_table.currentRow()
        try:
            if r < 0:
                for rr in range(self.change_table.rowCount()):
                    ch = self._change_row_dict(rr)
                    if ch["change_no"]:
                        save_change(self.case_id, ch, self.db_path)
            else:
                save_change(self.case_id, self._change_row_dict(r), self.db_path)
            self._reload_changes()
            row = get_case(self.case_id, self.db_path)
            if row:
                for key in ("change_no", "change_notice", "change_explain", "change_kessai_date",
                            "change_date", "change_dir", "change_amount", "change_end_date"):
                    if key in self.widgets and key in row:
                        kind = next(k for kk, _, k, _ in FIELD_DEFS if kk == key)
                        self._set_widget(key, kind, row[key])
            QMessageBox.information(self, "変更", "保存しました")
        except Exception as e:
            QMessageBox.warning(self, "変更", str(e))

    def _change_delete_row(self):
        if not self.case_id:
            return
        r = self.change_table.currentRow()
        if r < 0:
            return
        ch = self._change_row_dict(r)
        if QMessageBox.question(self, "削除", f"第{ch['change_no']}回を削除?") != QMessageBox.StandardButton.Yes:
            return
        delete_change(self.case_id, ch["change_no"], self.db_path)
        self._reload_changes()

    def _format_judge(self, result: dict) -> str:
        lines = []
        if result.get("警告"):
            lines.append("【警告】")
            for a in result["警告"]:
                lines.append(f"  ⚠ {a}")
            lines.append("")
        for k in [
            "決裁区分", "決裁判定額", "審査委員会", "随意契約範囲", "最低制限価格",
            "契約書", "予定価格調書", "議会", "検査者", "契約保証金", "事務委任",
            "会計管理者合議", "指名・見積人数", "入札方式の目安",
            "執行伺表題", "金額表示", "執行伺追記", "単価総合計", "推奨帳票シート", "根拠資料",
        ]:
            if k not in result:
                continue
            v = result[k]
            lines.append(f"■ {k}: {', '.join(map(str, v)) if isinstance(v, list) else v}")
        if isinstance(result.get("契約期間パターン"), dict):
            lines.append("■ 契約期間パターン")
            for kk, vv in result["契約期間パターン"].items():
                lines.append(f"   {kk}: {vv}")
        lines += ["", "◆ 根拠条文", result.get("根拠条文") or ""]
        return "\n".join(lines)

    def _judge(self):
        result = judge(self._values())
        self._last_judge = result
        if result.get("執行伺表題") and not self.widgets["shikkou_title"].text().strip():
            self.widgets["shikkou_title"].setText(str(result["執行伺表題"]))
        if result.get("金額表示") and not self.widgets["amount_display"].text().strip():
            self.widgets["amount_display"].setText(str(result["金額表示"]))
        self.result_view.setPlainText(self._format_judge(result))
        return result

    def _copy_konkyo(self):
        result = self._last_judge or judge(self._values())
        QGuiApplication.clipboard().setText(result.get("根拠条文") or "")
        QMessageBox.information(self, "コピー", "根拠条文をコピーしました")

    def _save(self):
        vals = self._values()
        errors, warnings = validate_save(vals)
        if errors:
            QMessageBox.warning(self, "入力エラー", "\n".join(errors)); return None
        try:
            cid = save_case(vals, self.case_id, self.db_path)
            self.case_id = cid
            msg = f"保存しました（ID: {cid})"
            if warnings:
                msg += "\n\n" + "\n".join(warnings)
            QMessageBox.information(self, "保存", msg)
            self._reload_changes()
            return cid
        except Exception as e:
            QMessageBox.warning(self, "保存", str(e)); return None

    def _save_close(self):
        if self._save() is not None:
            self.accept()

    def _generate_hinagata(self):
        vals = self._values()
        if not vals.get("title"):
            QMessageBox.warning(self, "入力", "名称必須"); return
        if not self.case_id:
            try:
                self.case_id = save_case(vals, None, self.db_path)
                vals["id"] = self.case_id
            except Exception as e:
                QMessageBox.warning(self, "保存", str(e)); return
        else:
            try:
                save_case(vals, self.case_id, self.db_path)
            except Exception as e:
                QMessageBox.warning(self, "保存", str(e)); return
            vals = get_case(self.case_id, self.db_path) or vals
        export, changes, errors, warnings = prepare_generate(vals, self.db_path)
        if errors:
            QMessageBox.warning(self, "生成不可", "\n".join(errors)); return
        if warnings:
            if QMessageBox.question(self, "確認", "警告あり。続行?\n\n" + "\n".join(warnings)) != QMessageBox.StandardButton.Yes:
                return
        try:
            out = generate_from_case(vals, export, changes=changes)
        except Exception as e:
            QMessageBox.warning(self, "生成", str(e)); return
        sheets = (self._last_judge or {}).get("推奨帳票シート") or []
        msg = f"生成完了\n{out}\n変更: {len(changes)}回"
        if sheets:
            msg += "\n推奨シート: " + ", ".join(sheets)
        QMessageBox.information(self, "生成", msg)
        self._open_path(out)

    def _generate_city(self):
        vals = self._values()
        if not self.case_id:
            if self._save() is None:
                return
            vals = get_case(self.case_id, self.db_path) or vals
        export = build_export_values(vals)
        try:
            paths = generate_recommended_city_forms(vals, export)
        except Exception as e:
            QMessageBox.warning(self, "市様式", str(e)); return
        if not paths:
            QMessageBox.information(
                self, "市様式",
                "生成対象なし。data/templates_excel/ に市様式（分割C）を置き、"
                "見積・随契などの契約方法を選んでください。",
            )
            return
        QMessageBox.information(self, "市様式", "生成:\n" + "\n".join(str(p) for p in paths))

    def _generate_any(self):
        vals = self._values()
        path, _ = QFileDialog.getOpenFileName(self, "テンプレ", "", "Excel/Word (*.xlsx *.xlsm *.docx)")
        if not path:
            return
        export = build_export_values(vals)
        name = f"{vals.get('case_no') or 'case'}_{os.path.basename(path)}"
        try:
            out = generate_form(path, export, output_name=name, case_type=vals.get("case_type") or "工事")
        except Exception as e:
            QMessageBox.warning(self, "生成", str(e)); return
        QMessageBox.information(self, "生成", str(out))
        self._open_path(out)

    def _open_path(self, path):
        try:
            p = str(path)
            if sys.platform == "win32":
                os.startfile(p)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", p])
            else:
                subprocess.Popen(["xdg-open", str(path.parent)])
        except Exception:
            pass


class SupplierPickDialog(QDialog):
    def __init__(self, parent=None, db_path=None):
        super().__init__(parent)
        self.db_path = db_path
        self.selected = None
        self.setWindowTitle("業者選択")
        self.resize(800, 500)
        lay = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.textChanged.connect(self.reload)
        lay.addWidget(self.search)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "CD", "業者名", "代表者", "住所", "電話"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._ok)
        lay.addWidget(self.table)
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        box.accepted.connect(self._ok)
        box.rejected.connect(self.reject)
        lay.addWidget(box)
        self.reload()

    def reload(self):
        rows = list_suppliers(self.db_path, self.search.text().strip())
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            addr = " ".join(filter(None, [row.get("address1"), row.get("address2")]))
            for c, v in enumerate([
                row.get("id"), row.get("supplier_code"), row.get("name"),
                row.get("representative"), addr, row.get("phone"),
            ]):
                item = QTableWidgetItem("" if v is None else str(v))
                if c == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row)
                self.table.setItem(r, c, item)

    def _ok(self):
        r = self.table.currentRow()
        if r < 0:
            return
        self.selected = self.table.item(r, 0).data(Qt.ItemDataRole.UserRole)
        self.accept()


class CaseListPage(QWidget):
    def __init__(self, db_path=None):
        super().__init__()
        self.db_path = db_path
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("検索")
        self.search.textChanged.connect(self.reload)
        top.addWidget(self.search, 1)
        self.filter_type = QComboBox()
        self.filter_type.addItem("種別:すべて", "")
        for t in CASE_TYPES:
            self.filter_type.addItem(t, t)
        self.filter_type.currentIndexChanged.connect(self.reload)
        top.addWidget(self.filter_type)
        self.filter_status = QComboBox()
        self.filter_status.addItem("状態:すべて", "")
        for code, label in STATUSES:
            self.filter_status.addItem(label, code)
        self.filter_status.currentIndexChanged.connect(self.reload)
        top.addWidget(self.filter_status)
        for text, fn in [("開く", self._open), ("新規", self._new), ("削除", self._delete), ("再読込", self.reload)]:
            b = QPushButton(text); b.clicked.connect(fn); top.addWidget(b)
        layout.addLayout(top)
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(
            ["ID", "番号", "種別", "名称", "方法", "パターン", "設計額", "契約額", "状態", "担当"]
        )
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(lambda *_: self._open())
        layout.addWidget(self.table)
        self.summary = QLabel("")
        layout.addWidget(self.summary)
        self.reload()

    def reload(self):
        try:
            rows = list_cases(self.db_path, self.search.text().strip())
        except Exception:
            rows = []
        ft, fs = self.filter_type.currentData(), self.filter_status.currentData()
        if ft:
            rows = [r for r in rows if r.get("case_type") == ft]
        if fs:
            rows = [r for r in rows if r.get("status") == fs]
        status_label = {c: l for c, l in STATUSES}
        self.table.setRowCount(len(rows))
        total = 0
        for r, row in enumerate(rows):
            amt = row.get("contract_amount") or row.get("design_amount") or 0
            try:
                total += int(amt)
            except (TypeError, ValueError):
                pass
            vals = [
                row.get("id"), row.get("case_no"), row.get("case_type"), row.get("title"),
                row.get("contract_method"), row.get("period_pattern") or "単年度契約",
                f"{int(row['design_amount']):,}" if row.get("design_amount") else "",
                f"{int(row['contract_amount']):,}" if row.get("contract_amount") else "",
                status_label.get(row.get("status"), row.get("status")),
                row.get("manager") or row.get("department") or "",
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem("" if v is None else str(v))
                if c == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row.get("id"))
                self.table.setItem(r, c, item)
        self.summary.setText(f"件数: {len(rows)}　合計: {total:,} 円")

    def _new(self):
        if CaseDetailDialog(self, self.db_path).exec():
            self.reload()

    def _open(self):
        idx = self.table.currentRow()
        if idx < 0:
            return
        case_id = self.table.item(idx, 0).data(Qt.ItemDataRole.UserRole)
        if CaseDetailDialog(self, self.db_path, case_id=case_id).exec():
            self.reload()

    def _delete(self):
        idx = self.table.currentRow()
        if idx < 0:
            return
        case_id = self.table.item(idx, 0).data(Qt.ItemDataRole.UserRole)
        title = self.table.item(idx, 3).text()
        if QMessageBox.question(self, "削除", f"「{title}」を削除?") != QMessageBox.StandardButton.Yes:
            return
        delete_case(case_id, self.db_path)
        self.reload()
