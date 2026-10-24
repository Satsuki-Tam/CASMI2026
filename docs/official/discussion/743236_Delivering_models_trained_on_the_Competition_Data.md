# Delivering models trained on the Competition Data
topic 743236 | by **Asir Can Aslan** (https://www.kaggle.com/asircanaslan) | posted 2026-09-25 | votes 0 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/743236

Hi, two questions about the winner's obligations.

- Model weights: our neural networks, LightGBM rankers and a reference spectral library are trained on or derived from the Competition Data (CC BY-NC 4.0). Rule 2.5.a says that for input data with an incompatible licence we do not need to grant an open-source licence. Should we deliver these weights to the Sponsor under MIT together with the code, or under that clause (code under MIT; weights and derived data delivered only to the Sponsor, not published)?

- Private datasets: our notebook uses private Kaggle datasets that we build in advance (a PubChem mass index, a COCONUT table, a reference library built from train.parquet, and the model weights). For the winner package, is it acceptable to share these datasets privately with the Sponsor, together with the scripts that rebuild them from the public sources? PubChem Extras files are updated continuously, so a rebuild would use a newer snapshot.

Thank you!

## Comments (1 top-level)

- **David Healey** **[HOST]** (2026-09-25, votes 0)
  - The Competition Data in train.parquet is a compilation of open-source databases, and so models trained on it can be open-sourced.   Sorry for the licensing confusion on that; the test data when it is released will be restricted to noncommercial use. 
  
  - I'm not sure I fully understand the question, but the winning solutions should be open-sourced.  And the artifacts you describe seem acceptable open-source-derived solutions.
