# Why the visible split says 0.99 and the leaderboard says 0.41: twenty negative results from CASMI26, with controls
topic 752846 | by **Marco Pereira** (https://www.kaggle.com/marcofpereira) | posted 2026-10-26 | votes 1 | comments 0 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/752846

9.2 The number that should stop you from optimising on the visible split

A competition ships two splits. If the visible one is drawn from the same rows as the
provided training data, then a pipeline measured on it is measuring itself.

We can quantify this, and it is not a small effect.

The measurement. We rebuilt one of our own submissions offline — the exact same
payloads, replayed through the exact same fusion code, producing a submission.csv
that matched our submitted file in 400 of 400 rows. We then scored that file
against the answers, which are present in the provided train.parquet because the
visible test rows are training rows.

## Comments (0 top-level)

