
<!-- cell 0 markdown -->
# CASMI26: 10.4% of Keys Change, 0.48% Cost You

CASMI 2026 does not score your answer by comparing SMILES. It canonicalizes the tautomer
first, then compares the first fourteen characters of the InChIKey. If you pull candidates
out of a structure library and key them yourself the obvious way, by slicing the InChIKey the
library already ships, your key is not always the key the scorer computes.

I keyed all 738,827 structures in COCONUT both ways and published the table. **76,993 of them,
10.42%, come out with a different InChIKey14 under the scorer's canonicalization than under
the naive slice.** One in ten. That is the number that made me build the table, and this
notebook is what happened when I tried to price it.

It is worth a great deal less than it sounds, and the reason is interesting.

1. **A changed key is almost never a changed answer.** The scorer keys your submitted SMILES
   and the truth's SMILES with the same function, so a key that changes on both sides changes
   nothing. What can actually move a score is a **disagreement**: two structures your keying
   calls different that the scorer calls the same, or two your keying calls the same that the
   scorer calls different. That set is **16,977 structures, 2.30%**, not 10.42%.
2. **Almost all of that 2.30% is still free.** I split the disagreement into its two
   directions and simulated MRR@25 over both. The direction where the scorer **merges** what
   you split covers 13,142 structures and costs **-0.0001 MRR**, which is to say nothing. The
   direction where the scorer **splits** what you merged covers 3,564 structures, 0.48% of the
   library, and costs **+0.105 MRR** on those molecules. Every bit of the damage is in the
   small half.
3. **Weighted by the library, naive keying costs 0.0004 MRR@25.** Four ten-thousandths. If
   your candidate pool looks like COCONUT, this is not your problem. Part 5 also shows what it
   becomes if your molecules are enriched in the risky set, because that is the case where it
   stops being free.
4. **The number it really breaks is your own validation score, and it breaks it in two
   directions at once.** A pipeline that keys naively believes it scored 0.2550 on the merge
   group when it actually scored 0.3532, and believes it scored 0.5178 on the split group when
   it actually scored 0.2623. Those are large errors of opposite sign. Library-weighted they
   cancel down to +0.0007 and look like nothing. They will not cancel on a different mix of
   molecules, and a local CV number built this way is not slightly wrong, it is two big wrongs
   that happen to be pointing at each other.

So the honest headline deflates the scary one. I would rather publish that than the version
that keeps the 10.42% and lets you assume it is coming out of your score.

**What this is not.** It is not a model, it produces no submission, and it says nothing about
how to rank candidates. It is about one function: the one that decides whether your answer
counts.

**Credit.** The structures are COCONUT, the Collection of Open Natural Products, Steinbeck Lab
and contributors, September 2026 CSV Lite release, CC BY 4.0. The keying convention is the one
the competition's evaluation page defines. The published table, the simulation and any mistakes
in either are mine.

<!-- cell 1 markdown -->
## The cell you edit

`PPM` sets how wide the candidate pool is in Part 5, `POOL_CAP` caps how deep the simulation
looks into a pool, and `UNAFFECTED_SAMPLE` sets how many control molecules the simulation
runs. Nothing else needs touching. The whole notebook is a few minutes on a CPU.

<!-- cell 2 code -->
```python
CFG = {
    # --- Part 5, the MRR@25 simulation -------------------------------------
    # Precursor-mass window for the candidate pool, in parts per million. 5 ppm
    # is an ordinary high-resolution MS tolerance. This is a STATED ASSUMPTION,
    # not a competition parameter: CASMI does not hand you a pool, you build one.
    "PPM": 5.0,

    # How deep into a mass window the simulation looks. Windows run to 1,760
    # structures; ranking all of them changes nothing about a top-25 metric and
    # costs a lot of wall clock.
    "POOL_CAP": 200,

    # MRR@25. The competition's own depth.
    "TOP_N": 25,

    # Control stratum size. The control is 97.7% of the library, so it is
    # sampled rather than run whole.
    "UNAFFECTED_SAMPLE": 15000,

    # Seeds, one per stratum, so each stratum reproduces independently.
    "SEED_MERGE": 21, "SEED_SPLIT": 22, "SEED_BOTH": 23,
    "SEED_NONE": 24, "SEED_SAMPLE": 3,

    # --- the dataset's own build receipt -----------------------------------
    # These are the ONLY numbers in this notebook that I did not compute here.
    # They come from `package_receipt.json`, written when the table was built.
    # Part 1 recomputes every one of them and prints the comparison, so if the
    # table ever drifts from its own receipt you will see it rather than me.
    "RECEIPT": {"rows": 738827, "n_changed": 76993,
                "n_raw14": 479718, "n_scorer": 476438,
                "coverage": 0.9999945860126931},
}
```

<!-- cell 3 markdown -->
---

## Part 1: The table, and whether it still says what it said

The dataset mounts at `/kaggle/input/...`, but this account mounts datasets under an
owner-prefixed path sometimes and a bare one other times, so nothing here assumes a path. The
parquet is found by walking the mount and the resolved path is printed before it is used.

<!-- cell 4 code -->
```python
import os, gc, json, math, time, warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")
T0 = time.time()

ROOT = os.environ.get("SMOKE_ROOT", "/kaggle/input")
WORK = os.environ.get("SMOKE_WORK", "/kaggle/working")
os.makedirs(WORK, exist_ok=True)

def find(name):
    for root, _, files in os.walk(ROOT):
        if name in files:
            return os.path.join(root, name)
    return None

PQ  = find("coconut_casmi26_scorer_keys.parquet")
CSV = find("coconut_casmi26_scorer_keys.csv")
print("mount root :", ROOT)
print("parquet    :", PQ)
print("csv        :", CSV)
assert PQ or CSV, (
    "The scorer-key table is not mounted. Add the dataset\n"
    "  dariushafshar/casmi26-coconut-scorer-keys-rdkit-2026-03-3\n"
    "to this kernel's inputs.")

NAIVE = "coconut_inchikey14"                        # first block of COCONUT's own InChIKey
SCOR  = "scorer_inchikey14_rdkit_2026_03_3"         # first block after tautomer canonicalization

t = time.time()
df = pd.read_parquet(PQ) if PQ else pd.read_csv(CSV)
print(f"\nloaded {len(df):,} rows x {df.shape[1]} columns in {time.time()-t:.1f}s")
print(df.columns.tolist())
```

<!-- cell 5 markdown -->
### What is in it, and what a row means

One row per COCONUT structure. `coconut_inchikey14` is the naive key: the first block of the
InChIKey COCONUT already ships, which is what you get for free if you slice the column.
`scorer_inchikey14_rdkit_2026_03_3` is the same molecule put through
`TautomerEnumerator().Canonicalize` under RDKit 2026.03.3 and then keyed. The scorer's
function is the second one.

<!-- cell 6 code -->
```python
print(df.head(3).to_string(max_colwidth=60))
print()
print(df["status"].value_counts(dropna=False).to_string())

OK = df[df["status"] == "ok"].reset_index(drop=True)
N_ROWS, N_OK = len(df), len(OK)
N_BAD = int((df["status"] != "ok").sum())
COVERAGE = N_OK / N_ROWS

CHG = OK["key_changed_by_scorer"].to_numpy().astype(bool)
N_CHANGED = int(CHG.sum())
RATE = N_CHANGED / N_OK
N_NAIVE = int(OK[NAIVE].nunique())
N_SCORER = int(OK[SCOR].nunique())

print(f"\nrows in table                 {N_ROWS:>10,}")
print(f"rows with a computed key      {N_OK:>10,}   ({COVERAGE:.5%} of the table)")
print(f"rows RDKit could not parse    {N_BAD:>10,}   (kept with a null key, not dropped)")
print(f"keys changed by canonicalizing{N_CHANGED:>10,}   ({RATE:.4%} of keyed rows)")
print(f"distinct naive keys           {N_NAIVE:>10,}")
print(f"distinct scorer keys          {N_SCORER:>10,}")
print(f"net collapse                  {N_NAIVE - N_SCORER:>10,}")
```

<!-- cell 7 markdown -->
### Against the table's own build receipt

Five numbers were written into `package_receipt.json` the day the table was built. Here they
are beside what this kernel just recomputed from the file it actually mounted. If a row of
this table ever reads anything other than `match`, do not trust anything after it.

<!-- cell 8 code -->
```python
R = CFG["RECEIPT"]
checks = [
    ("rows",                 R["rows"],      N_ROWS),
    ("structures changed",   R["n_changed"], N_CHANGED),
    ("distinct naive keys",  R["n_raw14"],   N_NAIVE),
    ("distinct scorer keys", R["n_scorer"],  N_SCORER),
]
print(f"{'quantity':<24}{'receipt':>14}{'recomputed':>14}   verdict")
allok = True
for name, want, got in checks:
    good = (want == got); allok &= good
    print(f"{name:<24}{want:>14,}{got:>14,}   {'match' if good else 'MISMATCH'}")
cov_ok = abs(R["coverage"] - COVERAGE) < 1e-9
allok &= cov_ok
print(f"{'coverage':<24}{R['coverage']:>14.7f}{COVERAGE:>14.7f}   {'match' if cov_ok else 'MISMATCH'}")
assert allok, "the mounted table disagrees with its own build receipt"
print("\nEvery published figure reproduces from the mounted file.")
print(f"Headline restated from this kernel's own arithmetic: "
      f"{N_CHANGED:,} of {N_OK:,} structures ({RATE:.2%}) are keyed differently by the scorer.")
```

<!-- cell 9 markdown -->
---

## Part 2: Which molecules change, and why

A rate is not a mechanism. If one structure in ten is keyed differently, a reader should
finish this section able to look at a molecule and guess.

The cause is tautomerism. Canonicalization moves a mobile hydrogen to a fixed position, so a
molecule is at risk exactly when it has a hydrogen that can move: a donor next to an acceptor
across a conjugated path. A molecule with no heteroatom-hydrogen and no multiple bond to move
it onto has nothing to canonicalize and its key cannot change.

**How I am measuring, and why it is weaker than it should be.** RDKit is not in the Kaggle
image, so I cannot run SMARTS over these structures inside this kernel. What I have is the
SMILES text and the molecular formula, and I use substring motifs on the SMILES. Substring
matching on SMILES is a blunt instrument: it does not know about rings, it does not know which
atoms are connected, and `C(=O)N` will match an amide and also some things that are not one.
Treat every motif below as a label with noise in it. The direction and the size of the effects
survive that, and the control group at the end is the part I would defend hardest.

One thing to know before the table: **COCONUT writes SMILES in Kekule form.** Benzene is
`C1=CC=CC=C1`, not `c1ccccc1`. So the lowercase aromatic notation that most tautomer
discussions are written in, `[nH]` and friends, does not appear here at all, and the cell
below confirms that by matching zero rows on it.

<!-- cell 10 code -->
```python
smi = OK["canonical_smiles"]
BASE = CHG.mean()
print(f"base rate across all keyed structures: {BASE:.4%}\n")

MOTIFS = [
    ("N=C(N)      amidine / guanidine",  "N=C(N)"),
    ("C(O)=C      enol",                 "C(O)=C"),
    ("[N+](=O)[O-]  nitro",              "[N+](=O)[O-]"),
    ("C(=O)N      amide",                "C(=O)N"),
    ("N=          double bond from N",   "N="),
    ("=O          any carbonyl",         "=O"),
    ("NC(=O)      amide, other order",   "NC(=O)"),
    ("=S          thiocarbonyl",         "=S"),
    ("=N          double bond onto N",   "=N"),
    ("C(=O)O      acid or ester",        "C(=O)O"),
    ("[nH]        lowercase aromatic NH","[nH]"),
    ("c1ccccc1    lowercase benzene",    "c1ccccc1"),
]
rows = []
for label, pat in MOTIFS:
    m = smi.str.contains(pat, regex=False).to_numpy()
    n = int(m.sum())
    if n == 0:
        rows.append((label, 0, 0.0, float("nan"), float("nan"), 0.0)); continue
    r = CHG[m].mean()
    rows.append((label, n, m.mean()*100, r*100, r/BASE, CHG[m].sum()/N_CHANGED*100))
tab = pd.DataFrame(rows, columns=["motif", "structures", "pct_of_library",
                                  "change_rate_pct", "lift", "pct_of_all_changes"])
print(tab.sort_values("lift", ascending=False).to_string(index=False,
      float_format=lambda v: f"{v:8.3f}"))
```

<!-- cell 11 markdown -->
Read the two right-hand columns together. `lift` is how much more likely this motif is to be
re-keyed than an average structure; `pct_of_all_changes` is how much of the problem it
accounts for.

The enol motif is the one to look at: it is present in 10.7% of the library, doubles the
change rate, and accounts for 21.4% of every re-keyed structure in COCONUT. Amide is the other
big block at 20.2%. Amidine and nitro have the highest lift but are rare enough not to matter
in aggregate. Carbonyl of any kind is present in 80.7% of the library and covers 94.4% of all
changes, which is the mechanism stated as coverage rather than as lift.

The one that goes the other way is worth a second: **carboxylic acids and esters are
depleted**, lift 0.81. A carboxyl group is drawn with its hydrogen already in the canonical
place, so there is nothing to move.

### The control

The clean version of the claim is a negative one. Take the structures with no nitrogen at all
in the SMILES and no carbonyl, so no mobile-hydrogen donor and no acceptor to move it to, and
the change rate should collapse.

<!-- cell 12 code -->
```python
has_N  = smi.str.contains("N", regex=False).to_numpy()
has_CO = smi.str.contains("=O", regex=False).to_numpy()

for label, m in [("no N and no =O  (nothing to tautomerize)", ~has_N & ~has_CO),
                 ("=O but no N",                              ~has_N &  has_CO),
                 ("N but no =O",                               has_N & ~has_CO),
                 ("both N and =O",                             has_N &  has_CO)]:
    n = int(m.sum()); r = CHG[m].mean()
    print(f"{label:<42} n={n:>7,}  change {r:7.3%}  lift {r/BASE:5.2f}  "
          f"{CHG[m].sum()/N_CHANGED:6.1%} of all changes")

CTRL = CHG[~has_N & ~has_CO].mean()
print(f"\nThe control group changes at {CTRL:.3%} against a base of {BASE:.3%}: "
      f"{BASE/CTRL:.1f}x lower.")
print("That is the mechanism. No mobile hydrogen, no re-keying.")
```

<!-- cell 13 markdown -->
### Where it concentrates: element counts, curation level, mass

Three cuts a reader can apply without parsing anything. Element counts come out of the
`formula` column with a regular expression, so they are exact rather than inferred from text.

<!-- cell 14 code -->
```python
import re
def element_count(formula, el):
    m = re.search(el + r"(\d*)(?![a-z])", formula)
    if not m: return 0
    return 1 if m.group(1) == "" else int(m.group(1))

forms = OK["formula"].to_numpy()
for el in ["N", "S"]:
    c = np.array([element_count(f, el) for f in forms])
    print(f"-- {el} count --")
    for k in range(5):
        m = (c == k) if k < 4 else (c >= 4)
        if not m.sum(): continue
        lbl = f"{el}>=4" if k == 4 else f"{el}={k}"
        print(f"   {lbl:<6} n={m.sum():>7,}  change {CHG[m].mean():7.3%}  lift {CHG[m].mean()/BASE:5.2f}")

print("\n-- annotation_level (COCONUT's own curation confidence, 0 lowest) --")
for lv, g in OK.groupby("annotation_level"):
    r = g["key_changed_by_scorer"].mean()
    print(f"   level {lv:<4} n={len(g):>7,}  change {r:7.3%}  lift {r/BASE:5.2f}")

print("\n-- exact mass --")
bins = [0, 200, 300, 400, 500, 700, 1000, np.inf]
for lv, g in OK.groupby(pd.cut(OK["exact_mass"], bins), observed=True):
    r = g["key_changed_by_scorer"].mean()
    print(f"   {str(lv):>22}  n={len(g):>7,}  change {r:7.3%}  lift {r/BASE:5.2f}")
```

<!-- cell 15 markdown -->
Nitrogen count barely moves the rate once you are past zero, which surprised me: I expected
azole nitrogen to dominate. It does not, because this is a natural-product library and the
enol and amide channels are much bigger than the azole one.

The curation cut is the useful one. COCONUT's least-curated tier, annotation level 0, changes
at 14.24% against 7.49% at level 2, so the structures whose drawings nobody checked are close
to twice as likely to be drawn off-canonical. That is a fact about drawing conventions rather
than about chemistry, and it is the first hint of what Part 5 ends up concluding.

Mass rises from 7.25% below 200 Da to 13.65% in the 500 to 700 Da band, which is roughly
"bigger molecules have more places to put a hydrogen", then falls again above 700 Da where the
library is dominated by glycosides and peptides that are drawn to a house style.

<!-- cell 16 markdown -->
---

## Part 3: A changed key is not a changed answer

This is the part that turns the headline around, so I want to be slow about it.

The scorer takes your submitted SMILES, canonicalizes it, keys it. It takes the truth's SMILES,
canonicalizes it, keys it. Both sides go through the same function. So the fact that your
candidate's key changed under canonicalization is, on its own, **invisible**: it changed on
the truth's side too, and they still match.

What can actually move a score is a **disagreement between the two partitions**. Naive keying
and scorer keying each cut structure space into groups of "the same answer". Where those cuts
differ, and only there, your pipeline and the scorer will reach different verdicts. There are
exactly two ways they can differ.

**Merge.** Several naive keys land on one scorer key. Your pipeline thinks these are different
answers; the scorer thinks they are the same one. Any of them counts as correct.

**Split.** One naive key maps to several scorer keys. Your pipeline thinks these are the same
answer and will deduplicate down to one of them; the scorer thinks they are different. Deleting
the wrong one deletes your hit.

The counts are very different, and so, it turns out, are the consequences.

<!-- cell 17 code -->
```python
per_scorer = OK.groupby(SCOR)[NAIVE].nunique()     # naive keys inside each scorer key
per_naive  = OK.groupby(NAIVE)[SCOR].nunique()     # scorer keys inside each naive key
MERGED = per_scorer[per_scorer > 1]
SPLIT  = per_naive[per_naive > 1]

IN_M = (OK[SCOR].map(per_scorer).to_numpy() > 1)
IN_S = (OK[NAIVE].map(per_naive).to_numpy() > 1)
AFF  = IN_M | IN_S

print("MERGE  scorer keys holding more than one naive key")
print(f"   groups                      {len(MERGED):>9,}")
print(f"   naive keys per group        {MERGED.value_counts().sort_index().to_dict()}")
print(f"   structures involved         {IN_M.sum():>9,}   ({IN_M.mean():.4%} of the library)")
print("\nSPLIT  naive keys holding more than one scorer key")
print(f"   groups                      {len(SPLIT):>9,}")
print(f"   scorer keys per group       {SPLIT.value_counts().sort_index().to_dict()}")
print(f"   structures involved         {IN_S.sum():>9,}   ({IN_S.mean():.4%} of the library)")
print(f"\nstructures in EITHER direction {AFF.sum():>9,}   ({AFF.mean():.4%} of the library)")
print(f"structures in BOTH             {(IN_M & IN_S).sum():>9,}")
print(f"\nSo the set that can move a score is {AFF.mean():.2%}, not {RATE:.2%}. "
      f"The headline overstates the exposure by {RATE/AFF.mean():.1f}x.")
```

<!-- cell 18 markdown -->
### `key_changed_by_scorer` is the wrong safety check

The table ships a `key_changed_by_scorer` column, and the obvious thing to do with it is filter
on it: drop or flag the structures where it is true. I put it in the table and I now think
filtering on it is a mistake, because it answers a different question from the one you have.
Here it is scored as a detector against the set that can actually move a score.

<!-- cell 19 code -->
```python
ct = pd.crosstab(pd.Series(CHG, name="key_changed_by_scorer"),
                 pd.Series(AFF, name="can_actually_move_a_score"))
print(ct.to_string(), "\n")
tp = int((CHG & AFF).sum())
fp = int((CHG & ~AFF).sum())
fn = int((~CHG & AFF).sum())
print(f"flagged and really at risk (true positive)  {tp:>8,}")
print(f"flagged but inert          (false alarm)    {fp:>8,}")
print(f"not flagged but at risk    (missed)         {fn:>8,}")
print(f"\nprecision {tp/(tp+fp):.4f}   recall {tp/(tp+fn):.4f}")
print(f"\nIt raises {fp:,} alarms on structures where nothing can go wrong, and it stays "
      f"silent on {fn:,}\nstructures that can cost you. Use the key itself, not the flag.")
```

<!-- cell 20 markdown -->
Five and a half false alarms for every true one, and it misses 5,142 structures outright. The reason it misses
them is worth holding on to: a structure whose own key did not change can still sit in a scorer
group with a structure whose key did, and the disagreement belongs to the pair, not to either
molecule. **A property of a pair cannot be stored in a column about one row.** If you take one
operational thing from this notebook, take that: join on
`scorer_inchikey14_rdkit_2026_03_3` and never branch on `key_changed_by_scorer`.

<!-- cell 21 markdown -->
---

## Part 4: Two structures, one answer

479,718 naive keys collapse to 476,438 scorer keys. Here is what a collapse looks like from
the inside, with the SMILES, so you can see the hydrogen move.

<!-- cell 22 code -->
```python
# Rank by how many naive keys the group fuses, then by how many COCONUT rows it
# holds. Without the second sort the ties come out in hash order and the group
# the prose below is about would not necessarily be one of the three printed.
rank = pd.DataFrame({"naive_keys": MERGED,
                     "structures": OK[OK[SCOR].isin(MERGED.index)].groupby(SCOR).size()})
biggest = rank.sort_values(["naive_keys", "structures"], ascending=False).head(3)
for sk, row in biggest.iterrows():
    sub = OK[OK[SCOR] == sk]
    print(f"scorer key {sk}   <-  {int(row['naive_keys'])} naive keys, "
          f"{int(row['structures'])} structures")
    for nk, g in sub.groupby(NAIVE):
        r = g.iloc[0]
        print(f"   {nk}  {r['formula']:>12}  {r['canonical_smiles'][:86]}")
    print()
```

<!-- cell 23 markdown -->
The third group is the one to look at. `C6H8O6`, five naive keys, twelve COCONUT rows, one
scorer key `LPYXWGMUVRGUOY`. One of those five naive keys is `CIWBSHSKHKDKBQ`, which is
L-ascorbic acid: vitamin C, drawn five ways. A pipeline keying naively treats them as five
different answers and can spend five of its twenty-five candidate slots proposing vitamin C
five times. The scorer sees one.

### The small ones, where the mechanism is visible

The large groups are polyketides where it is hard to see what moved. Below are the shortest
two-key collapses in COCONUT, which are the textbook pairs.

<!-- cell 24 code -->
```python
two = OK[OK[SCOR].isin(MERGED[MERGED == 2].index)].copy()
two["_len"] = two["canonical_smiles"].str.len()
order = two.groupby(SCOR)["_len"].max().sort_values().head(400).index
shown = 0
print(f"{'scorer key':<16}{'formula':>10}   the two drawings, and the naive key each one gets")
for sk in order:
    reps = OK[OK[SCOR] == sk].groupby(NAIVE).first().reset_index()
    if len(reps) != 2 or reps["formula"].nunique() != 1:
        continue
    a, b = reps.iloc[0], reps.iloc[1]
    print(f"{sk:<16}{a['formula']:>10}   {a['canonical_smiles']:<16} [{a[NAIVE]}]")
    print(f"{'':<16}{'':>10}   {b['canonical_smiles']:<16} [{b[NAIVE]}]")
    shown += 1
    if shown >= 6:
        break
```

<!-- cell 25 markdown -->
`CC=O` and `C=CO` are acetaldehyde and vinyl alcohol. `CC(C)=O` and `C=C(C)O` are acetone and
its enol. Two rows in COCONUT, two different InChIKey14s if you slice the column, one answer
as far as CASMI is concerned.

### The other direction, which is the one that costs money

A naive key holding several scorer keys is rarer, 1,091 groups, and it is the dangerous one,
because a pipeline that deduplicates on naive keys will throw one of these away.

<!-- cell 26 code -->
```python
sp = OK[OK[NAIVE].isin(SPLIT.index)].copy()
sp["_len"] = sp["canonical_smiles"].str.len()
for nk in sp.groupby(NAIVE)["_len"].max().sort_values().head(5).index:
    s = OK[OK[NAIVE] == nk]
    print(f"naive key {nk}  ->  {s[SCOR].nunique()} different scorer keys")
    for sk, g in s.groupby(SCOR):
        r = g.iloc[0]
        print(f"   {sk}  {r['formula']:>14}  {r['canonical_smiles'][:70]}")
    print()
```

<!-- cell 27 markdown -->
Look at what the naive key is fusing. `C#N` and `[13CH]#[15N]` differ by isotope labelling.
`C[SH](C)CCC(=O)O` and `C[S](C)CCC(=O)O` do not even have the same molecular formula, one has
a hydrogen the other does not. The first block of an InChIKey is a skeleton hash and does not
carry isotope or charge information, so it fuses structures that are genuinely different
answers. Canonicalize first and they come apart.

If your deduplication step keys on the first block of a raw InChIKey, these are the rows where
it silently deletes a candidate that would have scored.

<!-- cell 28 markdown -->
---

## Part 5: Pricing it in MRR@25

Now the number that matters. A 2.30% disagreement rate is not a score. What does keying
naively actually do to MRR@25?

**The setup, and every assumption in it.**

- A CASMI submission is up to 25 SMILES per molecule. The scorer parses them, drops duplicates
  by scorer key, ranks what survives, and credits `1/rank` if the truth is in the first 25.
- I take a COCONUT structure as the query and as its own truth. Its candidate pool is every
  other COCONUT structure inside a `PPM` window on exact mass, which is what a precursor-mass
  filter gives you. **Assumption:** a mass window is a reasonable stand-in for a real candidate
  pool. It is the filter the public CASMI notebooks use.
- The pool is ranked by a **seeded random permutation**. This is deliberate. I am measuring
  what the keying does, not what a ranker does, and any real ranker would confound the two.
- The truth is then inserted at rank `r`, and `r` is swept over all of 1 to 25. **Assumption:**
  reporting the mean over that sweep weights every rank equally. The per-rank curve is printed
  too, so you can reweight it for a pipeline that lands the truth at rank 3 rather than 20.
- Two pipelines run on the identical ranked list. The **naive** one deduplicates by naive key
  and submits the first 25 survivors. The **scorer-keyed** one deduplicates by scorer key and
  submits the first 25 survivors. Both submissions are then scored by the scorer's rules.

The difference between those two MRRs is the price of keying naively. I also track what the
naive pipeline **believes** it scored, which is what it would compute on its own holdout, and
that turns out to be the interesting column.

<!-- cell 29 code -->
```python
O = OK.sort_values("exact_mass", kind="stable").reset_index(drop=True)
mass = O["exact_mass"].to_numpy()
nkc  = pd.factorize(O[NAIVE])[0]     # integer codes: comparisons get much cheaper
skc  = pd.factorize(O[SCOR])[0]
im   = O[SCOR].map(per_scorer).to_numpy() > 1
isp  = O[NAIVE].map(per_naive).to_numpy() > 1

PPM, TOP, CAP = CFG["PPM"], CFG["TOP_N"], CFG["POOL_CAP"]
LO = np.searchsorted(mass, mass * (1 - PPM * 1e-6), "left")
HI = np.searchsorted(mass, mass * (1 + PPM * 1e-6), "right")
SZ = HI - LO - 1
print(f"candidate pools at +/-{PPM:g} ppm on exact mass")
print(f"   median {np.median(SZ):.0f}   mean {SZ.mean():.1f}   p90 {np.percentile(SZ,90):.0f}"
      f"   max {SZ.max():,}")
print(f"   {(SZ >= TOP).mean():.2%} of structures sit in a window with at least {TOP} rivals")
```

<!-- cell 30 code -->
```python
def dedup(codes, idxs, cap=TOP):
    """First `cap` entries of `idxs` with distinct `codes`, order preserved."""
    seen, out = set(), []
    for j, c in zip(idxs, codes):
        if c in seen:
            continue
        seen.add(c); out.append(j)
        if len(out) >= cap:
            break
    return out

def reciprocal_rank(submission, truth_code, codes):
    """The scorer's rule: drop duplicate keys, rank, credit 1/rank inside TOP."""
    seen, rank = set(), 0
    for j in submission:
        c = codes[j]
        if c in seen:
            continue
        seen.add(c); rank += 1
        if c == truth_code:
            return 1.0 / rank
        if rank >= TOP:
            return 0.0
    return 0.0

def simulate(queries, seed, tag):
    rng = np.random.default_rng(seed)
    a = b = believed = 0.0
    misses = trials = 0
    distinct = []
    by_rank_a = np.zeros(TOP)      # so the assumption "average over r" can be undone
    by_rank_b = np.zeros(TOP)
    for i in queries:
        pool = np.arange(LO[i], HI[i]); pool = pool[pool != i]
        if len(pool) > CAP:
            pool = rng.choice(pool, CAP, replace=False)
        rng.shuffle(pool)
        ts, tn = skc[i], nkc[i]
        for r in range(1, TOP + 1):
            ranked = np.concatenate([pool[:r-1], [i], pool[r-1:]])
            sub_naive  = dedup(nkc[ranked], ranked)
            sub_scorer = dedup(skc[ranked], ranked)
            ra = reciprocal_rank(sub_naive,  ts, skc)   # what the naive sub really scores
            rb = reciprocal_rank(sub_scorer, ts, skc)   # what a correctly keyed sub scores
            a += ra; b += rb
            by_rank_a[r-1] += ra; by_rank_b[r-1] += rb
            believed += reciprocal_rank(sub_naive, tn, nkc)   # what the pipeline thinks
            misses += (ra == 0.0 and rb > 0.0)
            trials += 1
            if r == 1 and len(sub_naive) == TOP:
                distinct.append(len(set(skc[sub_naive])))
    q = max(len(queries), 1)
    return {"tag": tag, "n": len(queries),
            "naive": a/trials, "scorer": b/trials, "believed": believed/trials,
            "cost": (b-a)/trials, "self_error": (a-believed)/trials,
            "outright_miss": misses/trials,
            "by_rank_naive": by_rank_a/q, "by_rank_scorer": by_rank_b/q,
            "distinct_of_25": float(np.mean(distinct)) if distinct else float("nan")}
print("simulator defined")
```

<!-- cell 31 code -->
```python
strata = {
    "merge only": (np.where(im & ~isp)[0], CFG["SEED_MERGE"]),
    "split only": (np.where(isp & ~im)[0], CFG["SEED_SPLIT"]),
    "both":       (np.where(isp &  im)[0], CFG["SEED_BOTH"]),
}
unaff = np.where(~(im | isp))[0]
strata["unaffected"] = (
    np.random.default_rng(CFG["SEED_SAMPLE"]).choice(
        unaff, min(CFG["UNAFFECTED_SAMPLE"], len(unaff)), replace=False),
    CFG["SEED_NONE"])

t = time.time()
SIM = {}
for tag, (qs, seed) in strata.items():
    SIM[tag] = simulate(qs, seed, tag)
    s = SIM[tag]
    print(f"{tag:<12} n={s['n']:>6,}  naive {s['naive']:.6f}  scorer {s['scorer']:.6f}  "
          f"cost {s['cost']:+.6f}   believed {s['believed']:.6f}  "
          f"self-error {s['self_error']:+.6f}   outright miss {s['outright_miss']:6.2%}")
print(f"\n{time.time()-t:.1f}s")
```

<!-- cell 32 markdown -->
### Undoing the averaging assumption

Averaging over `r` from 1 to 25 weights every rank equally, which no real pipeline does. Here
is the same simulation resolved by rank, so you can reweight it for a pipeline that lands its
answer at rank 3 rather than rank 20. `cost` is what naive keying takes off at that rank.

<!-- cell 33 code -->
```python
print(f"{'rank':>5}{'split: naive':>15}{'split: scorer':>15}{'cost':>11}"
      f"{'merge: cost':>14}{'control: cost':>15}")
for r in range(1, TOP + 1):
    sn = SIM["split only"]["by_rank_naive"][r-1]
    ss = SIM["split only"]["by_rank_scorer"][r-1]
    mc = (SIM["merge only"]["by_rank_scorer"][r-1] - SIM["merge only"]["by_rank_naive"][r-1])
    uc = (SIM["unaffected"]["by_rank_scorer"][r-1] - SIM["unaffected"]["by_rank_naive"][r-1])
    print(f"{r:>5}{sn:>15.6f}{ss:>15.6f}{ss-sn:>+11.6f}{mc:>+14.6f}{uc:>+15.6f}")
c1 = (SIM["split only"]["by_rank_scorer"][0] - SIM["split only"]["by_rank_naive"][0])
print(f"\nAt rank 1 the split-group cost is {c1:+.6f}: if your ranker already has the answer "
      f"on top,\nnaive deduplication cannot have deleted it, so there is nothing to lose. The "
      f"cost grows\nwith rank because every candidate above the truth is another chance to "
      f"delete it.")
```

<!-- cell 34 markdown -->
### What those four rows say

`cost` is what naive keying takes off a real submission. `self-error` is how far the
pipeline's own estimate of its score sits from the truth, positive meaning it under-counts
itself.

**Merge only, 13,142 structures: cost -0.0001.** Nothing. And that is not luck, it is
arithmetic: if the scorer merges several of your candidates into one answer, any of them
counts, so merging can only ever help you. The sign is negative because the naive submission
occasionally scores a hair *better*, by spending a slot on a structure that the scorer folds
into the truth.

**Split only, 3,564 structures: cost +0.105.** That is the whole problem, and it is confined
to 0.48% of the library. Deduplicating on naive keys deletes a candidate the scorer would have
counted separately, and 41.5% of the time it deletes the one that was right.

**Unaffected, the 97.7% control: cost -0.0001.** Zero, which is the check that the simulation
is measuring keying and not noise.

<!-- cell 35 code -->
```python
w = {"merge only": int((im & ~isp).sum()), "split only": int((isp & ~im).sum()),
     "both": int((isp & im).sum()), "unaffected": int((~(im | isp)).sum())}
TOT = sum(w.values())
cost = sum(w[k]/TOT * SIM[k]["cost"] for k in w)
serr = sum(w[k]/TOT * SIM[k]["self_error"] for k in w)

print("stratum       structures     share      cost      contribution")
for k in w:
    print(f"{k:<13}{w[k]:>10,}{w[k]/TOT:>10.4%}{SIM[k]['cost']:>+11.6f}"
          f"{w[k]/TOT*SIM[k]['cost']:>+16.6f}")
print(f"\nLIBRARY-WEIGHTED COST OF KEYING NAIVELY : {cost:+.6f} MRR@25")
print(f"LIBRARY-WEIGHTED SELF-MEASUREMENT ERROR: {serr:+.6f} MRR@25")
print(f"\nSo on a COCONUT-shaped candidate pool this is worth about "
      f"{abs(cost)*1000:.1f} thousandths of MRR.")
```

<!-- cell 36 markdown -->
### When it stops being free

0.0004 is free. It is free because the risky stratum is 0.48% of COCONUT, not because the
effect is small when it lands. A test set is not a uniform sample of a structure library, and
Part 2 already showed the change rate is 1.9x higher in COCONUT's least-curated tier. So the
useful form of this result is not one number, it is a line: what the cost becomes if your
molecules are enriched in the split group.

<!-- cell 37 code -->
```python
base_split = w["split only"]/TOT
base_both  = w["both"]/TOT
print(f"{'enrichment':>11}{'split-group share':>20}{'cost in MRR@25':>18}")
for mult in (1, 2, 5, 10, 20, 50):
    ps, pb = min(1.0, base_split*mult), min(1.0, base_both*mult)
    c = ps*SIM["split only"]["cost"] + pb*SIM["both"]["cost"] + (1-ps-pb)*SIM["unaffected"]["cost"]
    print(f"{mult:>10}x{ps:>19.2%}{c:>+18.6f}")
print("\nIt takes roughly a twenty-fold enrichment before this reaches 0.01 MRR.")
print("I have no measurement of where a real CASMI test set sits on this line, and I am")
print("not going to guess one. The line is here so you can put your own pool on it.")
```

<!-- cell 38 markdown -->
### The column I did not expect: your own scoreboard

The `believed` column is what a naive pipeline computes when it scores itself on a holdout,
matching its candidate keys against its truth keys. Both sides naive, so it is at least
self-consistent. It is also wrong, and it is wrong in both directions at once.

<!-- cell 39 code -->
```python
print(f"{'stratum':<13}{'believed':>11}{'actually scored':>18}{'error':>11}")
for k in ["merge only", "split only", "both", "unaffected"]:
    s = SIM[k]
    print(f"{k:<13}{s['believed']:>11.4f}{s['naive']:>18.4f}{s['self_error']:>+11.4f}")
print(f"\nlibrary-weighted error: {serr:+.6f}")
mo, sp = SIM["merge only"]["self_error"], SIM["split only"]["self_error"]
print(f"\nOn the merge group it under-counts itself by {mo:+.4f}.")
print(f"On the split group it over-counts itself by  {sp:+.4f}.")
print(f"Those are {abs(mo)/abs(serr):.0f}x and {abs(sp)/abs(serr):.0f}x the size of the "
      f"weighted average they collapse into.")
```

<!-- cell 40 markdown -->
This is the finding I would actually act on. Library-weighted, the self-measurement error is
+0.0007, which rounds to nothing and would let you conclude the whole issue is cosmetic. It is
not nothing. It is a +0.098 error and a -0.256 error of opposite sign, weighted into
cancellation by the fact that the merge group happens to be about 3.7 times the size of
the split group in COCONUT.

That ratio is a property of COCONUT. It is not a law. Change the library, change the mass
range, change the curation tier, and the two errors reweight and stop cancelling. A validation
number built on naive keys is not approximately right, it is a difference of two large biases
that you have no particular reason to expect to stay balanced.

There is one more cost, and it is the plainest of the lot.

<!-- cell 41 code -->
```python
print("Of 25 candidate slots submitted after naive deduplication, the scorer sees:")
for k in ["merge only", "split only", "both", "unaffected"]:
    d = SIM[k]["distinct_of_25"]
    print(f"   {k:<13} {d:6.3f} distinct structures   ({TOP-d:.3f} slots wasted)")
d = SIM["merge only"]["distinct_of_25"]
print(f"\nOn the merge group that is {TOP-d:.2f} of your 25 guesses spent proposing a "
      f"molecule you already proposed.")
print("It does not lose you points on the molecules measured here, because the metric")
print("re-ranks after deduplicating. It does mean you got fewer real guesses than you paid")
print("for, and on a molecule whose answer sat at rank 26 that is the difference.")
```

<!-- cell 42 markdown -->
---

## Part 6: What to do about it, in two lines

The whole point of publishing the table is that you should not have to run a tautomer
enumerator. For any structure that is in COCONUT, the scorer's key is a join.

<!-- cell 43 code -->
```python
# The one-line version. Your candidate frame has a `canonical_smiles` column.
keys = (pd.read_parquet(PQ, columns=["canonical_smiles", SCOR]) if PQ else
        pd.read_csv(CSV, usecols=["canonical_smiles", SCOR])).drop_duplicates("canonical_smiles")

def attach_scorer_keys(candidates, smiles_col="canonical_smiles"):
    """Left-join the scorer's InChIKey14 onto your candidate frame."""
    return candidates.merge(keys.rename(columns={"canonical_smiles": smiles_col}),
                            on=smiles_col, how="left")

demo = pd.DataFrame({"canonical_smiles": ["CC=O", "C=CO", "CC(C)=O", "C=C(C)O", "O=CCO"]})
out = attach_scorer_keys(demo)
out["naive_key_if_you_slice_the_inchikey"] = (
    OK.set_index("canonical_smiles")[NAIVE].reindex(out["canonical_smiles"]).values)
print(out.to_string(index=False))
print("\nFive rows, five naive keys, three scorer keys. Rows 1 and 2 are one answer,")
print("rows 3 and 4 are one answer. A pipeline keying naively submits four guesses here")
print("and gets two.")
```

<!-- cell 44 markdown -->
For anything **not** in COCONUT, you have to compute the key, and that needs RDKit. Here is the
function, which is the scorer's definition and nothing more. The version pin is load-bearing:
tautomer canonicalization is an algorithm, and a different RDKit can canonicalize differently.

<!-- cell 45 code -->
```python
# One source of truth: the string below is printed AND executed, so what you
# read is exactly what runs. The imports sit inside the function on purpose, so
# this cell still defines and prints in an image that has no RDKit.
SCORER_KEY_SRC = '''
_TAUT = None

def scorer_key(smiles):
    # The key CASMI 2026 compares. None if RDKit cannot read the SMILES.
    # Pinned to RDKit 2026.03.3. Stereochemistry and tautomer form are both
    # discarded, which is the point: the scorer asks about the skeleton, after
    # the mobile hydrogens have been put somewhere canonical.
    global _TAUT
    from rdkit import Chem
    from rdkit.Chem.MolStandardize import rdMolStandardize
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return None
    if _TAUT is None:
        _TAUT = rdMolStandardize.TautomerEnumerator()
    return Chem.MolToInchiKey(_TAUT.Canonicalize(mol)).split("-")[0]
'''
print(SCORER_KEY_SRC)
exec(SCORER_KEY_SRC)

try:
    import rdkit
    from rdkit import Chem, RDLogger                          # noqa: F401
    from rdkit.Chem.MolStandardize import rdMolStandardize    # noqa: F401
    RDLogger.DisableLog("rdApp.*")   # the deliberate bad SMILES below is not an error
    HAVE_RDKIT, RDKIT_VERSION = True, rdkit.__version__
except Exception as e:
    HAVE_RDKIT, RDKIT_VERSION = False, None
    print(f"RDKit is not importable here ({type(e).__name__}), so the function above is "
          f"printed rather\nthan run. That is the expected case: RDKit is not in the Kaggle "
          f"image, which is exactly\nwhy the join above exists. No number in this notebook "
          f"depends on it.")

if HAVE_RDKIT:
    probe = ["CC=O", "C=CO", "CC(C)=O", "C=C(C)O", "O=CCO", "not a molecule"]
    table = OK.set_index("canonical_smiles")[SCOR]
    print(f"RDKit {RDKIT_VERSION} is present, so the function runs against the table.\n")
    print(f"{'smiles':<18}{'computed here':<18}{'published table':<18}verdict")
    agree = disagree = 0
    for s in probe:
        k, want = scorer_key(s), table.get(s, None)
        if want is None:
            v = "not in COCONUT"
        elif want == k:
            v = "match"; agree += 1
        else:
            v = "DIFFERS"; disagree += 1
        print(f"{s:<18}{str(k):<18}{str(want):<18}{v}")
    print(f"\n{agree} match, {disagree} differ. A disagreement here would mean this kernel's "
          f"RDKit is not\n2026.03.3, and the table's keys would not apply to it.")
```

<!-- cell 46 markdown -->
---

## Part 7: What this does not establish

**This is COCONUT, not the competition's candidate pool.** Every rate here, the 10.42%, the
2.30%, the 0.48%, is a rate on one open natural-product library with one set of drawing
conventions. CASMI's own structures are covered by the competition licence and are not in this
table and are not quoted in it. A different library, PubChem in particular, is curated
differently and will not give these numbers. Take the mechanism from this notebook and the
method; re-measure the rate on whatever pool you actually use.

**The simulation's truth comes from COCONUT too, and that is its biggest weakness.** I sample
a query from COCONUT and its answer is COCONUT's own drawing of it. In the real competition the
truth is drawn by someone else, and if their tautomer differs from COCONUT's for the same
molecule then a naive key misses where mine matches. That is a cross-library failure mode and
**this table cannot measure it**. It is the one place where the real cost could be materially
higher than 0.0004, and I am flagging it rather than burying it because it is the honest
counterweight to the deflation in Part 5. If I had to guess at its size I would not, which is
why there is no number here.

**The mechanism section is substring matching, not chemistry.** No RDKit in the image means no
SMARTS, no ring perception, no aromaticity model. `C(=O)N` catches amides and it also catches
things that are not amides. The control group, no nitrogen and no carbonyl at 2.19% against a
base of 10.42%, is the claim I would defend; the individual motif lifts are directional.

**RDKit 2026.03.3 is a pin, not a constant.** Tautomer canonicalization is an algorithm with a
version. The table's keys are correct for the scorer as long as the scorer runs 2026.03.3. If
the host moves, the table needs rebuilding, and so does anything you derived from it.

**The MRR numbers rest on stated assumptions**, listed at the top of Part 5 and repeated here:
a 5 ppm mass window as the candidate pool, a random ranker, and the truth's rank swept
uniformly over 1 to 25. The per-rank curve is in the output so you can reweight it. Change the
window and the pool sizes change; change the ranker and the absolute MRRs change. What is
robust across all of that is the shape: merge costs nothing, split costs a lot, and split is
small.

**Four structures have no key.** RDKit could not parse them. They are kept in the table with a
null key so it stays a complete mirror of COCONUT rather than a quietly filtered one. Coverage
is 99.9995%, which is a rounding error, but it is not zero and I would rather it be visible.

---

## What I would take from this

If you are keying candidates by slicing an InChIKey, you are not bleeding 10% of your score.
You are probably bleeding about 0.04% of it. Fix it anyway, because the fix is a join and
because the same mistake is doing something much worse to your local validation number than it
is doing to your leaderboard number.

And do not filter on `key_changed_by_scorer`. I shipped that column and it is the wrong tool:
six alarms in seven are false and it misses 5,142 structures that can actually cost you. Join
on the key.

If something here does not reproduce, say so in the comments with the cell and the number. I
would rather fix this notebook than be quietly wrong in it.

**COCONUT** is the Collection of Open Natural Products, Steinbeck Lab and contributors,
September 2026 CSV Lite release, released under CC BY 4.0. The derived key table keeps that
licence and ships its attribution file. COCONUT's contributors do not endorse anything
concluded here.

<!-- cell 47 code -->
```python
HEAD = {
    "rows": N_ROWS,
    "keyed": N_OK,
    "unparseable": N_BAD,
    "coverage": round(COVERAGE, 7),
    "n_changed": N_CHANGED,
    "change_rate": round(RATE, 6),
    "distinct_naive_keys": N_NAIVE,
    "distinct_scorer_keys": N_SCORER,
    "net_collapse": N_NAIVE - N_SCORER,
    "merge_groups": int(len(MERGED)),
    "split_groups": int(len(SPLIT)),
    "structures_merge": int(IN_M.sum()),
    "structures_split": int(IN_S.sum()),
    "structures_affected": int(AFF.sum()),
    "affected_rate": round(float(AFF.mean()), 6),
    "headline_overstates_by": round(float(RATE / AFF.mean()), 2),
    "flag_precision": round(tp/(tp+fp), 4),
    "flag_recall": round(tp/(tp+fn), 4),
    "flag_false_alarms": fp,
    "flag_missed": fn,
    "control_change_rate": round(float(CTRL), 6),
    "base_change_rate": round(float(BASE), 6),
    "cost_merge_only": round(SIM["merge only"]["cost"], 6),
    "cost_split_only": round(SIM["split only"]["cost"], 6),
    "cost_both": round(SIM["both"]["cost"], 6),
    "cost_unaffected": round(SIM["unaffected"]["cost"], 6),
    "cost_library_weighted": round(float(cost), 6),
    "self_error_merge_only": round(SIM["merge only"]["self_error"], 6),
    "self_error_split_only": round(SIM["split only"]["self_error"], 6),
    "self_error_library_weighted": round(float(serr), 6),
    "outright_miss_split_only": round(SIM["split only"]["outright_miss"], 4),
    "distinct_of_25_merge_only": round(SIM["merge only"]["distinct_of_25"], 3),
    "rdkit_available": bool(HAVE_RDKIT),
    "ppm": CFG["PPM"],
    "wall_seconds": round(time.time() - T0, 1),
}
with open(os.path.join(WORK, "headline.json"), "w") as fh:
    json.dump(HEAD, fh, indent=1)
for k, v in HEAD.items():
    print(f"  {k:<30} {v}")
print("\nwritten: headline.json")
```
