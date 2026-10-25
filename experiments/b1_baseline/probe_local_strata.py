"""Codex 023b: local conditional effects of the pool / Pc filters by view x truth COCONUT membership. For each (set, view, truth in COCONUT?)
cell: n, shortlist reach of the truth (truth row present in the view's shortlist), RR of the registered main list (all n, and conditional on
reach), and the filtered-list RR (pool = training or COCONUT candidates, Pc = neither; both computed by filtering the saved TOP-25 main list, which
is a lower bound of the full-order filter used by the probe kernels). COCONUT membership of the truth is read from its candidate row in the feature
table (in_coconut), so molecules whose truth is not in the table are reported as 'absent'.
Usage: python -X utf8 probe_local_strata.py --eval_dir DIR --features_run RUN --cand M2x --sets S1 ... [--md out.md]
"""
import argparse, os
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("--eval_dir", required=True); ap.add_argument("--features_run", required=True); ap.add_argument("--cand", default="M2x")
ap.add_argument("--out_name", default="blend21"); ap.add_argument("--sets", nargs="+", required=True); ap.add_argument("--md", default=""); a = ap.parse_args()
def rr_first(flags):
    for r, t in enumerate(flags, 1):
        if t: return 1.0 / r if r <= 25 else 0.0
    return 0.0
lines = [f"# pool / Pc filters by view x truth COCONUT membership ({a.cand} {a.out_name}; {a.eval_dir}; {a.features_run})", "",
         "| set | view | truth | n | reach | main RR | main RR given reach | pool RR | Pc RR | pool − main | Pc − main |", "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
for s in a.sets:
    f = pd.read_parquet(f"{a.features_run}/b1_features_{s}.parquet", columns=["molecule", "smiles", "is_truth", "in_train_c1", "in_train_c2", "in_coconut", "in_short_c1", "in_short_c2"])
    f["molecule"] = f.molecule.astype(str); fl = f.drop_duplicates(["molecule", "smiles"]).set_index(["molecule", "smiles"])
    for view in ("c1", "c2"):
        p = f"{a.eval_dir}/pred_{s}_{view}_{a.cand}_{a.out_name}.csv"
        if not os.path.exists(p): continue
        tr = f[f.is_truth].groupby("molecule").agg(coco=("in_coconut", "any"), short=(f"in_short_{view}", "any"))
        rows = []
        for mid, smi in zip(pd.read_csv(p).molecule_id.astype(str), pd.read_csv(p).smiles.astype(str)):
            lst = [x for x in smi.split(";") if x]; ist, grp = [], []
            for x in lst:
                if (mid, x) in fl.index:
                    r = fl.loc[(mid, x)]; ist.append(bool(r.is_truth)); grp.append(bool(r[f"in_train_{view}"]) or bool(r.in_coconut))
                else: ist.append(False); grp.append(None)
            truth = "absent" if mid not in tr.index else ("COCONUT" if tr.loc[mid, "coco"] else "not COCONUT")
            reach = bool(tr.loc[mid, "short"]) if mid in tr.index else False
            rows.append(dict(truth=truth, reach=reach, main=rr_first(ist), pool=rr_first([t for t, g in zip(ist, grp) if g is True]), pc=rr_first([t for t, g in zip(ist, grp) if g is False])))
        d = pd.DataFrame(rows)
        for tg, g in d.groupby("truth"):
            rm = g.main.mean(); rmr = g[g.reach].main.mean() if g.reach.any() else float("nan")
            lines.append(f"| {s} | {view} | {tg} | {len(g)} | {g.reach.mean():.2f} | {rm:.3f} | {rmr:.3f} | {g.pool.mean():.3f} | {g.pc.mean():.3f} | {g.pool.mean() - rm:+.3f} | {g.pc.mean() - rm:+.3f} |")
text = "\n".join(lines); print(text)
if a.md: open(a.md, "w", encoding="utf-8").write(text + "\n")
