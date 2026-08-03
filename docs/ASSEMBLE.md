# 組み立て手順（分割 A+B+C+D）

この環境では大容量 xlsx を GitHub API 経由でアップロードできないため、
**B/C/D は手元（またはバンドル展開先）で zip 化**し、Release に載せる想定です。

## 0. 元データ

会話添付 `keiyaku_conversation_bundle.zip.pdf` は実体 ZIP。

```text
拡張子を .zip に直して展開
→ keiyaku_conversation_bundle/02_ソースコード/data/
    keiyaku.db
    templates/hinagata_*.xlsx
    templates_excel/*.xlsx
```

## 1. ソース（A）

```bash
git clone https://github.com/toyfer/keiyaku-support.git
cd keiyaku-support
pip install -r requirements.txt
```

## 2. 分割 zip を作る（推奨）

```bash
# バンドルの data を指す
python scripts/pack_split.py --src "/path/to/keiyaku_conversation_bundle/02_ソースコード/data" --out dist
```

出力:

| ファイル | 包 |
|---|---|
| `dist/B_templates_hinagata.zip` | B |
| `dist/C_templates_excel.zip` | C |
| `dist/D_keiyaku_db.zip` | D |
| `dist/MANIFEST.txt` | 一覧 |

## 3. アプリ data/ に展開

```bash
# Linux/macOS 例
unzip -o dist/B_templates_hinagata.zip -d data/
unzip -o dist/C_templates_excel.zip -d data/
unzip -o dist/D_keiyaku_db.zip -d data/
```

Windows（PowerShell）:

```powershell
Expand-Archive -Force dist\B_templates_hinagata.zip -DestinationPath data
Expand-Archive -Force dist\C_templates_excel.zip -DestinationPath data
Expand-Archive -Force dist\D_keiyaku_db.zip -DestinationPath data
```

最終形:

```text
data/
  keiyaku.db
  templates/hinagata_koji.xlsx
  templates/hinagata_gyomu.xlsx
  templates/hinagata_kensetsu_gyomu.xlsx
  templates/hinagata_buppin.xlsx
  templates_excel/…
  output/
```

## 4. 起動

```bash
python run.py
# または run.bat / 起動.bat
```

DB が無い場合は空スキーマで起動します（業者・デモ案件なし）。
D を置くと業者 813・デモ案件が使えます。

## 5. GitHub Release に載せる（メンテナ）

1. https://github.com/toyfer/keiyaku-support/releases/new
2. Tag: `data-v1`（など）
3. Assets に B/C/D の 3 zip + MANIFEST.txt を添付
4. README の「Release」リンクを更新

Issue: https://github.com/toyfer/keiyaku-support/issues/1

## 6. バンドルから直接コピー（zip 不要の最短）

```text
copy  バンドル\02_ソースコード\data\*  →  keiyaku-support\data\
```

templates / templates_excel / keiyaku.db をそのまま置けば OK。
