"""109 (Codex 109 Q1): metadata census of molecules still available for NEW class-1 confirmation groups (label use = identity membership only).
Population: raw keys of eval_set2/census.parquet with spectra in >= 2 libraries (a query library + at least one other library = C1-capable), joined to
the GLOBAL identity groups (identity_folds); excluded = identity groups of every existing selection CSV under experiments/b1_baseline and p1_baseline
and of the panel (panel molecules resolved to global groups via scorer_key / inchikey14). Counts by identity fold x type:
  G-type  = has a timsTOF (enveda-180) spectrum + another library;  NP-type = in an NP library (gnps/riken/mona/massbank/msdial) + another library
  ref bins = n_ref 1-9 / >= 10 (all references of the identity, an upper bound of the usable other-library references), MSG membership split.
Usage: python -X utf8 c1census109.py"""
import glob, os
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
c = pl.read_parquet(os.path.join(HERE, "eval_set2", "census.parquet")).to_pandas()
st = pd.read_parquet(os.path.join(ROOT, "data", "external", "identity_folds", "structures.parquet"), columns=["inchikey14", "scorer_key", "identity_group", "fold_identity"])
r2g = dict(zip(st.inchikey14.astype(str), st.identity_group)); r2f = dict(zip(st.inchikey14.astype(str), st.fold_identity)); k2g = dict(zip(st.scorer_key.astype(str), st.identity_group))
c["g"] = c.inchikey14.map(r2g); c["fold"] = c.inchikey14.map(r2f)
used = set(); files = sorted(set(glob.glob(os.path.join(HERE, "*", "p1_molecules.csv")) + glob.glob(os.path.join(HERE, "*", "p2_molecules.csv")) + glob.glob(os.path.join(HERE, "*", "v2", "p2_molecules.csv"))
                              + glob.glob(os.path.join(HERE, "diag", "cf107", "*.csv")) + [os.path.join(ROOT, "experiments", "p1_baseline", "run1", "p1_molecules.csv")]))
for f in files:
    d = pd.read_csv(f)
    if "scorer_key" not in d.columns and "molecule" not in d.columns: continue
    for k, m in zip(d.get("scorer_key", d.get("molecule")).astype(str), d.get("molecule", d.get("scorer_key")).astype(str)):
        g = k2g.get(k, r2g.get(m))
        if g is not None: used.add(int(g))
avail = c[c.g.notna() & ~c.g.astype("Int64").isin(list(used)) & (c.n_libs >= 2)].copy()
NPL = ("gnps", "riken", "mona", "massbank", "msdial")
avail["G"] = avail.has_timstof & avail.libs.str.contains("enveda-180")
avail["NP"] = avail.libs.apply(lambda s: any(x in str(s) for x in NPL))
avail["msg"] = avail.in_msg_raw | avail.in_msg_scorer; avail["ref"] = np.where(avail.n_ref >= 10, ">=10", "1-9")
grp = avail.drop_duplicates("g")
L = [f"# 109 C1 census (available identity groups, one per group; excluded {len(used):,} used groups from {len(files)} selection files + panel)", "",
     "| fold | G-type (timsTOF + other lib) | NP-type refs 1-9 | NP-type refs >= 10 | of which MSG members (NP) | all C1-capable |", "|---|---:|---:|---:|---:|---:|"]
for f in sorted(grp.fold.dropna().unique()):
    q = grp[grp.fold == f]
    L.append(f"| {int(f)} | {int(q.G.sum())} | {int((q.NP & (q.ref == '1-9')).sum())} | {int((q.NP & (q.ref == '>=10')).sum())} | {int((q.NP & q.msg).sum())} | {len(q)} |")
q = grp; L.append(f"| all | {int(q.G.sum())} | {int((q.NP & (q.ref == '1-9')).sum())} | {int((q.NP & (q.ref == '>=10')).sum())} | {int((q.NP & q.msg).sum())} | {len(q)} |")
open(os.path.join(HERE, "diag", "c1census109.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
