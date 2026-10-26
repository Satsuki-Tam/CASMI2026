"""043 pre-submission audit (a) of gt3 (Codex 043 Q5a): is the structure gt3 inserts really absent from the databases by OFFICIAL identity?

The frozen rule calls a product novel when its raw InChIKey first block is not in the molecule's window (raw keys). A tautomer spelling of
a window structure has a different raw key but the same official key. For every inserted gt3 product (gen_eval2p --dump_choice rows with
gt3_insert), the structures of the PubChem tier, the v2 pool and COCONUT within 10 ppm of its exact mass with the SAME molecular formula are
canonicalised to official keys; a match means the product is a known (alias) structure, not a new one.
Usage: python -X utf8 gt3_audit.py --choice diag/genchoice2p_p2dev.parquet ... --out diag/gt3_audit
"""
import argparse, os, pickle, sys, time
import numpy as np, pandas as pd, polars as pl
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ap = argparse.ArgumentParser(); ap.add_argument("--choice", nargs="+", required=True); ap.add_argument("--out", required=True); ap.add_argument("--workers", type=int, default=16)
ap.add_argument("--tier", default="data/external/pubchem_tier"); ap.add_argument("--pool", default="data/external/v2_pool/pool_meta.parquet"); ap.add_argument("--coco", default="data/external/coconut")
a = ap.parse_args()
ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); T0 = time.time()
G = {}


def load():
    G["tm"] = np.load(f"{ROOT}/{a.tier}/pc_mass.npy", mmap_mode="r"); G["to"] = np.load(f"{ROOT}/{a.tier}/pc_off.npy", mmap_mode="r"); G["tb"] = np.load(f"{ROOT}/{a.tier}/pc_smiles.npy", mmap_mode="r")
    P = pl.read_parquet(f"{ROOT}/{a.pool}", columns=["smiles", "mass", "src"]).sort("mass"); G["pm"] = P["mass"].to_numpy(); G["ps"] = P["smiles"].to_numpy(); G["psrc"] = P["src"].to_numpy()
    cm = pickle.load(open(f"{ROOT}/{a.coco}/coco_meta.pkl", "rb")); G["cm"] = np.load(f"{ROOT}/{a.coco}/coco_mass.npy"); G["cs"] = np.asarray(cm["smiles"])


def job(t):
    import b1_gen as BG
    from rdkit import Chem, RDLogger
    from rdkit.Chem.Descriptors import ExactMolWt
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula
    RDLogger.DisableLog("rdApp.*")
    key, smi, okey = t
    m = Chem.MolFromSmiles(smi); M = ExactMolWt(m); f0 = CalcMolFormula(m); tol = M * 10e-6
    hits = {"tier": 0, "pool_train": 0, "pool_coco": 0, "coco": 0}; n_same = 0
    lo = int(np.searchsorted(G["tm"], M - tol, "left")); hi = int(np.searchsorted(G["tm"], M + tol, "right"))
    srcs = []
    if hi > lo:
        o = np.asarray(G["to"][lo:hi + 1]).astype(np.int64); raw = bytes(G["tb"][o[0]:o[-1]]); base = o[0]
        srcs += [("tier", raw[o[i] - base:o[i + 1] - base].decode("ascii")) for i in range(hi - lo)]
    lo = int(np.searchsorted(G["pm"], M - tol, "left")); hi = int(np.searchsorted(G["pm"], M + tol, "right"))
    srcs += [("pool_train" if int(G["psrc"][i]) in (1, 3) else "pool_coco", str(G["ps"][i])) for i in range(lo, hi)]
    lo = int(np.searchsorted(G["cm"], M - tol, "left")); hi = int(np.searchsorted(G["cm"], M + tol, "right"))
    srcs += [("coco", str(G["cs"][i])) for i in range(lo, hi)]
    for src, s2 in srcs:
        m2 = Chem.MolFromSmiles(s2)
        if m2 is None or CalcMolFormula(m2) != f0: continue
        n_same += 1
        if BG.official_key(s2) == okey: hits[src] += 1
    return key, dict(n_window=len(srcs), n_same_formula=n_same, **{f"match_{k}": v for k, v in hits.items()})


if __name__ == "__main__":
    load()
    C = pd.concat([pd.read_parquet(os.path.join(HERE, p)).assign(source=os.path.basename(p)) for p in a.choice], ignore_index=True)
    ins = C[C.gt3_insert.astype(bool) & C.gen_smiles.notna()]
    print(f"[audit] {len(C)} (molecule, view) rows, {len(ins)} gt3 insertions", flush=True)
    tasks = [((r.source, r.set, r.view, r.molecule), str(r.gen_smiles), str(r.gen_okey)) for r in ins.itertuples(index=False)]
    rows = []
    with Pool(a.workers) as p:
        for i, (key, d) in enumerate(p.imap_unordered(job, tasks, chunksize=2)):
            rows.append(dict(source=key[0], set=key[1], view=key[2], molecule=key[3], **d))
            if i % 200 == 0: print(f"[audit {time.time() - T0:5.0f}s] {i + 1}/{len(tasks)}", flush=True)
    R = pd.DataFrame(rows); R["known_any"] = R[[c for c in R.columns if c.startswith("match_")]].sum(axis=1) > 0
    R["known_db"] = (R.match_tier + R.match_coco + R.match_pool_coco) > 0
    R.to_csv(os.path.join(HERE, a.out + ".csv"), index=False)
    L = [f"# gt3 audit (a): inserted structures that are known by official identity ({time.strftime('%Y-%m-%d %H:%M')})", "",
         "| source | view | inserted | known in tier/COCONUT (alias) | known only as a train pool structure | median same-formula structures |", "|---|---|---:|---:|---:|---:|"]
    for (src, v), g in R.groupby(["source", "view"], sort=False):
        L.append(f"| {src} | {v} | {len(g)} | {int(g.known_db.sum())} ({g.known_db.mean():.3f}) | {int((g.known_any & ~g.known_db).sum())} | {g.n_same_formula.median():.0f} |")
    L.append(""); L.append(f"total inserted {len(R)}, known (any source) {int(R.known_any.sum())} ({R.known_any.mean():.4f})")
    open(os.path.join(HERE, a.out + ".md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
