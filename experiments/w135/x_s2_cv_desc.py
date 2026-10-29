"""Descriptive summary of the W135 stage-2 CV (leave-one-pair-out) and the frozen model (139: descriptive only; nothing is changed after it)."""
import json, os
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); S = os.path.join(ROOT, "experiments/w135/s2")
m = json.load(open(os.path.join(S, "fit_freeze.json"))); print("fit rows", m["n_rows"], "positive rows", m["n_pos_rows"], "positive identities", m["n_pos_identities"])
md = json.load(open(os.path.join(S, "fit_model.json"))); co = dict(zip(md["feats"], md["model"]["coef"]))
print("largest |coef|:", [(k, round(v, 3)) for k, v in sorted(co.items(), key=lambda kv: -abs(kv[1]))[:12]])
for bn in ("lib", "gl", "fb"): print("q", bn, "r1..3", [round(x, 3) for x in md["q_table"][bn][:3]], "sum r1..25", round(sum(md["q_table"][bn]), 3))
C = pd.read_parquet(os.path.join(S, "cv_queries.parquet")); C["d"] = C.rr - C.rrP
print("CV (descriptive, leave-one-pair-out)")
for p in (0, 30, 60):
    g = C[C.pi == p]; ins = g.action == "insert"
    print(f"  pi {p:2d}: n {len(g)} delta {g.d.mean():+.4f} | P {g.rrP.mean():.4f} -> {g.rr.mean():.4f} | insert rate {ins.mean():.3f}",
          "| C1", round(g[g.wclass == "C1"].d.mean(), 4), "C2", round(g[g.wclass == "C2"].d.mean(), 4), "C3", round(g[g.wclass == "C3"].d.mean(), 4) if (g.wclass == "C3").any() else "-")
c3 = C[(C.pi == 30) & (C.wclass == "C3")]; b = c3[c3.truth_in_B.astype(bool)]; ok = b[b.x_key == b.truth]
print("  pi 30 C3: n", len(c3), "| truth in B", len(b), "| x = truth", len(ok), "| inserted", int((ok.action == "insert").sum()), "| k", ok[ok.action == "insert"].k.value_counts().to_dict())
ins = C[C.action == "insert"]; print("  insertions", len(ins), "accuracy", round((ins.x_key == ins.truth).mean(), 3), "k counts", ins.k.value_counts().to_dict())
for p in (0, 30, 60):
    g = C[(C.pi == p) & (C.action == "insert")]
    if len(g): print(f"  pi {p:2d} wrong insertions by class:", g[g.x_key != g.truth].wclass.value_counts().to_dict(), "| harm on rows whose P had the truth in top 25:", round(g[(g.rrP > 0)].d.sum(), 3))
