"""Within-set relatedness (2026-10-26; cross-test propagation idea, forum topic 752297).

Question: does a molecule of an evaluation set have OTHER molecules of the same set that are structurally related, and do the
spectral similarities between the two molecules' query spectra find those pairs? If the hidden test (400 Enveda natural products)
looks like the Enveda NP panel, test neighbours could carry structure information that the train-library analogs lack.
Per molecule (truth labels used only for this measurement):
  * struct_nn      : max Morgan r2 2048 Tanimoto of the truth to the truth of another molecule of the set (different identity group)
  * spec_nn_sim    : max shifted-entropy similarity (b1_analog.sim_pair, same polarity) between a query spectrum of this molecule and
                     one of another molecule; spec_nn_tan = Tanimoto between the two truths of that best spectral pair
  * test_ap        : max over other molecules b of tan(truth, truth_b) * sim_b^3    (oracle test-neighbour analog score)
  * train_ap_c2    : the analog channel's ap of the truth under the C2 mask (truth key, raw keys, identity group removed)
  * train_top1_tan : Tanimoto of the truth to the structure of the best C2 train analog, train_top1_sim its similarity
Usage: python -X utf8 test_relatedness.py --sets EVAL_CSV:SET1,SET2 ... --out diag/relatedness_<name>
"""
import argparse, os, sys, time
import numpy as np, pandas as pd, polars as pl
from numba import set_num_threads
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries, clean_peaks, entropy_weight  # noqa: E402
import b1_analog as BA  # noqa: E402

ap_ = argparse.ArgumentParser()
ap_.add_argument("--store", default="data/processed/spectra_store")
ap_.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
ap_.add_argument("--folds", default="data/external/identity_folds/structures.parquet")
ap_.add_argument("--sets", nargs="+", required=True, help="EVAL_CSV:SET1,SET2 (paths relative to experiments/b1_baseline)")
ap_.add_argument("--no_train", action="store_true", help="skip the train-analog part (no store build)")
ap_.add_argument("--out", required=True); ap_.add_argument("--max_spectra", type=int, default=8); ap_.add_argument("--threads", type=int, default=8)
a = ap_.parse_args()
set_num_threads(a.threads)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); T0 = time.time()
def log(*x): print(f"[rel {time.time() - T0:6.0f}s]", *x, flush=True)

S_MZ = np.load(f"{ROOT}/{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{ROOT}/{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{ROOT}/{a.store}/spec_off.npy")
meta = pl.read_parquet(f"{ROOT}/{a.store}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean", "scorer_ik14"])
lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64); key_of_row = meta["scorer_ik14"].to_numpy()
ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
def spectrum(x): return np.asarray(S_MZ[S_OFF[x]:S_OFF[x + 1]], np.float64), np.asarray(S_IT[S_OFF[x]:S_OFF[x + 1]], np.float64)
store = None if a.no_train else BA.Store(np.arange(meta.height), lib_of_row, add_of_row, mode_of_row, ce_of_row, key_of_row, prec_of_row, spectrum, log=log)

from rdkit import Chem, RDLogger, DataStructs  # noqa: E402
from rdkit.Chem import rdFingerprintGenerator  # noqa: E402
RDLogger.DisableLog("rdApp.*"); GEN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
ts = pd.read_parquet(f"{ROOT}/{a.structs}", columns=["key", "smiles"]).drop_duplicates("key"); KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
_FP = {}
def fp_of(smi):
    if smi not in _FP:
        m = Chem.MolFromSmiles(smi) if smi else None; _FP[smi] = GEN.GetFingerprint(m) if m is not None else None
    return _FP[smi]
_idf = pd.read_parquet(f"{ROOT}/{a.folds}", columns=["scorer_key", "identity_group"]).dropna().drop_duplicates()
GROUP_KEYS = _idf.groupby("identity_group").scorer_key.apply(lambda x: set(x.astype(str))).to_dict(); KEY_GROUP = dict(zip(_idf.scorer_key.astype(str), _idf.identity_group))


def prep(s):
    cm, ci = clean_peaks(np.asarray(s["mz"], np.float64), np.asarray(s["it"], np.float64), float(s["prec"]), floor=BA.FLOOR, top=BA.TOP)
    if not len(ci): return None
    p = entropy_weight(ci); return (cm.astype(np.float64), p.astype(np.float64), float(-(p[p > 0] * np.log(p[p > 0])).sum()), float(s["prec"]))


out_rows = []
for spec in a.sets:
    eval_csv, sets = spec.split(":")
    ev = pd.read_csv(os.path.join(HERE, eval_csv)); ev["molecule"] = ev["molecule"].astype(str)
    for s in sets.split(","):
        mols = ev[ev.set == s].reset_index(drop=True); info = []
        for r in mols.itertuples(index=False):
            mid, lib, tk = str(r.molecule), r.lib, str(r.scorer_key)
            qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
            q = select_queries(qrows, a.max_spectra, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
            qspec, qp = [], []
            for x in q:
                sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
                mz, it = spectrum(x); d = dict(mz=mz - sh, it=it, prec=float(prec_of_row[x]) - sh, adduct=add_of_row[x], mode=mode_of_row[x]); qspec.append(d)
                pp = prep(d)
                if pp is not None: qp.append((d["mode"], pp))
            info.append(dict(mid=mid, lib=lib, key=tk, grp=KEY_GROUP.get(tk), q=q, qspec=qspec, qp=qp, fp=fp_of(KEY_SMI.get(tk))))
        fps = [d["fp"] for d in info]; n = len(info)
        T = np.zeros((n, n))
        for i in range(n):
            if fps[i] is None: continue
            T[i] = [DataStructs.TanimotoSimilarity(fps[i], f) if f is not None else 0.0 for f in fps]
        Ssp = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                v = 0.0
                for mi, pi in info[i]["qp"]:
                    for mj, pj in info[j]["qp"]:
                        if mi == mj: v = max(v, BA.sim_pair(pi, pj))
                Ssp[i, j] = Ssp[j, i] = v
        for i, d in enumerate(info):
            other = np.array([j != i and info[j]["key"] != d["key"] and (d["grp"] is None or info[j]["grp"] != d["grp"]) for j in range(n)])
            row = dict(set=s, molecule=d["mid"], lib=d["lib"], n_q=len(d["qp"]), has_fp=d["fp"] is not None)
            if other.any() and d["fp"] is not None:
                t_ = np.where(other, T[i], -1); s_ = np.where(other, Ssp[i], -1)
                jb = int(np.argmax(s_))
                row.update(struct_nn=float(t_.max()), spec_nn_sim=float(s_[jb]), spec_nn_tan=float(T[i, jb]), spec_nn_mol=info[jb]["mid"],
                           test_ap=float(np.max(np.where(other, T[i] * np.clip(Ssp[i], 0, 1) ** 3, 0))),
                           n_spec_ge05=int((s_ >= 0.5).sum()), n_struct_ge07=int((t_ >= 0.7).sum()))
            if store is not None and d["fp"] is not None:
                raw = {key_of_row[x] for x in ik_rows.get(d["mid"], []) if key_of_row[x] is not None}
                drop = raw | {d["key"]} | set(GROUP_KEYS.get(d["grp"], set()))
                an = store.analogs(d["qspec"], query_rows=d["q"], drop_keys=drop)
                afp = [(fp_of(KEY_SMI.get(k)), v) for k, v in an]; afp = [(f, v) for f, v in afp if f is not None]
                if afp:
                    tan = np.array(DataStructs.BulkTanimotoSimilarity(d["fp"], [f for f, _ in afp])); w = np.array([v for _, v in afp])
                    row.update(train_ap_c2=float((tan * w ** 3).max()), train_top1_tan=float(tan[0]), train_top1_sim=float(w[0]), train_best_tan=float(tan.max()))
            out_rows.append(row)
        log(f"{s}: {n} molecules")
R = pd.DataFrame(out_rows); os.makedirs(os.path.dirname(os.path.join(HERE, a.out)) or ".", exist_ok=True)
R.to_csv(os.path.join(HERE, a.out + ".csv"), index=False)
L = [f"# Within-set relatedness ({time.strftime('%Y-%m-%d %H:%M')})", "",
     "| set | n | struct_nn>=0.5 | >=0.7 | >=0.85 | spec_nn>=0.5 | >=0.7 | tan of spec-nn (sim>=0.7) | test_ap>train_ap | test_ap>=0.3 | train_ap>=0.3 |",
     "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
for s, g in R.groupby("set", sort=False):
    g = g[g.has_fp & g.struct_nn.notna()] if "struct_nn" in g else g
    hi = g[g.spec_nn_sim >= 0.7]
    tr = g.train_ap_c2.fillna(0) if "train_ap_c2" in g else pd.Series(0, index=g.index)
    L.append(f"| {s} | {len(g)} | {(g.struct_nn >= 0.5).mean():.2f} | {(g.struct_nn >= 0.7).mean():.2f} | {(g.struct_nn >= 0.85).mean():.2f} | {(g.spec_nn_sim >= 0.5).mean():.2f} | "
             f"{(g.spec_nn_sim >= 0.7).mean():.2f} | {hi.spec_nn_tan.mean() if len(hi) else float('nan'):.2f} | {(g.test_ap > tr + 1e-9).mean():.2f} | {(g.test_ap >= 0.3).mean():.2f} | {(tr >= 0.3).mean():.2f} |")
open(os.path.join(HERE, a.out + ".md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
