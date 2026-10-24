# All submissions since Sep 16 fail or score 0 - hidden test rerun issue
topic 742463 | by **woldy** (https://www.kaggle.com/woldywei) | posted 2026-09-22 | votes 0 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/742463

My full-pipeline notebooks have failed every submission since Sept 16 evening (previously scored fine, best 0.233), while the same kernel versions run cleanly interactively. Minimal kernels (passthrough, byte-exact train lookup, offline wheel installs + model loading) all score fine, so the rerun channel and attached datasets are healthy - only the full pipeline fails, now wrapped in fallbacks so it scores 0.000 instead of throwing. Since interactive runs on pinned inputs succeed, the difference is the hidden test itself. Could the hosts check the server-side rerun logs for my submissions (woldywei/casmi26-evidence-v12..v17)? Thanks!

## Comments (1 top-level)

- **inversion** **[Kaggle]** (2026-09-23, votes 0)
  We are unable to provide individual support for unsuccessful runs. This is a list of things that might help.
  
  https://www.kaggle.com/code-competition-debugging
