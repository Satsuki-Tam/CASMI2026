
<!-- cell 0 markdown -->
# CASMI 2026: Data Pitfalls That Break Your CV

## The problem

Work out what a molecule is, from what a mass spectrometer saw.

An extract from a plant or a microbe contains thousands of different molecules. Some of them
may be worth turning into medicines, but the first obstacle is simply knowing what is in there.
Today, pinning down a single structure takes slow and expensive lab work. This competition asks
whether a model can do it instead.

Roughly, the instrument does three things:

1. Gives the molecule a charge. It picks up a proton, a sodium ion, or similar. What it picked
   up is called the **adduct**, written like `[M+H]+`
2. Measures the charged molecule's mass precisely. This is the **precursor m/z**
3. Smashes it against a gas and records the mass and abundance of every fragment

That list of fragment masses and abundances is the **MS/MS spectrum**, and it is our input.
How hard you smash is the **collision energy** (eV) — more energy, smaller pieces. The same
molecule measured at different energies gives different spectra, which is why one molecule
comes with several of them.

The output is a SMILES string describing the 2D structure. You submit **up to 25 of them per
molecule, most confident first**. MRR@25 scores the reciprocal of the rank of the first correct
guess: 1.0 at position one, 0.5 at position two, 0.04 at position 25, and 0 if it is not in
the list at all.

Matching ignores stereochemistry and tautomer form, so getting the flat skeleton right is
enough. How exactly it ignores them turns out to matter — see section 4.

## What ships with the competition

| File | Contents |
|---|---|
| train.parquet | ~2.5M spectra / ~275k structures, labelled. An aggregation of 11 public libraries |
| test.parquet | ~1,500 spectra / ~400 molecules, structures withheld |

Predictions are made **per molecule, not per spectrum**. Each molecule carries about three
spectra, and you have to fold them into a single ranked list.

Every test spectrum was acquired on one instrument, a Bruker timsTOF, and every test molecule
is a natural product — something found in plants, mammals or microbes, or something that
plausibly could be.

## What this notebook covers

2.5 million spectra sounds like plenty. Open the box, though, and the data measured on the
test set's instrument barely overlaps with the data covering the test set's chemistry.

What follows is a walk through the shipped data, and the things I actually tripped over while
building a pipeline on it. None of them are modelling problems. Miss them and your local
validation stops meaning anything, or you quietly waste slots in your list of 25.

Along the way we need the scoring key recomputed for every structure. That needs RDKit, which
is not in the Kaggle image — but it installs offline from
[`aidensong123/casmi26-offline-rdkit-2026033`](https://www.kaggle.com/datasets/aidensong123/casmi26-offline-rdkit-2026033),
a wheel of the exact 2026.03.3 the scorer pins. Keying all 275,810 train structures takes about
21 minutes on one core, 5 across four. This notebook reads a precomputed table
(`casmi-2026-scoring-keys-and-contamination-map`, CC0) instead, to keep the run short. Sections
4 and 5 use it.

<!-- cell 1 code -->
```python
import os
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import matplotlib.pyplot as plt

# Mount points move around, so go looking for them
def find_dir(*candidates):
    for c in candidates:
        if os.path.isdir(c):
            return c
    for root, dirs, _ in os.walk("/kaggle/input"):
        for d in dirs:
            if any(c.rstrip("/").endswith(d) for c in candidates):
                return os.path.join(root, d)
    return candidates[0]

COMP = os.environ.get("CASMI_COMP") or find_dir(
    "/kaggle/input/enveda-CASMI26-molecule-id-mass-spectra")
IK = os.environ.get("CASMI_IK") or find_dir(
    "/kaggle/input/casmi-2026-scoring-keys-and-contamination-map")
print("competition:", COMP)
print("keys dataset:", IK)
```

<!-- cell 2 markdown -->
## 1. What is in the training data

train is eleven public libraries stacked together. The hosts call it a convenience aggregation,
and it shows: the instruments differ, the preprocessing differs. Start by seeing who brought what.

<!-- cell 3 code -->
```python
meta = pq.read_table(
    f"{COMP}/train.parquet",
    columns=["ingest_lib", "inchikey14", "adduct", "instrument_type",
             "precursor_mz", "precursor_error_ppm", "num_peaks",
             "collision_energy_orig_units"],
).to_pandas()

summary = (
    meta.groupby("ingest_lib")
    .agg(spectra=("inchikey14", "size"), structures=("inchikey14", "nunique"))
    .sort_values("spectra", ascending=False)
)
summary["spectra_%"] = (summary.spectra / len(meta) * 100).round(1)
print(f"{len(meta):,} spectra / {meta.inchikey14.nunique():,} unique structures")
summary
```

<!-- cell 4 markdown -->
Two libraries account for 66% of everything, and `enveda-180` alone dominates.

Collision energy is recorded in different units depending on the library. eV and NCE are
different quantities on different scales, so they cannot simply be pooled.

<!-- cell 5 code -->
```python
print(meta.collision_energy_orig_units.value_counts().to_string())
print()
print(f"distinct instrument_type strings: {meta.instrument_type.nunique()}")
print(meta.instrument_type.value_counts(dropna=False).head(8).to_string())
```

<!-- cell 6 markdown -->
Label quality varies too, and there is a column that measures it: `precursor_error_ppm`.

If you know the structure, you can calculate the mass it should have once it picks up a given
adduct. The instrument, meanwhile, measured the mass. Those two numbers ought to agree — within
a few ppm on a high-resolution instrument (ppm is parts per million; at m/z 300, 10 ppm is
0.003 Da).

A large disagreement means something is wrong: the labelled structure, the adduct assignment,
or the instrument's calibration. So this column is effectively **a measure of how far you can
trust that row's label**. The hosts ship it uncleaned on purpose, and the Data page says as
much — it doubles as a label-quality signal.

<!-- cell 7 code -->
```python
err = meta.precursor_error_ppm.abs()
for t in [5, 10, 50, 1000]:
    print(f"|error| > {t:>4} ppm : {(err > t).sum():>7,} ({(err > t).mean():.2%})")
print(f"maximum: {err.max():,.0f} ppm")
```

<!-- cell 8 markdown -->
6.9% exceed 10 ppm. Reaching for a 10 ppm filter at this point **makes things worse.**

A large error does not have to mean a wrong label. It also depends on **how many digits that
library reports precursor m/z to**. Split it by library and it shows.

<!-- cell 9 code -->
```python
def decimals(x):
    s = ("%.10f" % x).rstrip("0")
    return len(s.split(".")[1]) if "." in s else 0

rows = []
for lib, g in meta.groupby("ingest_lib"):
    d = int(g.precursor_mz.head(20000).map(decimals).median())
    rows.append({"library": lib, "spectra": len(g), "median_decimals": d,
                 "within_10ppm_%": round((g.precursor_error_ppm.abs() <= 10).mean() * 100, 1),
                 "lost_by_10ppm": int((g.precursor_error_ppm.abs() > 10).sum())})
pd.DataFrame(rows).sort_values("spectra", ascending=False)
```

<!-- cell 10 markdown -->
`riken` reports precursor m/z to a median of **two decimal places**. Rounding m/z 350 to
0.01 Da is 28.6 ppm on its own. The labels are fine; the precision is low.

Filter everything at 10 ppm and **53% of the 175,068 spectra you lose are `riken`** — 347k
spectra of plant specialised metabolites, the closest thing in this file to the test set's
chemistry.

Measured, dropping the filter is clearly better: the Class 1 retrieval in section 8 goes from
MRR 0.8733 to 0.9277, and candidate recall from 90.8% to 96.8%.

[@josefreitasalvesneto's notebook](https://www.kaggle.com/code/josefreitasalvesneto/casmi-2026-a-complete-statistical-tour)
makes this point first (item 9: "riken's huge ppm errors are a precision artifact, not bad
labels"). I had already submitted a baseline filtered at a flat 10 ppm before reading it.

Values like 470 million ppm are obviously broken and can go. But **a sensible-looking threshold
applied uniformly across libraries throws away the data you want most.**

<!-- cell 11 markdown -->
## 2. The test.parquet you downloaded is enveda-180

**This section's conclusion was published first by
[@josefreitasalvesneto](https://www.kaggle.com/code/josefreitasalvesneto/casmi-2026-a-complete-statistical-tour)**
(item 10: "The public test file is 100% `enveda-180` rows, verified by exact peak-array match").
I arrived at the same check independently, so it stays here as a reproduction — credit for the
finding is theirs.

The Data page says the file you see "is comprised of examples from the training dataset".
Which examples? Let us match every shipped test spectrum against train.

The match narrows on four fields (precursor_mz, adduct, peak count, base_peak_intensity),
then checks whether **the m/z and intensity arrays themselves are identical**.

<!-- cell 12 code -->
```python
test = pd.read_parquet(f"{COMP}/test.parquet")
test["num_peaks"] = test.ms2_mzs.apply(len)

def key_of(pmz, adduct, n, bpi):
    return f"{round(float(pmz), 4)}|{adduct}|{n}|{round(float(bpi), 0)}"

test["k"] = [key_of(p, a, n, b) for p, a, n, b
             in zip(test.precursor_mz, test.adduct, test.num_peaks, test.base_peak_intensity)]
want = set(test.k)

pf = pq.ParquetFile(f"{COMP}/train.parquet")

# Match on keys first, without touching the peak arrays. At scoring time `test` is swapped for
# the hidden set and this comes back empty, so the expensive part only runs when there are hits —
# otherwise the loop below would read all 3 GB looking for matches that cannot exist.
kcols = ["ingest_lib", "normalized_smiles", "inchikey14",
         "adduct", "precursor_mz", "num_peaks", "base_peak_intensity"]
tmeta = pq.read_table(f"{COMP}/train.parquet", columns=kcols).to_pandas()
tmeta["k"] = [key_of(p, a, n, b) for p, a, n, b
              in zip(tmeta.precursor_mz, tmeta.adduct, tmeta.num_peaks, tmeta.base_peak_intensity)]
hit = tmeta[tmeta.k.isin(want)].drop_duplicates("k").set_index("k")
print(f"key matches: {len(hit)} / {len(want)}")
```

<!-- cell 13 code -->
```python
if len(hit) == 0:
    print("No matches — this is the hidden test set, which is exactly what we expect here.")
else:
    rowmap = {k: i for i, k in enumerate(tmeta.k) if k in hit.index}
    need = set(rowmap.values())
    peak_of, offset = {}, 0
    for rg in range(pf.metadata.num_row_groups):
        n = pf.metadata.row_group(rg).num_rows
        w = [r for r in range(offset, offset + n) if r in need]
        if w:
            df = pf.read_row_group(rg, columns=["ms2_mzs", "ms2_normalized_intensities"]).to_pandas()
            for r in w:
                row = df.iloc[r - offset]
                peak_of[r] = (row.ms2_mzs, row.ms2_normalized_intensities)
        offset += n
        if len(peak_of) == len(need):
            break

    n_mz = n_int = 0
    libs = {}
    for _, t in test.iterrows():
        s = hit.loc[t.k]
        libs[s.ingest_lib] = libs.get(s.ingest_lib, 0) + 1
        pm, pi = peak_of[rowmap[t.k]]
        n_mz += np.array_equal(np.asarray(t.ms2_mzs), np.asarray(pm))
        n_int += np.array_equal(np.asarray(t.ms2_normalized_intensities), np.asarray(pi))

    print(f"identical m/z arrays       : {n_mz} / {len(test)}")
    print(f"identical intensity arrays : {n_int} / {len(test)}")
    print(f"source libraries           : {libs}")

del tmeta
```

<!-- cell 14 markdown -->
All 1,213 spectra match `enveda-180` rows bit for bit. All 400 molecules resolve to exactly one
structure, with no conflicts.

Submit this notebook and the same cell reports no matches at all, because `test.parquet` has
been swapped for the hidden set. That is the claim of this section, demonstrating itself.

The catch is what `enveda-180` contains: synthetic drug-like screening compounds. That is a
different region of chemical space from the natural products in the real test set. Lined up
against the Data page:

| | shipped test.parquet | hidden test set (per Data page) |
|---|---|---|
| chemistry | synthetic, drug-like | natural products |
| precursor m/z | 245 – 460 | monoisotopic mass 157 – 1,159 Da |
| adducts | 7 | 10 |

It is worth being explicit about which file feeds which number:

| | contents | downloadable | used for scoring |
|---|---|---|---|
| the test.parquet you have | a slice of train (enveda-180) | yes | no |
| hidden test set (~400 molecules) | natural products, timsTOF | no | yes |
| └ Public LB | ~33% of the hidden set | no | provisional standing |
| └ Private LB | ~67% of the hidden set | no | final standing |

Your submitted notebook is re-run on Kaggle, and `test.parquet` is swapped for the real thing
at that point. Both leaderboards come from that file, not from the one on your disk.

So **scoring yourself against the shipped test.parquet means scoring a different problem**.
It is fine for checking that the pipeline runs and for timing it. It is useless for deciding
whether an idea works.

For the same reason, adversarial validation between your local train and test does not work.
The current test is a subset of train, so the classifier just learns to spot those 1,213 rows.
The only moment you can compare against the real test set is while your notebook is being re-run.

One more consequence: the Public LB reflects about 33% of the hidden set, roughly 130 molecules.
A single molecule moves it by up to 0.0076, so differences around 0.005 are noise.

<!-- cell 15 code -->
```python
print(f"shipped test precursor_mz : {test.precursor_mz.min():.1f} - {test.precursor_mz.max():.1f}")
print(f"shipped test adduct types : {test.adduct.nunique()}")
print(f"adducts used for real      : 10 (adds [M-H2O+H]+, [M-2H2O+H]+, [M-H2O-H]-)")
```

<!-- cell 16 markdown -->
Conditions appear at re-run time that never appear locally, so it is worth pushing 1,159 Da and
the three extra adducts through the pipeline before you need to. There is no second attempt
if it falls over there.

<!-- cell 17 markdown -->
## 3. The right instrument and the right chemistry live in different libraries

Also covered by the statistical tour above (items 3-5: `enveda-180` is a chemical island whose
Jaccard overlap with the natural-product libraries is ~0.000). Here it is in raw structure counts.

Every test spectrum is a Bruker timsTOF. In train, only `enveda-180` and `enveda-np-examples`
carry that label.

The natural-product chemistry sits elsewhere — `riken` (plant specialised metabolites) and
`gnps` (the community natural-product collection) — measured on a jumble of instruments.
So how much do the two sides overlap?

<!-- cell 18 code -->
```python
e180 = set(meta.loc[meta.ingest_lib == "enveda-180", "inchikey14"])
rows = []
for lib in summary.index:
    if lib == "enveda-180":
        continue
    s = set(meta.loc[meta.ingest_lib == lib, "inchikey14"])
    rows.append({"library": lib, "structures": len(s),
                 "shared_with_enveda180": len(s & e180),
                 "%": round(len(s & e180) / len(s) * 100, 2)})
pd.DataFrame(rows).sort_values("%")
```

<!-- cell 19 markdown -->
Seven structures out of 15,892 for `riken`. Zero for `spectraverse`. Zero for all 250 of
`enveda-np-examples`. Only `gnps` and `pluskal_ms2` reach a few percent. In practice these are
two disjoint chemical spaces sitting side by side.

Which means the material for adapting to the instrument and the material for learning natural
product chemistry never come in the same box. Take one and you give up the other.

Read the other way round: those 180k `enveda-180` structures are useless as natural-product
knowledge, but they are **the largest resource available for learning what a timsTOF does to a
molecule**. There is room to use them for pretraining.

<!-- cell 20 code -->
```python
tims = meta.instrument_type.fillna("").str.contains("timsTOF", case=False)
print(f"spectra labelled timsTOF: {tims.sum():,} ({tims.mean():.1%})")
print(meta.loc[tims, "ingest_lib"].value_counts().to_string())
```

<!-- cell 21 markdown -->
## 4. `inchikey14` is not the key you are scored on

Per the Evaluation page, matching runs your SMILES through RDKit's tautomer canonicalization
(pinned at 2026.03.3) and compares the first 14 characters of the InChIKey.

train ships an `inchikey14` column, but it is derived from `normalized_smiles` **without**
that canonicalization step. The two disagree.

**Correction, 2026-09-21.** This section used to say RDKit is absent from the Kaggle image and
internet is off, so the key cannot be recomputed inside a notebook. The premise is right, the
conclusion is wrong. `aidensong123/casmi26-offline-rdkit-2026033` ships the 2026.03.3 wheel, and

```python
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--no-index", whl])
```

installs it with internet disabled. Keying all 275,810 train structures took 21 minutes on one
core here (4.7 ms each), 5 minutes across four.

So the table below saves time, it is not a workaround for something impossible. And if your
candidate pool comes from COCONUT or PubChem rather than train, you have to key it yourself at
submission time anyway — the wheel is the thing you actually need.

<!-- cell 22 code -->
```python
ik14 = pd.read_csv(f"{IK}/ik14_map.csv")
print(f"{len(ik14):,} structures")
print(f"disagree with the scoring key: {ik14.tautomer_shifted.sum():,} "
      f"({ik14.tautomer_shifted.mean():.3%})")
ik14[ik14.tautomer_shifted].head(8)
```

<!-- cell 23 markdown -->
4,370 of 275,810 structures, or 1.58%.

**That 1.58% is not a loss, though.** The scorer keys your guess and the answer with the same
function, so a key that moves on both sides changes nothing. What costs you is a
**disagreement about which structures are the same** — and that is the next section.

[@dariushafshar's notebook](https://www.kaggle.com/code/dariushafshar/casmi26-10-4-of-keys-change-0-48-cost-you)
got to this first and works it out more carefully: over COCONUT's 738,827 structures, 10.4% are
re-keyed, only 2.30% can affect anything, and simulating MRR@25 puts the cost at 0.48%. The
rates are not comparable across different structure populations, but the reasoning — that the
change itself is free and only the disagreement bites — is theirs and it is right.

<!-- cell 24 markdown -->
## 5. The part that actually costs you — disagreement about identity

Canonicalization has a second effect: **distinct `inchikey14` values collapse onto the same
scoring key**. Unlike the shift in section 4, this one does change your conclusions if you key
things the naive way.

<!-- cell 25 code -->
```python
col = pd.read_csv(f"{IK}/collapsed_structures.csv")
print(f"collapsed groups : {len(col):,}")
print(f"structures involved: {col.n_inchikey14.sum():,}")
print(f"largest group    : {col.n_inchikey14.max()} structures under one key")
col.head(5)
```

<!-- cell 26 markdown -->
3,167 structures are involved, 1.15% of the total. Two things follow.

1. **Wasted slots.** List two members of a group as separate candidates and the second cannot
   score, because the metric already considers it the same molecule. With 25 slots, that is loss
2. **Validation that undercounts.** Score yourself on raw keys and you will mark correct answers
   wrong, because your keying splits what the scorer merges

Both disappear if deduplication and answer-matching both run on the canonical key — not on the
SMILES string, not on `inchikey14`.

And 1.15% is still an upper bound on what it can cost. It only bites when one member of a
collapsed group ranks high and the answer is another member. The notebook linked in section 4
simulates that configuration and puts it at 0.48% over COCONUT.

<!-- cell 27 markdown -->
## 6. Holding out `enveda-np-examples` does not hold it out

`enveda-np-examples` is the one library that matches the test set on both axes: timsTOF and
natural products. It is the obvious choice for validation queries. Filtering on `ingest_lib`
is not enough, though.

<!-- cell 28 code -->
```python
cont = pd.read_csv(f"{IK}/np_examples_contamination.csv")
print(f"structures in np-examples        : 250")
print(f"also present in other libraries  : {len(cont)} ({len(cont) / 250:.0%})")
print(f"their spectra in those libraries : {cont.n_other_spectra.sum():,}")
cont.head(5)
```

<!-- cell 29 markdown -->
All 250 appear elsewhere, across 55,599 other spectra. A holdout built by excluding
`ingest_lib == 'enveda-np-examples'` leaves the answers sitting in the index, and a plain
library search walks straight to them.

Exclude by structure — by canonical key — and then **run an exact spectral match against your
holdout and assert that it returns nothing**.

<!-- cell 30 markdown -->
## 7. Where the score actually comes from

The Data page splits the test molecules into three regimes:

| Class | Definition | How you reach it |
|---|---|---|
| 1 | Reference MS/MS exists in public libraries | spectral similarity search |
| 2 | Structure is in PubChem / COCONUT, no reference spectrum | database retrieval + reranking |
| 3 | Not in PubChem at all | de novo generation |

The proportions are not published. The discussion forum has worked backwards from the fact that
a library-search-only submission lands at 0.151 on the public LB, putting Class 1 at roughly 16%.

If that holds, then **solving Class 1 perfectly caps you at 0.16**. The fact that the top of the
leaderboard sits around 0.36 means they are converting a good share of Class 2. Polishing your
spectral search hits a ceiling early.

<!-- cell 31 code -->
```python
for f1 in [0.14, 0.16, 0.18]:
    print(f"Class 1 share {f1:.0%} -> perfect library search caps at {f1:.3f}")
```

<!-- cell 32 markdown -->
## 8. A baseline — how far library search alone gets you

Three steps, nothing more:

1. For each test spectrum, take train rows within ±10 ppm on precursor m/z with the same adduct
2. Score them by spectral entropy similarity
3. Per molecule, keep each structure's best score and rank the top 25

Entropy similarity, from Li et al., asks how much entropy increases when you add two spectra
together and renormalise. The closer the match, the less it grows. It discriminates better than
cosine on MS/MS search.

<!-- cell 33 code -->
```python
LN4 = np.log(4.0)

def clean_spectrum(mzs, ints, precursor_mz, min_rel=0.01, max_peaks=128, margin=1.6):
    mzs = np.asarray(mzs, dtype=np.float64)
    ints = np.asarray(ints, dtype=np.float64)
    if mzs.size == 0:
        return mzs, ints
    keep = (ints > 0) & (mzs <= precursor_mz + margin)
    mzs, ints = mzs[keep], ints[keep]
    if mzs.size == 0:
        return mzs, ints
    keep = ints >= ints.max() * min_rel
    mzs, ints = mzs[keep], ints[keep]
    if mzs.size == 0:
        return mzs, ints
    if mzs.size > max_peaks:
        idx = np.sort(np.argpartition(ints, -max_peaks)[-max_peaks:])
        mzs, ints = mzs[idx], ints[idx]
    order = np.argsort(mzs)
    mzs, ints = mzs[order], ints[order]
    return mzs, ints / ints.sum()

def _entropy(p):
    p = p[p > 0]
    return float(-(p * np.log(p)).sum())

def _weight(ints):
    s = _entropy(ints)
    if s < 3.0:
        ints = np.power(ints, 0.25 + 0.25 * s)
        ints = ints / ints.sum()
    return ints

def entropy_similarity(mz_a, int_a, mz_b, int_b, tol_da=0.02):
    if mz_a.size == 0 or mz_b.size == 0:
        return 0.0
    int_a, int_b = _weight(int_a), _weight(int_b)
    merged, i, j = [], 0, 0
    while i < mz_a.size and j < mz_b.size:
        d = mz_a[i] - mz_b[j]
        if abs(d) <= tol_da:
            merged.append(int_a[i] + int_b[j]); i += 1; j += 1
        elif d < 0:
            merged.append(int_a[i]); i += 1
        else:
            merged.append(int_b[j]); j += 1
    merged.extend(int_a[i:]); merged.extend(int_b[j:])
    ab = np.asarray(merged); ab = ab / ab.sum()
    sim = 1.0 - (2 * _entropy(ab) - _entropy(int_a) - _entropy(int_b)) / LN4
    return float(min(max(sim, 0.0), 1.0))
```

<!-- cell 34 markdown -->
Before submitting, it would be good to know how well this works. But as section 2 showed,
measuring on the shipped test.parquet tells you nothing. Do it anyway and MRR comes out at
1.0000, every one of the 400 molecules ranked first — the answers are sitting in the reference
set. That confirms the plumbing, not the method.

So simulate Class 1 instead:

- draw query molecules from the natural-product libraries
- use the spectra from one library as the queries
- remove that library's spectra for that structure from the reference

Other libraries keep their copies of the same structure on different instruments, which is
exactly the Class 1 situation: a reference exists, but this particular measurement is new.
This is where I broke my own validation. The first number I got was **MRR 0.9583, with 378 of
400 ranked first.** Too good. What had happened:

**I applied the ppm filter before choosing the query molecules.**

As section 1 showed, low `|ppm|` does not select rows with correct labels so much as rows whose
precursor m/z was recorded precisely. Draw queries from those and you have quietly assembled a
set of spectra that are unusually easy to pin down with a mass window.

The hidden test has no labels, so `precursor_error_ppm` cannot be computed for it.
**Filtering the query side was a condition that does not exist at scoring time.**

Apply the filter to the reference side only, hold the query set fixed, and it reads:

<!-- cell 35 markdown -->
| ppm filter on the reference | answer in candidate pool | MRR@25 | ranked first |
|---|---|---|---|
| flat 10 ppm | 90.8% | 0.8733 | 342 / 400 |
| per-library threshold | 90.8% | 0.8733 | 342 / 400 |
| **none** | **96.8%** | **0.9277** | **362 / 400** |

Two things fall out.

**One. The real number is 0.8733, not 0.9583.** The 0.085 difference was me selecting queries
by how easy their answers were to find — entirely self-inflicted.

**Two. The ppm filter should come off.** 90.8% to 96.8%. What it was removing was not broken
labels but correct labels from imprecise libraries.

The rule worth keeping: **never let a quantity you cannot compute at test time influence which
queries you validate on.** Anything derived from the labels — `precursor_error_ppm` here — is
fair game for cleaning the reference side, and breaks your validation the moment it touches the
query side.

<!-- cell 36 markdown -->
Back to section 7's arithmetic. If Class 1 is 16% of the test set, this baseline is worth

    0.16 × 0.9277 ≈ 0.148

The flat-10-ppm version (Class 1 simulation 0.8733) is the one I actually submitted, and it
scored **0.151** on the public LB. Working backwards, that puts Class 1 at 0.151 / 0.8733 =
**17.3%** — the same neighbourhood as the 16% the forum arrived at by probing.

Either way, **refining entropy similarity runs into a ceiling around 0.16-0.17**. The leaderboard
reaching 0.36 comes from pulling in molecules that have no reference spectrum at all. That is
where the headroom is.

<!-- cell 37 markdown -->
The rest builds the actual submission. Under a minute over the whole test set, a small fraction
of the nine-hour budget, so there is plenty of room to put something heavier on top.

No ppm filter, per section 1.

<!-- cell 38 code -->
```python
TOL_PPM, TOL_DA = 10.0, 0.02

ref = meta.copy()
ref["row"] = ref.index.to_numpy()
index = {}
for adduct, g in ref.groupby("adduct", sort=False):
    mz = g.precursor_mz.to_numpy()
    o = np.argsort(mz)
    index[adduct] = (mz[o], g.row.to_numpy()[o])

cand_per_spec, needed = [], set()
for adduct, pmz in zip(test.adduct, test.precursor_mz):
    e = index.get(adduct)
    if e is None:
        cand_per_spec.append(np.empty(0, dtype=np.int64)); continue
    mzs, rows = e
    d = float(pmz) * TOL_PPM * 1e-6
    lo, hi = np.searchsorted(mzs, [float(pmz) - d, float(pmz) + d])
    cand_per_spec.append(rows[lo:hi]); needed.update(rows[lo:hi].tolist())
print(f"mean candidates/spectrum {np.mean([len(c) for c in cand_per_spec]):.0f} / rows to read {len(needed):,}")
```

<!-- cell 39 code -->
```python
peaks, offset = {}, 0
for rg in range(pf.metadata.num_row_groups):
    n = pf.metadata.row_group(rg).num_rows
    want = [r for r in range(offset, offset + n) if r in needed]
    if want:
        df = pf.read_row_group(rg, columns=["ms2_mzs", "ms2_normalized_intensities", "precursor_mz"]).to_pandas()
        for r in want:
            row = df.iloc[r - offset]
            peaks[r] = clean_spectrum(row.ms2_mzs, row.ms2_normalized_intensities, float(row.precursor_mz))
    offset += n
    if len(peaks) == len(needed):
        break

smiles_of = pq.read_table(f"{COMP}/train.parquet", columns=["normalized_smiles"]).to_pandas().normalized_smiles
ik_of = meta.inchikey14
```

<!-- cell 40 code -->
```python
best = {}
for si, (mid, mzs, ints, pmz) in enumerate(
    zip(test.molecule_id, test.ms2_mzs, test.ms2_normalized_intensities, test.precursor_mz)
):
    qm, qi = clean_spectrum(mzs, ints, float(pmz))
    b = best.setdefault(mid, {})
    for r in cand_per_spec[si]:
        pk = peaks.get(int(r))
        if pk is None or pk[0].size == 0:
            continue
        sim = entropy_similarity(qm, qi, pk[0], pk[1], TOL_DA)
        ik = ik_of.iloc[int(r)]
        if sim > b.get(ik, (-1, None))[0]:
            b[ik] = (sim, smiles_of.iloc[int(r)])
```

<!-- cell 41 markdown -->
Section 5 matters when the list gets assembled. Two candidates sharing a scoring key means the
second one cannot score, so deduplication happens on the canonical key — not on SMILES, not on
`inchikey14`.

<!-- cell 42 code -->
```python
key_of = dict(zip(ik14.inchikey14, ik14.metric_ik14))

rows = []
for mid in test.molecule_id.unique():
    seen, cands = set(), []
    for ik, (sim, smi) in sorted(best.get(mid, {}).items(), key=lambda kv: -kv[1][0]):
        k = key_of.get(ik, ik)
        if k in seen:
            continue
        seen.add(k); cands.append(smi)
        if len(cands) == 25:
            break
    if not cands:  # never leave it empty — wrong guesses cost nothing, so an empty slot is pure loss
        cands = ["Cn1c(=O)c2c(ncn2C)n(C)c1=O"]
    rows.append((mid, ";".join(cands)))

sub = pd.DataFrame(rows, columns=["molecule_id", "smiles"])
sub.to_csv("submission.csv", index=False)
print(f"{len(sub)} rows / mean candidates {sub.smiles.str.count(';').add(1).mean():.1f}")
sub.head()
```

<!-- cell 43 markdown -->
## Summary

The things that can break your validation, in the order I walked into them.

- **Never let label-derived quantities choose your queries.** Filtering queries on
  `precursor_error_ppm` turned Class 1 retrieval from 0.8733 into 0.9583. The test set has no
  labels, so that 0.085 was pure self-deception
- **A flat ppm filter deletes the data you want most.** `riken` reports two decimals, so rounding
  alone is 28.6 ppm. Dropping the filter takes recall from 90.8% to 96.8%
- **The shipped test.parquet is a slice of enveda-180**, in different chemistry from the real test
  set. Do not choose methods by how they score on it
- **The timsTOF data and the natural-product data do not overlap.** Which one you train on is a
  design decision, not a detail
- **`inchikey14` is not the scoring key** (1.58% re-keyed), but the re-keying itself is free. What
  costs you is disagreement about identity: 1,541 collapsed groups, 3,167 structures. Deduplicate
  candidates and match answers on the canonical key
- **Hold out `enveda-np-examples` by structure**, and assert the contamination is gone

The baseline says library search is close to solved for Class 1 (MRR 0.93 in simulation) and caps
out around 0.16 because that is all Class 1 is worth. Going further means retrieving molecules
that have no reference spectrum at all.

Sections 1, 2 and 3 were reached first by
[@josefreitasalvesneto's statistical tour](https://www.kaggle.com/code/josefreitasalvesneto/casmi-2026-a-complete-statistical-tour),
and section 4 by
[@dariushafshar](https://www.kaggle.com/code/dariushafshar/casmi26-10-4-of-keys-change-0-48-cost-you).
Both are worth reading.

The key table and contamination map are in the attached dataset, in case they save someone else
the same detour.
