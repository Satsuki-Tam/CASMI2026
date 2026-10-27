"""Exact reference comparability for saved b1_features tables (Codex 075 (a)): replays b1_features' library block (query selection, cleaning,
exact / suspected duplicate rule, MAX_REF cap with same-adduct priority, C1 / C2 masks) for every train-structure candidate of a run, and records
  n_ref_<v>     = number of kept references (must equal lib_nref_<v> of the table)
  n_cmp_pol_<v> = kept references whose polarity matches a query polarity (similarity actually computed)
  n_cmp_add_<v> = kept references whose adduct equals a query adduct
  sim_<v>       = max same-polarity entropy similarity over the kept references (must equal lib_sim_<v> of the table = exactness check)
Usage: python -X utf8 refcmp_exact.py --run run_np053_f1dev --eval_csv np053_f1dev/p2_molecules.csv --sets NP_H [--limit N] [--workers 4]"""
import argparse, os, sys, time
import numpy as np, pandas as pd, polars as pl
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MAX_REF, DUP_SIM, MAX_SPECTRA = 24, 0.98, 8
_G = {}
def _init():
    from b1_common import ADDUCT_SHIFT, ELECTRON, clean_peaks, entropy_similarity, select_queries
    st = f"{ROOT}/data/processed/spectra_store"
    meta = pl.read_parquet(f"{st}/spec_meta.parquet", columns=["row", "inchikey14", "scorer_ik14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean"])
    _G.update(ADD=ADDUCT_SHIFT, EL=ELECTRON, clean=clean_peaks, esim=entropy_similarity, sel=select_queries,
              lib=meta["ingest_lib"].to_numpy(), add=meta["adduct"].to_numpy(), mode=meta["ionization_mode"].to_numpy(), prec=meta["precursor_mz"].to_numpy(), ce=meta["ce_mean"].to_numpy(),
              key_rows={k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("scorer_ik14").is_not_null()).group_by("scorer_ik14").agg(pl.col("row")).iter_rows()},
              ik_rows={k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()},
              MZ=np.load(f"{st}/spec_mz.npy", mmap_mode="r"), IT=np.load(f"{st}/spec_int.npy", mmap_mode="r"), OFF=np.load(f"{st}/spec_off.npy"), cache={})
def _spec(x, sh):
    s, e = int(_G["OFF"][x]), int(_G["OFF"][x + 1]); return np.asarray(_G["MZ"][s:e], np.float64) - sh, np.asarray(_G["IT"][s:e], np.float64)
def _exact_dup(q, rmz, rit, rprec, radd):
    if q["adduct"] != radd or abs(q["prec"] - rprec) >= 0.005: return False
    qmz, qit = q["clean"]; return len(qmz) == len(rmz) and len(qmz) > 0 and np.allclose(qmz, rmz, atol=2e-4) and np.allclose(qit, rit, atol=1e-3)
def job(t):
    mid, lib, truth_key, cands = t   # cands: list of (official_key, is_truth, train_flag)
    L, A, Mo, P = _G["lib"], _G["add"], _G["mode"], _G["prec"]
    shift = _G["EL"] if lib == "enveda-180" else 0.0
    qrows = sorted(int(x) for x in _G["ik_rows"].get(mid, []) if L[x] == lib and A[x] in _G["ADD"])
    q = _G["sel"](qrows, MAX_SPECTRA, lambda x: A[x], lambda x: float(_G["ce"][x]))
    qspec = []
    for x in q:
        sh = shift if Mo[x] == "positive" else 0.0; mz, it = _spec(x, sh); pr = float(P[x]) - sh
        qspec.append(dict(row=x, prec=pr, adduct=A[x], mode=Mo[x], clean=_G["clean"](mz, it, pr)))
    qrows_set = {s["row"] for s in qspec}; qmodes = {s["mode"] for s in qspec}; qadds = {s["adduct"] for s in qspec}
    out = []
    for okey, is_truth, train in cands:
        if not train or okey not in _G["key_rows"]: continue
        is_tc = bool(is_truth) or okey == truth_key
        kept = []
        for x in (int(v) for v in _G["key_rows"][okey] if int(v) not in qrows_set):
            if x not in _G["cache"]:
                sh = _G["EL"] if (L[x] == "enveda-180" and Mo[x] == "positive") else 0.0; mz, it = _spec(x, sh)
                _G["cache"][x] = (_G["clean"](mz, it, float(P[x]) - sh), float(P[x]) - sh)
            (rmz, rit), rp = _G["cache"][x]
            if any(_exact_dup(s, rmz, rit, rp, A[x]) for s in qspec): continue
            if any(abs(s["prec"] - rp) < 0.005 and s["mode"] == Mo[x] and _G["esim"](s["clean"][0], s["clean"][1], rmz, rit) >= DUP_SIM for s in qspec): continue
            kept.append(x)
        refs = [x for x in kept if not (is_tc and L[x] == lib)]
        if len(refs) > MAX_REF:
            pri = np.array([0 if A[x] in qadds else 1 for x in refs]); refs = [refs[i] for i in np.argsort(pri, kind="stable")[:MAX_REF]]
        best = 0.0
        for x in refs:
            (rmz, rit), _ = _G["cache"][x]
            for s in qspec:
                if s["mode"] != Mo[x]: continue
                best = max(best, _G["esim"](s["clean"][0], s["clean"][1], rmz, rit))
        n, npol, nadd = len(refs), sum(Mo[x] in qmodes for x in refs), sum(A[x] in qadds for x in refs)
        out.append(dict(molecule=mid, official_key=okey, n_ref_c1=n, n_cmp_pol_c1=npol, n_cmp_add_c1=nadd, sim_c1=best,
                        n_ref_c2=0 if is_tc else n, n_cmp_pol_c2=0 if is_tc else npol, n_cmp_add_c2=0 if is_tc else nadd, sim_c2=0.0 if is_tc else best))
    if len(_G["cache"]) > 200_000: _G["cache"].clear()
    return out
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--eval_csv", required=True); ap.add_argument("--sets", nargs="+", required=True)
    ap.add_argument("--limit", type=int, default=0); ap.add_argument("--workers", type=int, default=4); ap.add_argument("--out", default="")
    a = ap.parse_args(); t0 = time.time()
    ev = pd.read_csv(os.path.join(HERE, a.eval_csv)); ev["molecule"] = ev.molecule.astype(str); ev = ev.drop_duplicates("molecule").set_index("molecule")
    allrows = []
    for s in a.sets:
        F = pd.read_parquet(os.path.join(HERE, a.run, f"b1_features_{s}.parquet")); F["molecule"] = F.molecule.astype(str)
        tasks = []
        for mid, g in F.groupby("molecule", sort=False):
            if mid not in ev.index: continue
            g1 = g.drop_duplicates("official_key")
            tasks.append((mid, ev.loc[mid, "lib"], str(ev.loc[mid, "scorer_key"]), list(zip(g1.official_key.astype(str), g1.is_truth.astype(bool), g1.in_train_c1.astype(bool)))))
        if a.limit: tasks = tasks[:a.limit]
        with Pool(a.workers, initializer=_init) as p:
            res = [r for chunk in p.imap(job, tasks, chunksize=2) for r in chunk]
        R = pd.DataFrame(res); R.insert(0, "set", s)
        # exactness check against the table
        T = F.drop_duplicates(["molecule", "official_key"])[["molecule", "official_key", "lib_sim_c1", "lib_sim_c2", "lib_nref_c1", "lib_nref_c2"]]
        x = R.merge(T, on=["molecule", "official_key"], how="left")
        for v in ("c1", "c2"):
            ds = (x[f"sim_{v}"] - x[f"lib_sim_{v}"]).abs(); dn = (x[f"n_ref_{v}"] - x[f"lib_nref_{v}"]).abs()
            print(f"{s} {v}: candidates {len(x)} | sim exact {int((ds < 1e-9).sum())} (max diff {float(ds.max()):.2e}) | nref exact {int((dn == 0).sum())} | "
                  f"n_ref>0 & n_cmp_pol==0: {int(((x[f'n_ref_{v}'] > 0) & (x[f'n_cmp_pol_{v}'] == 0)).sum())}", flush=True)
        allrows.append(R)
    D = pd.concat(allrows, ignore_index=True); p = a.out or os.path.join(HERE, f"diag/refcmpx_{os.path.basename(a.run)}.parquet"); D.to_parquet(p, index=False)
    print(p, len(D), f"rows ({time.time() - t0:.0f}s)")
