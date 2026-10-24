"""Effect of forward-model adduct proxies: compare a base feature run with proxy runs (same molecules, same candidates, runner spectra differ
only for molecules without a covered positive spectrum). Runs the inference probe (b1_learned_probe.py) on every run x model and reports,
for the molecules that gained forward coverage, the paired change of the truth's reciprocal rank under the fixed rule, the learned model and
the pipeline output (learned with GL-cover fallback); also the overall strict MRR before/after.
Usage: python b1_proxy_compare.py --base RUN --runs LABEL:RUN [...] --set S --models rank_v4b:0 [...] --out md
"""
import argparse, os, subprocess, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from b1_evaluate import boot

ap = argparse.ArgumentParser(); ap.add_argument("--base", required=True); ap.add_argument("--runs", nargs="+", required=True); ap.add_argument("--set", required=True)
ap.add_argument("--models", nargs="+", default=["rank_v4b:0"]); ap.add_argument("--views", nargs="+", default=["c2", "c1"]); ap.add_argument("--out", required=True)
a = ap.parse_args()
B = os.path.dirname(a.base.rstrip("/")); runs = [("base", a.base)] + [tuple(r.split(":", 1)) for r in a.runs]
md = [f"# forward-model adduct proxies: {a.set}", "", f"base {a.base}; proxy runs: " + ", ".join(f"{l} = {r}" for l, r in runs[1:]), ""]


def probe(run, model, w_ice, view):
    out = f"{run}/diag_probe_{model}.md"; csv = out.replace(".md", f"_{view}.csv")
    if not os.path.exists(csv):
        subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "b1_learned_probe.py"), "--run", run, "--set", a.set, "--model", f"{B}/{model}/lambdarank.txt", "--w_ice", str(w_ice),
                        "--views", *a.views, "--guards", "0.8:0.2,0.9:0.2", "--out", out], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = pd.read_csv(csv); d["molecule"] = d.molecule.astype(str); return d.set_index("molecule")


rr = lambda r: 1.0 / r if r <= 25 else 0.0
for mspec in a.models:
    model, w_ice = mspec.split(":"); w_ice = float(w_ice)
    for view in a.views:
        base = probe(a.base, model, w_ice, view)
        md += [f"## model {model} (w_ice {w_ice}) / view {view}", "", "| proxy run | molecules newly covered | fixed RR base -> proxy (paired Δ) | learned RR base -> proxy (paired Δ) | pipeline RR base -> proxy (paired Δ) | strict MRR all molecules: fixed base -> proxy | learned | pipeline |", "|---|---:|---|---|---|---|---|---|"]
        for label, run in runs[1:]:
            P = probe(run, model, w_ice, view); j = base.join(P, rsuffix="_p", how="inner")
            ok_b = j.gl_ok.astype(str).str.lower() == "true"; ok_p = j.gl_ok_p.astype(str).str.lower() == "true"
            new = j[(~ok_b) & ok_p & (j.reachable == True) & (j.reachable_p == True)]
            cells = []
            for col in ("r_fixed", "r_learned", "r_pipeline"):
                x = new[col].map(rr).values; y = new[col + "_p"].map(rr).values
                d = y - x; ci = boot(d) if len(d) > 1 else [np.nan, np.nan]
                cells.append(f"{x.mean() if len(x) else float('nan'):.3f} -> {y.mean() if len(y) else float('nan'):.3f} ({d.mean() if len(d) else float('nan'):+.3f} [{ci[0]:+.3f}, {ci[1]:+.3f}])")
            n_all = len(base)
            tot = []
            for col in ("r_fixed", "r_learned", "r_pipeline"):
                xb = base.loc[base.reachable == True, col].map(rr).sum() / n_all; xp = P.loc[P.reachable == True, col].map(rr).sum() / n_all
                tot.append(f"{xb:.3f} -> {xp:.3f}")
            md.append(f"| {label} | {len(new)} | {cells[0]} | {cells[1]} | {cells[2]} | {tot[0]} | {tot[1]} | {tot[2]} |")
            if len(new):
                new.assign(model=model, view=view, proxy=label).to_csv(a.out.replace(".md", f"_{model}_{view}_{label}.csv"))
        md.append("")
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); open(a.out, "w", encoding="utf-8").write("\n".join(md) + "\n"); print("\n".join(md))
