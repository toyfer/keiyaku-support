# 市様式セルマップ（Phase 2）

`app/form_templates.py` の `FORM_CELL_MAPS` に、市様式 xlsx のセル座標を追加します。

## 手順

1. `data/templates_excel/` に xlsx を置く
2. Excel / JustOffice でラベル位置を確認
3. `FORM_CELL_MAPS["見積書_業務"] = {"B5": "title", ...}` のように追記
4. またはシート内に `{{title}}` `{{supplier_name}}` 等のプレースホルダを埋め込む（座標不要）

## 推奨プレースホルダ

`title`, `case_no`, `supplier_name`, `supplier_address`, `supplier_rep`,
`contract_date`, `design_amount`, `contract_amount`, `bid_date`, `location`,
`department`, `manager`

## 生成 API

```python
from app.form_templates import fill_city_form, generate_recommended_city_forms
from app.case_service import build_export_values, get_case

case = get_case(1)
values = build_export_values(case)
paths = generate_recommended_city_forms(case, values)
```
