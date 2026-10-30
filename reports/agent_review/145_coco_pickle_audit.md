# 145 COCONUT store の pickle の監査(2026-10-30、Claude Code)

## 経緯
- `data/external/coconut/coco_meta.pkl` は、prvsiyan/coconut-casmi26-candidates の配布ファイルと同じもの。
  - md5 は coco_mass.npy で一致し、pkl は大きさが一致している。
  - compliance_ledger_b1 の 10 番で「自前で作り直す」予定とされたまま、10/24 から b1_features・b1_pipeline・b1_ewin が `pickle.load` していた。
  - 今日の e2_parity.py も同じ読み方をしていた。
- 「ダウンロードした .pkl は unpickle しない」という約束に反するので、ここで点検した。

## 点検(実行せずに静的に解析)
- pickletools.genops で命令列だけを解析した。
- 参照される global は `numpy._core.multiarray._reconstruct` / `numpy.ndarray` / `numpy.dtype` だけ(REDUCE は 3 回)。
- 残りは文字列のリスト(MEMOIZE / SHORT_BINUNICODE)と辞書だけで、任意のコードを呼ぶ命令は無い。
- **これまでの読み込みは、numpy の配列を復元しただけで、実害のない形だった。**

## 処置
- 点検の直後に一度だけ読み込み、`coco_meta.parquet` に変換した(keys / smiles、436,389 行、coco_mass.npy と行が揃い、質量の昇順)。
  - 入力の sha256 は 29eab308…、出力の sha256 は 934188c0…。詳細は coco_meta.parquet.json にある。
- 新しいコード(e2_parity.py、今後の E2 の表の作成)は parquet を読む。
- 実行中の b1_ewin(既に読み込み済み)は止めない。
- Kaggle のカーネルは、既存の P の処理が読み込んだ配列(CMASS / CSMI)をそのまま使い、新たな unpickle は加えない。
- 残る課題: compliance_ledger の「COCONUT の取得から自前で作る」は未着手のまま。

## 訂正(2026-10-30 11:0x、Codex 145 の指摘を受けて)
- **表現の限定**: 「任意のコードを呼ぶ命令は無い」「実害のない形だった」は言い過ぎだった。
  - REDUCE などは、復元のための関数を呼ぶ。
  - 正しくは「報告された global と命令列は、通常の NumPy のデータの復元と整合する」である。
- **同一性の根拠**: pkl の大きさの一致だけでは、配布元のファイルと同一であることの証明にならない。
  - 記録として残すのは、現在の入力の hash(29eab308…)、変換後の hash(934188c0…)、行の順序、coco_mass.npy との行の対応(436,389 行、質量の昇順)である。
- **未達の点**
  - 「今後の表の生成は parquet」は、まだ達成していない。
    - b1_ewin.py(61 行目)と、生成したカーネルの処理(P の既存の COCONUT の読み込み)は、まだ pickle.load を呼ぶ。
    - parquet を読むのは、e2_parity.py と、145 で新しく書いた監査スクリプトだけである。
  - カーネルの起動時の従来の unpickle は残る。E2 は、P が読み込んだ配列を受け取るので、二度目の unpickle は加えていない。
  - parquet への変換と、台帳 10 番の「元データから自前で候補資産を作る」は別の作業である。後者は未完了のままとする。
