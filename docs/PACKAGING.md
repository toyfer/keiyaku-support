# 配布・分割パッケージ

容量が大きいため、次のように**分割**します。

組み立ての具体手順は **[ASSEMBLE.md](ASSEMBLE.md)** を参照。

## パッケージ一覧

| 包 | 内容 | 目安 | 生成 |
|---|---|---|---|
| **A. ソース** (本リポ) | `app/` `scripts/` `run.py` 等 | < 1 MB | git |
| **B. ひな形テンプレート** | `hinagata_*.xlsx` ×4 | ~5–6 MB | `scripts/pack_split.py` |
| **C. 市様式 Excel** | `templates_excel/*.xlsx` | < 1 MB | 同上 |
| **D. DBシード** | `keiyaku.db` | ~0.6 MB | 同上 |
| **E. 例規・ガイド** | ガイドブック等 | 別途 | バンドル 04 |
| **F. 起動フル** | Embeddable Python + libs | ~40 MB | 別途 |

```bash
python scripts/pack_split.py --src /path/to/bundle/data --out dist
# → dist/B_templates_hinagata.zip
# → dist/C_templates_excel.zip
# → dist/D_keiyaku_db.zip
```

## 組み立て後の配置

```text
KeiyakuSupport/
  起動.bat
  run.py
  app/                 ← A
  data/
    keiyaku.db         ← D
    templates/         ← B
    templates_excel/   ← C
    output/
  python/              ← F（オフライン時のみ）
```

## 本リポに含まないもの

- 公式ひな形 xlsx（市章 EMF 含む）
- Embeddable Python
- 契約関係様式 ~515 点の実ファイル（メタは DB）

## バックアップ

`data/keiyaku.db` のみコピーすれば案件・業者・進捗が復元可能。  
生成 xlsx は再生成可能。
