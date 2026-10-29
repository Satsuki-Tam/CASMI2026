"""W135 stage 1 generator v2 (136_decision.md; Codex 136 Q2 (c) / Q3 / Q5 -- written before any reach number). One world (batch x pi3):
parents from the frozen parent bank, b1_gen products, B-budget pre-selection, and (full mode) the truth's location.
Changes from v1 (w135_gen.py, kept unchanged because the v1 world manifests record it):
  - roster: the batch, the world molecules table, the generation dump and the world P must hold exactly the same molecules (STOP otherwise);
  - peers: only queries with at least one same-polarity pair of usable query spectra with i (a valid comparison; a similarity of 0 is allowed,
    no threshold); P rank-1 structures grouped by official key BEFORE the cap (max similarity kept), the --n_peer best distinct structures;
  - parents: train-analog parents (world analog list order, first --n_train train structures) + peer parents, de-duplicated by official key
    with every source recorded (train / peer / both); a train parent must not be a C2 / C3 key of the world (train_hide; STOP), a peer parent
    may be a C2 structure (legal), never a C3 official key (STOP); the parents (key, sources, similarity) are written;
  - products: the representative SMILES and its raw key are updated together; location by OFFICIAL identity: 'top25' (P's top 25),
    'in_window' (official key of a world-window structure, b1_world v2 dump), 'out_of_window' (neither; NOT a claim of DB absence);
    'off_mass' marks products outside every adduct window of the query (+-10 ppm) -- auxiliary;
  - B list: the official keys of the pre-selected products (f.z desc, ties: parent score desc, key) with their hash; ranks of the truth;
  - world invariants re-checked here: no C3 official key in P's top 25 / the world window official keys / the analog lists; no train_hide key
    in the analog lists;
  - --fold_safe must be the world's FPNet directory (fp_bits.npy hash compared with the world manifest).
--speed_only: products / timing only (no truth, class or P rank is read).
v2.1 (2026-10-30 01:2x, before the stage-1 run): adds B_detail_<arm> (key, SMILES, f.z, parent score, parents, sources, edit, location, off_mass
of every B product) for a later stage 2; no registered number reads it.
Usage (Spark, experiments/b1_baseline as cwd): python -X utf8 ../w135/w135_gen_v2.py --batch CSV --wclass_col wclass_p30 --world DIR --set dF1 --fold_safe DIR
       --out OUT [--speed_only] [--n_train 10 --n_peer 10 --budget 50] [--workers 16]"""
import argparse, hashlib, json, os, sys, time
import numpy as np, pandas as pd, polars as pl
from multiprocessing import Pool
B = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "b1_baseline")); sys.path.insert(0, B); ROOT = os.path.abspath(os.path.join(B, "..", ".."))
ap = argparse.ArgumentParser()
for k in ("batch", "wclass_col", "world", "set", "out", "fold_safe"): ap.add_argument(f"--{k}", required=True)
ap.add_argument("--speed_only", action="store_true"); ap.add_argument("--n_train", type=int, default=10); ap.add_argument("--n_peer", type=int, default=10); ap.add_argument("--budget", type=int, default=50)
ap.add_argument("--workers", type=int, default=16); ap.add_argument("--store", default="data/processed/spectra_store"); ap.add_argument("--v3", default="data/external/v3_models/code")
ap.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
a = ap.parse_args(); T0 = time.time()
def log(*x): print(f"[w135_gen_v2 {time.time() - T0:6.0f}s]", *x, flush=True)
def stop(m): sys.exit(f"STOP (w135_gen_v2): {m}")
H = lambda s: hashlib.sha256(s.encode()).hexdigest(); sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
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
    from rdkit.Chem.Descriptors import ExactMolWt
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
                    info[smi] = None if (not rk or ok is None or f is None) else dict(rk=rk, ok=ok, fz=float(f[_W["bits"]].astype(np.float32) @ zlog), mfp=_W["mg"].GetFingerprint(m), mass=float(ExactMolWt(m)))
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
                if d is None: d = prods[d0["ok"]] = dict(smiles=smi, rk=d0["rk"], rks={d0["rk"]}, fz=d0["fz"], mass=d0["mass"], apsc=-1.0, parents=set(), srcs=set(), bp=None, bc=None)
                d["parents"].add(pi); d["srcs"].add(src); d["rks"].add(d0["rk"])
                if sc > d["apsc"]: d["apsc"] = sc; d["bp"] = pi; d["bc"] = "+".join(combo)
                if d0["fz"] > d["fz"]: d["fz"] = d0["fz"]; d["smiles"] = smi; d["rk"] = d0["rk"]   # v2: representative SMILES and raw key together
        out[arm] = {k: dict(smiles=v["smiles"], rk=v["rk"], rks=sorted(v["rks"]), fz=v["fz"], mass=v["mass"], apsc=v["apsc"], n_parents=len(v["parents"]), srcs="|".join(sorted(v["srcs"])), combo=v["bc"]) for k, v in prods.items()}
    return mid, out, time.time() - t0


if __name__ == "__main__":
    import b1_gen as BG
    import b1_analog as BA
    from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries, clean_peaks, entropy_weight
    from rdkit import Chem, RDLogger
    from rdkit.Chem.Descriptors import ExactMolWt
    RDLogger.DisableLog("rdApp.*")
    # ---- provenance: the world manifest (sha of every file) and the FPNet bit order
    man = {}
    for ln in open(os.path.join(a.world, "manifest.txt")):
        h, f = ln.split(); man[f] = h
        if sha(os.path.join(ROOT, f)) != h: stop(f"{f} differs from the world manifest")
    fb = [f for f in man if f.endswith("fp_bits.npy")]
    if len(fb) != 1 or sha(os.path.join(ROOT, a.fold_safe, "fp_bits.npy")) != man[fb[0]]: stop("fp_bits.npy differs from the world's")
    bt = pd.read_csv(a.batch); bt["molecule"] = bt.molecule.astype(str); bt = bt[bt.set == a.set].set_index("molecule")
    if bt.index.duplicated().any(): stop("duplicate batch molecules")
    Pq = pd.read_parquet(os.path.join(a.world, "P.parquet")); Pq["molecule"] = Pq.molecule.astype(str); Pq = Pq[Pq.set == a.set]
    if Pq.molecule.duplicated().any(): stop("duplicate P rows");
    Pq = Pq.set_index("molecule")
    Mw = pd.read_csv(os.path.join(a.world, f"b1_molecules_{a.set}.csv")); Mw["molecule"] = Mw.molecule.astype(str)
    G = np.load(os.path.join(a.world, "gen", f"gen_{a.set}.npz")); gm = [str(x) for x in G["mol"]]
    ZL = dict(zip(gm, G["zlog"])); MASS = dict(zip(gm, [json.loads(x) for x in G["masses"]]))
    for name, ids in (("world molecules", list(Mw.molecule)), ("generation dump", gm), ("world P", list(Pq.index))):
        if len(ids) != len(set(ids)) or set(ids) != set(bt.index): stop(f"roster: {name} ({len(set(ids))}) != batch ({len(bt)})")
    WO = pd.read_parquet(os.path.join(a.world, "gen", f"gen_{a.set}_window_okeys.parquet")); WO["molecule"] = WO.molecule.astype(str)
    WOK = WO.groupby("molecule").official_key.apply(lambda x: set(x.dropna().astype(str))).to_dict()
    W = json.load(open(os.path.join(a.world, "world_masks.json"))); HIDE = set(W["train_hide"]); C3OK = set(W["c3_okeys"])
    if dict(W["wclass"]) != {m: str(bt.loc[m, a.wclass_col]) for m in bt.index}: stop("world classes differ from the batch column")
    # ---- world invariants (independent of the generation)
    for m in bt.index:
        t25 = json.loads(Pq.loc[m, "top25"]); an = json.loads(Pq.loc[m, "analogs"])
        if any(e[1] in C3OK for e in t25): stop(f"{m}: C3 official key in P's top 25")
        if WOK.get(m, set()) & C3OK: stop(f"{m}: C3 official key in the world window")
        if any(k in HIDE for k, _ in an): stop(f"{m}: hidden (C2 / C3) key in the analog list")
    ts = pd.read_parquet(f"{ROOT}/{a.structs}", columns=["key", "smiles"]).drop_duplicates("key"); KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
    # ---- query spectra (selection library, select_queries with the raw CE, as b1_world) for the peer similarity
    S_MZ = np.load(f"{ROOT}/{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{ROOT}/{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{ROOT}/{a.store}/spec_off.npy")
    meta = pl.read_parquet(f"{ROOT}/{a.store}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean"])
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
    prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64)
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("inchikey14").is_in(list(bt.index))).group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    QP = {}
    for m in bt.index:
        lib = str(bt.loc[m, "lib"]); qrows = sorted(int(x) for x in ik_rows.get(m, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
        q = select_queries(qrows, 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x])); lst = []
        for x in q:
            sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
            mz = np.asarray(S_MZ[S_OFF[x]:S_OFF[x + 1]], np.float64) - sh; it = np.asarray(S_IT[S_OFF[x]:S_OFF[x + 1]], np.float64); prec = float(prec_of_row[x]) - sh
            cm, ci = clean_peaks(mz, it, prec, floor=BA.FLOOR, top=BA.TOP)
            if not len(ci): continue
            p = entropy_weight(ci); lst.append((mode_of_row[x], (cm.astype(np.float64), p.astype(np.float64), float(-(p[p > 0] * np.log(p[p > 0])).sum()), prec)))
        QP[m] = lst
    def qq_sim(i, j):   # None = no same-polarity pair of usable spectra (not comparable)
        v = None
        for mi, qi in QP.get(i, []):
            for mj, qj in QP.get(j, []):
                if mi == mj: s_ = BA.sim_pair(qi, qj); v = s_ if v is None else max(v, s_)
        return v
    mols = sorted(bt.index)
    TOP1 = {}
    for m in mols:
        t25 = json.loads(Pq.loc[m, "top25"])
        if t25: TOP1[m] = (t25[0][1], t25[0][2])
    Mt = {m: float(np.median(list(MASS[m].values()))) for m in mols}
    tasks, PAR = [], {}
    for m in mols:
        tr_par = []
        for k_, sv in json.loads(Pq.loc[m, "analogs"]):
            smi_ = KEY_SMI.get(k_)
            if smi_ is None: continue
            if k_ in HIDE: stop(f"{m}: train parent {k_} is a hidden C2 / C3 key")
            tr_par.append((smi_, float(sv), "train", k_))
            if len(tr_par) >= a.n_train: break
        pk = {}   # peer structures by official key: (max similarity, smiles, peers)
        for j in mols:
            if j == m or j not in TOP1: continue
            okj, smj = TOP1[j]
            try: pm_ = ExactMolWt(Chem.MolFromSmiles(smj))
            except Exception: continue
            if not BG.matching(Mt[m] - pm_, BG.tol_for(Mt[m])): continue
            sv = qq_sim(m, j)
            if sv is None: continue
            if okj in C3OK: stop(f"{m}: peer parent {okj} is a C3 key")
            cur = pk.get(okj)
            if cur is None or (sv, H(f"w135peer|{m}|{j}")) > (cur[0], cur[3]): pk[okj] = (sv, smj, (cur[2] if cur else []) + [j], H(f"w135peer|{m}|{j}"))
            else: cur[2].append(j)
        peers = sorted(pk.items(), key=lambda kv: (-kv[1][0], kv[1][3]))[:a.n_peer]
        pe_par = [(v[1], float(v[0]), "peer", k) for k, v in peers]
        def dedup(lst):
            seen, out_ = {}, []
            for smi_, w_, s_, key_ in lst:
                ok_ = BG.official_key(smi_)
                if ok_ is None: continue
                if ok_ in seen: out_[seen[ok_]][2].add(s_); continue
                seen[ok_] = len(out_); out_.append([smi_, w_, {s_}, ok_])
            return [(x[0], x[1], "|".join(sorted(x[2])), x[3]) for x in out_]
        tr_d, both_d = dedup(tr_par), dedup(tr_par + pe_par)
        for smi_, w_, s_, ok_ in both_d:
            if ok_ in C3OK: stop(f"{m}: parent {ok_} is a C3 official key")
        arms = {"train": [(x[0], x[1], x[2]) for x in tr_d], "both": [(x[0], x[1], x[2]) for x in both_d]}
        PAR[m] = dict(n_train=len(tr_d), n_both=len(both_d), n_peer_struct=len(pk), n_peer=len(pe_par), parents=json.dumps([[x[3], x[2], round(x[1], 6)] for x in both_d]))
        tasks.append((m, Mt[m], ZL[m], arms))
    log(f"{a.set}: parent bank for {len(tasks)} queries")
    GEN, SEC = {}, {}
    with Pool(a.workers, initializer=_winit, initargs=(os.path.join(ROOT, a.v3), os.path.join(ROOT, a.fold_safe))) as pool_:
        for mid, res, sec in pool_.imap_unordered(gen_job, tasks, chunksize=1): GEN[mid] = res; SEC[mid] = sec
    log(f"{a.set}: generated")
    rows = []
    for m in mols:
        t25 = json.loads(Pq.loc[m, "top25"]); short = {e[1] for e in t25}; wok = WOK.get(m, set())
        lo_hi = [(M_ * (1 - 1e-5), M_ * (1 + 1e-5)) for M_ in MASS[m].values()]
        rec = dict(set=a.set, molecule=m, seconds=SEC[m], **PAR[m])
        for arm in ("train", "both"):
            P_ = GEN[m][arm]
            loc = {k: ("top25" if k in short else ("in_window" if k in wok else "out_of_window")) for k in P_}
            off = {k: not any(l_ <= v["mass"] <= h_ for l_, h_ in lo_hi) for k, v in P_.items()}
            cand = sorted([k for k in P_ if loc[k] != "top25"], key=lambda k: (-P_[k]["fz"], -P_[k]["apsc"], k))
            Bl = cand[:a.budget]
            if len(set(Bl)) != len(Bl) or len(Bl) > a.budget or not all(np.isfinite(P_[k]["fz"]) for k in Bl): stop(f"{m} {arm}: B list invalid")
            rec.update({f"n_prod_{arm}": len(P_), f"n_in_window_{arm}": sum(1 for k in P_ if loc[k] == "in_window"), f"n_out_of_window_{arm}": sum(1 for k in P_ if loc[k] == "out_of_window"),
                        f"n_off_mass_{arm}": int(sum(off.values())), f"n_pre_{arm}": len(Bl), f"B_hash_{arm}": hashlib.sha1(";".join(Bl).encode()).hexdigest()[:16], f"B_{arm}": json.dumps(Bl),
                        f"B_detail_{arm}": json.dumps([[k, P_[k]["smiles"], round(P_[k]["fz"], 6), round(P_[k]["apsc"], 6), P_[k]["n_parents"], P_[k]["srcs"], P_[k]["combo"], loc[k], bool(off[k])] for k in Bl])})   # v2.1: for stage 2 (no registered number uses it)
            if not a.speed_only:
                tk = str(bt.loc[m, "scorer_key"]); cls = str(bt.loc[m, a.wclass_col])
                rk_all = next((i + 1 for i, k in enumerate(cand) if k == tk), 0)
                rec.update({"wclass": cls, f"truth_prod_{arm}": tk in P_, f"truth_loc_{arm}": loc.get(tk, ""), f"truth_off_mass_{arm}": bool(off.get(tk, False)), f"truth_rank_fz_{arm}": rk_all,
                            f"reach_{arm}": bool(tk in set(Bl)), f"truth_srcs_{arm}": (P_[tk]["srcs"] if tk in P_ else ""), f"truth_combo_{arm}": (P_[tk]["combo"] if tk in P_ else "")})
        if not a.speed_only:
            rec["rP"] = int(Pq.loc[m, "rP"]); rec["main"] = float(Pq.loc[m, "main"]); rec["truth_in_top25"] = str(bt.loc[m, "scorer_key"]) in short
            rec["truth_in_window_okey"] = str(bt.loc[m, "scorer_key"]) in wok
        rows.append(rec)
    R = pd.DataFrame(rows); R.to_parquet(a.out + ".parquet", index=False)
    json.dump(dict(args=vars(a), world_manifest_sha256=sha(os.path.join(a.world, "manifest.txt")), script_sha256=sha(os.path.abspath(__file__)), b1_gen_sha256=sha(os.path.join(B, "b1_gen.py")),
                   output_sha256=sha(a.out + ".parquet"), n=len(R), seconds=round(time.time() - T0)), open(a.out + ".meta.json", "w"), indent=1)
    log(f"{a.set}: {len(R)} queries; products median train {R.n_prod_train.median():.0f} / both {R.n_prod_both.median():.0f}; seconds median {R.seconds.median():.1f} -> {a.out}.parquet"
        + ("" if a.speed_only else " (full mode)"))
