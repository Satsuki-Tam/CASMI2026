# Test spectra appear verbatim in train.parquet (all 400 molecules).
topic 742278 | by **Odim David Emeka** (https://www.kaggle.com/odimdavidchukwuemeka) | posted 2026-09-21 | votes -4 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/742278

Hi Enveda team,
While building a spectral library baseline I found that the test spectra are present unchanged inside train.parquet, which makes the labels recoverable. Flagging it early so it can be corrected rather than sat on.
What I found
Every one of the 1,213 rows in test.parquet has a byte-identical counterpart in train.parquet: the ms2_mzs and ms2_normalized_intensities arrays match exactly, not approximately. Those matches cover 400 of 400 test molecules, and all of them come from the enveda-180 ingest library. 399 of the 400 map to a single inchikey14; one (m_6ebcf9) matches two different structures.
How to reproduce
Hash the raw peak arrays on both sides and intersect:

import hashlib, numpy as np, pandas as pd, pyarrow.parquet as pq
def sig(mzs, ins):
  h = hashlib.blake2b(digest_size=16)
  h.update(np.asarray(mzs, dtype=np.float64).tobytes())
  h.update(np.asarray(ins, dtype=np.float64).tobytes())
  return h.hexdigest()
test = pd.read_parquet("test.parquet")
test_sigs = {sig(m, i) for m, i in
           zip(test.ms2_mzs, test.ms2_normalized_intensities)}
pf = pq.ParquetFile("train.parquet")
cols = ["inchikey14", "ms2_mzs", "ms2_normalized_intensities", "ingest_lib"]
hits = 0
for rg in range(pf.metadata.num_row_groups):
  df = pf.read_row_group(rg, columns=cols).to_pandas()
  hits += sum(sig(r.ms2_mzs, r.ms2_normalized_intensities) in test_sigs
              for r in df.itertuples())
print(hits)   # 1215 rows matching 1213 test spectra

  **
  A quicker smell test: run any binned-cosine library search of test against train. Every test molecule returns a best match of exactly 1.000. For comparison, the same code on a held-out split of train (query spectra removed from the library) gives a median around 0.94 — so 1.000 across the board is the tell.
  Why it matters
  As it stands, a lookup table scores close to the 1.0 ceiling on MRR@25 without doing any structure elucidation, which isn't the task you set. I haven't submitted a solution built on this, and I'm not posting the recovered structures.

  Happy to share more detail privately if useful.

## Comments (1 top-level)

- **PC Jimmmy** (2026-09-21, votes 2)
  test.parquet — the spectra to identify. One row per spectrum; the structure is not given. Note: the file you see is comprised of examples from the training dataset; it will be replaced by the hidden test set during re-run, and will be approximately the same size.
  
  Is this the reason for your finding?
  
  Also - sharing more detail privately sounds a bit like a violation of the rules.  Hopefully you just meant you would be happy to discuss in more detail in this post if folks have questions.
