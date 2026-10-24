# Data leak: every test spectrum appears verbatim in train.parquet
topic 741756 | by **Nipon Sriwasut** (https://www.kaggle.com/nipon16840) | posted 2026-09-17 | votes -5 | comments 3 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/741756

Hi organizers, and thanks for putting this competition together — reviving CASMI is a great thing to do.

I want to flag a leak I ran into while profiling the data, before it distorts the leaderboard. All 1,213 spectra in test.parquet are present in train.parquet as bitwise-identical rows, and those train rows carry normalized_smiles, inchikey14 and molecular_formula. That makes all 400 test molecules resolvable by exact lookup, with no modeling involved.

I'm reporting this rather than using it, and I haven't submitted anything based on it.

What I found
1,213 / 1,213 test spectra have an exact match in train.parquet.
Matches are bitwise identical — same num_peaks, and ms2_mzs / ms2_normalized_intensities compare equal under np.array_equal, not merely within a tolerance.
All 1,213 matches come from a single source library: enveda-180, instrument_type == 'timsTOF'.
400 / 400 test molecules are resolved, each to exactly one inchikey14 — the molecule_id → inchikey14 mapping is 1:1, with no conflicts across the multiple spectra belonging to a molecule.
The adduct field agrees between the test row and its matched train row in 100% of cases.

How to reproduce
Prefilter on peak count and precursor m/z, then compare the raw arrays:
`import numpy as np, pandas as pd, pyarrow.parquet as pq

test = pd.read_parquet("test.parquet")
test["n"] = test.ms2_mzs.apply(len)
by_n = {}
for pos, n in enumerate(test.n.values):
    by_n.setdefault(int(n), []).append(pos)

cols = ["num_peaks", "precursor_mz", "inchikey14", "normalized_smiles", "ms2_mzs",
        "ms2_normalized_intensities"]
pf = pq.ParquetFile("train.parquet")
hits = {}
for rg in range(pf.metadata.num_row_groups):
    df = pf.read_row_group(rg, columns=cols).to_pandas()
    for row in df.itertuples(index=False):
        for pos in by_n.get(int(row.num_peaks), ()):
            if pos in hits or abs(row.precursor_mz - test.precursor_mz.values[pos]) > 1e-4:
                continue
            if np.array_equal(np.asarray(row.ms2_mzs),
                              np.asarray(test.ms2_mzs.values[pos])):
                hits[pos] = row.inchikey14          # <- the answer
    if len(hits) == len(test):
        print("all matched at row group", rg + 1)   # -> 9
        break
print(len(hits), "/", len(test))                    # -> 1213 / 1213`

Runs in a few minutes — it stops at row group 9 of 21, because by then every test spectrum has already been matched.

Worked examples
molecule_id    spectrum_id adduct  precursor m/z   peaks   formula recovered from train
m_005e53    s_4d19d522  [M+H]+  375.0709    183 C18H19BrN2O2
m_006153    s_3c74e9fe  [M+H]+  342.1569    219 C17H19N5O3
m_00b5aa    s_04dffc2a  [M+H]+  307.2023    244 C17H26N2O3
I'm deliberately not posting the recovered structures or the full mapping.

Why it matters
A plain spectral-library lookup against enveda-180 scores close to MRR@25 = 1.0 without learning anything about structure elucidation, which is the opposite of what the competition is trying to measure. Anyone who runs a routine nearest-neighbour baseline will stumble into this by accident, so the leaderboard will stop being informative fairly quickly.

Suggested fix
Remove the test molecules from train.parquet by inchikey14 — not just the identical spectra, since other replicate spectra of the same compounds are also in enveda-180 and would still allow near-exact retrieval. It would also be worth confirming that the intended held-out set really is disjoint from the public library at the structure level (ideally scaffold-level too), since the interesting part of CASMI is performance on molecules that are not in any reference library.

Happy to share my verification script or re-run the check against a re-released dataset if that's useful.

## Comments (3 top-level)

- **c-number** (2026-09-17, votes 5)
  test.parquet — the spectra to identify. One row per spectrum; the structure is not given. Note: the file you see is comprised of examples from the training dataset; it will be replaced by the hidden test set during re-run, and will be approximately the same size.
  
  https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/data
- **?** (2026-09-17, votes 0)
  
- **Shair Khan** (2026-09-20, votes 3)
  Huge thanks for responsibly flagging this before the leaderboard got totally ruined! Finding that $100\%$ bitwise match with the enveda-180 library is a massive save for everyone trying to build actual $de$ $novo$ models.Really hope the organizers update train.parquet soon so we can get back to proper evaluation!
