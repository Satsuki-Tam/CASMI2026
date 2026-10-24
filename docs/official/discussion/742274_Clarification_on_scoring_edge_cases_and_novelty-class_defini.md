# Clarification on scoring edge cases and novelty-class definitions
topic 742274 | by **Ghaisan K** (https://www.kaggle.com/ghaisank) | posted 2026-09-21 | votes 0 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/742274

Hi, thanks for hosting this competition. A few clarification questions so that local validation can match the official evaluation exactly:

- Empty entries in the prediction list. How does the evaluator treat an empty entry inside the semicolon-separated list, for example A;;B? Is B counted at rank 2 or rank 3? And does a trailing ; count as a guess, or could such a row be rejected?

- Reference implementation of the metric. Would you be able to share the evaluation code, or a reference implementation, including the exact RDKit 2026.03.3 tautomer canonicalisation settings used before taking the InChIKey first block? That would let everyone reproduce the scoring precisely.

- Novelty classes and COCONUT. The data page defines class 2 as structures in PubChem or COCONUT, and class 3 as structures not in PubChem at all. Can a class 3 molecule be present in COCONUT (in COCONUT but not in PubChem), or is class 3 absent from both databases?

Thank you!

## Comments (1 top-level)

- **David Healey** **[HOST]** (2026-09-23, votes 0)
  Hi, and thank you for participating!
  
  - Empty entries are discarded before ranks are assigned. A;;B is read as two guesses, so B is at rank 2, not rank 3. A trailing ; is not a guess and does not affect your score;
  
  - The evaluation code is linked in the Overview section.  It is here: https://www.kaggle.com/code/metric/casmi-mean-reciprocal-rank. 
  
  - Class 3 is absent from both PubChem and COCONUT.
