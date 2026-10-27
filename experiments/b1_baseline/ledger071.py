"""071 training-group ledger (Codex 070): per training run x set x view, the ranking groups the trainer builds (same keep rule as
b1_rank_train.load_run), split by the production GL path (gl_ok = finite GL >= max(2, 0.5 * n_cand); else the pipeline uses the insurance list),
by 'positive in the view shortlist' and by 'truth COCONUT-listed'. Prints a table; no model, no evaluation result is read."""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = [("run_v3_p1", "../p1_baseline/run1/p1_molecules.csv", "v3"), ("run_v3_eval", "eval_set/p1_molecules.csv", "v3"), ("run_v3_c1", "eval_c1/p1_molecules.csv", "v3"),
        ("run_tp_f3a", "train_pool_f3a/p2_molecules.csv", "v8w"), ("run_tp_f4a", "train_pool_f4a/p2_molecules.csv", "v8w"),
        ("run_tp_f3b", "train_pool_f3b/p2_molecules.csv", "add_a"), ("run_tp_f4b", "train_pool_f4b/p2_molecules.csv", "add_a"),
        ("run_np061_f3pool", "np061_f3pool/p2_molecules.csv", "add_b")]
rows = []
for run, csv, tag in RUNS:
    ev = pd.read_csv(os.path.join(HERE, csv)); sets = sorted(set(ev.set.astype(str)))
    for s in sets:
        fpq = os.path.join(HERE, run, f"b1_features_{s}.parquet")
        if not os.path.exists(fpq): continue
        F = pd.read_parquet(fpq); M = pd.read_csv(os.path.join(HERE, run, f"b1_molecules_{s}.csv")).set_index("molecule")
        p = os.path.join(HERE, run, "work", f"gl_{s}.json")
        try: ok = json.load(open(p + ".meta.json")).get("status") in ("ok", "partial")
        except Exception: ok = False
        gl = json.load(open(p)) if ok else {}
        if run.startswith("run_v3") and "group" in ev.columns:   # v3 runs: only FIT groups train (run_v3_p1 is all fit via override)
            fitset = set(ev[ev.group == "fit"].molecule.astype(str)) if run != "run_v3_p1" else set(ev.molecule.astype(str))
        else: fitset = None
        for mid, g0 in F.groupby("molecule", sort=False):
            if mid not in M.index or (fitset is not None and str(mid) not in fitset): continue
            m = M.loc[mid]; tcoco = bool(g0[g0.is_truth].in_coconut.any()) if g0.is_truth.any() else False
            for view in ("c2", "c1"):
                if view == "c1" and not bool(m["c1_usable"] if "c1_usable" in M.columns else m.c1_possible): continue
                keep = g0[f"in_short_{view}"].values.astype(bool)
                if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0[f"in_train_{view}"].values).astype(bool)
                g = g0[keep]
                if len(g) == 0: continue
                fin = sum((gl.get(mid) or {}).get(sm) is not None for sm in g.smiles)
                rows.append(dict(tag=tag, run=run, set=s, view=view, gl_ok=bool(fin >= max(2, 0.5 * len(g))), pos=bool(g.is_truth.any()), tcoco=tcoco))
D = pd.DataFrame(rows)
pv = D.groupby(["tag", "set", "view"]).agg(groups=("pos", "size"), pos=("pos", "sum"), gl_ok=("gl_ok", "sum"), pos_gl=("gl_ok", lambda x: int((x & D.loc[x.index, "pos"]).sum())),
                                          tcoco=("tcoco", "sum")).reset_index()
pd.set_option("display.width", 200); pd.set_option("display.max_rows", 200)
print(pv.to_string(index=False))
tot = D.groupby("tag").agg(groups=("pos", "size"), pos=("pos", "sum"), pos_gl=("gl_ok", lambda x: int((x & D.loc[x.index, "pos"]).sum())), c1=("view", lambda x: int((x == "c1").sum())), tcoco=("tcoco", "sum"))
print(tot.to_string())
D.to_csv(os.path.join(HERE, "diag/ledger071.csv"), index=False)
