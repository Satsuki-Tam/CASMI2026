"""W135 C1-eligibility audit (Codex 136 Q2 (a); run before any reach number): C1 eligibility recomputed with the WORLD rule for every batch
molecule, then the registered hash-order assignment re-applied and compared with the batch CSV columns.
World rule (b1_world.py): queries = select_queries over the molecule's selection-library rows with test adducts (raw CE, as b1_world); the
truth candidate's references = rows of its scorer key minus the query rows, minus every row of its selection library, minus the other-library
rows that are an exact duplicate (same adduct, |dprec| < 5 mDa, identical cleaned peaks) or a suspected duplicate (|dprec| < 5 mDa, same mode,
entropy similarity >= 0.98) of a query spectrum; eligible = at least one remaining reference with a query polarity ("independent" = passed
this de-duplication rule, a proxy, not a proof of a separate acquisition). Also counts the replacement analog representatives (test adducts).
Assignment (w135_batches.py): identities in hash order w135cls|batch|molecule; C3 = first round(pi N) (nested, unchanged); of the rest, C1 =
the first floor(rest / 2) eligible, the others C2. Writes experiments/w135/c1audit/<tag>.parquet / .json; exit 1 if any registered assignment
differs from the re-applied one (the affected worlds must then be rebuilt from corrected CSVs before any reach is read).
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_c1audit.py --batches dF1 dF2 dF3 dR1 dR2 dR3 --tag d"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd, polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); B = os.path.join(ROOT, "experiments/b1_baseline"); sys.path.insert(0, B)
from b1_common import ADDUCT_SHIFT, ELECTRON, clean_peaks, entropy_similarity, select_queries
from b1_features import exact_dup, DUP_SIM
ap = argparse.ArgumentParser(); ap.add_argument("--batches", nargs="+", required=True); ap.add_argument("--tag", required=True); a = ap.parse_args()
H = lambda s: hashlib.sha256(s.encode()).hexdigest(); PIS = (0.0, 0.3, 0.6)
store = os.path.join(ROOT, "data/processed/spectra_store")
S_MZ = np.load(f"{store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{store}/spec_off.npy")
meta = pl.read_parquet(f"{store}/spec_meta.parquet")
lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
prec_of_row = meta["precursor_mz"].to_numpy(); ce_of_row = meta["ce_mean"].to_numpy()
key_rows = {k: np.asarray(r, np.int64) for k, r in meta.filter(pl.col("scorer_ik14").is_not_null()).group_by("scorer_ik14").agg(pl.col("row")).iter_rows()}
ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
def spectrum(row, shift=0.0):
    s, e = int(S_OFF[row]), int(S_OFF[row + 1]); return np.asarray(S_MZ[s:e], np.float64) - shift, np.asarray(S_IT[s:e], np.float64)
def query_spectra(mid, lib):   # = b1_world.query_spectra
    shift = ELECTRON if lib == "enveda-180" else 0.0
    qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
    q = select_queries(qrows, 8, lambda x: add_of_row[x], lambda x: float(ce_of_row[x])); out = []
    for x in q:
        sh = shift if mode_of_row[x] == "positive" else 0.0
        mz, it = spectrum(x, sh); prec = float(prec_of_row[x]) - sh
        out.append(dict(row=x, prec=prec, adduct=add_of_row[x], mode=mode_of_row[x], clean=clean_peaks(mz, it, prec)))
    return out
rows, changes = [], []
for b in a.batches:
    bt = pd.read_csv(os.path.join(ROOT, "experiments/w135/batches", f"{b}.csv")); bt["molecule"] = bt.molecule.astype(str)
    elig = {}
    for r in bt.itertuples(index=False):
        mid, tk, lib = str(r.molecule), str(r.scorer_key), str(r.lib); qs = query_spectra(mid, lib); qrows = {s["row"] for s in qs}; modes = {s["mode"] for s in qs}
        eff, alt = [], 0
        for x in key_rows.get(tk, []):
            x = int(x)
            if x in qrows or lib_of_row[x] == lib: continue
            sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
            mz, it = spectrum(x, sh); rprec = float(prec_of_row[x]) - sh; rmz, rit = clean_peaks(mz, it, rprec)
            if any(exact_dup(s, rmz, rit, rprec, add_of_row[x]) for s in qs): continue
            if any(abs(s["prec"] - rprec) < 0.005 and s["mode"] == mode_of_row[x] and entropy_similarity(s["clean"][0], s["clean"][1], rmz, rit) >= DUP_SIM for s in qs): continue
            alt += int(add_of_row[x] in ADDUCT_SHIFT)
            if mode_of_row[x] in modes: eff.append(x)
        elig[mid] = len(eff) >= 1
        rows.append(dict(batch=b, molecule=mid, c1_eligible_batch=bool(r.c1_eligible), n_ref_after_world_mask=len(eff), c1_eligible_world=len(eff) >= 1, n_alt_analog_rows=alt,
                         query_rows=json.dumps(sorted(qrows)), ref_rows=json.dumps(eff[:50]), **{f"wclass_p{int(p * 100)}": getattr(r, f"wclass_p{int(p * 100)}") for p in PIS}))
    ms = sorted(bt.molecule, key=lambda m: H(f"w135cls|{b}|{m}")); N = len(ms)
    for p in PIS:
        n3 = int(round(p * N)); rest = ms[n3:]; n1 = len(rest) // 2; c1 = set([m for m in rest if elig[m]][:n1])
        new = {m: ("C3" if i < n3 else ("C1" if m in c1 else "C2")) for i, m in enumerate(ms)}; old = dict(zip(bt.molecule, bt[f"wclass_p{int(p * 100)}"]))
        d = [m for m in ms if new[m] != old[m]]
        if d: changes.append(dict(batch=b, pi=p, n_changed=len(d), molecules=d[:20], new_counts={k: sum(1 for v in new.values() if v == k) for k in ("C1", "C2", "C3")}))
R = pd.DataFrame(rows); os.makedirs(os.path.join(ROOT, "experiments/w135/c1audit"), exist_ok=True); R.to_parquet(os.path.join(ROOT, "experiments/w135/c1audit", f"{a.tag}.parquet"), index=False)
summ = dict(batches=a.batches, n=len(R), eligible_batch=int(R.c1_eligible_batch.sum()), eligible_world=int(R.c1_eligible_world.sum()),
            batch_yes_world_no=int((R.c1_eligible_batch & ~R.c1_eligible_world).sum()), batch_no_world_yes=int((~R.c1_eligible_batch & R.c1_eligible_world).sum()),
            assigned_c1_p30_without_world_ref=int(((R.wclass_p30 == "C1") & ~R.c1_eligible_world).sum()), assignment_changes=changes)
json.dump(summ, open(os.path.join(ROOT, "experiments/w135/c1audit", f"{a.tag}.json"), "w"), indent=1); print(json.dumps(summ, indent=1)[:3000])
print("C1AUDIT " + ("PASS (registered assignment = re-applied world-rule assignment)" if not changes else "CHANGES (rebuild the affected worlds from corrected CSVs)"))
sys.exit(0 if not changes else 1)
