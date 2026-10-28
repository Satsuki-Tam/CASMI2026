# CFM-ID 4 pretrained models (trained on METLIN) — eligible for prize-winning solutions?
topic 743774 | by **gennexuslabsDDM** (https://www.kaggle.com/gennexuslabsddm) | posted 2026-09-27 | votes 2 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/743774

Hi David, a follow-up to threads 741912 (CFM-ID spectra generated from COCONUT structures are compliant) and 742193 / 742991 (weights derived from proprietary libraries such as NIST or METLIN are not eligible).

The ESI models shipped with CFM-ID 4 (cfm-pretrained-models/cfmid4 in the Bitbucket repo, and the Docker image) were trained on METLIN. The CFM-ID 4.0 paper states: "We used experimental ESI-MS/MS data obtained from the Scripps Research Institute's Metlin MS database to train CFM-ID 4.0" (Wang et al., Anal. Chem. 2021). The same stock models produced the public ISDB in-silico spectral libraries (CC BY 4.0) that some participants may be using.

Could you clarify which reading is right for a prize-eligible solution?
(a) CFM-ID 4 as shipped, and spectra predicted with its stock models (including ISDB), are fine because the tool itself is LGPL and publicly available; or
(b) the stock models count as METLIN-derived weights and are not eligible, so CFM-ID could only be used after retraining (cfm-train) on open data such as train.parquet or MassSpecGym.

Thanks — better to know now than at solution review.

## Comments (1 top-level)

- **David Healey** **[HOST]** (2026-09-27, votes 0)
  Thanks for this question. CFM ID 4 is fine.  It's published by a major lab in a major journal, so we'll proceed with the assumption that the authors had permission to distribute the weights.
