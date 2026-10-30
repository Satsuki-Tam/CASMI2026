"""145 parity: e2_engine.E2Engine (the code the Kaggle kernel will run) against the development tables built by b1_ewin.py + e2_feats.py,
on the first N molecules of given sets, in the C1 regime (the masks of the development C1 view). Compares the official-key sets and every
C1 feature column; with --model also the E2 order. Exit 1 on any difference above the tolerance.
Usage (Spark): .venv/bin/python -X utf8 experiments/e2/e2_parity.py --ewin experiments/e2/ewin/np053_f1dev --eval_csv experiments/b1_baseline/np053_f1dev/p2_molecules.csv
               --sets NP_H --fold_safe data/external/fpnet_fold1_as_fold0 --n 20 [--model experiments/e2/model_v1/e2_lgb.txt]"""
import os as _os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"): _os.environ.setdefault(_v, "1")
import argparse, os, sys, time
from collections import Counter
from multiprocessing import Pool
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "experiments/b1_baseline"))
from b1_common import ADDUCT_SHIFT, ELECTRON, clean_peaks, select_queries
import b1_features as BF
K = os.path.join(ROOT, "data/external_kaggle")
PCLP = f"{K}/casmi26-pubchem-popularity-prior/pubchemlite_annotations.parquet"
BIOP = f"{K}/casmi26-attributed-v4g-reproduction-assets/casmi-chebi-lmsd-structures/casmi-chebi-lmsd-structures/bio_structures.parquet"
STRUCTS = f"{K}/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet"


def _frag(t):
    import b1_frag as FR
    smiles, spectra = t; return {s: float(FR.score(FR.fragments(s), spectra)) for s in smiles}


def main():
    ap = argparse.ArgumentParser()
    for k in ("ewin", "eval_csv", "fold_safe"): ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--sets", nargs="+", required=True); ap.add_argument("--n", type=int, default=20); ap.add_argument("--model", default=""); ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args(); P_ = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p); t0 = time.time()
    import torch, lightgbm as lgb
    sys.path.insert(0, P_("data/external/v3_models/code"))
    from casmi import fpnet, chem
    from casmi.spectra import merge_spectra
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    from rdkit.Chem.MolStandardize import rdMolStandardize
    import b1_analog as BA
    from e2_engine import EStores, E2Engine
    RDLogger.DisableLog("rdApp.*"); TAUT = rdMolStandardize.TautomerEnumerator(); MG = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    model = fpnet.load_model(f"{P_(a.fold_safe)}/fpnet_fold0.pt", "cuda"); dtype = fpnet.autocast_dtype("cuda")
    st = P_("data/processed/spectra_store"); S_MZ = np.load(f"{st}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{st}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{st}/spec_off.npy")
    meta = pl.read_parquet(f"{st}/spec_meta.parquet")
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
    prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64); key_of_row = meta["scorer_ik14"].to_numpy()
    key_rows = {k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("scorer_ik14").is_not_null()).group_by("scorer_ik14").agg(pl.col("row")).iter_rows()}
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    spectrum = lambda x: (np.asarray(S_MZ[S_OFF[x]:S_OFF[x + 1]], np.float64), np.asarray(S_IT[S_OFF[x]:S_OFF[x + 1]], np.float64))
    tier = P_("data/external/pubchem_tier"); tmass = np.load(f"{tier}/pc_mass.npy", mmap_mode="r"); toff = np.load(f"{tier}/pc_off.npy", mmap_mode="r"); tbuf = np.load(f"{tier}/pc_smiles.npy", mmap_mode="r")
    pcl_rows = pl.read_parquet(PCLP, columns=["tier_row"]).filter(pl.col("tier_row") >= 0)["tier_row"].unique().to_numpy()
    pool = pl.read_parquet(P_("data/external/v2_pool/pool_meta.parquet")).select("key", "smiles", "mass", "src", "pid")
    csmi = pd.read_parquet(P_("data/external/coconut/coco_meta.parquet"), columns=["smiles"]).smiles.to_numpy(); cmass = np.load(P_("data/external/coconut/coco_mass.npy"))   # 145: parquet converted once from the opcode-verified pickle (no unpickling here)
    bio = pl.read_parquet(BIOP, columns=["smiles", "monoisotopic_mass"]).drop_nulls()
    stores = EStores(tmass, toff, tbuf, pcl_rows, pool, cmass, csmi, bio)
    ana = BA.Store(np.arange(meta.height), lib_of_row, add_of_row, mode_of_row, ce_of_row, key_of_row, prec_of_row, spectrum, log=lambda *x: None)
    ts = pd.read_parquet(STRUCTS, columns=["key", "smiles"]).drop_duplicates("key"); key_smi = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
    _fp = {}
    def mfp(s):
        if s not in _fp:
            m = Chem.MolFromSmiles(s) if s else None; _fp[s] = MG.GetFingerprint(m) if m is not None else None
        return _fp[s]
    booster = lgb.Booster(model_file=P_(a.model)) if a.model else None
    eng = E2Engine(stores, booster, key_rows, spectrum, lib_of_row, add_of_row, mode_of_row, prec_of_row, ana, key_smi, mfp)
    key2smiles = dict(zip(pool.filter(pl.col("src").is_in([1, 3]))["key"].to_list(), pool.filter(pl.col("src").is_in([1, 3]))["smiles"].to_list()))
    def alias_keys(smi, raw):
        keys = {raw} if raw else set()
        if not smi: return keys
        try:
            m = Chem.MolFromSmiles(smi); Chem.RemoveStereochemistry(m)
            for t in TAUT.Enumerate(m):
                try: keys.add(Chem.MolToInchiKey(t)[:14])
                except Exception: pass
        except Exception: pass
        return keys
    mols = pd.read_csv(P_(a.eval_csv)); mols["molecule"] = mols.molecule.astype(str)
    COLS = ["fp", "ppm_err", "lib_sim_c1", "lib_same_c1", "lib_nref_c1"]; FCOLS = ["frag"] + [f"ana_{f}_c1" for f in ("ap", "a1", "best_tan", "top_tan", "mean_tan")]
    BCOLS = ["in_train_c1", "in_coconut", "in_pcl", "in_bio", "is_truth"]; worst = dict(keys=0, rows=0, **{c: 0.0 for c in COLS + FCOLS}, **{c: 0 for c in BCOLS}, order=0); n_done = 0
    with Pool(a.workers, initializer=BF._init, initargs=(P_("data/external/v3_models/code"), P_(a.fold_safe))) as wp, torch.no_grad():
        for s_name in a.sets:
            E0 = pd.read_parquet(f"{P_(a.ewin)}/ewin_{s_name}.parquet"); F0 = pd.read_parquet(f"{P_(a.ewin)}/e2f_{s_name}.parquet"); E0["molecule"] = E0.molecule.astype(str); F0["molecule"] = F0.molecule.astype(str)
            for r in mols[mols.set == s_name].head(a.n).itertuples(index=False):
                mid, tk, lib = r.molecule, str(r.scorer_key), r.lib; shift = ELECTRON if lib == "enveda-180" else 0.0
                qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
                qr = select_queries(qrows, 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
                if not qr: continue
                q = []
                for x in qr:
                    sh = shift if mode_of_row[x] == "positive" else 0.0; mz, it = spectrum(x); mz = mz - sh; prec = float(prec_of_row[x]) - sh
                    q.append(dict(row=x, mz=mz, it=it, prec=prec, adduct=add_of_row[x], mode=mode_of_row[x], ce=float(ce_of_row[x]) if np.isfinite(ce_of_row[x]) else None, clean=clean_peaks(mz, it, prec)))
                M_by_add = {}
                for s in q: M_by_add.setdefault(s["adduct"], []).append(s["prec"] + ADDUCT_SHIFT[s["adduct"]])
                M_by_add = {k: float(np.median(v)) for k, v in M_by_add.items()}
                zl, wsum = None, 0.0
                for mode in ("positive", "negative"):
                    grp = [s for s in q if s["mode"] == mode]
                    if not grp: continue
                    pairs = [(s["mz"], s["it"]) for s in grp]; mz, it = pairs[0] if len(pairs) == 1 else merge_spectra(pairs)
                    prec = float(np.median([s["prec"] for s in grp])); ces = [s["ce"] for s in grp if s["ce"] is not None]; ad = Counter(s["adduct"] for s in grp).most_common(1)[0][0]
                    pm, pi = fpnet.prep_peaks(mz, it, prec)
                    inp = fpnet.collate([dict(mz=pm, it=pi, prec=prec, adduct_ix=chem.adduct_index(ad), ce=float(np.mean(ces)) if ces else 0.0, ce_known=1.0 if ces else 0.0,
                                              n_merged=min(len(grp), 8), mode=1.0 if mode == "positive" else -1.0)], "cuda")
                    with torch.autocast("cuda", dtype=dtype): z = model(*inp)[0].float().mean(0).cpu().numpy().astype(np.float32)
                    zl = z * len(grp) if zl is None else zl + z * len(grp); wsum += len(grp)
                zlog = (zl / wsum).astype(np.float32)
                def feat_map(sm):
                    res = wp.map(BF._feat, [(sm[i:i + 400], zlog) for i in range(0, len(sm), 400)]); return [k for rr in res for k in rr[0]], np.concatenate([rr[1] for rr in res])
                okey_map = lambda sm: [k for rr in wp.map(BF._okey, [sm[i:i + 200] for i in range(0, len(sm), 200)]) for k in rr]
                frag_map = lambda tasks: wp.map(_frag, tasks)
                E, F = eng.tables(q, M_by_add, feat_map, okey_map, frag_map, query_rows=frozenset(s["row"] for s in q), c1_truth=(tk, alias_keys(key2smiles.get(tk, ""), getattr(r, "raw_key", None)), lib),
                                  mol_id=mid, set_name=s_name)
                e0 = E0[E0.molecule == mid].set_index("official_key"); f0 = F0[F0.molecule == mid].set_index("official_key")
                if E is None:
                    if len(e0): worst["keys"] += 1; print(f"  {mid}: engine empty, table {len(e0)} rows")
                    continue
                e1 = E.set_index("official_key"); f1 = F.set_index("official_key")
                if set(e1.index) != set(e0.index): worst["keys"] += 1; print(f"  {mid}: key sets differ ({len(set(e1.index) ^ set(e0.index))})"); continue
                worst["rows"] += len(e1); e1 = e1.loc[e0.index]; f1 = f1.loc[e0.index]
                for c in COLS: worst[c] = max(worst[c], float(np.nanmax(np.abs(e1[c].astype(float).values - e0[c].astype(float).values))) if len(e0) else 0.0)
                for c in FCOLS: worst[c] = max(worst[c], float(np.nanmax(np.abs(f1[c].astype(float).values - f0.loc[e0.index, c].astype(float).values))) if len(e0) else 0.0)
                for c in BCOLS: worst[c] += int((e1[c].astype(bool).values != e0[c].astype(bool).values).sum())
                if booster is not None:
                    o1 = eng.rank(E, F); o0 = eng.rank(E0[E0.molecule == mid].reset_index(drop=True), F0[F0.molecule == mid].reset_index(drop=True)); worst["order"] += int(o1[:25] != o0[:25])
                n_done += 1
            print(f"  {s_name}: {n_done} molecules compared ({time.time()-t0:.0f}s)", flush=True)
    print({k: (round(v, 6) if isinstance(v, float) else v) for k, v in worst.items()})
    bad = worst["keys"] or any(worst[c] > 1e-4 for c in COLS + FCOLS) or any(worst[c] for c in BCOLS) or worst["order"]
    print("E2_PARITY_" + ("FAIL" if bad else "PASS"), n_done); sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
