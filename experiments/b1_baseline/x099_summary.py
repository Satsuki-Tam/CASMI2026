"""099 reading (exploratory): t099_{A,B,C,D}.csv on the fold-safe panel table. A baseline (+ dump), B test-side parents only, C 10 train-analog parents,
D = C + test-side. Per run: c3 view gt3 MRR and truth-generated rate (truth_loc novel), c2 / c1 gt3 - main (cost); parent quality from A's dump."""
import numpy as np, pandas as pd
R = {k: pd.read_csv(f"diag/t099_{k}.csv") for k in "ABCD"}
T = pd.read_parquet("diag/top_panelf0.parquet")
p1 = T[(T.view == "c2") & (T["rank"] == 1)]
L = ["# 099 transductive generation on the fold-safe panel (exploratory)", "", f"- parent quality: c2-view rank-1 correct for {p1.is_truth.mean():.3f} of {p1.molecule.nunique()} molecules", "",
     "| run | c3 n | c3 gt3 MRR | c3 truth generated (novel) | c2 main | c2 gt3 - main | c1 gt3 - main |", "|---|---:|---:|---:|---:|---:|---:|"]
for k, x in R.items():
    c3 = x[x.view == "c3"]; c2 = x[x.view == "c2"]; c1 = x[x.view == "c1"]
    gen = (c3.truth_generated.astype(str).isin(["True", "1", "1.0"]) & (c3.truth_loc.astype(str) == "novel")).mean() if len(c3) else np.nan
    L.append(f"| {k} | {len(c3)} | {c3.gt3.mean():.4f} | {gen:.3f} | {c2.main.mean():.4f} | {(c2.gt3 - c2.main).mean():+.4f} | {(c1.gt3 - c1.main).mean():+.4f} |")
open("diag/x099_summary.md", "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
# leak diagnostic (Codex 099): C3 molecules whose truth was generated (novel) while some OTHER molecule's c2 rank-1 has the truth's official key
truth = dict(zip(pd.read_csv("panel_np250/p1_molecules.csv").molecule.astype(str), pd.read_csv("panel_np250/p1_molecules.csv").scorer_key.astype(str)))
top1 = dict(zip(p1.molecule.astype(str), p1.okey.astype(str)))
L2 = ["", "| run | c3 truth generated (novel) | of which a parent (another molecule's top-1) has the truth key | c2 insertions (gt3 != main) | c1 insertions |", "|---|---:|---:|---:|---:|"]
for k, x in R.items():
    c3 = x[x.view == "c3"].copy(); c3["gen"] = c3.truth_generated.astype(str).isin(["True", "1", "1.0"]) & (c3.truth_loc.astype(str) == "novel")
    leak = sum(1 for m in c3[c3.gen].molecule.astype(str) if any(v == truth.get(m) for j, v in top1.items() if j != m))
    L2.append(f"| {k} | {int(c3.gen.sum())} | {leak} | {int((x[x.view == 'c2'].gt3 != x[x.view == 'c2'].main).sum())} | {int((x[x.view == 'c1'].gt3 != x[x.view == 'c1'].main).sum())} |")
open("diag/x099_summary.md", "a", encoding="utf-8").write("\n".join(L2) + "\n"); print("\n".join(L2))
