"""W135 world check (Codex 136 Q2 (b) / (c); before any reach number): invariants of one built world, read from its outputs only.
  1. C1 analog re-pick (w135_p.py analogs_world): for every C1 key, the replacement representatives are re-derived (rows of the key outside
     its selection library and the duplicate rows of world_masks c1_excl, test adducts, Store.pick per mode); no forbidden row is among them;
     for every query whose analog list holds a C1 key, the recorded similarity equals the maximum shifted entropy similarity between the
     query spectra and those representatives (same mode, +-200 Da window, > 0.05); a C1 key without a replacement never appears; a C1 key
     whose recomputed similarity would enter a query's list (above its 80th entry, or > 0.05 when the list is shorter) is not missing.
     Counted: C1 keys whose original representatives (Store.pick over all rows) contained a forbidden row (the branch was exercised).
  2. No C2 / C3 key (train_hide) in any analog list; no C3 official key in any P top 25, world table or window official key list; no
     struct_drop raw key in any window raw-key list.
Prints WORLD_CHECK PASS / FAIL; exit 1 on FAIL.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_world_check.py --world experiments/w135/worlds/dF1_p30 --set dF1"""
import argparse, json, os, sys
import numpy as np, pandas as pd, polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); B = os.path.join(ROOT, "experiments/b1_baseline"); sys.path.insert(0, B)
import b1_analog as BA
from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries, clean_peaks, entropy_weight
ap = argparse.ArgumentParser(); ap.add_argument("--world", required=True); ap.add_argument("--set", required=True); a = ap.parse_args()
Wd = a.world if os.path.isabs(a.world) else os.path.join(ROOT, a.world); bad, info = [], {}
W = json.load(open(os.path.join(Wd, "world_masks.json"))); HIDE = set(W["train_hide"]); C3OK = set(W["c3_okeys"]); SDROP = set(W["struct_drop"])
P = pd.read_parquet(os.path.join(Wd, "P.parquet")); P["molecule"] = P.molecule.astype(str)
F = pd.read_parquet(os.path.join(Wd, f"b1_features_{a.set}.parquet"), columns=["molecule", "official_key"])
WK = pd.read_parquet(os.path.join(Wd, "gen", f"gen_{a.set}_window.parquet")); WO = pd.read_parquet(os.path.join(Wd, "gen", f"gen_{a.set}_window_okeys.parquet"))
# ---- 2. hidden / C3 invariants
for r in P.itertuples(index=False):
    if any(k in HIDE for k, _ in json.loads(r.analogs)): bad.append(f"{r.molecule}: hidden key in the analog list")
    if any(e[1] in C3OK for e in json.loads(r.top25)): bad.append(f"{r.molecule}: C3 official key in P top 25")
if F.official_key.astype(str).isin(C3OK).any(): bad.append("C3 official key in the world table")
if WO.official_key.astype(str).isin(C3OK).any(): bad.append("C3 official key in a world window")
if WK.key.astype(str).isin(SDROP).any(): bad.append("struct_drop raw key in a world window")
# ---- 1. C1 re-pick
store = os.path.join(ROOT, "data/processed/spectra_store")
S_MZ = np.load(f"{store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{store}/spec_off.npy")
meta = pl.read_parquet(f"{store}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean", "scorer_ik14"])
lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64); key_of_row = meta["scorer_ik14"].to_numpy()
key_rows = {k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("scorer_ik14").is_not_null()).group_by("scorer_ik14").agg(pl.col("row")).iter_rows()}
ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
def spectrum(x): return np.asarray(S_MZ[S_OFF[x]:S_OFF[x + 1]], np.float64), np.asarray(S_IT[S_OFF[x]:S_OFF[x + 1]], np.float64)
st = BA.Store([], lib_of_row, add_of_row, mode_of_row, ce_of_row, key_of_row, prec_of_row, spectrum, log=lambda *x: None)   # pick / prepared only
bt = pd.read_csv(os.path.join(ROOT, "experiments/w135/batches", f"{a.set}.csv")); bt["molecule"] = bt.molecule.astype(str)
QP = {}
for r in bt.itertuples(index=False):   # = w135_p.py qspec, prepared like Store.analogs
    qrows = sorted(int(x) for x in ik_rows.get(r.molecule, []) if lib_of_row[x] == r.lib and add_of_row[x] in ADDUCT_SHIFT)
    q = select_queries(qrows, 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x])); lst = []
    for x in q:
        sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
        mz, it = spectrum(x); mz = mz - sh; prec = float(prec_of_row[x]) - sh
        cm, ci = clean_peaks(mz, it, prec, floor=st.floor, top=st.top)
        if not len(ci): continue
        p = entropy_weight(ci); lst.append((add_of_row[x], mode_of_row[x], (cm.astype(np.float64), p.astype(np.float64), float(-(p[p > 0] * np.log(p[p > 0])).sum()), prec)))
    QP[r.molecule] = lst
C1 = {k: (lib_, set(W["c1_excl"].get(k, []))) for m_, (tk_, lib_, ks_) in W["c1_lib"].items() for k in ks_}
AN = {r.molecule: json.loads(r.analogs) for r in P.itertuples(index=False)}
n_orig_forbidden = n_noalt = n_checked = 0
for k, (lib_, excl) in C1.items():
    allrows = [int(x) for x in key_rows.get(k, []) if add_of_row[x] in ADDUCT_SHIFT]
    alt = [x for x in allrows if lib_of_row[x] != lib_ and x not in excl]
    if set(alt) & excl or any(lib_of_row[x] == lib_ for x in alt): bad.append(f"{k}: forbidden row among the replacements")
    orig = [y for md in ("positive", "negative") for y in st.pick([x for x in allrows if mode_of_row[x] == md])]
    n_orig_forbidden += int(any(lib_of_row[y] == lib_ or y in excl for y in orig))
    reps = {md: [(y, st.prepared(y)) for y in st.pick([x for x in alt if mode_of_row[x] == md])] for md in ("positive", "negative")}
    if not alt: n_noalt += 1
    for mq, lst in QP.items():
        v = 0.0
        for ad, md, q in lst:
            Mq = q[3] + ADDUCT_SHIFT[ad]
            for y, cy in reps.get(md, []):
                if cy is None or abs((cy[3] + ADDUCT_SHIFT[add_of_row[y]]) - Mq) > BA.WIN: continue
                s_ = BA.sim_pair(q, cy)
                if s_ > 0.05 and s_ > v: v = s_
        rec = dict(AN.get(mq, []))
        if k in rec:
            n_checked += 1
            if abs(rec[k] - round(v, 6)) > 2e-6: bad.append(f"{mq}: C1 key {k} similarity {rec[k]} != recomputed {v:.6f}")
        elif v > 0.05:
            sims = sorted((s_ for _, s_ in AN.get(mq, [])), reverse=True)
            if len(sims) < BA.N_ANALOG or v > sims[BA.N_ANALOG - 1] + 2e-6: bad.append(f"{mq}: C1 key {k} (recomputed {v:.4f}) missing from the analog list")
info = dict(c1_keys=len(C1), c1_keys_original_rep_forbidden=n_orig_forbidden, c1_keys_without_replacement=n_noalt, c1_entries_checked=n_checked, n_queries=len(QP))
print(json.dumps(info)); print("WORLD_CHECK " + ("PASS" if not bad else "FAIL")); [print(" ", b) for b in bad[:20]]
json.dump(dict(info, bad=bad[:200], result=("PASS" if not bad else "FAIL")), open(os.path.join(Wd, "world_check.json"), "w"), indent=1)
sys.exit(0 if not bad else 1)
