"""Error ledger of P (v8w7a, view c2) on the fold-1 development tables (140_decision.md §7; descriptive). P's top 25 come from w135_p.py
--parity_c2 (parity with the r133 outputs checked in each log). Layers per molecule:
  ok      : truth at rank 1;
  absent  : truth not in the c2 view list (split: not in the window / in the window but not shortlisted / shortlisted but outside the c2 source
            condition);
  isomer  : truth in the list below rank 1 and P's rank-1 candidate has the truth's neutral formula (same-formula discrimination);
  formula : truth in the list below rank 1 and P's rank-1 candidate has another formula.
For isomer / formula rows: which scores rank the truth above P's rank-1 (FP f.z, GL, library similarity). MRR loss = 1 - RR summed per layer.
Usage (Spark, experiments/b1_baseline as cwd): python -X utf8 ../w135/x_error_ledger.py"""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.abspath(os.path.join(HERE, "..", "b1_baseline")); sys.path.insert(0, B)
from wf_common import neutral_formula
SETS = [("np053f1", "run_np053_f1dev", s) for s in ("NP_H", "NP_X", "NP_N")] + [("f1dev", "run_f1dev", s) for s in ("C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib")]
rows = []
for tag, run, s in SETS:
    P = pd.read_parquet(os.path.join(HERE, "ledger", f"p_{tag}_{s}.parquet")); P["molecule"] = P.molecule.astype(str)
    F = pd.read_parquet(os.path.join(B, run, f"b1_features_{s}.parquet")); F["molecule"] = F.molecule.astype(str)
    M = pd.read_csv(os.path.join(B, run, f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
    gl = json.load(open(os.path.join(B, run, "work", f"gl_{s}.json")))
    for r in P.itertuples(index=False):
        m = r.molecule; t25 = json.loads(r.top25) if r.top25 else []; g = F[F.molecule == m]
        tr = g[g.is_truth.astype(bool)]; view = g[g.in_short_c2.astype(bool) & (g.in_tier | g.in_coconut | g.in_train_c2).astype(bool)]
        rec = dict(set=s, molecule=m, rr=float(r.main), rank=int(r.rP))
        if r.main == 1.0: rec["layer"] = "ok"
        elif not len(view) or not view.is_truth.astype(bool).any():
            sub = "not_in_window" if not bool(M.loc[m, "truth_in_window"]) else ("not_shortlisted" if not len(tr) or not tr.in_short_c2.astype(bool).any() else "outside_c2_source")
            rec["layer"] = "absent"; rec["sub"] = sub
        else:
            top = t25[0]; tk_smi = str(view[view.is_truth.astype(bool)].smiles.iloc[0]); top_smi = top[2]
            ft, f1 = neutral_formula(tk_smi), neutral_formula(top_smi); rec["layer"] = "isomer" if (ft and ft == f1) else "formula"
            tv = view[view.is_truth.astype(bool)].iloc[0]; t1 = view[view.official_key.astype(str) == top[1]].iloc[0]; gq = gl.get(m) or {}
            g_t, g_1 = gq.get(tk_smi), gq.get(top_smi)
            rec.update(fp_prefers_truth=bool(float(tv.fp or -1e9) > float(t1.fp or -1e9)), gl_prefers_truth=(None if g_t is None or g_1 is None else bool(g_t > g_1)),
                       lib_prefers_truth=bool(float(tv.lib_sim_c2) > float(t1.lib_sim_c2)), truth_pop_higher=bool(float(tv.pop_public) > float(t1.pop_public)))
        rows.append(rec)
D = pd.DataFrame(rows); D["loss"] = 1.0 - D.rr
print(f"molecules {len(D)}, MRR {D.rr.mean():.4f}")
for lay, g in D.groupby("layer"):
    print(f"  {lay:8s} n {len(g):4d} ({len(g)/len(D):.1%}) loss {g.loss.sum():6.1f} ({g.loss.sum()/D.loss.sum():.1%} of all loss) mean RR {g.rr.mean():.3f}")
A = D[D.layer == "absent"]; print("  absent split:", A["sub"].value_counts().to_dict())
for lay in ("isomer", "formula"):
    g = D[D.layer == lay]
    if len(g): print(f"  {lay}: truth preferred by FP {g.fp_prefers_truth.mean():.2f}, by GL {g.gl_prefers_truth.dropna().mean():.2f} (n {g.gl_prefers_truth.notna().sum()}), by library {g.lib_prefers_truth.mean():.2f}, truth more popular {g.truth_pop_higher.mean():.2f}")
print("by set:"); print(D.groupby(["set", "layer"]).size().unstack(fill_value=0).to_string())
D.to_parquet(os.path.join(HERE, "ledger", "ledger.parquet"), index=False)
