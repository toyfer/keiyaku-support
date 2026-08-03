"""会話バンドルの data/ から分割パッケージ B/C/D を作る

使い方:
  python scripts/pack_split.py --src path/to/02_ソースコード/data --out dist/

出力:
  dist/B_templates_hinagata.zip   (~5–6MB)
  dist/C_templates_excel.zip      (~1MB)
  dist/D_keiyaku_db.zip           (~0.6MB)
  dist/MANIFEST.txt
"""
from __future__ import annotations

import argparse
import zipfile
from datetime import datetime
from pathlib import Path


def _zip_dir(src_dir: Path, zip_path: Path, arc_prefix: str) -> list[str]:
    files = []
    if not src_dir.is_dir():
        return files
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src_dir.rglob("*")):
            if p.is_file() and p.suffix.lower() != ".gitkeep":
                arc = f"{arc_prefix}/{p.relative_to(src_dir).as_posix()}"
                z.write(p, arc)
                files.append(arc)
    return files


def _zip_file(src: Path, zip_path: Path, arcname: str) -> list[str]:
    if not src.is_file():
        return []
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(src, arcname)
    return [arcname]


def main():
    ap = argparse.ArgumentParser(description="Build split packages B/C/D")
    ap.add_argument(
        "--src",
        type=Path,
        required=True,
        help="Path to data/ (contains templates/, templates_excel/, keiyaku.db)",
    )
    ap.add_argument("--out", type=Path, default=Path("dist"), help="Output directory")
    args = ap.parse_args()
    src: Path = args.src.resolve()
    out: Path = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    if not src.is_dir():
        raise SystemExit(f"src not found: {src}")

    manifest = [f"# keiyaku-support split packages", f"created: {datetime.now().isoformat(timespec='seconds')}", f"src: {src}", ""]

    # B
    b_path = out / "B_templates_hinagata.zip"
    b_files = _zip_dir(src / "templates", b_path, "templates")
    # also accept flat hinagata_*.xlsx in src
    if not b_files:
        with zipfile.ZipFile(b_path, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(src.glob("hinagata_*.xlsx")):
                z.write(p, f"templates/{p.name}")
                b_files.append(f"templates/{p.name}")
    manifest.append(f"## B {b_path.name} ({b_path.stat().st_size if b_path.exists() else 0} bytes)")
    manifest.extend(f"  - {f}" for f in b_files)
    manifest.append("")

    # C
    c_path = out / "C_templates_excel.zip"
    c_files = _zip_dir(src / "templates_excel", c_path, "templates_excel")
    manifest.append(f"## C {c_path.name} ({c_path.stat().st_size if c_path.exists() else 0} bytes)")
    manifest.extend(f"  - {f}" for f in c_files)
    manifest.append("")

    # D
    d_path = out / "D_keiyaku_db.zip"
    db = src / "keiyaku.db"
    d_files = _zip_file(db, d_path, "keiyaku.db")
    manifest.append(f"## D {d_path.name} ({d_path.stat().st_size if d_path.exists() else 0} bytes)")
    manifest.extend(f"  - {f}" for f in d_files)
    manifest.append("")

    man = out / "MANIFEST.txt"
    man.write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print("Wrote:")
    for p in (b_path, c_path, d_path, man):
        if p.exists():
            print(f"  {p}  ({p.stat().st_size:,} bytes)")
    if not b_files:
        print("WARN: B empty — check templates/ or hinagata_*.xlsx")
    if not c_files:
        print("WARN: C empty — check templates_excel/")
    if not d_files:
        print("WARN: D empty — check keiyaku.db")
    print("\nUpload these to GitHub Release (see docs/ASSEMBLE.md).")


if __name__ == "__main__":
    main()
