# 契約手続き支援システム（keiyaku-support）

東松島市の契約事務向け **Windows ポータブル GUI**（Python / PySide6）。  
案件入力・決裁判定・手続チェックリストを GUI で行い、公式 Excel ひな形の **入力シート Q 列** に流し込んで JustOffice 等で印刷します。

**本リポジトリはソースのみ**（大容量のひな形 xlsx / DB / Embeddable Python は分割配布）。

- リポ: https://github.com/toyfer/keiyaku-support  
- 組み立て: **[docs/ASSEMBLE.md](docs/ASSEMBLE.md)**（B/C/D の作り方・配置）  
- 分割方針: [docs/PACKAGING.md](docs/PACKAGING.md)  
- Issue: [#1 Release に B/C/D を載せる](https://github.com/toyfer/keiyaku-support/issues/1)

---

## 分割パッケージ（容量対策）

| 包 | 内容 | 置き場所 | 作り方 |
|---|---|---|---|
| **A. ソース** | 本リポ | clone | `git clone` |
| **B. ひな形4種** | `hinagata_*.xlsx` | `data/templates/` | `scripts/pack_split.py` → `B_*.zip` |
| **C. 市様式** | 入札書・見積書等 | `data/templates_excel/` | 同上 → `C_*.zip` |
| **D. DB** | `keiyaku.db` | `data/` | 同上 → `D_*.zip` |
| **E. 例規** | ガイド等（任意） | 別 | バンドル `04_元資料` |
| **F. ランタイム** | Embeddable Python（任意） | `python/` | 別途 |

```text
KeiyakuSupport/
  起動.bat / run.py / run.bat
  app/                 ← A
  data/
    keiyaku.db         ← D
    templates/         ← B
    templates_excel/   ← C
    output/
  python/              ← F（オフライン時）
```

### 最短セットアップ（バンドルがある場合）

```bash
git clone https://github.com/toyfer/keiyaku-support.git
cd keiyaku-support
pip install -r requirements.txt

# 会話バンドルを .zip として展開した data を指す
python scripts/pack_split.py \
  --src "/path/to/keiyaku_conversation_bundle/02_ソースコード/data" \
  --out dist

# data/ に展開（Windows は Expand-Archive）
unzip -o dist/B_templates_hinagata.zip -d data/
unzip -o dist/C_templates_excel.zip -d data/
unzip -o dist/D_keiyaku_db.zip -d data/

python run.py
# または 起動.bat
```

バンドルの `data/` を **そのままコピー**しても同じです（zip 不要）。

---

## 画面

1. ダッシュボード  
2. 案件管理（入力・判定・**変更契約タブ**・ひな形／市様式生成）  
3. 手続チェックリスト  
4. 様式検索  
5. 業者マスタ  
6. ひな形診断  

---

## Phase 状態

| Phase | 内容 | 状態 |
|---|---|---|
| **1** | 変更1–5、case_changes、段書き、単価、validation、CLマージ、ippan修正 | **完了** |
| **2** | BUPPIN_MAP、form_templates、フィルタ、分割 docs / pack_split | **リポ完了**（Release 添付は手元） |
| **3** | inspections、stage_progress、様式515ツール等 | 未着手 |

詳細: [docs/PHASE.md](docs/PHASE.md)

### 変更契約 Q 列（実測）

| 種別 | 第1回 | ストライド | 2–5回開始 |
|---|---:|---:|---|
| 工事 | Q61 | 17 | 78, 95, 112, 129 |
| 業務 | Q67 | 17 | 84, 101, 118, 135 |

---

## テスト

```bash
python scripts/test_rules.py          # ひな形不要
python scripts/test_maps.py           # B 必要（無ければ SKIP）
python scripts/test_export_smoke.py   # B+D 必要
```

---

## 主要モジュール

| パス | 役割 |
|---|---|
| `app/rule_engine.py` | 決裁・随契・根拠条文・警告 |
| `app/document_engine.py` | ひな形 Q 列・変更1–5 |
| `app/form_templates.py` | 市様式（Phase2） |
| `app/case_service.py` | 案件/変更 CRUD |
| `app/fields.py` | フィールド・マップ |
| `scripts/pack_split.py` | B/C/D zip 生成 |

---

## 注意

- 市の例規・様式・業者データは庁内利用想定。  
- ひな形の EMF（市章）欠けは JustOffice で再挿入。  
- バックアップは `data/keiyaku.db`。  
