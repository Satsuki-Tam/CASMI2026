"""Per-molecule effect of the library-priority insurance rule (libpri) against its base rule, on the evaluator's stored scores
(same shortlist, same features, same official identities). Input: b1_evaluate per-molecule CSVs (results/b1_per_molecule_<set>.csv).
For each CSV and view (c2 = identity hidden, c1 = other-library references):
  dRR = RR[rule] - RR[base]; molecules are rescued (dRR > 0), hurt (dRR < 0) or unchanged;
  'lib_max >= tau' approximates where the rule can fire; 'list changed' = truth rank differs between rule and base;
  among lib_max >= tau: top reference match is the truth (truth_lib == lib_max) vs mis-promotion (truth_lib < lib_max);
  dRR and reference-match precision by lib_max bin (how often the best reference match IS the truth).
Usage: python b1_libpri_delta.py --per LABEL:CSV [LABEL:CSV ...] --base "S(2,1,0.5)" --rules "libpri(tau=0.9,m=0.2)>S(2,1,0.5)" --out <md>
"""
import argparse, re
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--per", nargs="+", required=True); ap.add_argument("--base", default="S(2,1,0.5)")
ap.add_argument("--rules", nargs="+", default=["libpri(tau=0.9,m=0.2)>S(2,1,0.5)", "libpri(tau=0.8,m=0.2)>S(2,1,0.5)"])
ap.add_argument("--out", required=True)
a = ap.parse_args()
BINS = [(0.0, 0.6), (0.6, 0.8), (0.8, 0.9), (0.9, 0.95), (0.95, 1.01)]
md = [f"# library-priority rule: per-molecule dRR vs base {a.base}", "", "fired ~ lib_max >= tau (margin condition not recoverable from the CSV); 'changed' = truth rank differs.", ""]
summary = []
for item in a.per:
    label, path = item.split(":", 1); D = pd.read_csv(path, index_col=0)
    for view in ("c2", "c1"):
        if f"{view}:n" not in D.columns: continue
        V = D[D[f"{view}:n"].notna()].copy()
        if not len(V): continue
        base = V[f"{view}:{a.base}"].astype(float); lm = V[f"{view}:lib_max"].astype(float); tl = V[f"{view}:truth_lib"].astype(float)
        brank = V[f"{view}:{a.base}@rank"]
        md += [f"## {label} / view {view} (n={len(V)}; base MRR {base.mean():.3f}; lib-only MRR {V[f'{view}:lib'].astype(float).mean():.3f})", ""]
        md += ["| lib_max bin | n | best-match-is-truth | base MRR | lib-only MRR |", "|---|---:|---:|---:|---:|"]
        for lo, hi in BINS:
            m = (lm >= lo) & (lm < hi)
            if m.sum() == 0: continue
            prec = (tl[m] >= lm[m] - 1e-9).mean()
            md.append(f"| [{lo:.2f},{min(hi,1.0):.2f}) | {int(m.sum())} | {prec:.3f} | {base[m].mean():.3f} | {V.loc[m, f'{view}:lib'].astype(float).mean():.3f} |")
        md.append("")
        md += ["| rule | MRR | dRR mean | rescued (sum dRR) | hurt (sum dRR) | changed | lib_max>=tau | of which truth is best match | mis-promotion (truth_lib < lib_max) : n / hurt / dRR sum | hurt among base top-1 |", "|---|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
        for rule in a.rules:
            col = f"{view}:{rule}"
            if col not in V.columns: md.append(f"| {rule} | (not in CSV) |"); continue
            r = V[col].astype(float); d = r - base; tau = float(re.search(r"tau=([0-9.]+)", rule).group(1))
            fired = lm >= tau; good = fired & (tl >= lm - 1e-9); bad = fired & (tl < lm - 1e-9)
            changed = (V[f"{col}@rank"].fillna(-1) != brank.fillna(-1))
            res = (d > 0); hurt = (d < 0)
            md.append(f"| {rule} | {r.mean():.3f} | {d.mean():+.4f} | {int(res.sum())} ({d[res].sum():+.2f}) | {int(hurt.sum())} ({d[hurt].sum():+.2f}) | {int(changed.sum())} | {int(fired.sum())} | {int(good.sum())} (dRR {d[good].sum():+.2f}) | {int(bad.sum())} / {int((bad & hurt).sum())} / {d[bad].sum():+.2f} | {int((hurt & (brank == 1)).sum())} |")
            summary.append(dict(label=label, view=view, rule=rule, n=len(V), base=base.mean(), rule_mrr=r.mean(), d=d.mean(), rescued=int(res.sum()), hurt=int(hurt.sum()), fired=int(fired.sum()), mis=int(bad.sum()), mis_hurt=int((bad & hurt).sum())))
            # per-bin dRR for this rule
            parts = []
            for lo, hi in BINS:
                m = (lm >= lo) & (lm < hi)
                if m.sum(): parts.append(f"[{lo:.2f},{min(hi,1.0):.2f}) n={int(m.sum())} dRR={d[m].mean():+.3f}")
            md.append(f"|  ↳ by lib_max bin | " + "; ".join(parts) + " | | | | | | | | |")
        md.append("")
S = pd.DataFrame(summary)
if len(S):
    md += ["## summary", "", "| label | view | rule | n | base | rule | dRR | rescued | hurt | fired | mis-promotions (hurt) |", "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    md += [f"| {s.label} | {s.view} | {s.rule} | {s.n} | {s.base:.3f} | {s.rule_mrr:.3f} | {s.d:+.4f} | {s.rescued} | {s.hurt} | {s.fired} | {s.mis} ({s.mis_hurt}) |" for s in S.itertuples()]
open(a.out, "w", encoding="utf-8").write("\n".join(md) + "\n"); print("\n".join(md))
