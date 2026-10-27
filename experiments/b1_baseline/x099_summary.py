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
