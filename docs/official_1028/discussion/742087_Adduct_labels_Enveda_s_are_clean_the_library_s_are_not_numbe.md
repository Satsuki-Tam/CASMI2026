# Adduct labels: Enveda's are clean, the library's are not (numbers)
topic 742087 | by **DancingLumberjack** (https://www.kaggle.com/jamesmcgarryiv) | posted 2026-09-19 | votes 1 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/742087

We measured whether "wrong adduct label" is a recall problem worth handling in candidate generation. Library-wide it looks like one: 6.9 % of NP-library rows in train.parquet (174,977 of 2,532,125) have a labelled-adduct neutral mass more than 10 ppm from the true structure, and on a 40,000-row random sample of those an alternative adduct hypothesis lands within 10 ppm for 40.1 %. But 12,043 of the 16,037 rescues are [M+CH2O2-H]- (formate) mislabels — a GNPS/MassBank curation artefact, not an acquisition effect.

Per molecule on the Enveda-curated enveda-np-examples structures (the set that shares the hidden test's provenance): 0 of 250 miss the truth under their labelled adduct. On a GNPS-heavy held-out set: 8 of 350 miss, 7 rescuable.

Two takeaways: (1) do not spend effort in candidate generation on adduct re-hypothesis for the test — Enveda label their own adducts correctly; (2) if you train on the library, the formate mislabels are worth cleaning or down-weighting.

## Comments (1 top-level)

- **Frenio Redeker** (2026-09-24, votes 0)
  Thank you, that's helpful. Two questions:
  
  - How many of the 174,977 rows whose neutral mass is more than 10 ppm off can be explained with low mass accuracy measurements, e.g. they were acquired on a triple quadrupole instrument?
  
  - Does the majority of the formate mislabels have a uniformly wrong label or are they all over the place?
  
  Thanks again!
