# Clarification on pretrained weights and training code
topic 750612 | by **Truthseeking** (https://www.kaggle.com/truthseeking) | posted 2026-10-19 | votes 0 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/750612

Clarification on pretrained weights and training code

Following the discussion on train.parquet and open-source models: does the requirement to provide "original training code and access to permitted training data" apply to models trained exclusively on train.parquet? For example, if a competitor releases weights for an FPNet model trained only on train.parquet but does not release the training script, are those weights eligible for use in a winning solution?

## Comments (1 top-level)

- **Marie Killian** **[Organizer]** (2026-10-19, votes 0)
  No, the requirement applies to all weights, including competitor released weights trained on train.parquet. You need to have access to the original training code to include weights in your solution.
