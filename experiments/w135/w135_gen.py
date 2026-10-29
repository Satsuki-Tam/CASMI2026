"""W135 stage 1 (136 pre-registration): generation from the frozen parent bank of ONE world and the reach / oracle numbers.
Inputs: the batch CSV (proxy classes in --wclass_col), the world run (b1_world.py: b1_molecules / gen dump with the query FPNet logits,
neutral masses and window raw keys), the world P (w135_p.py: top-25 per molecule, analog list under the world mask).
Parents of query i (all label-free, fixed caps):
  train-analog parents : the first --n_train analog keys of i's world analog list with a train structure (gen_eval2fd par());
  peer parents         : P's rank-1 structure of other batch queries j whose mass difference to i is reachable by the b1_gen edit set
                         (b1_gen.matching non-empty), the --n_peer most similar by query-query MS/MS similarity (max shifted entropy
                         similarity over same-polarity spectrum pairs; ties by key hash);
  parents are de-duplicated by official key (a structure predicted for several peers counts once).
Generation: b1_gen.derive (v2 edit set and caps unchanged) at the query neutral mass (median over adducts, as gen_eval2fd); products by
official key (best f.z SMILES kept), located as 'short' (in P's top 25: never added), 'window' (in the world window: a DB candidate below P's
top 25) or 'novel' (not in the world DB). Pre-selection: the --budget best 'window' + 'novel' products by f.z (ties: parent score, key).
--speed_only: products / timing per query only (no truth, no class, no P rank is read) -- used to fix the budgets before any reach is seen.
Full mode (only after 136 is registered): per query the truth's location among the products (class, rescue type), the oracle gain
1[truth in the pre-selected set] (the truth is then not in P's top 25), train-only vs train+peer parents at the same budget; written to
<out>.parquet; the reading is w135_read.py.
Usage (Spark, experiments/b1_baseline as cwd): python -X utf8 ../w135/w135_gen.py --batch CSV --wclass_col wclass_p30 --world DIR --p P.parquet
       --set dF1 --out OUT [--speed_only] [--n_train 10 --n_peer 10 --budget 50] [--workers 16]"""
import argparse, hashlib, json, os, sys, time
import numpy as np, pandas as pd, polars as pl
from multiprocessing import Pool
B = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "b1_baseline")); sys.path.insert(0, B); ROOT = os.path.abspath(os.path.join(B, "..", ".."))
ap = argparse.ArgumentParser()
for k in ("batch", "wclass_col", "world", "p", "set", "out"): ap.add_argument(f"--{k}", required=True)
ap.add_argument("--speed_only", action="store_true"); ap.add_argument("--n_train", type=int, default=10); ap.add_argument("--n_peer", type=int, default=10); ap.add_argument("--budget", type=int, default=50)
ap.add_argument("--workers", type=int, default=16); ap.add_argument("--store", default="data/processed/spectra_store"); ap.add_argument("--v3", default="data/external/v3_models/code")
ap.add_argument("--fold_safe", default="data/external/fold_safe_fpnet", help="only fp_bits.npy (bit selection) is read")
ap.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
a = ap.parse_args(); T0 = time.time()
def log(*x): print(f"[w135_gen {time.time() - T0:6.0f}s]", *x, flush=True)
H = lambda s: hashlib.sha256(s.encode()).hexdigest()
_W = {}


def _winit(v3, fs):
    sys.path.insert(0, v3)
    from casmi import chem
    from rdkit import RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*"); _W["chem"] = chem; _W["bits"] = np.load(f"{fs}/fp_bits.npy"); _W["mg"] = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def gen_job(t):
    """one query: (mid, Mt, zlog, {arm: [(parent smiles, weight, source)]}) -> (mid, {arm: {official key: product record}}, seconds)."""
    import b1_gen as BG
    from rdkit import Chem, DataStructs
    mid, Mt, zlog, arms = t; t0 = time.time(); cache, info, out = {}, {}, {}
    def prod_of(psmi):
        if psmi not in cache:
            res = []
            for smi, combo in BG.derive(psmi, Mt).items():
                if smi not in info:
                    m = Chem.MolFromSmiles(smi)
                    if m is None: info[smi] = None; continue
                    try: rk = Chem.MolToInchiKey(m)[:14]
                    except Exception: info[smi] = None; continue
                    ok = BG.official_key(smi); f = _W["chem"].raw_fingerprint(smi)
                    info[smi] = None if (not rk or ok is None or f is None) else dict(rk=rk, ok=ok, fz=float(f[_W["bits"]].astype(np.float32) @ zlog), mfp=_W["mg"].GetFingerprint(m))
                if info[smi] is not None: res.append((smi, combo))
            cache[psmi] = res
        return cache[psmi]
    for arm, parents in arms.items():
        prods = {}
        for pi, (psmi, w, src) in enumerate(parents):
            pm = Chem.MolFromSmiles(psmi)
            if pm is None: continue
            pfp = _W["mg"].GetFingerprint(pm)
            for smi, combo in prod_of(psmi):
                d0 = info[smi]; sc = w ** 3 * DataStructs.TanimotoSimilarity(d0["mfp"], pfp)
                d = prods.get(d0["ok"])
                if d is None: d = prods[d0["ok"]] = dict(smiles=smi, rk=d0["rk"], fz=d0["fz"], apsc=-1.0, parents=set(), srcs=set(), bp=None, bc=None)
                d["parents"].add(pi); d["srcs"].add(src)
                if sc > d["apsc"]: d["apsc"] = sc; d["bp"] = pi; d["bc"] = "+".join(combo)
                if d0["fz"] > d["fz"]: d["fz"] = d0["fz"]; d["smiles"] = smi
        out[arm] = {k: dict(smiles=v["smiles"], rk=v["rk"], fz=v["fz"], apsc=v["apsc"], n_parents=len(v["parents"]), srcs="|".join(sorted(v["srcs"])), combo=v["bc"]) for k, v in prods.items()}
    return mid, out, time.time() - t0


if __name__ == "__main__":
    import b1_gen as BG
    import b1_analog as BA
    from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries, clean_peaks, entropy_weight
    from rdkit import Chem, RDLogger
    from rdkit.Chem.Descriptors import ExactMolWt
    RDLogger.DisableLog("rdApp.*")
    bt = pd.read_csv(a.batch); bt["molecule"] = bt.molecule.astype(str); bt = bt[bt.set == a.set]
    Pq = pd.read_parquet(a.p); Pq["molecule"] = Pq.molecule.astype(str); Pq = Pq[Pq.set == a.set].set_index("molecule")
    G = np.load(os.path.join(a.world, "gen", f"gen_{a.set}.npz")); ZL = dict(zip([str(x) for x in G["mol"]], G["zlog"])); MASS = dict(zip([str(x) for x in G["mol"]], [json.loads(x) for x in G["masses"]]))
    Wk = pd.read_parquet(os.path.join(a.world, "gen", f"gen_{a.set}_window.parquet")); Wk["molecule"] = Wk.molecule.astype(str); WK = Wk.groupby("molecule").key.apply(set).to_dict()
    Fw = pd.read_parquet(os.path.join(a.world, f"b1_features_{a.set}.parquet"), columns=["molecule", "official_key"]); Fw["molecule"] = Fw.molecule.astype(str); FOK = Fw.groupby("molecule").official_key.apply(lambda x: set(x.astype(str))).to_dict()
    ts = pd.read_parquet(f"{ROOT}/{a.structs}", columns=["key", "smiles"]).drop_duplicates("key"); KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
    # ---- query spectra of every batch molecule (selection library, select_queries) for the peer similarity
    S_MZ = np.load(f"{ROOT}/{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{ROOT}/{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{ROOT}/{a.store}/spec_off.npy")
    meta = pl.read_parquet(f"{ROOT}/{a.store}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean"])
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
    prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64)
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("inchikey14").is_in(bt.molecule.tolist())).group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    QP = {}
    for r in bt.itertuples(index=False):
        qrows = sorted(int(x) for x in ik_rows.get(r.molecule, []) if lib_of_row[x] == r.lib and add_of_row[x] in ADDUCT_SHIFT)
        q = select_queries(qrows, 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x])); lst = []
        for x in q:
            sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
            mz = np.asarray(S_MZ[S_OFF[x]:S_OFF[x + 1]], np.float64) - sh; it = np.asarray(S_IT[S_OFF[x]:S_OFF[x + 1]], np.float64); prec = float(prec_of_row[x]) - sh
            cm, ci = clean_peaks(mz, it, prec, floor=BA.FLOOR, top=BA.TOP)
            if not len(ci): continue
            p = entropy_weight(ci); lst.append((mode_of_row[x], (cm.astype(np.float64), p.astype(np.float64), float(-(p[p > 0] * np.log(p[p > 0])).sum()), prec)))
        QP[r.molecule] = lst
    mols = [m for m in bt.molecule if m in ZL and m in Pq.index]
    def qq_sim(i, j):
        v = 0.0
        for mi, qi in QP.get(i, []):
            for mj, qj in QP.get(j, []):
                if mi == mj: v = max(v, BA.sim_pair(qi, qj))
        return v
    # ---- parent bank (frozen): P rank-1 of every query, analog lists under the world mask
    TOP1 = {}
    for m in mols:
        t25 = json.loads(Pq.loc[m, "top25"])
        if t25: TOP1[m] = (t25[0][1], t25[0][2])   # (official key, smiles)
    Mt = {m: float(np.median(list(MASS[m].values()))) for m in mols}
    tasks, PAR = [], {}
    for m in mols:
        tr_par = []
        for k_, sv in json.loads(Pq.loc[m, "analogs"]):
            smi_ = KEY_SMI.get(k_)
            if smi_ is None: continue
            tr_par.append((smi_, float(sv), "train"));
            if len(tr_par) >= a.n_train: break
        peers = []
        for j in mols:
            if j == m or j not in TOP1: continue
            try: pm_ = ExactMolWt(Chem.MolFromSmiles(TOP1[j][1]))
            except Exception: continue
            if not BG.matching(Mt[m] - pm_, BG.tol_for(Mt[m])): continue
            peers.append((qq_sim(m, j), H(f"w135peer|{m}|{j}"), j))
        peers.sort(key=lambda t: (-t[0], t[1])); pe_par = [(TOP1[j][1], float(sv), "peer") for sv, _, j in peers[:a.n_peer]]
        def dedup(lst):
            seen, out_ = set(), []
            for smi_, w_, s_ in lst:
                ok_ = BG.official_key(smi_)
                if ok_ is None or ok_ in seen: continue
                seen.add(ok_); out_.append((smi_, w_, s_))
            return out_
        arms = {"train": dedup(tr_par), "both": dedup(tr_par + pe_par)}
        PAR[m] = dict(n_train=len(arms["train"]), n_both=len(arms["both"]), n_peer_cand=len(peers))
        tasks.append((m, Mt[m], ZL[m], arms))
    log(f"{a.set}: parent bank for {len(tasks)} queries (train parents median {np.median([p['n_train'] for p in PAR.values()]):.0f}, train+peer median {np.median([p['n_both'] for p in PAR.values()]):.0f})")
    GEN, SEC = {}, {}
    with Pool(a.workers, initializer=_winit, initargs=(os.path.join(ROOT, a.v3), os.path.join(ROOT, a.fold_safe))) as pool_:
        for mid, res, sec in pool_.imap_unordered(gen_job, tasks, chunksize=1): GEN[mid] = res; SEC[mid] = sec
    log(f"{a.set}: generated")
    rows = []
    for m in mols:
        t25 = json.loads(Pq.loc[m, "top25"]); short = {e[1] for e in t25}; wk = WK.get(m, set()); fok = FOK.get(m, set())
        rec = dict(set=a.set, molecule=m, seconds=SEC[m], **PAR[m])
        for arm in ("train", "both"):
            P_ = GEN[m][arm]; loc = {k: ("short" if k in short else ("window" if (v["rk"] in wk or k in fok) else "novel")) for k, v in P_.items()}
            cand = sorted([k for k in P_ if loc[k] != "short"], key=lambda k: (-P_[k]["fz"], -P_[k]["apsc"], k))
            rec[f"n_prod_{arm}"] = len(P_); rec[f"n_novel_{arm}"] = sum(1 for k in P_ if loc[k] == "novel"); rec[f"n_window_{arm}"] = sum(1 for k in P_ if loc[k] == "window")
            rec[f"n_pre_{arm}"] = min(a.budget, len(cand))
            if not a.speed_only:
                tk = str(bt.set_index("molecule").loc[m, "scorer_key"]); cls = str(bt.set_index("molecule").loc[m, a.wclass_col])
                rk_all = next((i + 1 for i, k in enumerate(cand) if k == tk), 0)
                rec.update({"wclass": cls, f"truth_prod_{arm}": tk in P_, f"truth_loc_{arm}": loc.get(tk, ""), f"truth_rank_fz_{arm}": rk_all,
                            f"reach_{arm}": bool(0 < rk_all <= a.budget), f"truth_srcs_{arm}": (P_[tk]["srcs"] if tk in P_ else ""), f"truth_combo_{arm}": (P_[tk]["combo"] if tk in P_ else "")})
                rec["rP"] = int(Pq.loc[m, "rP"]); rec["main"] = float(Pq.loc[m, "main"])
        rows.append(rec)
    R = pd.DataFrame(rows); R.to_parquet(a.out + ".parquet", index=False)
    log(f"{a.set}: products per query median train {R.n_prod_train.median():.0f} / both {R.n_prod_both.median():.0f}; seconds per query median {R.seconds.median():.1f}, max {R.seconds.max():.1f} -> {a.out}.parquet"
        + ("" if a.speed_only else " (full mode)"))
