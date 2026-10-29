"""W135 P (135_decision.md): the registered main of gen_eval2fd.py (--v7f, view c2; P = rank_v8w7a) computed on a feature table, with the
analog channel under the world's mask; the score code below is copied from gen_eval2fd.py (main path only, no generation / variants).
Modes:
  --parity_c2 : analogs with gen_eval2fd's per-molecule c2 drop (raw keys of the molecule's spectra, scorer key, identity group); compare
                with an existing gen_eval2fd output (--ref_csv, e.g. diag/r133_P_np053f1dev.csv: main, gl_ok133, top25_133 = sha1 of the
                top-25 official keys) -> PARITY_P PASS / FAIL;
  world       : --masks <b1_world out>/world_masks.json: every key of the C2 / C3 identities (train_hide) is dropped from the analog store;
                the C1 identities' original representatives are dropped and re-picked (Store.pick) from their spectra outside their
                selection library and outside the duplicate rows of b1_world (c1_excl), then searched with the same mass window, threshold
                and shifted entropy similarity as Store.analogs (no truncation before they are merged).
Writes <out>.parquet: per (set, molecule) main RR, rank of the truth (rP, 0 = absent), n_cand, gl_ok, top-25 (rank, official key, smiles,
score), the analog list (key, sim; top 80) -- the frozen P / parent bank of the world.
Usage (Spark, experiments/b1_baseline as cwd for the shared modules):
  python -X utf8 ../w135/w135_p.py --run RUN --gl RUN/work/gl_SET.json --sets SET --eval_csv CSV --model rank_v8w7a/lambdarank.txt --out OUT
         [--parity_c2 --ref_csv diag/r133_P_np053f1dev.csv | --masks RUN/world_masks.json]"""
import argparse, hashlib, json, os, sys, time
import numpy as np, pandas as pd, polars as pl
B = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "b1_baseline")); sys.path.insert(0, B); ROOT = os.path.abspath(os.path.join(B, "..", ".."))
ap = argparse.ArgumentParser()
for k in ("run", "gl", "eval_csv", "out"): ap.add_argument(f"--{k}", required=True)
ap.add_argument("--sets", nargs="+", required=True); ap.add_argument("--model", default="rank_v8w7a/lambdarank.txt"); ap.add_argument("--parity_c2", action="store_true")
ap.add_argument("--ref_csv", default=""); ap.add_argument("--masks", default=""); ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--store", default="data/processed/spectra_store"); ap.add_argument("--folds", default="data/external/identity_folds/structures.parquet")
ap.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
ap.add_argument("--tau", type=float, default=0.9); ap.add_argument("--margin", type=float, default=0.2); ap.add_argument("--min_gl_cover", type=float, default=0.5)
a = ap.parse_args(); T0 = time.time()
if not a.parity_c2 and not a.masks: sys.exit("world mode needs --masks")
def log(*x): print(f"[w135_p {time.time() - T0:6.0f}s]", *x, flush=True)
import b1_locked_eval as E
import b1_analog as BA
from b1_evaluate import z, term
from b1_rankfeats import feature_matrix
from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries, clean_peaks, entropy_weight
import lightgbm as lgb
BST = lgb.Booster(model_file=os.path.join(B, a.model) if not os.path.isabs(a.model) else a.model); FEATS = BST.feature_name()
ev = pd.read_csv(a.eval_csv); ev["molecule"] = ev["molecule"].astype(str)
S_MZ = np.load(f"{ROOT}/{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{ROOT}/{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{ROOT}/{a.store}/spec_off.npy")
meta = pl.read_parquet(f"{ROOT}/{a.store}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean", "scorer_ik14"])
lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64); key_of_row = meta["scorer_ik14"].to_numpy()
ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
key_rows = {k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("scorer_ik14").is_not_null()).group_by("scorer_ik14").agg(pl.col("row")).iter_rows()}
def spectrum(x): return np.asarray(S_MZ[S_OFF[x]:S_OFF[x + 1]], np.float64), np.asarray(S_IT[S_OFF[x]:S_OFF[x + 1]], np.float64)
store = BA.Store(np.arange(meta.height), lib_of_row, add_of_row, mode_of_row, ce_of_row, key_of_row, prec_of_row, spectrum, log=log)
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
RDLogger.DisableLog("rdApp.*"); MG = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
ts = pd.read_parquet(f"{ROOT}/{a.structs}", columns=["key", "smiles"]).drop_duplicates("key"); KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
_FP = {}
def fp_of(smi):
    if smi not in _FP:
        m = Chem.MolFromSmiles(smi) if smi else None; _FP[smi] = MG.GetFingerprint(m) if m is not None else None
    return _FP[smi]
_idf = pd.read_parquet(f"{ROOT}/{a.folds}", columns=["scorer_key", "identity_group"]).dropna().drop_duplicates()
GROUP_KEYS = _idf.groupby("identity_group").scorer_key.apply(lambda x: set(x.astype(str))).to_dict(); KEY_GROUP = dict(zip(_idf.scorer_key.astype(str), _idf.identity_group))
W = json.load(open(a.masks)) if a.masks else None
if W is not None:
    assert sorted(W["sets"]) == sorted(a.sets) or set(a.sets) <= set(W["sets"]), (W["sets"], a.sets)
    HIDE = set(W["train_hide"]); C1 = {k: (lib_, set(W["c1_excl"].get(k, []))) for m_, (tk_, lib_, ks_) in W["c1_lib"].items() for k in ks_}
    C1_REPS = {}   # C1 key -> {mode: [prepared reps]} re-picked outside the selection library and the duplicate rows
    for k, (lib_, excl) in C1.items():
        alt = [int(x) for x in key_rows.get(k, []) if lib_of_row[x] != lib_ and int(x) not in excl and add_of_row[x] in ADDUCT_SHIFT]
        C1_REPS[k] = {md: [(y, store.prepared(y)) for y in store.pick([x for x in alt if mode_of_row[x] == md])] for md in ("positive", "negative")}
    log(f"world masks {a.masks}: hidden keys {len(HIDE):,}, C1 keys {len(C1)} (re-picked representatives {sum(len(v_) for d_ in C1_REPS.values() for v_ in d_.values())})")


def analogs_world(qspec, query_rows, n_analog=BA.N_ANALOG, win=BA.WIN):
    """Store.analogs with drop_keys = hidden keys + C1 keys, then the C1 keys' re-picked representatives searched with the same rules."""
    qset = set(int(x) for x in query_rows); best = {}
    drop_ix = {store.kix[k] for k in (HIDE | set(C1)) if k in store.kix}
    prepped = []
    for s in qspec:
        cm, ci = clean_peaks(np.asarray(s["mz"], np.float64), np.asarray(s["it"], np.float64), float(s["prec"]), floor=store.floor, top=store.top)
        if not len(ci): continue
        p = entropy_weight(ci); q = (cm.astype(np.float64), p.astype(np.float64), float(-(p[p > 0] * np.log(p[p > 0])).sum()), float(s["prec"]))
        prepped.append((s, q))
        st = store.S.get(s["mode"])
        if st is None or not len(st["M"]): continue
        Mq = q[3] + ADDUCT_SHIFT[s["adduct"]]
        lo = int(np.searchsorted(st["M"], Mq - win, "left")); hi = int(np.searchsorted(st["M"], Mq + win, "right"))
        if hi <= lo: continue
        sims = BA._search(q[0], q[1], q[2], q[3], lo, hi, st["off"], st["mz"], st["p"], st["ent"], st["prec"])
        for kk in np.flatnonzero(sims > 0.05):
            r = lo + int(kk)
            if int(st["row"][r]) in qset: continue
            ki = int(st["key"][r])
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


OUTR = []
for s in a.sets:
    F = pd.read_parquet(os.path.join(a.run, f"b1_features_{s}.parquet")); F["molecule"] = F["molecule"].astype(str)
    M = pd.read_csv(os.path.join(a.run, f"b1_molecules_{s}.csv")).set_index("molecule"); M.index = M.index.astype(str)
    gl = json.load(open(a.gl)); gmeta = json.load(open(a.gl + ".meta.json"))
    assert gmeta.get("status") in ("ok", "partial") or (gmeta.get("status") == "error" and int(gmeta.get("n_mols_scored") or 0) == 0), gmeta
    mols = ev[ev.set == s]
    if a.limit: mols = mols.head(a.limit)
    frag_cache = {}
    for r in mols.itertuples(index=False):
        mid, lib, tk = str(r.molecule), r.lib, str(r.scorer_key)
        if mid not in M.index: continue
        qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
        q = select_queries(qrows, 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
        qspec = []
        for x in q:
            sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
            mz, it = spectrum(x); qspec.append(dict(mz=mz - sh, it=it, prec=float(prec_of_row[x]) - sh, adduct=add_of_row[x], mode=mode_of_row[x]))
        if a.parity_c2:
            raw = {key_of_row[x] for x in ik_rows.get(mid, []) if key_of_row[x] is not None}
            an = store.analogs(qspec, query_rows=q, drop_keys=raw | {tk} | set(GROUP_KEYS.get(KEY_GROUP.get(tk), set())))
        else: an = analogs_world(qspec, q)
        g = E.view_frame(F, M, mid, "c2")
        rec = dict(set=s, molecule=mid, n_cand=len(g), analogs=json.dumps([[k_, round(float(v_), 6)] for k_, v_ in an]))
        if len(g) == 0:
            OUTR.append(dict(rec, main=0.0, rP=0, gl_ok=0, top25=json.dumps([]), top25_hash="")); continue
        # ---- gen_eval2fd main path (copied; c2 view, --v7f, single model)
        fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); lib_ = g["lib_sim_c2"].values.astype(float)
        glv = np.array([np.nan if (gl.get(mid) or {}).get(sm) is None else float((gl.get(mid) or {}).get(sm)) for sm in g.smiles], float)
        zgl = term(glv, True)
        S = z(fp) + (2 * zgl if zgl is not None else 0) + 0.5 * pop
        top = np.sort(lib_)[::-1]; second = top[1] if len(top) > 1 else 0.0
        fire = bool(lib_.max() >= a.tau and lib_.max() - second >= a.margin); ins = np.where(lib_ >= a.tau, 100.0 + lib_, S) if fire else S
        gl_ok = np.isfinite(glv).sum() >= max(2, a.min_gl_cover * len(g))
        afp = [(fp_of(KEY_SMI.get(k)), sv) for k, sv in an]; afp = [(f_, sv) for f_, sv in afp if f_ is not None]
        feats = BA.features([fp_of(str(sm)) for sm in g.smiles], [f_ for f_, _ in afp], [sv for _, sv in afp])
        if gl_ok:
            X = feature_matrix(fp, glv, np.full(len(g), np.nan), pop, g.lsid.values, g.lpmid.values, g.lsynonyms.values, g["np"].values, g.src_mask.values, g.lotus_refs.values, lib_,
                               g["lib_same_c2"].values, g["lib_nref_c2"].values, g.in_tier.values, g["in_train_c2"].values, g.in_coconut.values, g.ppm_err.values,
                               g.fp_rank_window.values, float(M.loc[mid, "n_query"]), float(M.loc[mid, "ce_known"]), n_window=float(M.loc[mid, "n_unique"]) if "n_unique" in M.columns else np.nan,
                               feats=list(FEATS), cmp=None, analog=(dict(ap=feats['ap'], mean_tan=feats['mean_tan']) if any(f_.startswith('ana_') or f_ == 'z_ana_ap' for f_ in FEATS) else None))
            pred_ = np.asarray(BST.predict(X), float); score = 2 * z(pred_) + z(np.asarray(S, float))
        else:
            score = np.asarray(ins, float); x_ = feats["ap"]
            import b1_frag as BF
            if mid not in frag_cache:
                frag_cache[mid] = {str(sm_): BF.score(BF.fragments(str(sm_)), [dict(mz=q_["mz"], it=q_["it"], prec=q_["prec"], mode=q_["mode"]) for q_ in qspec]) for sm_ in set(F[F.molecule == mid].smiles.astype(str))}
            fr_ = np.array([frag_cache[mid][str(sm_)] for sm_ in g.smiles], float)
            score = score + 1.0 * (x_ - x_.mean()) / (x_.std() + 1e-9) + 1.0 * (fr_ - fr_.mean()) / (fr_.std() + 1e-9)
        order = list(np.argsort(-score, kind="stable"))
        tr = g.is_truth.values.astype(bool); okeys = g.official_key.astype(str).values
        pos = next((k + 1 for k, i in enumerate(order) if tr[i]), 0)
        main = 1.0 / pos if 0 < pos <= 25 else 0.0
        t25 = [[k + 1, okeys[i], str(g.smiles.values[i]), float(score[i]), bool(tr[i])] for k, i in enumerate(order[:25])]
        OUTR.append(dict(rec, main=main, rP=pos, gl_ok=int(gl_ok), top25=json.dumps(t25), top25_hash=hashlib.sha1(";".join(okeys[int(i)] for i in order[:25]).encode()).hexdigest()[:16]))
    log(f"{s}: {sum(1 for o in OUTR if o['set'] == s)} molecules")
R = pd.DataFrame(OUTR); R.to_parquet(a.out + ".parquet", index=False)
log((f"main mean {R.main.mean():.4f} over " if a.parity_c2 else "world P (no score printed before 136 is read) for ") + f"{len(R)} molecules -> {a.out}.parquet")
if a.ref_csv:
    ref = pd.read_csv(os.path.join(B, a.ref_csv) if not os.path.isabs(a.ref_csv) else a.ref_csv); ref = ref[(ref.view == "c2") & ref.set.isin(a.sets)]; ref["molecule"] = ref.molecule.astype(str)
    J = R.merge(ref[["set", "molecule", "main", "gl_ok133", "top25_133"]], on=["set", "molecule"], how="inner", suffixes=("", "_ref"))
    bad = J[(np.abs(J.main - J.main_ref) > 1e-12) | ((J.n_cand > 0) & ((J.gl_ok != J.gl_ok133) | (J.top25_hash != J.top25_133.astype(str))))]   # empty lists: the reference has no gl_ok / hash
    miss = sorted(set(ref.molecule) - set(R.molecule)) if not a.limit else []
    print(f"PARITY_P {'PASS' if len(bad) == 0 and not miss and len(J) > 0 else 'FAIL'}: compared {len(J)} molecules (P rows {len(R)}, reference rows {len(ref)}), mismatches {len(bad)}, reference molecules missing {len(miss)}")
    if len(bad): print(bad[["set", "molecule", "main", "main_ref", "gl_ok", "gl_ok133", "top25_hash", "top25_133"]].head(10).to_string())
    if len(bad) or miss or len(J) == 0: sys.exit(1)   # v2 (Codex 136): a parity FAIL is a non-zero exit
