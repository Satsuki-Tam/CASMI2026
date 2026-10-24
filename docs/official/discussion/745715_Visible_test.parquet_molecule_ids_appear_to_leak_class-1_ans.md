# Visible test.parquet molecule_ids appear to leak class-1 answers
topic 745715 | by **Zihao Ou** (https://www.kaggle.com/nicholasooo) | posted 2026-10-03 | votes 22 | comments 11 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/745715

A public notebook (imranarif536/casmi26-v44-pairtail-locked-top1, V3, 0.417) hard-codes the 400 visible molecule_id → SMILES pairs (the structures of the train spectra copied into the dummy test file) and forces them to rank 1 for every row, unguarded; its previous version scored 0.402. That is only possible if (a) the hidden rerun reuses the visible molecule_ids and (b) for a substantial share of ids the dummy row's structure equals the hidden truth. Forks are spreading (two dozen teams at 0.416–0.418). Could you confirm whether molecule_ids are shared between the visible file and the hidden set, and shuffle/remap them before the final rerun? We are not using this and would prefer a level field.

## Comments (10 top-level)

- **Patrick Chan** (2026-10-03, votes 3)
  Can the admin confirm if the shuffle/remap will be done? Above is accurate according to my test.
- **Amin** (2026-10-04, votes 1)
  +1 from our team. We do not use the visible molecule_id → structure pairs in any way (ids only join rows in our pipeline), and we would welcome a shuffle/remap of the ids before the final rerun so the final leaderboard reflects spectrum-based identification only. Could the hosts also confirm whether the hidden rerun currently reuses the visible ids?
- **Bharath Varma** (2026-10-04, votes 0)
  +1: please remap the test molecule_ids (or confirm they are not shared) before the final rerun
  
  Thanks @NicholasOOO (/NicholasOOO) for raising this. Our team doesn't use the visible molecule_id → structure pairs either, and we'd also prefer a level field.
  
  As described above, the visible test.parquet is a placeholder built from training spectra, so each visible molecule_id can be joined back to a known structure. If the hidden rerun reuses the same IDs, and the placeholder structure matches the hidden truth for some of them, ranking those structures first raises the score without any spectrum-based identification.
  
  Two small requests to the hosts:
  
  Could you confirm whether the hidden rerun currently uses the same molecule_id values as the visible file?
  If it does, please remap or shuffle the IDs (and ideally build the visible placeholder from structures that aren't in the hidden set) before the final private rerun.
  
  Thanks for looking into this. It would be great for the final leaderboard to reflect identification from the spectra alone.
- **Pratham** (2026-10-04, votes 0)
  Good finding. Hosts should clarify this.
- **Raagav Anand** (2026-10-05, votes 0)
  My tests re-confirm this. Can something be done about this? 
  People who use the visible molecule ID will get a huge advantage, atleast in the open test cases
  
  I'm optimistic that those types of predictions will fail in the hidden test cases, but it's fairly easy to just a run a check beforehand and operate differently on hidden test cases, so I wouldn't back this too much
  
  Ty in advance
- **kenneth uchegbu** (2026-10-05, votes -2)
  please can anyone give a guide on how to use neural networks alongside the morgan, maccs fingerprints on how to retrieve structures and also how to go about the ranking.
- **kenneth uchegbu** (2026-10-05, votes -2)
  are you in need of a team member?
- **Ranger789** (2026-10-06, votes 2)
  +1 from our team. We don't use the visible molecule_id to structure pairs in any form, neither in submissions nor for diagnostics, and we'd welcome a remap or shuffle of the molecule_ids before the final rerun (ideally with the visible placeholder built from structures outside the hidden set), so the final leaderboard reflects identification from the spectra alone. Thanks for raising this.
    - **MarvinTMB** (2026-10-09, votes 0)
      A remap before the end would be great
- **MY** (2026-10-06, votes 0)
  Anyone from hosts gonna answer??
- **inversion** **[Kaggle]** (2026-10-07, votes 4)
  There is no overlap in IDs between train and test, or between dummy test and rerun test. It's a relatively low-observation test set, so participants should be careful that they don't interpret noise with causation.
