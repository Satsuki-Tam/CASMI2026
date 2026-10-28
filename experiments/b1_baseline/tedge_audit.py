"""Transductive edge audit (exploratory, label-free edges): how often a query molecule has a spectrally similar OTHER molecule in the same batch,
and whether such spectral neighbours are structural relatives (truth-truth Morgan Tanimoto; labels used only for this audit and for removing
pairs of the same official identity). Query spectra are selected exactly like gen_eval2fd (selection library, test adducts, select_queries 8,
enveda-180 positive m/z electron-corrected) and prepared like the analog store (clean_peaks floor 0.005 / top 64, entropy weights); pair
similarity = max shifted entropy similarity (b1_analog.sim_pair) over same-polarity spectrum pairs, molecules within +-200 Da neutral mass.
Usage: python -X utf8 tedge_audit.py --out diag/tedge_audit TAG:EVAL_CSV [TAG:EVAL_CSV ...]  (batches = each tag alone + the union of all tags
except 'panel')."""
import argparse, os, sys
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from b1_common import ADDUCT_SHIFT, ELECTRON, clean_peaks, entropy_weight, select_queries
from b1_analog import sim_pair, FLOOR, TOP
ap = argparse.ArgumentParser(); ap.add_argument("specs", nargs="+"); ap.add_argument("--out", default="diag/tedge_audit"); ap.add_argument("--store", default="data/processed/spectra_store")
ap.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
a = ap.parse_args()
S_MZ = np.load(f"{ROOT}/{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{ROOT}/{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{ROOT}/{a.store}/spec_off.npy")
meta = pl.read_parquet(f"{ROOT}/{a.store}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean"])
lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64)
ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
ts = pd.read_parquet(f"{ROOT}/{a.structs}", columns=["key", "smiles"]).drop_duplicates("key"); KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
from rdkit import Chem, RDLogger, DataStructs
from rdkit.Chem import rdFingerprintGenerator
RDLogger.DisableLog("rdApp.*"); MG = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
def fp_of(smi):
    m = Chem.MolFromSmiles(smi) if smi else None
    return MG.GetFingerprint(m) if m is not None else None
MOL = {}   # (tag, molecule) -> dict(key, M, specs=[(mode, q)], fp)
for spec in a.specs:
    tag, csv = spec.split(":", 1)
    ev = pd.read_csv(os.path.join(HERE, csv)); ev["molecule"] = ev.molecule.astype(str)
    for r in ev.itertuples(index=False):
        mid, lib = str(r.molecule), r.lib
        qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
        q = select_queries(qrows, 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
        specs, Ms = [], []
        for x in q:
            sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
            mz = np.asarray(S_MZ[S_OFF[x]:S_OFF[x + 1]], np.float64) - sh; it = np.asarray(S_IT[S_OFF[x]:S_OFF[x + 1]], np.float64); prec = float(prec_of_row[x]) - sh
            cm, ci = clean_peaks(mz, it, prec, floor=FLOOR, top=TOP)
            if not len(ci): continue
            p = entropy_weight(ci); specs.append((mode_of_row[x], (cm.astype(np.float64), p.astype(np.float64), float(-(p[p > 0] * np.log(p[p > 0])).sum()), prec)))
            Ms.append(prec + ADDUCT_SHIFT[add_of_row[x]])
        if not specs: continue
        MOL[(tag, mid)] = dict(key=str(r.scorer_key), M=float(np.median(Ms)), specs=specs, fp=fp_of(KEY_SMI.get(str(r.scorer_key), "")), set=str(r.set))
print(f"molecules with query spectra: {len(MOL):,}", flush=True)
def audit(name, members):
    ks = sorted(members, key=lambda k: MOL[k]["M"]); Ms = np.array([MOL[k]["M"] for k in ks]); out = []
    for i, k in enumerate(ks):
        lo = int(np.searchsorted(Ms, Ms[i] - 200.0, "left")); hi = int(np.searchsorted(Ms, Ms[i] + 200.0, "right"))
        best, bj = 0.0, None
        for j in range(lo, hi):
            if j == i or MOL[ks[j]]["key"] == MOL[k]["key"]: continue
            s = 0.0
            for md, q in MOL[k]["specs"]:
                for md2, q2 in MOL[ks[j]]["specs"]:
                    if md == md2: s = max(s, sim_pair(q, q2))
            if s > best: best, bj = s, j
        tt = DataStructs.TanimotoSimilarity(MOL[k]["fp"], MOL[ks[bj]]["fp"]) if (bj is not None and MOL[k]["fp"] is not None and MOL[ks[bj]]["fp"] is not None) else np.nan
        oth = [MOL[ks[j]]["fp"] for j in range(len(ks)) if j != i and MOL[ks[j]]["key"] != MOL[k]["key"] and MOL[ks[j]]["fp"] is not None]
        fam = max(DataStructs.BulkTanimotoSimilarity(MOL[k]["fp"], oth)) if (MOL[k]["fp"] is not None and oth) else np.nan   # label-based family density (audit only)
        out.append(dict(batch=name, tag=k[0], molecule=k[1], set=MOL[k]["set"], nn_sim=best, nn=(ks[bj][1] if bj is not None else ""), nn_dmass=(abs(Ms[bj] - Ms[i]) if bj is not None else np.nan), truth_tan=tt, fam_tan=fam))
    return pd.DataFrame(out)
tags = sorted({k[0] for k in MOL}); R = []
for t in tags: R.append(audit(t, [k for k in MOL if k[0] == t])); print(f"batch {t} done", flush=True)
uni = [k for k in MOL if k[0] != "panel"]
if len({k[0] for k in uni}) > 1: R.append(audit("union_dev", uni)); print("union done", flush=True)
R = pd.concat(R, ignore_index=True); R.to_csv(os.path.join(HERE, a.out + ".csv"), index=False)
L = ["# transductive edge audit (label-free edges; truth Tanimoto only for the audit)", "", "| batch | n | nn_sim >= 0.5 | >= 0.6 | >= 0.7 | nearest (sim >= 0.6): truth Tanimoto median | its share >= 0.7 | family density: any other truth Tanimoto >= 0.7 | families reached by an edge (sim >= 0.6) |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
for b, g in R.groupby("batch", sort=False):
    e6 = g[g.nn_sim >= 0.6]
    L.append(f"| {b} | {len(g)} | {(g.nn_sim >= 0.5).mean():.3f} | {(g.nn_sim >= 0.6).mean():.3f} | {(g.nn_sim >= 0.7).mean():.3f} | {e6.truth_tan.median() if len(e6) else float('nan'):.3f} | "
             f"{(e6.truth_tan >= 0.7).mean() if len(e6) else float('nan'):.3f} | {(g.fam_tan >= 0.7).mean():.3f} | {((g.fam_tan >= 0.7) & (g.nn_sim >= 0.6) & (g.truth_tan >= 0.7)).sum()}/{int((g.fam_tan >= 0.7).sum())} |")
open(os.path.join(HERE, a.out + ".md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
