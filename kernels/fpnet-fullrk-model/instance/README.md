# casmi26-b1-fpnet-fullrk (private) — FPNet weights trained by us for the B1 pipeline (ranker-table variant)

**What**: one FPNet checkpoint (`full_rk_final.pt`; spectrum -> fingerprint logits; 49.7M parameters; sha256 in `SHA256SUMS`) trained on
2026-10-25 on our own machine (RTX 5070 Ti, Windows) with the public training recipe (fresh initialisation), plus everything needed to reproduce it:
`TRAINING_MANIFEST.json` (full training arguments read from the checkpoint, sha256 of every code file / input / record, environment, final
evaluation), `code/` (exact code used) and `records/` (input gate, split, dropped rows, exposure ledger, holdout lists).

**Training code**: `code/train_fivefold.py` = the public trainer of `dmitriigluzdov/casmi26-fold-safe-fpnet` (Dmitrii Gluzdov), run through
`code/train_fivefold_win2.py`, generated from it by `code/make_win_trainer.py` (fork -> spawn, per-worker memory-mapped data, SIGHUP guard,
recipe-aware input gate; optimisation recipe unchanged: 82,855 updates, batch 256, lr 3e-4 with warm-up and cosine decay, wd 0.01, seed 0,
8 layers, d 512). Model, spectrum preprocessing and data access: `code/casmi/` = the `casmi` package of `ahmedberatozer/casmi26-v3-models`
(Ahmed Berat Ozer). Fingerprint bits `fp_bits.npy` of `ahmedberatozer/casmi26-v2-pool` unchanged.

**Data**: MS/MS-structure supervision comes only from the competition `train.parquet` (no NIST-derived data). Prepared by `code/prep_full_rk.py`:
the query acquisitions of our evaluation molecules (enveda-np-examples panel, W7 = `records/w7_eval_set_p1_molecules.csv`, eval_c1 =
`records/eval_c1_p1_molecules.csv`) are removed at spectrum level together with identity-group duplicates (similarity >= 0.95; 6,943 rows),
and the identity groups of dev2 (hold), locked2 (lock) and the ranker-fit molecules (rkfit = `records/rkfit_p1_run1_p1_molecules.csv`) are
held out (`records/split.parquet`; overlap with the trainer's training set computed as 0, `records/gocheck.json`). Decoys for the ranking
loss are sampled from the whole v2 pool (training structures and COCONUT-derived structures). The purpose of this variant is to build ranker
training tables in the "identity seen, query unseen" regime (`records/query_identity_exposure.csv`).

**Use**: loaded by the B1 submission pipeline with `--fpnet_ckpt full_rk_final.pt` (repository https://github.com/Satsuki-Tam/CASMI2026,
`experiments/b1_baseline/b1_pipeline.py`); the run manifest of each kernel records the checkpoint sha256.

**Licence / terms**: the weights are derived from competition data and are subject to the competition data terms (non-commercial use with
attribution). Code keeps its original licences (casmi package and trainer as published by their authors; our scripts in the repository above).
