# casmi26-b1-fpnet-fulleval (private) — FPNet weights trained by us for the B1 pipeline

**What**: one FPNet checkpoint (`full_eval_final.pt`; spectrum → fingerprint logits; 49.7M parameters; sha256 in `SHA256SUMS`) trained on
2026-10-25 on our own machine (RTX 5070 Ti, Windows) with the public training recipe, plus everything needed to reproduce it:
`TRAINING_MANIFEST.json` (full training arguments read from the checkpoint, sha256 of every code file / input / record, environment, final
evaluation, repository commit), `code/` (exact code used) and `records/` (gate, split, dropped rows, audits, holdout lists).

**Training code**: `code/train_fivefold.py` = the public trainer of `dmitriigluzdov/casmi26-fold-safe-fpnet` (Dmitrii Gluzdov), run through
`code/train_fivefold_win.py`, generated from it by `code/make_win_trainer.py` (fork → spawn, per-worker memory-mapped data, SIGHUP guard,
recipe-aware input gate; the optimisation recipe is unchanged: 82,855 updates, batch 256, lr 3e-4 with warm-up and cosine decay, wd 0.01,
seed 0, 8 layers, d 512). Model, spectrum preprocessing and data access: `code/casmi/` = the `casmi` package of `ahmedberatozer/casmi26-v3-models`
(Ahmed Berat Özer). Fingerprint bits `fp_bits.npy` of `ahmedberatozer/casmi26-v2-pool` unchanged (sha256 c3869e86…).

**Data**: MS/MS–structure supervision comes only from the competition `train.parquet` (no NIST-derived data). The spectrum cache was rebuilt with
the public builder `casmi.build.build_spec_cache` from a copy of train.parquet without the rows in `records/dropped_train_rows.json` (1,196 rows:
all 1,184 enveda-np-examples spectra and 12 same-molecule duplicates of them in other libraries; recomputed and verified). Identity groups of
our evaluation sets dev2 (500) and locked2 (500) are held out (`records/split.parquet`); the overlap of held-out groups with the trainer's actual
training set (`Data.tr`) was computed as 0 (`records/gocheck.json`). Every identity fold is trained (no held-out fold): 2,524,870 training
spectra. Decoys for the ranking loss are sampled by `traindata.Data.negatives()` from the whole v2 pool (training structures and
COCONUT-derived structures, `ahmedberatozer/casmi26-v2-pool`). Panel near-copy audit (`records/panel_dup_audit_summary.json`): no panel query
has a remaining training spectrum with similarity ≥ 0.95 in its identity group (265 keys); 48 molecules with ≥ 0.90 are listed as "uncertain"
in `records/panel_molecule_audit_groups.csv` (fixed before evaluation).

**Use**: loaded by the B1 submission pipeline with `--fpnet_ckpt full_eval_final.pt` (repository https://github.com/Satsuki-Tam/CASMI2026,
`experiments/b1_baseline/b1_pipeline.py`); the run manifest of each kernel records the checkpoint sha256.

**Licence / terms**: the weights are derived from competition data and are subject to the competition data terms (non-commercial use with
attribution). Code keeps its original licences (casmi package and trainer as published by their authors; our scripts in the repository above).
