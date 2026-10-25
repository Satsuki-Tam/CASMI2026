# E0 offline: run the public 0.464 pipeline on OUR molecules (the key experiment for a proper evaluation)

Goal: per-molecule, per-stage comparison of E0 (public lineage, `kernels/baseline-v18/casmi26-baseline-v18.ipynb`) and B1 on the same
molecules (dev A/B 600, panel 250), in the class-2 proxy (the molecule's own spectra removed from train) and the class-1 proxy (kept).
This turns the LB gap (E0 0.464 vs B1 fixed 0.334 / learned 0.322) into "where exactly does B1 lose".

## Assets (downloaded 2026-10-25 03:00–04:17, mirrored to the Spark under data/external_kaggle/)
- `casmi26-natural-product-knowledge-table/` (130 MB): natural_products.parquet, external_reference_spectra/, candidate_joins.parquet, descriptors.parquet
- `casmi26-attributed-v4g-reproduction-assets/` (20 GB, 220 files): casmi26-glacier/, casmi26-iceberg/ (+wheels), casmi26-v2-pool/, casmi26-v3-models/code/casmi,
  casmi26-v4b-models/code/casmi, casmi26-fpnet-full1/, casmi26-fp-models-v2/, casmi26-pubchemlite-cc0-candidate-fingerprints/, coconut-casmi26-candidates/,
  casmi-chebi-lmsd-structures/, chebi-lipidmaps-casmi26/, hengck23-dreams-enveda-casmi26/ (6.4 GB), pubchem_tier__pc_{mass,off,smiles}.npy, rdkit wheels,
  casmi26-ranker-features/, casmi26-simulated-ranker-rows/
- already present (data/external/): fold_safe_fpnet, pubchem_popularity, panel_benchmark

## Port plan (Spark; cells extracted to cells/NN.py)
1. Input tree: create `<run>/kaggle_input/` with symlinks `competitions/enveda-CASMI26-molecule-id-mass-spectra/{train,test}.parquet,sample_submission.csv`
   and `datasets/<slug>/...` for the five datasets (the notebook finds datasets by `glob('/kaggle/input/**/<slug>/<marker>')`; `locate_data_dir()` also
   accepts `data/raw`). Patch the string `/kaggle/input` -> `$E0_INPUT` and `/kaggle/working` -> `$E0_WORK` in the extracted cells (sed at run time).
2. Test file: `CASMI_TEST_PATH` = our test-format parquet (`make_eval_test.py` output, e.g. eval_test_full3/test.parquet); its spectrum ids differ
   from the dummy test, so `IS_RERUN` is true and all molecules are processed.
3. Class-2 proxy: `train.parquet` with the evaluation molecules' own rows removed (`exclude_rows_c2.json` of the same eval_test dir) placed next to the
   test file as the competition data dir (`locate_data_dir` -> that dir). Class-1 proxy: the full train.parquet.
4. Simulators: the notebook preseeds a pip site from `casmi26-iceberg/wheels` (`_claw_preseed_site`); on the Spark use `.venv-ice` (GB10 patches) and
   pass `--site none` to the runners (same runner lineage as ours). RDKit 2026.03.3 is in `.venv`; the notebook asserts that version in the main process.
5. Outputs to keep per molecule: engine-1 / engine-2 lists, PubChem channel list, library merge decision (`lib_max`), final submission; join with B1's
   `b1_candidates.parquet` by official identity -> stage table (not in window / not in shortlist / ranked lower) and per-class paired deltas.
6. Runtime estimate: 400 molecules ~4 h on a T4; the GB10 should be faster. Run dev A/B (600) first, then the panel (250).

## Port (2026-10-25, fork of the night session)
- `e0_prepare.py shared` builds `runs/_shared/kaggle_input/datasets/dmitriigluzdov/<slug>/` per-file symlink mirrors in the **Kaggle layout** (the per-file download had nested every file
  under its own directory twice and flattened some names), with the GB10-patched runner packages (`data/external/{iceberg,glacier}`; only `src/ms_pred/nn_utils/{nn_utils,dgl_graph_ops}.py`
  differ from the asset copies) and the PubChem tier arrays mounted where the notebook finds them (`casmi26-pubchem-popularity-prior/casmi26-pubchem-tier/`). It also builds the proxy train
  files: `train_c2_<tag>.parquet` (every train row of the truth identity removed via `train_scorer_keys.parquet`, alternative notations included) and `train_c1_<tag>.parquet` (query rows +
  same-library references removed, other libraries kept = B1's C1 view). `e0_prepare.py run` writes a run's competition dir (our test file in the real test schema, sample_submission, train link).
- `run_e0_offline.py` executes cells 00-22 in one namespace with textual patches (all recorded in `<work>/e0_port_manifest.json`): paths, plotting stubs, Python-3.11/GB10 observer asserts,
  no pip, runners in `.venv-ice` through `spark/jobs/ice_resume.py` (`--site none`), budgets from the CLI, merge-decision + engine-1 candidate audit hooks, relaxed stage-status asserts
  (recorded instead). Model code, weights, candidate generation, fusion rules and thresholds are the notebook's own. Outputs per run: `submission*.csv` after each overlay, `eng_lists.json`,
  `pc_lists.json`, `e0_base_lists.json` (engine-1 top-60 with scores), `e0_engine1_candidates.parquet` (window candidates with provenance + component features), `e0_{ice,gl}_scores.json`,
  `e0_merge_decisions.json`, `e0_n1.json`, `e0_frag_gap.json`, `e004_candidate_inputs.json`, audits, `e0_run_audit.json` (budgets, coverage, runner part metas, hashes).
- Missing assets found and fetched (local Kaggle CLI, then scp): `casmi26-pubchem-popularity-prior` delta/growth supplements + `pc_formula_isomers.npy` + `pc_different_parent_rows.npy`
  (-> `data/external_kaggle/casmi26-pubchem-popularity-prior/`), `casmi26-fold-safe-fpnet` `MANIFEST_FIVEFOLD.json` / `check_inputs_fold*.json` (-> `data/external_kaggle/casmi26-fold-safe-fpnet/`;
  without them the PubChem channel asserts and silently falls back to "base lists only"). `dreams_np_{mass,smiles}.npy` (cell-17 tail filler when < 25 valid candidates) exist in none of the
  five mounted datasets' current versions -> filler inactive (recorded as optional-missing).
- Smoke (5 molecules, C2 proxy, `runs/smoke5`): all 23 cells ok in 7 min (engine 2 ≈ 290 s fixed cost); engine-2 lists 5, PubChem lists 5, ICEBERG 5/5 and GLACIER 5/5 scored on cuda
  (rdkit 2025.03.6 runner venv, 59 / 271 pred/s), N1 0 blind molecules, merge untouched 1 / gentle 4, rank-2 overlay inserted 2.
- `spark/jobs/spark_e0_chain.sh` runs c2_full3 (W7 600, C2 proxy) -> c1_full3 -> panel_c2 -> panel_c1 (panel test file built with `make_eval_test.py --sets P_np250`, 1086 spectra),
  each followed by `e0_vs_b1_stages.py` when a B1 pipeline run of the same view exists (`eval_test_full3/run_{c2,c1}`; none yet for the panel).

## Status
- 2026-10-25 04:45: assets downloaded and mirrored to the Spark; cells extracted; port not started (the submission flow had priority).
- 2026-10-25 07:42 JST: **c2_full3 launched** on the Spark (`spark_e0_chain.sh`, PID 1410949 / run PID 1410952, log `logs/spark_e0_chain.log` + `logs/e0_c2_full3.log`;
  budgets ICE 21600 s / GL 10800 s / N1 3600 s, NUMBA 4 threads). Hook smoke `runs/smoke5c` running in parallel.
- 2026-10-25 07:46 JST: hook smoke `runs/smoke5c` passed (engine-1 candidate audit 395 rows / 5 molecules; `e0_run_audit.json` written).
- 2026-10-25 07:53 JST: `e0_vs_b1_stages.py` rewritten to the Codex-016 ledger layout (ledger.csv / stages.csv / candidates.parquet / gates.csv / summary.json / report.md;
  C2 leak audit = truth rows remaining in the run's train.parquet + truth lib_nspec in the engine + B1 truth lib_nref / in_train; per-component training-overlap flags;
  loss classes candidate_absent / dropped_at_shortlist / pushed_down_by_merge / forward_missing_reranked_lower / reranked_lower / dropped_in_fusion_overlays). Validated on
  `runs/smoke5c` against `eval_test_full3/run_c2` (2 min; 595 molecules without an E0 list excluded from the paired statistics). The chain runs it after each full run.
  Known gaps: B1's fused per-candidate score is not written by the pipeline (lists only); E0 stage times are run-level (the notebook does not time per molecule);
  E0 window identity counts use E0's own score_key (top lists are re-canonicalised with src/metric.py); the truth remains a pool train structure in E0's analog set
  (structure-level membership, flagged per molecule, not removable without rebuilding sha-pinned assets).
- 2026-10-25 09:41 JST: c2_full3 **failed at cell 17**: `AssertionError('Engine 2 did not cover all active molecules')` — engine 2 returned 593 of 600 lists. The 7 missing
  molecules (all B_nplib: 6 gnps, 1 massbank; positive mode) have an EMPTY candidate window in engine 2 (`casmi_engine.py`: `if not len(r["cand"]): continue`, no entry written):
  5 of them have low-precision / wrong precursor m/z (203.7, 353.8, 278.4, 1181.02 → 780–144,000 ppm; LDXZRRQKXWEUAR 10.9 ppm, just outside ±10 ppm; `window_any` False in
  p1_molecules.csv — B1 also scores 0 on all 7), 2 are multi-adduct ToF molecules (UTULUEQFRJAYOL, YKFXSYSRTPPQBX: [M+H]+/[M+K]+/[M+NH4]+/water losses) whose window is tiny
  (pool 5 / 14) and empty in engine 2 (its single target mass over mixed adducts). Engine-1 base lists are empty for all 7; the PubChem channel returned lists for 5.
  ICE (596/596, 3870 s) and GL (595/596) had finished; cells 08 1002 s, 09 816 s, 12 498 s, 13 4671 s, 15 111 s.
- Patch (recorded in `e0_port_manifest.json`, 45 patch records): cells 17 and 19 record the coverage instead of asserting (`e0_engine2_coverage.json`, `engine2_uncovered` in
  `e0_run_audit.json`; `eng[mid]` → `eng.get(mid, {})` in the cell-19 payload); the ledger has `e0_engine2_covered` per molecule and a stratum table. `--reuse <work dir>`
  (job env `REUSE_FROM`) copies engine-2 / PubChem lists, restores the engine-1 base lists + candidate audit, seeds ICE/GL through `ice_resume.py --seed --reuse_complete`
  and copies the N1 output when its input is identical; refused unless test sha / limit / proxy train file match. `--dry_run` patches + compiles every cell and checks
  that every `E0_*` name a patched cell uses exists in the namespace (the first relaunch at 09:55 failed on exactly that: helpers not injected into the cell namespace).
- 2026-10-25 09:57 JST: `spark/jobs/spark_e0_chain2.sh` launched (old chain bash stopped; its child c1_full3 left running to collect caches): **c2_full3r** (reuse of
  `runs/c2_full3/work`: all lists reused, ICE 595 reused + 1 rerun = 596/596 in 13 s, GL 595/596 partial as before, cell 17 recorded 593/600) → wait for the first c1_full3
  to end (it will fail at cell 17 at about 11:50) → **c1_full3r** (reuse of `runs/c1_full3/work`) → panel_c2 → panel_c1; the ledger runs after each W7 run.
- 2026-10-25 10:18 JST: **c2_full3r done** (E0 10:10, ledger 10:18; `runs/c2_full3r/{work,compare}`, mirrored locally without the large per-candidate files).
  Headline (600 paired molecules, C2 proxy, official scorer replica, unreached truth = 0): E0 final **0.681** vs B1 main (blend21 + fallback) **0.616** / insurance 0.510;
  Δ(E0 − B1 main) **+0.065 [+0.028, +0.102]**; A_timstof −0.071 [−0.116, −0.026] (E0 0.718 / B1 0.790), B_nplib **+0.201 [+0.145, +0.255]** (E0 0.644 / B1 0.443);
  by split role: fit (B1 ranker training groups) −0.002, tune +0.084, eval **+0.112 [+0.049, +0.176]**. Leak audit: truth train rows remaining 0/0 (E0/B1), truth in E0's
  external refs 1 molecule, all 600 truths are pool train structures (E0 structure-level membership flag). E0 stage MRR on the same molecules: engine-1 base-60 0.939
  (model-level overlap: engine-1's models saw every molecule) → merge 0.907 → **fuse2 + GLACIER (cell 15) 0.696** → final 0.681: on these molecules E0's own fusion with
  engine 2 / GLACIER costs 0.21 against its (leaky) engine-1 list. The PubChem channel never holds the truth here (recall 0.000) because it lists keys NOT in the pool and
  every truth is a pool structure — its hidden-test value is unmeasurable on train-derived sets. B1 recall: window 0.958, **shortlist 0.755**; molecules only E0 gets right
  (top-1) by the B1 stage that lost them: not_in_shortlist **54**, rank>1 40, lost_fusion 1; E0 wins Σ Δ +79 over 120 molecules B1 lost at the shortlist. Where both have
  the truth (E0 loss class reranked_lower, n 269) B1 is better (0.538 vs 0.393). Engine 2 covered 593/600 (7 empty windows, both systems 0 there).
- 2026-10-25 10:3x JST: B1 panel pipeline runs (M2x blend21, eval mode) are at `runs/_shared/eval_test_panel/run_{c2,c1}`; chain2 had been launched with empty
  `B1_PANEL_*`, so `spark/jobs/spark_e0_panel_compare.sh` (detached) waits for each panel E0 run and produces `runs/panel_{c2,c1}/compare/` against them.
  Ledger note: B1 library values come from `b1_stage_stats.csv` / `b1_candidates.parquet`, never from pipeline log lines (the progress-line "lib_max>=0.6" statistic
  contradicts the 21 lib_priority firings in C1 and is not used).

