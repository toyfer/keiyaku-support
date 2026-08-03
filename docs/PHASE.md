# 実装フェーズ

## Phase 1（完了）— 実務完成の芯

- [x] 変更契約 1–5回 Q列（ストライド 17）
- [x] `case_changes` CRUD + cases ミラー
- [x] 未使用変更ブロッククリア
- [x] 執行伺表題・段書き（`shikkou_text`）
- [x] 単価×予定数量 → 決裁基準
- [x] 4/1 警告・ CL 分岐・マージ
- [x] validation（保存/判定/生成）
- [x] `ippan_kyoso_target` 7000万先判定
- [x] 工事 Q47–51 / 業務 Q5–6,12–15 / 前払金額
- [x] 回帰: `scripts/test_*.py`

## Phase 2（リポ反映済み）— 運用品質

- [x] 物品 `BUPPIN_MAP`（基本項目）
- [x] `form_templates.py` — 市様式 Excel
- [x] 推奨帳票シート案内
- [x] 一覧フィルタ（種別・状態）
- [x] 分割配布ドキュメント + `pack_split.py`
- [ ] templates_excel 各ファイルの実測セル座標完備
- [ ] GitHub Release に B/C/D 添付（Issue #1・手元 zip）

## Phase 3（任意）

- inspections 複数回
- case_stage_progress 連動
- 様式 515 選択同梱ツール
- users 職員マスタ
- 祝日対応営業日
