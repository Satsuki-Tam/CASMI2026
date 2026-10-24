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

## Status
- 2026-10-25 04:45: assets downloaded and mirrored to the Spark; cells extracted; port not started (the submission flow had priority).
