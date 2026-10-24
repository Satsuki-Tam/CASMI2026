# Looking to merge: validation harness + own FPNet pipeline, 30 GPU h/week (public LB 0.413)
topic 745952 | by **YahiaZakaria20** (https://www.kaggle.com/yahiazakaria20) | posted 2026-10-05 | votes 0 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/745952

Hi all, I'm looking to merge with a team before the Dec 7 deadline, ideally one in the 0.42+ range that wants more validation and compute behind its pipeline.

Where I am: public LB 0.413 with a fork of the public fusion pipeline (v4 engine + engine 2 + PubChem channel + ICEBERG/GLACIER). Everything below is built on top of it and runs offline as Kaggle kernels.

What I bring

- Three-mask validation on the fusion pipeline. Class-1 (other libraries' spectra stay), class-2 (all spectra of the structure purged), and a class-3 mode that also removes the held-out structures from the engine pool, the PubChem "already in pool" set and the PubChem gate window. Current numbers: 0.933 / 0.630 / 0.347.

- Exact local replay of the fusion stage. It runs from stage dumps on CPU and reproduces the kernel's validation score to the fourth decimal, so a 50-setting grid over the fusion and re-ranking knobs costs no GPU.

- An FPNet training kernel in the v4 engine's checkpoint format. It uses BCE plus hard negatives from the 10 ppm pool window, merge augmentation, and bit-prior initialisation. It holds out np-examples, so its checkpoints are leak-free on validation and drop straight into the engine bank.

- 30 GPU hours a week, and time to spend on this until the end.

Lessons I can save you a submission on

- On the np-examples split, the v4 engine ranks the truth first for 236/250 molecules, yet the fused list keeps only 100. Locking the engine's confident picks lifts validation from 0.63 to 0.89, but the leaderboard went from 0.413 to 0.409. Those structures are well-documented training structures, so they do not behave like the test's class 2, which is in COCONUT or PubChem without spectra.

- A second FPNet trained with the public recipe lands close to bank A (0.548 vs 0.579 window MRR) and adds about 0.002 in the ensemble. More of the same model is not where the next points are.

What I'm looking for: a team with its own ideas for class 2 and class 3 (formula-first ranking, forward models, de novo generation, extra legal reference spectra) that would benefit from a validation harness and extra GPU budget. Reply here or DM me

## Comments (1 top-level)

- **?** (2026-10-11, votes 0)
  
