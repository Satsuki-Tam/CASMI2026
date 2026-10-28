# How much of a +0.005 public gain is real? A noise model for a ~125-molecule leaderboard
topic 753511 | by **Akhil nath reddy** (https://www.kaggle.com/akhilnathreddy) | posted 2026-10-28 | votes 0 | comments 0 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/753511

With 258 teams tied at 0.472 and many forks separated by 0.002–0.005, I wanted to know what the public board can actually resolve. Below is a small simulation with its assumptions stated, so you can swap in your own.

Setup. Public ≈ 125 molecules (31% of ~400), private ≈ 275. Compare two submissions where a share q of molecules change between them, each by one rank-1 ↔ rank-2 swap (±0.5). The ~0.016 standard error Udam Liyanage reported (https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/743254) corresponds to q ≈ 0.13 here.

Two submissions with no true difference

q
SE public
SE private
P(public ≥ +0.005)
P(|public| ≥ 0.010)

0.05
0.010
0.007
0.27
0.31

0.10
0.014
0.010
0.34
0.47

0.20
0.020
0.013
0.38
0.62

Winner's curse: pick the best public score of K variants that all have zero true gain (q = 0.10).

K variants
Expected public gain of the best
Private gain

3
+0.012
0

7
+0.019
0

20
+0.026
0

A real gain of +0.005: the public board shows it as a loss 31% of the time, and the private board 27%.

What I take from it

- One public comparison can't separate +0.005 from zero. Even a ±0.010 swing happens by chance in about half of comparisons when 10% of molecules change.

- Picking the best of 7 probes adds about +0.019 of pure noise on public, none of which carries to private.

- Identical submissions get identical private scores, so the 0.472 block will move together. A real gain moves you past that whole block at once.

- A paired offline comparison on 600 held-out molecules has a standard error of ~0.0065, about half the public board's. That's where decisions should be made.

Caveats. The rank-change model is crude. Real changes include misses turning into hits (worth up to 1.0), which makes noise larger. Probes from the same pipeline are correlated, so the winner's-curse numbers are an upper bound for very similar variants.

import numpy as np
rng = np.random.default_rng(0)

def paired_diff(n, q, e, size):
    # with prob q a molecule's rank changes by one 1<->2 swap (+/-0.5); e = share improving
    changed = rng.random((size, n)) < q
    up = rng.random((size, n)) < (1 + e) / 2
    return np.where(changed, np.where(up, 0.5, -0.5), 0.0).mean(axis=1)

pub = paired_diff(125, 0.10, 0.0, 200_000)          # public, no true gain
print("SE public:", pub.std(), "P(>= +0.005):", (pub >= 0.005).mean())
best7 = paired_diff(125, 0.10, 0.0, 140_000).reshape(-1, 7).max(axis=1)
print("best of 7, expected public gain:", best7.mean())

A question for you: on your own validation set, what share of molecules change their top-1 between two of your variants? That q sets your noise floor, and I'd like to calibrate this with real numbers. Also, if anyone has pinned down the public split size more precisely, I'll update the tables.

## Comments (0 top-level)

