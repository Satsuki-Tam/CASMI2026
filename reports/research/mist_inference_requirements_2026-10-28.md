# MIST (coleygroup/MIST・Zenodo 23303289) 推論要件の調査

- 作成: 2026-10-28 23:36 (ローカル時刻、`date` で取得)。Web 閲覧のみ (インストール・ダウンロード・実行は一切なし)。
- 対象: GitHub `coleygroup/MIST` main (最新コミット `48e339b`, 2026-10-21)、Zenodo 23303289 v1、arXiv 2606.19624 v1 (MassSpecGym in the Wild)、FRIGID arXiv 2604.16648 (最新版 = v3 相当)、MassSpecGym 論文 (arXiv 2410.23326)、旧 MIST (`samgoldman97/mist` main_v2)、`samgoldman97/mist-cf`。
- 注意: GitHub のソースは要約付きフェッチャで読んだため、逐語引用は短い断片のみ。関数名・定数・既定値は複数回の照会で一致したものだけ書き、確認できないものは「未確認」とした。導入後に `grep` で再確認すること (6 章 A0)。
- 略語: MSG = MassSpecGym、ckpt = チェックポイント、CLS = 前駆体トークン、aug / noaug = `mist_msg_aug.ckpt` / `mist_msg_noaug.ckpt`。

## 要約

1. **新規スペクトル用の推論手順は repo に無い。** 公式の予測コマンド `mist-predict-fingerprints` (`src/mist/data/input_signal.py`) は MSG/CANOPUS 形式の compact キャッシュしか受け付けない (split = val/test、dataset_name = msg_all/canopus_all のみ)。新規スペクトルでは、同じ形式の配列を自前で作るか、`ScaledMIST` を直接呼ぶ薄いラッパーを書く必要がある。
2. **必須入力はピーク列、前駆体の中性分子式、付加体 (正イオン 7 種のみ) の 3 つ。** 前駆体 m/z はピーク除外 (m/z ≤ prec+1) にしか使わない。衝突エネルギーはモデルに入らない。装置名は保存されるが `embed_instrument=False` (既定値、MSG の設定でも未指定) のため実質使われない。
3. **ピークへのサブフォーミュラ割当は `src/mist/data/featurizers.py::assign_subformulae`。** 与えた式の部分式を列挙し、20 ppm 以内で割り当てる (誤差の分母は max(m/z, 200))。MAGMa も MIST-CF も使わない。MSG の学習特徴は `msg_all/subformulae/no_subform.hdf5` の事前計算済み割当から作られており、その生成方法は書かれていない。
4. **式は単なるラベル。** 「真の式か」の検査も前駆体 m/z との整合検査も無いので、**候補の式ごとに 1 回ずつ呼ぶ運用はそのまま可能**。質量の整合は自分で課す必要がある。repo には検索 (retrieval) コードも未知式の扱いも無い。公表されている唯一の未知式での運用例は「MIST-CF の上位 5 式で FP を 5 本作り要素ごとの max を取る」もの (MSG in the Wild 表 8、質量ベース候補で hit@1 28.23%)。
5. **Zenodo の中身:** MIST の ckpt 4 本 (各 289.2 MB、EMA 重みのみ、7,230 万パラメータ)、GLACIER 2 本、データアーカイブ 6 本 (計 16.0 GB)。今回必要なのは `mist_msg_{aug,noaug}.ckpt` と、検証用の `msg_compact.tar.gz` (15.7 MB)・`msg_all.tar.gz` (292 MB) だけ。
6. **依存は torch>=2.7, numpy, pandas, h5py, pyyaml, rdkit のみ。** Lightning・DGL・C/CUDA 拡張は無く、純 PyTorch。ARM64 + CUDA 13 + Python 3.11 は、Spark で既に動いている torch (2.7 以上) を流用できれば障害になりにくい。GLACIER 部分だけは DGL などが要るが、今回は不要。
7. **パディングマスクのバグは現行 repo で修正済み。** バグは bool マスクを `attn += attn_mask` でそのまま加算していたもの。現行コードでは -inf のマスクに変換してから加える。ただし、バッチサイズ・並び順で結果が変わらないことを確かめるテストは repo に無い。推論は eval + inference_mode + FP32 で、シード固定は無い。`mist-evaluate` は TF32 を有効にしているため、`mist-predict-fingerprints` と数値が僅かにずれ得る。
8. **aug / noaug の検索性能 (hit@k) は公表されていない。** 唯一の公表値は aug (= FRIGID の "MIST 4M-aug") の MSG test 平均 FP Tanimoto 0.433 (閾値 0.1879101470、EMA step 430,965)。noaug は数値の公表が無い。天然物 (NP) や timsTOF での評価も見つからなかった。
9. **付加体の制約:** MSG の学習付加体は [M+H]+ と [M+Na]+ のみで、合成データも同じ。CASMI の他の正イオン 4 種は語彙にはあるが未学習、負イオン 4 種は非対応。
10. **計画:** 許可を得てから、Spark 上で次の 4 つの事前確認を通す。(A) 公表値との整合、(B) バッチ・順序で結果が変わらないこと、(C) 特徴化が MSG キャッシュと一致すること、(D) MSG 上の小規模な検索評価。その後、CASMI dev (約 1,000 スペクトル × 約 250 候補) について「候補の式ごとに 1 回」条件付けしたスコアを 2 つの ckpt で計算して比較する。推論の計算量は GPU で数分以内の見込み (推定)。

## 1. 新規スペクトルの推論パイプライン (Q1)

### 1.1 入口と制約
- `mist-predict-fingerprints` → `mist.data.input_signal:main` → `predict_input_signal(checkpoint_path, cache_path, output, allow_test_input, batch_size=256, num_workers=4, device_name="cuda:0")`。
- キャッシュの検査: `manifest.json` の `schema_version==1`、`kind=="real_spectrum"`、`split∈{val,test}`、`dataset_name∈{msg_all,canopus_all}` (ckpt の `config["data"]["dataset_name"]` と一致必須)。part ごとに `form_vec/ion_vec/intens/peak_type/lengths/instruments/names.npy`。名前の重複は ValueError。test split では `--allow-test-input` が必須で、val に付けるとエラーになる。
- 読み込み: `torch.load(..., weights_only=False)` → `ScaledMIST(**ckpt["config"]["model"])` → `load_state_dict(ckpt["ema_model"], strict=True)` → `.eval()` → `torch.inference_mode()`。autocast は無い (FP32)。DataLoader は `shuffle=False`。
- バッチ辞書のキー: `form_vec`・`intens` (float32)、`ion_vec`、`types` (= peak_type)、`num_peaks` (= lengths)、`instruments` (いずれも int64)。
- 出力: `probabilities.npy` (float32, N×4096)、`spectrum_names.npy`、SHA-256 付きの `manifest.json`。
- 新規スペクトルの作り方は README にも docs にも無い。docs/data.md が説明しているのは MSG/CANOPUS キャッシュの再構築 (`mist-build-real-cache`) だけ。

### 1.2 必要な入力
| 入力 | 使われ方 | 根拠 |
|---|---|---|
| ピーク (m/z, 強度) | 割当の対象。merge 経路では次の順に処理: m/z を小数 4 桁に丸めて統合 → m/z ≤ prec+1 → 強度を sqrt(I/max) → 上位 60 → 0.001 超を残す | `featurizers.py::merge_ms_spectrum` |
| 前駆体 m/z | merge 経路のピーク除外だけ (.ms ヘッダの `parentmass`/`pepmass`。無ければ 1e6) | 同上 |
| 前駆体の**中性**分子式 | **必須** (docs/data.md: "A precursor formula is required")。CLS の元素ベクトルになり、全フラグメント割当の上限にもなる | `featurizers.py`, `datasets.py` |
| 付加体 | `ION_LST` = [M+H]+, [M+Na]+, [M+K]+, [M-H2O+H]+, [M+H3N+H]+, [M]+, [M-H4O2+H]+。未知の付加体は KeyError、負イオンは無い。CLS と全フラグメントに同じ付加体を付け、one-hot (8 次元) で入力 | `utils/chem_utils.py`, `models/modules.py` |
| 装置 | `instruments.npy` に保存される (fticr 0 / iontrap 1 / orbitrap 2 / qtof 3 / unknown 4。"Bruker Q-ToF (LCMS)" と "QTOF" は qtof)。ただし `embed_instrument=False` のためゼロ行列に置き換わり、使われない | 同上、`configs/*/msg.yaml` (model キーに無し) |
| 衝突エネルギー | 使わない。MSG は CE ごとのレコード (`<spec>_collision <CE>.json`) | `data/datasets.py` |

- 元素の語彙は 18 種 `C H As B Br Cl Co F Fe I K N Na O P S Se Si`。これ以外の元素は `formula_to_dense` で ValueError になる。
- 元素数は 254 以下が前提 (`pos-cos` 埋め込みの `MAX_COUNT_INT=255`)。

### 1.3 サブフォーミュラ割当
`src/mist/data/featurizers.py` の各関数:
- `_heavy_formula_space(formula)` (lru_cache 付き): 前駆体式の非 H 元素を 0..n の全組合せで列挙する。各組合せの H 上限は min(floor(2·RDBE), 前駆体の H 数)。
- `assign_subformulae(tree, mass_diff_thresh=20.0)`: ピークごとに H 数を最寄りの整数に丸め、誤差が最小の部分式を選ぶ。`abs_err / max(m/z, 200) * 1e6 < 20` なら採用する。
  - 同じ式に複数のピークが当たっても統合しない (旧実装は強度を合算していた)。
  - 前駆体ピークも通常のフラグメントとして残る。
- `PeakFormula._peak_dict`: データセットで経路が分かれる。
  - MSG: `no_subform.hdf5` の JSON (`cand_form`, `cand_ion`, `output_tbl{mz, ms2_inten, formula, ions, …}`) を読む。表が壊れているときだけ再割当する。
  - CANOPUS (`merge_collision_energies=True`): `spec_files.hdf5` の `.ms` を `merge_ms_spectrum` → `assign_subformulae` でその場で計算する。
  - どちらも強度の降順で上位 `max_peaks` (既定 10) 本を取る。`tree["cand_form"]` がラベルの式と違えば ValueError (式の整合性チェックはこれだけ)。
- `PeakFormula.featurize`: フラグメント行 (peak_type 0) の末尾に CLS 行を足す。CLS は前駆体式・前駆体の付加体・強度 1.0・peak_type 3。
- 呼び出し元は `mist-build-real-cache` (`mist.data.build_all_cache`、`--max-peaks 10 --subformula-ppm 20.0`)。
- MAGMa は新実装に無い (`ScaledMIST` は MAGMa ヘッドを削除済み。旧実装でも学習時の補助ラベル専用)。MIST-CF も新 repo には含まれない。
- 旧実装での対応物: `samgoldman97/mist` の `src/mist/subformulae/assign_subformulae.py` (labels の `formula`/`ionization` 列を使う。20 ppm、max-formulae 50) と `src/mist/utils/spectra_utils.py::process_spec_file` (max で正規化 → sqrt)。新しい `merge_ms_spectrum` は同じ前処理を再現している。

### 1.4 真の式でない式でも動くか / 未知式の扱い
- **動く。** 式は文字列のラベルにすぎず、与えた式の部分式でピークを割り当てて CLS にその式を入れるだけ。したがって次の使い方がそのままできる。
  - 候補構造の式ごとに (スペクトル, 式, 付加体) の行を作り、1 回ずつ推論する。同じ式の候補は予測 FP を共有する。
  - 質量窓から列挙した式や、MIST-CF の予測式を与える。
  - いずれの場合も、|m(式)+付加体 − prec| ≤ 許容誤差 の検査は自前で行う。
- **repo 自体の扱い:**
  - 新 repo には retrieval コードが無い。`mist-evaluate` は、正解 FP との Tanimoto を測るだけ。
  - 旧 repo は、式が既知という前提で同式 PubChem 候補を cos 順に並べる (`quickstart/01_run_models.sh` → `retrieval_fp.py`)。式の推定は MIST-CF に委ねている。MIST-CF は別 repo で、候補式を SIRIUS 5.5.7 の `decomp` (linux64) で列挙し、正イオン専用、公開モデルは NPLIB1 で学習。
  - FRIGID と DiffMS は真の式を与える設定で評価しており、「式は MS1 から BUDDY/MIST-CF で推定可能」と書いているだけ。
- **公表されている未知式での運用 (MSG in the Wild §4.3、表 2・表 8):** 質量ベース候補で、候補は式で絞らない。
  - MIST-CF の top-1 式 → hit@1 26.64%。
  - top-5 式で FP を 5 本作り要素ごとに max → hit@1 / hit@5 / hit@20 = 28.23 / 40.77 / 56.22。
  - 真の式 → hit@1 51.45%。
  - どの ckpt を使ったか、式ごとに割当を計算し直したかは書かれていない。
  - データ安全版 MIST-CF の式正解率は top-1 50.5%、top-5 73.2% (表 7)。

## 2. Zenodo 23303289 の中身 (Q2)

- v1、公開 2026-10-20。作成者は Hongxuan Liu (MSG in the Wild の筆頭著者)。MIT、計 16.0 GB。
- 関連識別子は GitHub repo だけで、コミットは指定されていない。

| ファイル | サイズ | 内容 |
|---|---|---|
| `mist_msg_noaug.ckpt` | 289.2 MB | MSG の実データのみで学習 (ピーク脱落・強度ジッタは使用) |
| `mist_msg_aug.ckpt` | 289.2 MB | MSG の実データ + GLACIER 合成 78,450,500 行 (refined-4M) |
| `mist_canopus_{noaug,aug}.ckpt` | 各 289.2 MB | CANOPUS (NPLIB1) 用。aug は random-2M・4,000 万行 |
| `glacier_{msg,canopus}.ckpt` | 各 54.3 MB | 合成スペクトルの生成器 |
| `msg_compact.tar.gz` | 15.7 MB | 特徴 (train 194,119 / val 19,429 / test 17,556 行 = MSG 全件) |
| `msg_all.tar.gz` | 292.1 MB | `labels.tsv` (spec, formula, ionization, instrument, smiles, inchikey)、`spec_files.hdf5`、`subformulae/no_subform.hdf5`、`splits/split.tsv` |
| `msg_synthetic.tar.gz` | 12.1 GB | 合成特徴 (今回は不要) |
| `canopus_all` / `canopus_compact` / `canopus_synthetic` | 84.6 MB / 976 kB / 2.3 GB | CANOPUS 用 |

- **SHA-256** (`src/mist/artifacts.json` から転記。`mist-download` が取得時に自動で照合する):
  - noaug: `6f8df582df36aa4a984f120efee14ee0a62f3a7723caa770b856a6e704236727`
  - aug: `9f251d772f68315ba6fe2dc75a3b2e1ec477d3f41ffbeaf5143749157b67b177`
  - msg_compact: `a19e657a802cf5869d97b3486c7ce41021cba9c9a6279818e5d186307e3e7a35`
  - msg_all: `f8665e6a3be019ddb6adaa5f87bc670634d4bb5965fdd3e583bd81918008463c`
  - Zenodo の MD5 は noaug `80594e4d…`、aug `3e921792…`。
- **ckpt の中身:** `config` (`model` と `data.dataset_name`)、`ema_model` (EMA 重み)、`step`。推論専用で、学習の再開はできない (Zenodo の記述)。
- **対応するコード:** Zenodo v1 (10-20) と GitHub `48e339be6535546c87ba4f6b81a0f787c2e4ac40` (10-21、"Publish Zenodo artifact downloads and checkpoint documentation"。artifacts.json に SHA-256 を登録したコミット)。その前の `8c03c5d` (10-20) は CANOPUS の CE 統合で、MSG には関係しない。ckpt を作ったコミットは明記されていない。**`48e339b` に固定し、ckpt 内の config と step を記録する**のが妥当。
- **学習レシピ** (`configs/{noaug,aug}/msg.yaml`、`docs/training.md`):
  - 共通: hidden 1024・16 head・peak attention 4 層・refine 4 層・ペア特徴あり・no_diffs・`pos-cos`・出力 4096・72,296,996 パラメータ。損失は cos 1.0 + Tanimoto 0.1 + iterative 0.4。bf16 で学習し EMA を使う。
  - noaug: 1 GPU、batch 77 × 累積 4、30,000 step で停止 (120,000 step の cosine スケジュールの途中)。AdamW 3.75e-4。実データ約 48 パス。
  - aug: 4 GPU、1 rank あたり実 75 + 合成 2,048、478,850 step、Adam 2e-4、EMA ≈ 0.9975。val で最良の ckpt を出力。実データは約 740 パス反復される。
  - FRIGID v3 によると、aug は EMA step 430,965 で、閾値 0.1879101470 (val で on-bit 数が一致するよう校正)。
- **合成データ** (FRIGID v3 App. B.2.3): MSG v1.0 公式の約 4M 未ラベル分子から、test と MCES 距離 2 以内の分子を除いた 3,922,525 分子 × 20 (付加体・装置・CE の組合せ) = 78,450,500 行。GLACIER は MSG train で学習されており、扱えるのは [M+H]+/[M+Na]+ と Orbitrap/QTOF のみ (`docs/glacier.md`)。
- **ckpt が期待する特徴** (docs/data.md)。W = max_peaks+1 = 11 (既定値。実際の値は manifest で要確認)。

| 配列 | 形状 / 型 | 内容 |
|---|---|---|
| `form_vec` | [N,W,18] int16 | 元素数 (上記の順) |
| `ion_vec` | [N,W] uint8 | ION_LST の index (行内はすべて同じ付加体) |
| `intens` | [N,W] float16 | 強度 (CLS は 1.0)。**MSG で sqrt 変換済みかは要確認** |
| `peak_type` | [N,W] uint8 | 0 = フラグメント、3 = CLS (1 行に 1 個、末尾)。パディングは 0 |
| `lengths` | [N] uint8 | CLS を含む有効トークン数 (1..W) |
| `instruments` | [N] uint8 | 装置の index (モデルでは未使用) |
| `names` | [N] Unicode | 行 ID |

- **候補 FP** は `mist.data.atlas.morgan4096_packed` で作ると学習ターゲットと完全に一致する。中身は `rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=4096)` (キラリティ無し) で、`np.packbits(bitorder="little")` で 512 バイトに詰める。

## 3. 依存と環境 (Q3)

- **依存:** `pyproject.toml` (1.0.0) は `requires-python >=3.10`、依存は `h5py numpy pandas pyyaml rdkit torch>=2.7` (torch 以外はバージョン指定なし)、test 用に `pytest ruff>=0.17`。`environment.yml` も同等 (チャネルは pytorch と conda-forge)。
- **不要なもの:** PyTorch Lightning、DGL、PyG、torch-scatter はいずれも不要。C/C++/CUDA 拡張は無い。注意機構は `torch.bmm`/`einsum`/`softmax` で書かれており、SDPA も flash attention も使わない。`compile` は off なので Triton も不要。
- **GLACIER (`mist-glacier-predict`) だけは別:** ms-pred (rev `708148c`)、DGL 1.1.3、torch-scatter 2.1.2、PyG、PL 1.9.5 が必要 (検証環境は Py3.10 / PyTorch 2.7.0)。ARM64 + CUDA 13 では DGL が障害になり得るが、MIST の推論には不要。
- **ARM64 (GB10) + CUDA 13 + Py3.11:** 純 PyTorch なので、Spark で既に動いている torch (2.7 以上か要確認) を流用すれば動く公算が高い。rdkit と h5py には aarch64 用 wheel がある。repo に書かれた動作実績は PyTorch 2.7.0 / CUDA 12.8 (RTX PRO 6000 ×2 ノード) だけ。
- **Kaggle:**
  - T4 (sm_75) は問題ない。
  - P100 (sm_60) は、PyTorch 2.8 以降の CUDA 12.8/12.9 ビルドでは非対応 (CUDA 12.6 ビルドのみ対応。[PyTorch dev-discuss](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128))。実質 T4 か CPU。
  - イメージの torch が 2.7 未満なら `--no-deps` で入れて動作を確認する (2.7 固有の API を使っているかは未確認)。
- **速度とメモリ:** 文書化されていない。以下は**推定 (未計測)**。
  - 重みは 72.3M × 4 B ≈ 289 MB で、ckpt のサイズと一致する。
  - 1 行あたり約 1.5 GFLOP (11 トークン + 121 ペアの特徴)。
  - T4 の FP32 で毎秒 1,000〜2,000 行、Kaggle の CPU で毎秒 30〜70 行。
  - batch 256 の活性メモリは 1〜2 GB 以下。

## 4. 既知の落とし穴 (Q4)

### 4.1 パディングマスクのバグ (MSG in the Wild §6.1、App. A.8)
- **内容:** 旧 MIST と DiffMS の注意機構は、bool のパディングマスクを `attn += attn_mask` でそのまま加算していた。その結果、パディング位置に有限の +1 が乗るだけで、softmax から除外されない。単一スペクトルでは発生せず、パディングを伴うバッチ (学習・推論の両方) で発生する。修正値を計算したのに捨てて生の bool を足す「変種」もある。正しい修正は `zeros_like(dtype=q.dtype)` に `masked_fill_(mask, -inf)` してから加算すること。
- **影響例:** バグ入りで学習された MIST vDiffMS ckpt + MolForge の結果。
  - top-1: batch 24 で 31.75% → 単一スペクトルで 10.73%。
  - MIST Tanimoto: 0.812 → 0.457。
  - 著者らはこの水増しを学習レシピから再現できず、リークに似たパターンだとしている。vDiffMS の MSG bonus hit@1 46.42% は信用できない。
- **現行 coleygroup/MIST:** `src/mist/models/transformer_layer.py` の `_scaled_dot_product_attention` と `_additive_attn` の両方で、マスクを -inf に変換してから加えている → **修正済み**。
  - マスクは `FormulaTransformer.forward` で `~(arange < num_peaks)` から作る。
  - パディング位置の出力はプーリング前に 0 にされ、プーリングは CLS 位置だけで行う。
  - 公開 ckpt がこの修正版コードで学習されたという明示は無い (同じ著者が同時期に公開しているので修正版だと推定)。
- **MassSpecGym 側:** 論文は MassSpecGym v1.5 にも修正版 MIST が入るとしている。しかし MassSpecGym の main (v1.5 マージは 2026-05-08) では、論文に書かれたパス `massspecgym/models/encoders/mist/transformer_layer.py` が 404 で、所在は未確認。

### 4.2 決定性、バッチサイズと並び順
- 推論にはシード固定も deterministic 設定も無い。dropout は eval で無効になる。
- キャッシュは全行を固定幅 W にパディングするので、マスクが正しければ理論上はバッチ構成に依存しない。残るのは GEMM カーネルの選択による浮動小数点の差だけ。
- repo のテスト (`tests/test_formula_transformer.py`、`test_inference_workflow.py`) には、バッチサイズ・並び順・パディングで結果が変わらないことや、CPU と GPU の一致を確かめるものが**無い** → 自分で確認する。
- `mist-evaluate` は TF32 を有効にしている (`set_float32_matmul_precision("high")`、`allow_tf32=True`) が、`mist-predict-fingerprints` は FP32。GB10 では両者の確率が僅かに異なり得る (T4 には TF32 が無い)。
- `CompactFeatureDataset` の `index` は狭義単調増加しか許さない。したがって並び順を入れ替えるテストは CLI ではできず、ラッパーで行う。

### 4.3 その他
- **付加体:** MSG の学習付加体は [M+H]+/[M+Na]+ のみ (MSG 論文の図 4)。他の ION_LST 項目に対応する one-hot の重みは実質初期値のまま。負イオンは扱えない。
- **式リーク:** 質量ベースの評価で真の式を与えると、hit@1 が約 2 倍になる (51.45% 対 26.64%)。dev 評価では、真の式も真の式から導いた情報も使わないこと。
- **学習分子の重複:** MSG の train/val 分子と 4M 合成分子は、CASMI dev の公開ライブラリ分子と重なり得る。重なった分の dev 指標は水増しになる。aug は実データを約 740 パス反復しているため、記憶の効果も強い可能性がある。
- **撤回された旧 ckpt:** FRIGID v2 時代の ICEBERG 拡張 MIST ("MIST vFRIGID"、bonus hit@1 53.76%) は、後にテスト情報を使っていたと判明して置き換えられた。Zenodo の aug はその後継 (GLACIER 4M-aug)。
- **MSG の JSON 経路:** featurizer は m/z ≤ prec+1 の除外も sqrt 変換も行わず、JSON 作成時の前処理に依存する (作成方法は非公開)。
- **pickle の読み込み:** `torch.load(weights_only=False)` を使うので、SHA-256 を照合してから読む。

## 5. 報告されている数値 (Q5)

| モデル / 設定 | 候補 | hit@1 | hit@5 | hit@20 | MCES@1 | 出典 |
|---|---|---|---|---|---|---|
| MIST (MSG 論文のベースライン) | 質量 (≤256) | 14.64 | 34.87 | 59.15 | 15.37 | MSG 論文 表 5 |
| 同上 | 同式 (bonus) | 9.57 | 22.11 | 41.12 | 12.75 | 同上 |
| MIST + 真の式 (ckpt 不明) | 質量 | 51.45 | — | — | 6.98 | MSG in the Wild 表 2 |
| MIST + MIST-CF top-1 (データ安全版) | 質量 | 26.64 | — | — | 16.41 | 同 表 2 |
| MIST + MIST-CF top-5、max 集約 | 質量 | 28.23 | 40.77 | 56.22 | 15.51 | 同 表 8 |
| MIST vDiffMS (バグ・リークの疑い) | 同式 | 46.42 | 54.74 | 66.27 | 7.72 | 同 表 3 |
| MIST vFRIGID (旧版、撤回) | 同式 | 53.76 | 65.32 | 74.71 | 5.16 | 同 表 3 |

- 表の数値はすべて MSG の MCES 分割 (閾値 10) の test fold での値。
- **aug (= MIST 4M-aug):** MSG test の FP Tanimoto は 0.433 (閾値 0.1879101470。FRIGID v3 の表 6)。比較対象の vDiffMS は、単一スペクトルで 0.457、batch 24 で 0.812。**hit@k は未報告。**
- **noaug:** 数値の公表が無い。
- **NP と timsTOF:** 旧 MIST 論文は NPLIB1 (GNPS 由来の天然物) で評価している (canopus ckpt の系統)。timsTOF での評価は見つからなかった。MIST は装置を入力に使わないので、timsTOF に特化した適応も無い。

## 6. 最小実行計画 (許可後に実行。現時点では何も実行していない) (Q6)

**Step 0 — 許可をもらう項目:**
- Spark への clone (`48e339b` に固定) と、venv への `pip install -e .`。
- Zenodo からの取得: ckpt 2 本 (各 289 MB)、`msg_compact` (16 MB)、`msg_all` (292 MB)。合成データ (12 GB) は取らない。
- MSG v1.5 の検索候補 (手元に無い場合のみ)。
- 後で Kaggle に private Model / Dataset としてアップロードすること。
- 証跡として、URL・DOI・コミット・SHA-256・取得日時 (`date`) を記録する。ホストが条件にしている「学習コードとデータアクセスの文書化」もこれで満たす (`configs/*/msg.yaml`、`scripts/train_recipe.sh msg-{aug,noaug}`、MSG の HF、GLACIER)。

**Step 1 — 環境構築 (Spark):**
```bash
git clone https://github.com/coleygroup/MIST.git ~/ext/MIST && cd ~/ext/MIST
git checkout 48e339be6535546c87ba4f6b81a0f787c2e4ac40
python3.11 -m venv --system-site-packages ~/venvs/mist && . ~/venvs/mist/bin/activate
python -c "import torch;print(torch.__version__,torch.version.cuda,torch.cuda.get_device_name(0))"  # >=2.7
python -m pip install --no-deps -e . && python -c "import h5py,pandas,yaml,rdkit"   # 不足分だけ追加
pytest -q
for a in msg-noaug msg-aug msg-compact msg-source; do mist-download "$a" --output-dir downloads; done
mkdir -p checkpoints && mv downloads/mist_msg_*.ckpt checkpoints/
tar -xzf downloads/msg_compact.tar.gz && tar -xzf downloads/msg_all.tar.gz   # repo ルートで展開 (Zenodo の指示)
```

**Step 2 — 事前確認 (どれかが不合格なら CASMI には進まない):**
- **A0. 静的な確認:** `grep` で `attn += new_attn_mask`、`embed_instrument`、`max(float(mass), 200.0)` を確かめる。ckpt のキー・`config.model`・`step` (aug は 430,965 の想定)・パラメータ数 72,296,996 を表示する。`manifest.json` で max_peaks = 10 を確認する。
- **A. 公表値との整合:**
  ```bash
  for v in aug noaug; do
    mist-evaluate --checkpoint checkpoints/mist_msg_$v.ckpt --cache data/compact/msg/val --output runs/eval/$v-val
    mist-evaluate --checkpoint checkpoints/mist_msg_$v.ckpt --cache data/compact/msg/test --output runs/eval/$v-test \
      --threshold-file runs/eval/$v-val/threshold.json --allow-test
  done
  ```
  合格条件: aug の閾値が 0.18791 から ±1e-3 以内、test の平均 Tanimoto が 0.433 から ±0.01 以内。FRIGID の評価集合は 17,082 件の可能性があるので、件数の差は許容する。noaug の閾値はここで初めて得られる。
- **B. バッチと並び順で結果が変わらないこと:**
  - CLI で `mist-predict-fingerprints --cache data/compact/msg/test --allow-test-input` を `--batch-size 256` と `--batch-size 1 --num-workers 0` の 2 通りで実行し、比較する。
  - ラッパーで、並び順をシャッフルした場合と、長さの違う行を混ぜた場合を確かめる。
  - 500 行で CPU と GPU の出力を比べる。
  - 合格条件: 同じデバイスなら max|Δp| ≤ 1e-5、CPU と GPU なら ≤ 1e-4。候補の順位は同点を除いて一致。
- **C. 特徴化のパリティ:**
  - `msg_all` の JSON を 20 件読み、強度の慣行 (最大値が 1 か、sqrt 済みか、prec+1 超のピークがあるか) を確定する。
  - `.ms` の生ピークと真の式から自前の特徴化で配列を作り、`msg_compact` の test の行と比べる。
  - 合格条件: form_vec・ion_vec・peak_type・lengths は 99.5% 以上の行で完全一致、intens の差は 1e-3 以下 (float16 のため)。
- **D. MSG での小規模な検索評価:** MSG test と v1.5 の候補 (質量ベースと同式) を使い、2 つの ckpt それぞれで次の 3 条件を比べる。aug / noaug の hit@k はここで初めて得られる。
  - (i) 真の式: 健全性の確認用。
  - (ii) 候補ごとに自分の式で条件付け: 式は未知という扱い。
  - (iii) 説明強度の上位 k 式の FP を集約。
- **E. 自前ラッパーと CLI の一致:** 同じデバイスと batch で、確率がビット単位で一致すること。

**Step 3 — CASMI dev (約 1,000 スペクトル × 約 250 候補)。ファイルは `experiments/mist/` に置く案:**
- **`mist_rows.py`:** スペクトルごとに次の手順で行を作る。
  1. 付加体を下の表に従って対応付ける。
  2. 候補の中性分子式 (RDKit の `CalcMolFormula`) の集合 F_s を作る。電荷を持つもの・語彙外元素・同位体は除く。
  3. 質量が整合しない式を落とす。
  4. 自前のピークを `>parentmass` 付きの `.ms` テキストにする。
  5. `merge_ms_spectrum` → `assign_subformulae(tree, 20.0)` → 上位 10 本 + CLS (`PeakFormula.featurize` と同じ並び) で配列を作る。repo の関数をそのまま import して使う。
  6. 割当ピーク数と説明強度の割合も保存する。
- **`mist_infer.py`:** ckpt ごとに FP32・batch 256 で推論する。確率は float16 で保存し、manifest (コミット、SHA-256、torch/CUDA のバージョン、デバイス、batch、日時) を付ける。
- **`mist_score.py`:** 候補 FP を `morgan4096_packed` で作り、次のスコアを計算する。
  - スコアの種類: cos(p_{s,f(c)}, x_c)、ベルヌーイ対数尤度、val で校正した閾値での Tanimoto。
  - 分子単位の集約: 対応している付加体のスペクトルについて平均する。
  - 変種: V1 = 自分の式で条件付け、V2 = 説明強度が最大の式 1 本、V3 = 上位 5 式の要素ごとの max。
- **評価:**
  - 指標: hit@1/5/20、MRR、同式の候補だけでの MRR。
  - 層別: MSG での分割 (train/val/test/不在。公式スコアラーキーで照合)、4M 集合に含まれるか (aug のみ)、付加体 (そのまま / 代理 / 非対応)、timsTOF かそれ以外か、NP かどうか。
  - aug 対 noaug は分子単位のペア bootstrap で比べる。locked セットを開ける前に事前登録する。
- **付加体の対応 (提案。未検証):**

| CASMI の付加体 | MIST での扱い |
|---|---|
| [M+H]+, [M+Na]+ | そのまま (学習済み) |
| [M-H2O+H]+ / [M-2H2O+H]+ | 式を M−H2O / M−H4O2 にして [M+H]+ として代理 |
| [M+NH4]+ | 式 M の [M+H]+ として代理 (前駆体付近のピークを除去) |
| [M+K]+ | 既定では欠測扱い (未学習の index 2 は実験としてのみ試す) |
| 負イオン 4 種 | 非対応 (欠測フラグを立てる) |

- **計算量:** 行数は Σ_s |F_s| で、dev では 1 万〜3 万行 / ckpt 程度の見込み。GPU で 1 分前後 (推定)。

**Step 4 — Kaggle:**
- `src/mist` (MIT。LICENSE と NOTICE も同梱) を Dataset に、ckpt を private Model に置き、オフラインで `pip install --no-deps --no-index` する。
- T4 で動かし、torch のバージョンを確認する。Spark と同じ 200 行で E のパリティを確かめる。
- 全確率を保存するとメモリが大きくなるので、バッチごとにスコアへ畳み込む。

## リスクと未確認事項
1. **性能が未知:** aug / noaug の検索性能は未公表で、D で初めて分かる。noaug は 30k step で止めた短い学習で、品質も公表されていない。
2. **MSG 特徴の作り方が非公開:** MSG の `no_subform.hdf5` をどう作ったか (sqrt の有無、ppm、ピーク除外) が書かれていない。C で確かめないと、CASMI の特徴が学習分布からずれる。
3. **誤った式で条件付けしたときの挙動が未検証:** 文献にあるのは MSG in the Wild の top-5 集約だけ。自分の式で条件付けすると式ごとに自己整合的な FP ができるので、式をまたぐ比較が歪む可能性がある → 式の妥当性は別の特徴 (説明強度など) で補う。
4. **付加体の制約:** [M+H]+/[M+Na]+ 以外は未学習で、負イオンは扱えない。CASMI の一部の分子では MIST の特徴が欠測になるか、代理に頼ることになる。
5. **dev の水増し:** MSG の train/val 分子や 4M 合成分子と重なる分、dev 指標が水増しされる。層別しないと、隠しテストへの転移を過大に見積もる。
6. **ckpt の素性:** ckpt を作ったコミットも、修正版コードで学習されたことも明示されていない (推定で補っている)。
7. **Kaggle 環境:** torch の版、P100 が非対応であること、オフライン導入、pickle の読み込み。速度とメモリは推定値。
8. **MassSpecGym v1.5:** 修正版 MIST とデータ安全版 MIST-CF の所在が未確認。MIST-CF は SIRIUS (x86_64) に依存し、正イオン専用。
9. **ホストのルール:** canopus の ckpt はホスト裁定の文言 (MSG で学習したもの) から外れるので、使うなら別途確認する (NIST 由来でないことも含めて)。
10. **読み取りの精度:** ソースは要約フェッチャ経由で読んだため、行レベルの細部 (例: 同じ式の重複ピークの扱い、H の上限式) は導入後に原文で再確認する。

## 出典
- coleygroup/MIST: https://github.com/coleygroup/MIST (README, docs/data.md, docs/training.md, docs/glacier.md, pyproject.toml, environment.yml, configs/{noaug,aug}/msg.yaml, src/mist/data/{input_signal,build_all_cache,featurizers,datasets,data,atlas,compact,augmentation}.py, src/mist/utils/chem_utils.py, src/mist/models/{scaled_mist,modules,transformer_layer,form_embedders}.py, src/mist/{evaluate_scaled,download}.py, src/mist/artifacts.json, tests/)
- Zenodo 23303289: https://zenodo.org/records/23303289 (DOI 10.5281/zenodo.23303289)
- MassSpecGym in the Wild: https://arxiv.org/abs/2606.19624 (§4.3, §6.1, 表 2–4・7・8, App. A.1.2/A.2.2/A.2.3/A.8)
- FRIGID: https://arxiv.org/abs/2604.16648 (表 6, 表 12, App. B.2.3), https://github.com/coleygroup/FRIGID
- MassSpecGym: https://arxiv.org/abs/2410.23326 (表 5, 図 4), https://github.com/pluskal-lab/MassSpecGym
- 旧 MIST: https://github.com/samgoldman97/mist (main_v2: quickstart/01_run_models.sh, src/mist/subformulae/assign_subformulae.py, src/mist/utils/spectra_utils.py)
- MIST-CF: https://github.com/samgoldman97/mist-cf
- GLACIER: https://arxiv.org/abs/2606.29161
- DiffMS: https://github.com/coleygroup/DiffMS (README は Zenodo 23303289 の ckpt を参照)
