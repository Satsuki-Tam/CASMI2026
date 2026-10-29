# W135 census: rules fixed BEFORE running w135_census.py (2026-10-29 23:2x JST)

- Family rule (fixed now): Morgan radius 2 / 2048 bits on the official-key structure, Butina sphere exclusion at Tanimoto >= 0.5.
  Fallback written now: if fewer than 300 population identities are in families of size >= 2 at 0.5, use 0.4 (never above 0.5).
  Other thresholds in the census output are descriptive only. Murcko generic scaffolds are an auxiliary column, never the family rule.
- Query-library rule (fixed now): the hidden test is all timsTOF, so if >= 1,000 population identities have enveda-180 (timsTOF) spectra with a
  test adduct, every W135 query is drawn from enveda-180 (timsTOF); otherwise the p3_select_np.py policy (non-timsTOF libraries) is used for all.
- The census reads no candidate, generation, model or score output (structure, fold, library and spectrum-count metadata only).
