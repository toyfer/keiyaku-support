# 契約手続き支援システム（keiyaku-support）

東松島市の契約事務向け **Windows ポータブル GUI**（Python / PySide6）。  
案件入力・決裁判定・手続チェックリストを GUI で行い、公式 Excel ひな形の **入力シート Q 列** に流し込んで JustOffice 等で印刷します。

**本リポジトリはソースのみ**（大容量のひな形 xlsx / DB / Embeddable Python は分割配布）。

- リポ: https://github.com/toyfer/keiyaku-support  
- 設計メモ: 会話バンドル内 `01_ドキュメント/06_実装設計書_完成に向けて.md`

---

## 分割パッケージ（容量対策）

| 包 | 内容 | 置き場所 |
|---|---|---|
| **A. ソース**（本リポ） | `app/` `scripts/` `run.py` | ルート |
| **B. ひな形4種** | `hinagata_*.xlsx` | `data/templates/` |
| **C. 市様式 Excel** | 入札書・見積書・委任状等 | `data/templates_excel/` |
| **D. DB** | `keiyaku.db`（業者・様式メタ・デモ） | `data/` |
| **E. 例規**（任意） | ガイドブック・決裁区分等 | 別フォルダ |
| **F. ランタイム**（任意） | Embeddable Python + PySide6 | `python/` |

詳細は [docs/PACKAGING.md](docs/PACKAGING.md)。

```
KeiyakuSupport/
  run.py / run.bat / 起動.bat
  app/
  data/
    keiyaku.db          ← D
    templates/          ← B
    templates_excel/    ← C
    output/
  python/               ← F（オフライン時）
```

---

## セットアップ

```bash
git clone https://github.com/toyfer/keiyaku-support.git
cd keiyaku-support
pip install -r requirements.txt
# B・C・D を data/ に配置してから:
python run.py
```

Windows: `run.bat` または `起動.bat`（F 同梱時は同梱 python を使用）。

環境変数 `KEIYAKU_DATA` でデータルートを変更可能。

---

## 画面

1. ダッシュボード  
2. 案件管理（入力・判定・変更契約タブ・ひな形生成）  
3. 手続チェックリスト  
4. 様式検索  
5. 業者マスタ  
6. ひな形診断  

---

## Phase 状態

| Phase | 内容 | 状態 |
|---|---|---|
| **1** | 変更1–5、case_changes、段書き、単価、validation、CLマージ、ippan修正 | **完了** |
| **2** | BUPPIN_MAP、form_templates、推奨シート、一覧フィルタ、分割docs | **進行中（本リポ）** |
| **3** | inspections、stage_progress、様式515同梱ツール等 | 未着手 |

詳細: [docs/PHASE.md](docs/PHASE.md)

### 変更契約 Q 列（実測）

| 種別 | 第1回 | ストライド | 2–5回開始 |
|---|---:|---:|---|
| 工事 | Q61 | 17 | 78, 95, 112, 129 |
| 業務 | Q67 | 17 | 84, 101, 118, 135 |

未使用回は生成時にクリア。税・変更後契約は数式保護。

---

## テスト

ひな形 B を `data/templates/` に置いたうえで:

```bash
python scripts/test_rules.py
python scripts/test_maps.py
python scripts/test_export_smoke.py
```

`test_rules.py` はひな形なしでも実行可。

---

## 主要モジュール

| パス | 役割 |
|---|---|
| `app/rule_engine.py` | 決裁・随契・根拠条文・警告 |
| `app/document_engine.py` | ひな形 Q 列投入・変更1–5 |
| `app/form_templates.py` | 市様式（Phase2） |
| `app/case_service.py` | 案件/変更 CRUD・export |
| `app/fields.py` | フィールド・マップ単一ソース |
| `app/shikkou_text.py` | 執行伺表題・段書き |
| `app/validation.py` | 保存/判定/生成チェック |

---

## ライセンス・注意

- 市の例規・様式・業者データは庁内利用を想定。  
- ひな形の EMF（市章）欠けは JustOffice で再挿入。  
- バックアップは `data/keiyaku.db`。  
