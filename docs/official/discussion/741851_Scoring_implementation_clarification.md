# Scoring implementation clarification
topic 741851 | by **Burhan Çalık** (https://www.kaggle.com/burhanalk) | posted 2026-09-17 | votes 1 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/741851

Two questions about how submissions are scored, so that local validation lines up with the leaderboard.

1) Is the scoring code, or the exact RDKit call sequence and settings, documented anywhere? Locally I count a guess as correct when the first 14 InChIKey characters match after: Chem.MolFromSmiles(smiles), then rdMolStandardize.TautomerEnumerator().Canonicalize(mol), then Chem.MolToInchiKey(mol)[:14], using RDKit 2026.03.3 with the default CleanupParameters (maxTautomers=1000, maxTransforms=1000, tautomerRemoveSp3Stereo=True). If the official pipeline differs anywhere, for example an extra standardization or sanitization step before canonicalization, different enumerator parameters, or a different key length, local scores would drift from the leaderboard.

2) Do guesses that RDKit cannot parse, or guesses that reduce to a key already used earlier in the same row, still take up their rank position? I drop unparseable SMILES and deduplicate by the canonical key before writing, so I do not rely on either behaviour, but it affects how I read my own submissions.

Thanks!

## Comments (1 top-level)

- **inversion** **[Kaggle]** (2026-09-19, votes 0)
  I added a link to the scoring notebook in the Evaluation section of the Overview page.
