# Rules on Open weights?
topic 742193 | by **Barno Barno** (https://www.kaggle.com/barnobarno) | posted 2026-09-20 | votes 1 | comments 2 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/742193

Are all open weights models fair game or does one have to check & make sure if their training corpus/training data source is openly available ?

## Comments (2 top-level)

- **David Healey** **[HOST]** (2026-09-20, votes 0)
  Good question. We can’t blanket approve all open weights models. It should be fine as long as the open weight model is distributed in compliance with the license for the data it was trained on. 
  
  For example there are proprietary commercial mass spec data sets that restrict redistribution of themselves or derivatives like model weights. Publishing such model weights under an open source license would still be in violation.
- **David Healey** **[HOST]** (2026-09-25, votes 1)
  I will add here some clarification about what we have in mind.  Many datasets (MassSpecGym perhaps) are functionally open source and many prominent open source models train on them.  These are fine for solutions, as are any models trained on this competitions train.parquet, which is compiled from open-source data.  (enveda-np-examples we neglected to assign a specific license to but should also be considered open source)
  
  The most illustrative example of a dataset that would be restricted is NIST.  NIST is not freely available (must be purchased), and its license heavily restricts any kind of redistribution of itself or derivatives including trained model weights.  There are also fully commercial datasets like METLIN and those distributed by the mass spec companies (Thermo, Bruker, SciEx).  Also to avoid.
