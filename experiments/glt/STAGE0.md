# 105 GLACIER の timsTOF 適応 — 段階 0 の記録(Claude Code)

## 環境(2026-10-29 20:4x、date)
- Spark に **.venv-glt** を作成: Python 3.12、推論環境 .venv-ice の site-packages を .pth で参照(torch 2.14.1+cu130、pytorch_lightning 2.6.6 等はそのまま)、学習専用に **pygmtools 0.6.0** と **本物の linsatnet 0.1.3**(MIT)を --no-deps で追加(推論環境 .venv-ice は変更しない)。
- 学習コード: data/external/ms-pred-train/ms-pred(commit 708148c2 = 推論資産と同じ)。dgl / torch_scatter は推論用 shim(純 torch)を使う予定、LinSATNet は本物を使う。

## 0a: LinSATNet の shim と本物(stage0_linsat.py / stage0_linsat_topk.py、CPU)
- checkpoint の linsat_tau = **15.0**(hyper_parameters;contr_weight 1.0 = 対照学習で仕上げた版)。
- tau 15 では、shim と本物の **top-k の原子の選択は全件一致**(logit の尺度 1 / 5、N 10 / 40 / 100、k 1〜3、各 2,000 行)→ 推論(top-k の index だけを使う)への影響はない。
- ただし**値は一致しない**(tau 15 で最大 0.04、tau 1 以下で大きくずれる)。値は学習の損失に入るので、**学習には本物の LinSATNet を使う**(shim は推論専用のまま)。
