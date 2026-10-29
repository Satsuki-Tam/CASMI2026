# 105 GLACIER の timsTOF 適応 — 段階 0 の記録(Claude Code)

## 環境(2026-10-29 20:4x、date)
- Spark に **.venv-glt** を作成: Python 3.12、推論環境 .venv-ice の site-packages を .pth で参照(torch 2.14.1+cu130、pytorch_lightning 2.6.6 等はそのまま)、学習専用に **pygmtools 0.6.0** と **本物の linsatnet 0.1.3**(MIT)を --no-deps で追加(推論環境 .venv-ice は変更しない)。
- 学習コード: data/external/ms-pred-train/ms-pred(commit 708148c2 = 推論資産と同じ)。dgl / torch_scatter は推論用 shim(純 torch)を使う予定、LinSATNet は本物を使う。

## 0a: LinSATNet の shim と本物(stage0_linsat.py / stage0_linsat_topk.py、CPU)
- checkpoint の linsat_tau = **15.0**(hyper_parameters;contr_weight 1.0 = 対照学習で仕上げた版)。
- tau 15 では、shim と本物の **top-k の原子の選択は全件一致**(logit の尺度 1 / 5、N 10 / 40 / 100、k 1〜3、各 2,000 行)→ 推論(top-k の index だけを使う)への影響はない。
- ただし**値は一致しない**(tau 15 で最大 0.04、tau 1 以下で大きくずれる)。値は学習の損失に入るので、**学習には本物の LinSATNet を使う**(shim は推論専用のまま)。

## 0b: 学習の順伝播・逆伝播(stage0_grad.py、CPU、21:00)
- 前処理の鎖(ms-pred 自身のコード、run_mspred.py 経由): make_msdata.py(MSG の [M+H]+ 16 分子 32 スペクトル、SIRIUS .ms を ms-pred の HDF5 形式で)→ run_magma.py(4 worker で 32 件 6 秒)→ 01_assign_subformulae.py → add_dag_intens.py --magma-output → magma_tree_with_inten.hdf5。spawn の worker のために PYTHONPATH に shim_train と ms-pred の src を入れる。追加した純 Python の依存(--no-deps): h5py、multiprocess / dill、platformdirs、pathos / pox / ppft、matplotlib / seaborn とその依存(numpy 等は推論環境のもの)。
- **STAGE0B_PASS**: checkpoint を JointModel に strict に読込;batch 8 で損失 0.389(有限);学習可能な 259 tensor(1,511 万 parameter)すべてに有限の勾配(0 勾配は embedder の 1 tensor のみ);AdamW 1 step で 259 tensor すべてが変化;同じ batch で 30 step 学習すると損失 0.389 → 0.24 前後(過学習の確認)。contrastive の枝(decoy)は段階 1 で確認する。

## 段階 1 の往復(export_ckpt.py、21:05)
- **C0'**(公開 checkpoint を学習環境の JointModel に読み、state_dict を公開形式 {hyper_parameters, state_dict, source} で保存): 264 tensor すべて公開版と bit 一致(sha a7ac08e6…)。
- 推論 runner(gl_runner.py --ckpt)で f1dev G_tims_crosslib の先頭 10 分子(候補 2,571、採点 2,320)を公開版と C0' で採点 → **2,320 組すべて差 0**(往復は厳密)。
- 両者と保存済み cache(過去の全件 run)の差は最大 0.0051(2,103 / 2,320 が一致):runner の batch 構成の違いによる浮動小数の差。→ 段階 2 の比較は、C0' と適応版を**同じ入力・同じ batch 構成で同時に**採点して行う(保存 cache との比較にしない)。
- 段階 1 のデータ(make_glt_data.py → data/glt/tims_s1): enveda-180 の [M+H]+、identity fold 3 / 4 のみ、全名簿の identity group(18,969)とパネル(250)を除外、固定 hash 順で 2,000 identity・5,135 スペクトル(CE 20 / 40 / 60 eV)、val は identity の hash で 202。前処理(MAGMa → 部分式 → 強度)を実行中。
