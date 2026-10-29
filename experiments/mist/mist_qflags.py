"""133 v2 (Codex 133 Q1(1)): molecule-level MIST query availability, independent of the candidate formulas, by the SAME query policy as
mist_score.py / mist_score_v4.py (selection library rows with a test adduct -> select_queries(max 8) -> keep [M+H]+ / [M+Na]+); no MIST
forward pass. Writes <out>/mist_<tag>_<set>_qflags.parquet: set, molecule, n_q0 (selected queries), n_mist_q (MIST-usable), qreason
(no_qrows / no_mist_adduct / ''). Consistency check against the v4 candidate table of the same tag: a molecule with any 'ok' candidate must
have n_mist_q > 0, and a molecule whose candidates carry no_qrows / no_mist_adduct must have exactly that qreason (stop otherwise).
Usage (Spark, .venv-mist or .venv): python -X utf8 experiments/mist/mist_qflags.py --store data/processed/spectra_store --eval_csv CSV --tag T --sets S1 ... --out DIR"""
import argparse, os, sys
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); B1 = os.path.abspath(os.path.join(HERE, "..", "b1_baseline")); sys.path.insert(0, B1)
from b1_common import select_queries, ADDUCT_SHIFT
MIST_ADD = ("[M+H]+", "[M+Na]+")
ap = argparse.ArgumentParser()
for k in ("store", "eval_csv", "tag", "out"): ap.add_argument(f"--{k}", required=True)
ap.add_argument("--sets", nargs="+", required=True); ap.add_argument("--max_spectra", type=int, default=8); a = ap.parse_args()
meta = pl.read_parquet(f"{a.store}/spec_meta.parquet")
lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); ce_of_row = meta["ce_mean"].to_numpy()
ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
mols = pd.read_csv(a.eval_csv); mols["molecule"] = mols.molecule.astype(str)
for s in a.sets:
    out = []
    for r in mols[mols.set == s].itertuples(index=False):
        mid = str(r.molecule); lib = r.lib
        qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
        q0 = select_queries(qrows, a.max_spectra, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
        q = [x for x in q0 if add_of_row[x] in MIST_ADD]
        out.append(dict(set=s, molecule=mid, n_q0=len(q0), n_mist_q=len(q), qreason=("no_qrows" if not q0 else ("no_mist_adduct" if not q else ""))))
    O = pd.DataFrame(out)
    cand_p = os.path.join(a.out, f"mist_{a.tag}_{s}.parquet")
    if os.path.exists(cand_p):   # consistency with the candidate table of the same tag
        C = pd.read_parquet(cand_p, columns=["molecule", "status"]); C["molecule"] = C.molecule.astype(str); qr = dict(zip(O.molecule, O.qreason)); nm = dict(zip(O.molecule, O.n_mist_q))
        for mid, h in C.groupby("molecule"):
            st = set(h.status.astype(str))
            if "ok" in st and nm[mid] == 0: sys.exit(f"{s} {mid}: an ok candidate but no MIST query")
            for x in ("no_qrows", "no_mist_adduct"):
                if x in st and qr[mid] != x: sys.exit(f"{s} {mid}: candidate status {x} but qreason {qr[mid]!r}")
    O.to_parquet(os.path.join(a.out, f"mist_{a.tag}_{s}_qflags.parquet"), index=False)
    print(f"{a.tag} {s}: {len(O)} molecules, no MIST query {int((O.n_mist_q == 0).sum())} ({O.qreason.value_counts().to_dict()})", flush=True)
