"""101 (Codex 101 Q3, days 1-2): label-free audit of a full-pool second-engine candidate window on the development tables.
Per molecule: query-derived neutral masses per adduct (gen dump), +-10 ppm windows over (a) the v2 pool (train U COCONUT, official keys, src bits),
(b) BIO = ChEBI / LIPID MAPS structures not in COCONUT (bio_structures.parquet, raw InChIKey14), (c) PubChemLite (annotations parquet, official
candidate_key, masses from pubchemlite_mass.npy). Window sizes per layer and the truth's reach in the C2 view (train membership hidden: a train-only
truth is NOT reachable through the pool; COCONUT / BIO / PubChemLite membership counts), compared with B1's shortlist reach (b1_molecules csv).
Only parquet / npy (allow_pickle=False) inputs are read. Usage: python -X utf8 pool_audit101.py TAG RUN EVAL_CSV [TAG RUN EVAL_CSV ...]"""
import json, os, sys
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
K = f"{ROOT}/data/external_kaggle"
pool = pl.read_parquet(f"{ROOT}/data/external/v2_pool/pool_meta.parquet", columns=["key", "mass", "src"])
pmass = pool["mass"].to_numpy().astype(np.float64); pkey = pool["key"].to_numpy(); psrc = pool["src"].to_numpy()
bio = pl.read_parquet(f"{K}/casmi26-attributed-v4g-reproduction-assets/casmi-chebi-lmsd-structures/casmi-chebi-lmsd-structures/bio_structures.parquet", columns=["inchikey14", "monoisotopic_mass"]).sort("monoisotopic_mass")
bmass = bio["monoisotopic_mass"].to_numpy().astype(np.float64); bkey = bio["inchikey14"].to_numpy()
pcl = pl.read_parquet(f"{K}/casmi26-pubchem-popularity-prior/pubchemlite_annotations.parquet", columns=["pubchemlite_row", "candidate_key"])
pclm = np.load(f"{K}/casmi26-attributed-v4g-reproduction-assets/casmi26-pubchemlite-cc0-candidate-fingerprints/casmi26-pubchemlite-cc0-candidate-fingerprints/pubchemlite_mass.npy", allow_pickle=False).astype(np.float64)
assert len(pclm) == pcl.height, (len(pclm), pcl.height)
o = np.argsort(pclm, kind="stable"); cmass = pclm[o]; ckey = pcl["candidate_key"].to_numpy()[o]
POOL_COCO = set(pool.filter(pl.col("src").is_in([2, 3]))["key"].to_list()); BIO_KEYS = set(bkey.tolist()); PCL_KEYS = set(ckey.tolist())
def win(sorted_mass, keys, masses):
    out = set()
    for M in masses:
        tol = M * 10e-6; lo = int(np.searchsorted(sorted_mass, M - tol, "left")); hi = int(np.searchsorted(sorted_mass, M + tol, "right")); out.update(keys[lo:hi].tolist())
    return out
rows = []
args = sys.argv[1:]
for i in range(0, len(args), 3):
    tag, run, csv = args[i], args[i + 1], args[i + 2]
    ev = pd.read_csv(os.path.join(HERE, csv)); ev["molecule"] = ev.molecule.astype(str)
    for s in sorted(ev.set.unique()):
        gp = os.path.join(HERE, run, "gen", f"gen_{s}.npz")
        if not os.path.exists(gp): continue
        G = np.load(gp, allow_pickle=False)
        MASS = {str(m): list(json.loads(str(x)).values()) for m, x in zip(G["mol"], G["masses"])}
        Mcsv = pd.read_csv(os.path.join(HERE, run, f"b1_molecules_{s}.csv")); Mcsv["molecule"] = Mcsv.molecule.astype(str); Mcsv = Mcsv.set_index("molecule")
        for r in ev[ev.set == s].itertuples(index=False):
            mid = str(r.molecule); tk = str(r.scorer_key); rk = str(getattr(r, "raw_key", mid))
            if mid not in MASS: continue
            ms = MASS[mid]; wp = win(pmass, pkey, ms); wb = win(bmass, bkey, ms); wc = win(cmass, ckey, ms)
            coco_pool = {k for k in wp if k in POOL_COCO}
            rows.append(dict(tag=tag, set=s, molecule=mid, n_pool=len(wp), n_pool_coco=len(coco_pool), n_bio=len(wb), n_pcl=len(wc), n_union=len(wp | wb | wc),
                             truth_coco=tk in POOL_COCO, truth_bio=(rk in BIO_KEYS) or (tk in BIO_KEYS), truth_pcl=tk in PCL_KEYS,
                             reach_pool_c2=tk in coco_pool, reach_bio=(rk in wb) or (tk in wb), reach_pcl=tk in wc,
                             b1_short=bool(Mcsv.loc[mid, "truth_in_shortlist"]) if mid in Mcsv.index and "truth_in_shortlist" in Mcsv.columns else np.nan,
                             b1_window=bool(Mcsv.loc[mid, "truth_in_window"]) if mid in Mcsv.index and "truth_in_window" in Mcsv.columns else np.nan))
R = pd.DataFrame(rows); R["reach_union_c2"] = R.reach_pool_c2 | R.reach_bio | R.reach_pcl
R.to_csv(os.path.join(HERE, "diag/pool_audit101.csv"), index=False)
L = ["# 101 pool-window audit (label-free sizes; truth reach in the C2 view)", "", "| tag | n | window pool (median) | pool COCONUT | BIO | PubChemLite | union | reach pool(COCO) | +BIO | +PCLite | union reach | B1 window | B1 shortlist |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
for tag, g in R.groupby("tag", sort=False):
    L.append(f"| {tag} | {len(g)} | {int(g.n_pool.median())} | {int(g.n_pool_coco.median())} | {int(g.n_bio.median())} | {int(g.n_pcl.median())} | {int(g.n_union.median())} | {g.reach_pool_c2.mean():.3f} | {(g.reach_pool_c2 | g.reach_bio).mean():.3f} | {(g.reach_pool_c2 | g.reach_pcl).mean():.3f} | {g.reach_union_c2.mean():.3f} | {g.b1_window.mean():.3f} | {g.b1_short.mean():.3f} |")
open(os.path.join(HERE, "diag/pool_audit101.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
