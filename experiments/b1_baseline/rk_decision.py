"""Decision table for the full_rk ranker pair (pre-registered in reports/agent_review/023_decision.md section 4).

Reads the registered evaluator outputs rk_eval_{panel,p2dev,devAB}/pred_<set>_<view>_<cand>_<output>.csv (molecule_id, smiles, rr) and
reports paired molecule-level bootstrap deltas of the main output (blend21 + GL-cover fallback) for:
  main      RK_new - RK_old   (same full_rk tables; panel C1 = identity seen / query unseen; clean / uncertain from the fixed audit CSV)
  control   RK_new - RK_new0  (effect of dropping the class-2 rows of FPNet-seen identities from the ranker's training rows)
  adoption  RK_new - M2x      (different FPNet and ranker: not a ranker effect)
Protection (dev2 = full_rk hold groups = unseen): C2 of C/D/E/F/G and C1 of C/E/F/G need point AND 95% lower >= -0.02.
W7 (devAB): ranker fit groups were trained on -> only tune/eval groups, split by the FPNet exposure of the query identity.
Usage: python -X utf8 rk_decision.py [--out diag/rk_decision.md]
"""
import argparse, os, numpy as np, pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument("--out", default="diag/rk_decision.md"); ap.add_argument("--boot", type=int, default=10000)
ap.add_argument("--audit", default="../fpnet_full/full_eval_audit/panel_molecule_audit_groups.csv"); ap.add_argument("--exposure", default="../fpnet_full/full_rk/query_identity_exposure.csv")
ap.add_argument("--w7", default="eval_set/p1_molecules.csv"); ap.add_argument("--output", default="blend21"); ap.add_argument("--eps", type=float, default=0.02)
a = ap.parse_args()
rng = np.random.default_rng(0)

def pred(d, s, v, c):
    p = os.path.join(d, f"pred_{s}_{v}_{c}_{a.output}.csv")
    return pd.read_csv(p, usecols=["molecule_id", "rr"]).rename(columns={"molecule_id": "molecule"}).set_index("molecule").rr if os.path.exists(p) else None

def boot(x):
    x = np.asarray(x, float)
    if len(x) == 0: return np.nan, np.nan, np.nan
    idx = rng.integers(0, len(x), (a.boot, len(x))); bs = x[idx].mean(1)
    return x.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)

def row(label, cand, ref, mols=None):
    if cand is None or ref is None: return None
    j = pd.concat([cand.rename("c"), ref.rename("r")], axis=1, join="inner")
    if mols is not None: j = j[j.index.isin(mols)]
    assert j.c.notna().all() and j.r.notna().all()
    m, lo, hi = boot(j.c - j.r)
    return dict(stratum=label, n=len(j), cand=j.c.mean(), ref=j.r.mean(), delta=m, lo=lo, hi=hi, better=int((j.c > j.r).sum()), worse=int((j.c < j.r).sum()))

audit = pd.read_csv(a.audit); clean = set(audit[audit.audit_group.str.startswith("clean")].molecule); unc = set(audit.molecule) - clean
ex = pd.read_csv(a.exposure); w7 = pd.read_csv(a.w7, usecols=["set", "group", "molecule"])
lines = ["# full_rk ranker pair: pre-registered decision table (023_decision section 4)", "",
         f"Main output = {a.output} (+ GL-cover fallback, registered evaluator). Paired molecule-level bootstrap ({a.boot:,}, seed 0). eps = {a.eps}.", ""]
def table(title, rows, protect=None):
    lines.extend([f"## {title}", "", "| stratum | n | cand | ref | Δ | 95% CI | better / worse |" + (" protection |" if protect else ""), "|---|---:|---:|---:|---:|---|---|" + ("---|" if protect else "")])
    for r in rows:
        if r is None: continue
        flag = ""
        if protect and protect(r["stratum"]):
            ok = r["delta"] >= -a.eps and r["lo"] >= -a.eps; flag = " PASS |" if ok else (" point ok, lower < -eps (undetermined) |" if r["delta"] >= -a.eps else " FAIL |")
        elif protect: flag = " (not protection) |"
        lines.append(f"| {r['stratum']} | {r['n']} | {r['cand']:.4f} | {r['ref']:.4f} | {r['delta']:+.4f} | [{r['lo']:+.4f}, {r['hi']:+.4f}] | {r['better']} / {r['worse']} |" + flag)
    lines.append("")

for comp, cn, rn in (("main: RK_new - RK_old", "RK_new", "RK_old"), ("control: RK_new - RK_new0", "RK_new", "RK_new0"), ("adoption: RK_new - M2x", "RK_new", "M2x"), ("FPNet only: RK_old - M2x", "RK_old", "M2x")):
    d = "rk_eval_panel"; rows = []
    for v in ("c1", "c2"):
        c, r = pred(d, "P_np250", v, cn), pred(d, "P_np250", v, rn)
        rows += [row(f"panel {v.upper()} all", c, r), row(f"panel {v.upper()} clean", c, r, clean), row(f"panel {v.upper()} uncertain", c, r, unc)]
    table(f"{comp} -- panel (identity seen by full_rk, query unseen; C2 view not a protection layer)", rows)
    d = "rk_eval_p2dev"; rows = []
    for s in ("C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"):
        for v in ("c1", "c2"):
            rows.append(row(f"{s} {v.upper()}", pred(d, s, v, cn), pred(d, s, v, rn)))
    prot = lambda st: (st.endswith("C2") or (st.endswith("C1") and not st.startswith("D_")))
    table(f"{comp} -- dev2 (full_rk hold groups = unseen)", rows, protect=prot if comp.startswith("main") else None)
    d = "rk_eval_devAB"; rows = []
    for s in ("A_timstof", "B_nplib"):
        for v in ("c1", "c2"):
            c, r = pred(d, s, v, cn), pred(d, s, v, rn)
            if c is None: continue
            for g in ("tune", "eval"):
                mols = set(w7[(w7.set == s) & (w7.group == g)].molecule)
                for e in ("c1_seen", "unseen_after_removal"):
                    em = set(ex[(ex.set == s) & (ex.exposure == e)].molecule)
                    rows.append(row(f"W7 {s} {v.upper()} {g} {('seen' if e == 'c1_seen' else 'unseen')}", c, r, mols & em))
    table(f"{comp} -- W7 tune/eval groups (fit groups trained on), by FPNet exposure of the query identity", [r for r in rows if r and r["n"] > 0])
os.makedirs(os.path.dirname(a.out), exist_ok=True); open(a.out, "w", encoding="utf-8").write("\n".join(lines)); print("\n".join(lines))
