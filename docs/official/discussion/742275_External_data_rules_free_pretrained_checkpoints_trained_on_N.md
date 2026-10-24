# External data rules: free pretrained checkpoints trained on NIST-derived spectra
topic 742275 | by **Ghaisan K** (https://www.kaggle.com/ghaisank) | posted 2026-09-21 | votes 0 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/742275

Hi, a question about Rule 2.6.a, which says external data must be "publicly available and equally accessible … at no cost".

Several published MS/MS models release their pretrained checkpoints for free under permissive licences (MIT or Apache), but their training spectra came partly from NIST-derived collections (for example NPLIB1), which are not free to obtain.

Are such checkpoints acceptable for use in a winning submission, given that the checkpoint itself is free and publicly available but part of the data it was trained on is not?

Thank you!

## Comments (1 top-level)

- **Frenio Redeker** (2026-09-23, votes 0)
  My sense is that pretrained models published under MIT or Apache licenses are fine if their public release wasn't in itself in violation of the licenses of their underlying training data.
  
  Edit: Just pasting an exchange from a different thread  (https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/742193) below since it seems relevant.
  
  Rules on Open weights?
  
  Barno Barno:
  
  "Are all open weights models fair game or does one have to check & make sure if their training corpus/training data source is openly available ?"
  
  David Healey (Competition Host):
  
  "Good question. We can’t blanket approve all open weights models. It should be fine as long as the open weight model is distributed in compliance with the license for the data it was trained on.
  
  For example there are proprietary commercial mass spec data sets that restrict redistribution of themselves or derivatives like model weights. Publishing such model weights under an open source license would still be in violation."
