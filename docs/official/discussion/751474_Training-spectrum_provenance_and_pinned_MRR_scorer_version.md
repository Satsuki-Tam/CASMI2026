# Training-spectrum provenance and pinned MRR scorer version
topic 751474 | by **fagbola peter** (https://www.kaggle.com/fagbolapeter) | posted 2026-10-21 | votes 0 | comments 0 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/751474

I'm evaluating source-independent library matching in the Enveda CASMI 2026 training data. Is there a released or obtainable crosswalk from each training Parquet row — by zero-based row ordinal or another stable identifier — to its original library record/accession and its original acquisition or raw run/scan? For merged or redistributed spectra, could that crosswalk include parent record and acquisition IDs, or explicitly mark lineage as unknown? A source-library label alone can't distinguish a new measurement from a copy of one already represented in another library.

My preserved train.parquet has SHA-256 9423f90ec08b941a9646b535bf0606183e86ff0c5a297978f5a70693d41bcd98. Does that hash identify the currently distributed training revision? If not, is a row crosswalk available for that earlier revision as well as the current one? A versioned file hash and exact field definitions would let me join the mapping reliably.

Could you also identify the scoring notebook version or scriptVersionId currently pinned to this competition, and whether the same version was used for leaderboard scores on 13 October 2026? The Overview links to the public scorer, but its current public revision doesn't establish the competition deployment pin.

## Comments (0 top-level)

