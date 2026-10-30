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
