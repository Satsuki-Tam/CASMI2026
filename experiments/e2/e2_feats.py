"""143 E2 step 2: the second engine's own evidence for every E-window row (b1_ewin.py tables), per view.
  MetFrag-lite (b1_frag, own implementation; max explained-intensity fraction over the query spectra) -- view independent;
  analog propagation (b1_analog Store, as the evaluator): C1 = the truth key re-represented outside its selection library (relib), C2 = the truth's
  raw keys, scorer key and identity group dropped; features ap / a1 / best_tan / top_tan / mean_tan of every candidate (Morgan r2 2048).
Writes <ewin dir>/e2f_<set>.parquet keyed by (set, molecule, official_key) + a manifest; the E-window table is not modified.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/e2/e2_feats.py --ewin experiments/e2/ewin/np053_f1dev --eval_csv experiments/b1_baseline/np053_f1dev/p2_molecules.csv --sets NP_H NP_X NP_N"""
import argparse, json, os, sys, time
from multiprocessing import Pool
import numpy as np, pandas as pd, polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); B = os.path.join(ROOT, "experiments/b1_baseline"); sys.path.insert(0, B)
_F = {}
def _frag(t):
    import b1_frag as BF
    mid, smiles, spectra = t; sp = [dict(mz=np.asarray(s[0]), it=np.asarray(s[1]), prec=s[2], mode=s[3]) for s in spectra]
    return mid, {s: float(BF.score(BF.fragments(s), sp)) for s in smiles}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ewin", required=True); ap.add_argument("--eval_csv", required=True); ap.add_argument("--sets", nargs="+", required=True)
    ap.add_argument("--workers", type=int, default=10); ap.add_argument("--store", default="data/processed/spectra_store"); ap.add_argument("--folds", default="data/external/identity_folds/structures.parquet")
    ap.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet"); a = ap.parse_args(); t0 = time.time()
    P_ = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p)
    import b1_analog as BA
    from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*"); MG = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    st = P_(a.store); S_MZ = np.load(f"{st}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{st}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{st}/spec_off.npy")
    meta = pl.read_parquet(f"{st}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean", "scorer_ik14"])
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
    prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64); key_of_row = meta["scorer_ik14"].to_numpy()
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    key_rows = {k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("scorer_ik14").is_not_null()).group_by("scorer_ik14").agg(pl.col("row")).iter_rows()}
    def spectrum(x): return np.asarray(S_MZ[S_OFF[x]:S_OFF[x + 1]], np.float64), np.asarray(S_IT[S_OFF[x]:S_OFF[x + 1]], np.float64)
    store = BA.Store(np.arange(meta.height), lib_of_row, add_of_row, mode_of_row, ce_of_row, key_of_row, prec_of_row, spectrum, log=lambda *x: print(*x, flush=True))
    ts = pd.read_parquet(P_(a.structs), columns=["key", "smiles"]).drop_duplicates("key"); KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
    idf = pd.read_parquet(P_(a.folds), columns=["scorer_key", "identity_group"]).dropna().drop_duplicates()
    GROUP_KEYS = idf.groupby("identity_group").scorer_key.apply(lambda x: set(x.astype(str))).to_dict(); KEY_GROUP = dict(zip(idf.scorer_key.astype(str), idf.identity_group))
    _FP = {}
    def fp_of(smi):
        if smi not in _FP:
            m = Chem.MolFromSmiles(smi) if smi else None; _FP[smi] = MG.GetFingerprint(m) if m is not None else None
        return _FP[smi]
    ev = pd.read_csv(P_(a.eval_csv)); ev["molecule"] = ev.molecule.astype(str)
    man = dict(sets={})
    with Pool(a.workers) as wp:
        for s in a.sets:
            E = pd.read_parquet(os.path.join(P_(a.ewin), f"ewin_{s}.parquet")); E["molecule"] = E.molecule.astype(str); out_rows = []
            mols = ev[ev.set == s]; Q = {}; tasks = []
            for r in mols.itertuples(index=False):
                mid, lib = str(r.molecule), r.lib
                g = E[E.molecule == mid]
                if not len(g): continue
                qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
                q = select_queries(qrows, 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x])); qspec = []
                for x in q:
                    sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
                    mz, it = spectrum(x); qspec.append(dict(mz=mz - sh, it=it, prec=float(prec_of_row[x]) - sh, adduct=add_of_row[x], mode=mode_of_row[x]))
                Q[mid] = (r, q, qspec, g); tasks.append((mid, g.smiles.astype(str).tolist(), [(s_["mz"].tolist(), s_["it"].tolist(), s_["prec"], s_["mode"]) for s_ in qspec]))
            FR = dict(wp.imap_unordered(_frag, tasks, chunksize=2)); print(f"  {s}: MetFrag-lite for {len(FR)} molecules ({time.time()-t0:.0f}s)", flush=True)
            for mid, (r, q, qspec, g) in Q.items():
                tk = str(r.scorer_key); raw = {key_of_row[x] for x in ik_rows.get(mid, []) if key_of_row[x] is not None}
                an = {"c1": store.analogs(qspec, query_rows=q, relib=(tk, r.lib), key_rows=key_rows), "c2": store.analogs(qspec, query_rows=q, drop_keys=raw | {tk} | set(GROUP_KEYS.get(KEY_GROUP.get(tk), set())))}
                cfp = [fp_of(sm) for sm in g.smiles.astype(str)]; feats = {}
                for v, lst in an.items():
                    afp = [(fp_of(KEY_SMI.get(k)), sv) for k, sv in lst]; afp = [(f_, sv) for f_, sv in afp if f_ is not None]
                    feats[v] = BA.features(cfp, [f_ for f_, _ in afp], [sv for _, sv in afp])
                for i, (ok, sm) in enumerate(zip(g.official_key.astype(str), g.smiles.astype(str))):
                    rec = dict(set=s, molecule=mid, official_key=ok, frag=FR[mid].get(sm, 0.0))
                    for v in ("c1", "c2"):
                        for f in ("ap", "a1", "best_tan", "top_tan", "mean_tan"): rec[f"ana_{f}_{v}"] = float(feats[v][f][i])
                    out_rows.append(rec)
            pd.DataFrame(out_rows).to_parquet(os.path.join(P_(a.ewin), f"e2f_{s}.parquet"), index=False); man["sets"][s] = len(out_rows)
            print(f"saved {s}: {len(out_rows)} rows ({time.time()-t0:.0f}s)", flush=True)
    man["seconds"] = round(time.time() - t0); json.dump(man, open(os.path.join(P_(a.ewin), "e2f_manifest.json"), "w"), indent=1); print("done")


if __name__ == "__main__":
    main()
