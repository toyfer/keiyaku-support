# 配布・分割パッケージ

容量が大きいため、次のように**分割**します。

## パッケージ一覧

| 包 | 内容 | 目安 |
|---|---|---|
| **A. ソース** (`keiyaku-support` 本リポ) | `app/` `scripts/` `run.py` 等 | < 1 MB |
| **B. ひな形テンプレート** | `hinagata_koji/gyomu/kensetsu_gyomu/buppin.xlsx` | ~5–6 MB |
| **C. 市様式 Excel** | `templates_excel/*.xlsx`（入札書・委任状・見積書等） | < 1 MB |
| **D. DBシード** | `keiyaku.db`（業者 813・様式 429・デモ案件） | ~0.6 MB |
| **E. 例規・ガイド** | ガイドブック・決裁区分・RTF 等 | 別途（任意） |
| **F. 起動フル** | Embeddable Python 3.12 + PySide6 同棲 | ~40 MB |

## 組み立て（Windows）

```
KeiyakuSupport/
  起動.bat
  run.py
  app/                 ← A
  scripts/             ← A
  requirements.txt
  data/
    keiyaku.db         ← D
    templates/         ← B
    templates_excel/   ← C
    output/
  python/              ← F（オフライン時のみ）
```

1. A を clone または展開
2. B・C・D を `data/` 下に配置
3. 開発時: `pip install -r requirements.txt` → `python run.py`
4. オフライン: F を同棲し `\u8d77\u52d5.bat`

## 本リポに含まないもの

- 官方ひな形 xlsx（市章 EMF 含む大容量）
- Embeddable Python
- 契約関係様式 ~515 点の実ファイル（メタは DB）

## バックアップ

`data/keiyaku.db` のみコピーすれば案件・業者・進捗が復元可能。
生成 xlsx は再生成可能。
