"""156 (v2 prep; world version of e2_feats.py 143): the second engine's own evidence for every row of a WORLD E-window table
(b1_ewin_world.py), under the world's batch-level masks (world_masks.json, the single source of truth):
  MetFrag-lite (b1_frag; view independent);
  analog propagation (b1_analog Store) with the W135 world rule of experiments/w135/w135_p.py (analogs_world): every key of the C2 / C3
  identities (train_hide) and every C1 key is dropped from the analog store for every query; the C1 keys' representatives are re-picked
  from their spectra outside their selection library and outside the duplicate rows (c1_excl) and searched with the same rules.
  The c1 and c2 feature columns are written identical (the world view), ap / a1 / best_tan / top_tan / mean_tan (Morgan r2 2048).
Writes <ewin dir>/e2f_<set>.parquet keyed by (set, molecule, official_key) + manifest. No label is read.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/e2/e2_feats_world.py --ewin DIR --eval_csv BATCH.csv --masks WORLD/world_masks.json --sets SET"""
import argparse, hashlib, json, os, sys, time
from multiprocessing import Pool
import numpy as np, pandas as pd, polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); B = os.path.join(ROOT, "experiments/b1_baseline"); sys.path.insert(0, B)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def _frag(t):
    import b1_frag as BF
    mid, smiles, spectra = t; sp = [dict(mz=np.asarray(s[0]), it=np.asarray(s[1]), prec=s[2], mode=s[3]) for s in spectra]
    return mid, {s: float(BF.score(BF.fragments(s), sp)) for s in smiles}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ewin", required=True); ap.add_argument("--eval_csv", required=True); ap.add_argument("--masks", required=True)
    ap.add_argument("--sets", nargs="+", required=True); ap.add_argument("--workers", type=int, default=10); ap.add_argument("--store", default="data/processed/spectra_store")
    ap.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
    a = ap.parse_args(); t0 = time.time()
    P_ = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p)
    import b1_analog as BA
    from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries, clean_peaks, entropy_weight
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
    W = json.load(open(P_(a.masks)))
    if not set(a.sets) <= set(W["sets"]): sys.exit("STOP: sets not in the world masks")
    HIDE = set(W["train_hide"]); C1 = {k: (lib_, set(W["c1_excl"].get(k, []))) for m_, (tk_, lib_, ks_) in W["c1_lib"].items() for k in ks_}
    C1_REPS = {}
    for k, (lib_, excl) in C1.items():
        alt = [int(x) for x in key_rows.get(k, []) if lib_of_row[x] != lib_ and int(x) not in excl and add_of_row[x] in ADDUCT_SHIFT]
        C1_REPS[k] = {md: [(y, store.prepared(y)) for y in store.pick([x for x in alt if mode_of_row[x] == md])] for md in ("positive", "negative")}
    print(f"world masks: hidden keys {len(HIDE):,}, C1 keys {len(C1)} ({time.time()-t0:.0f}s)", flush=True)

    def analogs_world(qspec, query_rows, n_analog=BA.N_ANALOG, win=BA.WIN):   # w135_p.analogs_world (same rules)
        qset = set(int(x) for x in query_rows); best = {}
        drop_ix = {store.kix[k] for k in (HIDE | set(C1)) if k in store.kix}
        prepped = []
        for s in qspec:
            cm, ci = clean_peaks(np.asarray(s["mz"], np.float64), np.asarray(s["it"], np.float64), float(s["prec"]), floor=store.floor, top=store.top)
            if not len(ci): continue
            p = entropy_weight(ci); q = (cm.astype(np.float64), p.astype(np.float64), float(-(p[p > 0] * np.log(p[p > 0])).sum()), float(s["prec"]))
            prepped.append((s, q))
            st_ = store.S.get(s["mode"])
            if st_ is None or not len(st_["M"]): continue
            Mq = q[3] + ADDUCT_SHIFT[s["adduct"]]
            lo = int(np.searchsorted(st_["M"], Mq - win, "left")); hi = int(np.searchsorted(st_["M"], Mq + win, "right"))
            if hi <= lo: continue
            sims = BA._search(q[0], q[1], q[2], q[3], lo, hi, st_["off"], st_["mz"], st_["p"], st_["ent"], st_["prec"])
            for kk in np.flatnonzero(sims > 0.05):
                r = lo + int(kk)
                if int(st_["row"][r]) in qset: continue
                ki = int(st_["key"][r])
                if ki in drop_ix: continue
                v = float(sims[kk])
                if v > best.get(ki, 0.0): best[ki] = v
        for k, reps in C1_REPS.items():
            if k in HIDE or k not in store.kix: continue
            ki = store.kix[k]
            for s, q in prepped:
                Mq = q[3] + ADDUCT_SHIFT[s["adduct"]]
                for y, cy in reps.get(s["mode"], []):
                    if cy is None or int(y) in qset or abs((cy[3] + ADDUCT_SHIFT[add_of_row[y]]) - Mq) > win: continue
                    v = BA.sim_pair(q, cy)
                    if v > 0.05 and v > best.get(ki, 0.0): best[ki] = v
        top = sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))[:n_analog]
        return [(store.keys[k], v) for k, v in top]

    _FP = {}
    def fp_of(smi):
        if smi not in _FP:
            m = Chem.MolFromSmiles(smi) if smi else None; _FP[smi] = MG.GetFingerprint(m) if m is not None else None
        return _FP[smi]
    ev = pd.read_csv(P_(a.eval_csv)); ev["molecule"] = ev.molecule.astype(str)
    man = dict(sets={}, masks=sha(P_(a.masks)), eval_csv=sha(P_(a.eval_csv)), script=sha(os.path.abspath(__file__)), version="2.1")
    with Pool(a.workers) as wp:
        for s in a.sets:
            out = os.path.join(P_(a.ewin), f"e2f_{s}.parquet")
            if os.path.exists(out): sys.exit(f"STOP: {out} exists (no overwrite)")
            ein = os.path.join(P_(a.ewin), f"ewin_{s}.parquet"); E = pd.read_parquet(ein); E["molecule"] = E.molecule.astype(str); out_rows = []; an_dump = {}
            mols = ev[ev.set == s] if "set" in ev.columns else ev; Q = {}; tasks = []
            for r in mols.itertuples(index=False):
                mid, lib = str(r.molecule), r.lib
                g = E[E.molecule == mid]
                if not len(g): continue
                qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
                q = select_queries(qrows, 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x])); qspec = []
                for x in q:
                    sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
                    mz, it = spectrum(x); qspec.append(dict(mz=mz - sh, it=it, prec=float(prec_of_row[x]) - sh, adduct=add_of_row[x], mode=mode_of_row[x]))
                Q[mid] = (q, qspec, g); tasks.append((mid, g.smiles.astype(str).tolist(), [(s_["mz"].tolist(), s_["it"].tolist(), s_["prec"], s_["mode"]) for s_ in qspec]))
            FR = dict(wp.imap_unordered(_frag, tasks, chunksize=2)); print(f"  {s}: MetFrag-lite for {len(FR)} molecules ({time.time()-t0:.0f}s)", flush=True)
            for mid, (q, qspec, g) in Q.items():
                lst = analogs_world(qspec, q); an_dump[mid] = [[str(k_), float(v_)] for k_, v_ in lst]   # v2.1: checked against the W135 world P analogs
                afp = [(fp_of(KEY_SMI.get(k)), sv) for k, sv in lst]; afp = [(f_, sv) for f_, sv in afp if f_ is not None]
                feats = BA.features([fp_of(sm) for sm in g.smiles.astype(str)], [f_ for f_, _ in afp], [sv for _, sv in afp])
                for i, (ok, sm) in enumerate(zip(g.official_key.astype(str), g.smiles.astype(str))):
                    rec = dict(set=s, molecule=mid, official_key=ok, frag=FR[mid].get(sm, 0.0))
                    for v in ("c1", "c2"):
                        for f in ("ap", "a1", "best_tan", "top_tan", "mean_tan"): rec[f"ana_{f}_{v}"] = float(feats[f][i])
                    out_rows.append(rec)
            cols = ["set", "molecule", "official_key", "frag"] + [f"ana_{f}_{v}" for v in ("c1", "c2") for f in ("ap", "a1", "best_tan", "top_tan", "mean_tan")]
            tmp_ = out + ".tmp"; pd.DataFrame(out_rows, columns=cols).to_parquet(tmp_, index=False); os.replace(tmp_, out)   # typed (an empty set keeps the schema)
            ap_ = os.path.join(P_(a.ewin), f"e2f_analogs_{s}.json"); json.dump(an_dump, open(ap_, "w"))
            man["sets"][s] = dict(rows=len(out_rows), input_ewin=sha(ein), output=sha(out), analogs=sha(ap_))
            print(f"saved {s}: {len(out_rows)} rows ({time.time()-t0:.0f}s)", flush=True)
    man["seconds"] = round(time.time() - t0); json.dump(man, open(os.path.join(P_(a.ewin), "e2f_world_manifest.json"), "w"), indent=1); print("done")


if __name__ == "__main__":
    main()
