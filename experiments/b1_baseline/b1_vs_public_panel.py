"""Where does B1 lose against the public pipeline? Same molecules (enveda-np-examples panel, 250), same official identities.

Public side: data/external/panel_benchmark/main_candidates.parquet (the public lineage's ranked main list per molecule and scenario:
'reference_in_other_libraries' ~ our class-1 view, 'structure_in_pool_no_reference' ~ our class-2 view). B1 side: the panel run of
b1_features (window / shortlist membership), the fixed-rule per-molecule RR (results/b1_per_molecule_*.csv) and the learned / insurance /
fixed predictions of the frozen model (learned_eval/pred_*.csv). For every view: public RR vs B1 RR, and for molecules the public pipeline
ranks first but B1 does not, the stage where B1 loses the truth (not in window / not in shortlist / ranked lower). Also the prior alignment:
public 'popularity' vs B1 'pop_public' on common candidates.
Usage: python b1_vs_public_panel.py --panel_dir data/external/panel_benchmark --run experiments/b1_baseline/run_panel_v2 --set P_np250 --out <md>
"""
import argparse, glob, os
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument("--panel_dir", required=True); ap.add_argument("--run", required=True); ap.add_argument("--set", default="P_np250"); ap.add_argument("--out", required=True)
a = ap.parse_args()
mc = pd.read_parquet(f"{a.panel_dir}/main_candidates.parquet"); mc["molecule"] = mc.molecule.astype(str)
M = pd.read_csv(f"{a.run}/b1_molecules_{a.set}.csv"); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
F = pd.read_parquet(f"{a.run}/b1_features_{a.set}.parquet"); F["molecule"] = F.molecule.astype(str)
per = pd.read_csv(f"{a.run}/results/b1_per_molecule_{a.set}.csv"); per["molecule"] = per.molecule.astype(str); per = per.set_index("molecule")
SCEN = {"c1": "reference_in_other_libraries", "c2": "structure_in_pool_no_reference"}
md = [f"# B1 vs public pipeline on the panel ({a.run}, {a.set})", ""]


def pub_rr(view):
    g = mc[mc.scenario == SCEN[view]].sort_values(["molecule", "rank"]); out = {}
    for m, gm in g.groupby("molecule", sort=False):
        gm = gm.drop_duplicates("candidate_key"); hit = np.flatnonzero(gm.is_truth.values)
        out[m] = (1.0 / (hit[0] + 1) if len(hit) and hit[0] < 25 else 0.0, int(hit[0] + 1) if len(hit) else None, len(gm))
    return out


def b1_pred_rr(view, kind):
    p = glob.glob(f"{a.run}/learned_eval/pred_{a.set}_{view}_*_{kind}.csv")
    if not p: return None
    d = pd.read_csv(p[0]); d["molecule_id"] = d.molecule_id.astype(str); return dict(zip(d.molecule_id, d.rr))


for view in ("c2", "c1"):
    pub = pub_rr(view); rows = []
    learned = b1_pred_rr(view, "learned") or {}; ins = b1_pred_rr(view, "insurance") or {}; fixed = b1_pred_rr(view, "fixed") or {}
    for m in M.index:
        if view == "c1" and not bool(M.loc[m].get("c1_usable", True)): continue
        pr, prank, pn = pub.get(m, (None, None, None))
        in_win = bool(M.loc[m, "truth_in_window"]); in_short = bool(M.loc[m, f"truth_in_short_{view}"]) if f"truth_in_short_{view}" in M.columns else bool(M.loc[m, "truth_in_shortlist"])
        fixed_rr = per.loc[m, f"{view}:S(2,1,0.5)"] if m in per.index and f"{view}:S(2,1,0.5)" in per.columns else np.nan
        rows.append(dict(molecule=m, pub_rr=pr, pub_rank=prank, pub_n=pn, b1_in_window=in_win, b1_in_short=in_short, b1_fixed=fixed_rr, b1_learned=learned.get(m, np.nan), b1_ins=ins.get(m, np.nan),
                         lib_max_pub=float(mc[(mc.scenario == SCEN[view]) & (mc.molecule == m)].lib_max.max()) if pn else np.nan))
    R = pd.DataFrame(rows); R = R[R.pub_rr.notna()]
    n = len(R)
    md += [f"## view {view} (public scenario '{SCEN[view]}'; {n} molecules with a public main list)", "",
           f"| system | MRR@25 | top-1 |", "|---|---:|---:|",
           f"| public main list | {R.pub_rr.mean():.3f} | {(R.pub_rr == 1).mean():.3f} |",
           f"| B1 fixed S(2,1,0.5) | {R.b1_fixed.mean():.3f} | {(R.b1_fixed == 1).mean():.3f} |",
           f"| B1 learned (rank_v2) | {R.b1_learned.mean():.3f} | {(R.b1_learned == 1).mean():.3f} |",
           f"| B1 insurance (libpri 0.9) | {R.b1_ins.mean():.3f} | {(R.b1_ins == 1).mean():.3f} |", ""]
    for name, col in (("learned", "b1_learned"), ("fixed", "b1_fixed")):
        pw = R[(R.pub_rr == 1) & (R[col] < 1)]; bw = R[(R[col] == 1) & (R.pub_rr < 1)]
        stage = pw.apply(lambda r: "not in window" if not r.b1_in_window else ("not in shortlist" if not r.b1_in_short else ("rank 2-5" if r[col] >= 0.2 else ("rank 6-25" if r[col] > 0 else "rank > 25"))), axis=1) if len(pw) else pd.Series(dtype=str)
        md += [f"### public top-1 but B1 {name} not top-1: {len(pw)} molecules (reverse: {len(bw)})", "",
               "| B1 stage where the truth is lost | molecules |", "|---|---:|"] + [f"| {k} | {v} |" for k, v in stage.value_counts().items()] + [""]
        if len(pw): md.append(f"public lib_max for these (median): {pw.lib_max_pub.median():.3f}; B1 {name} RR mean {pw[col].mean():.3f}")
        md.append("")
    md += [f"paired mean ΔRR (B1 learned − public): {(R.b1_learned - R.pub_rr).mean():+.4f} | (B1 fixed − public): {(R.b1_fixed - R.pub_rr).mean():+.4f}", ""]
    R.to_csv(a.out.replace(".md", f"_{view}.csv"), index=False)
# ---- prior alignment on common candidates (class-2 scenario list vs B1 shortlist)
g = mc[mc.scenario == SCEN["c2"]][["molecule", "candidate_key", "popularity"]].drop_duplicates(["molecule", "candidate_key"])
j = g.merge(F[["molecule", "official_key", "pop_public", "lsid", "lpmid"]], left_on=["molecule", "candidate_key"], right_on=["molecule", "official_key"], how="inner")
if len(j):
    md += ["## prior alignment (public 'popularity' vs B1 'pop_public' on common candidates)", "",
           f"common candidates {len(j)} of {len(g)} public-list rows; Spearman(popularity, pop_public) = {j[['popularity', 'pop_public']].corr(method='spearman').iloc[0, 1]:.3f}; "
           f"share public popularity > 0 : {(j.popularity > 0).mean():.3f}; share pop_public > 0 : {(j.pop_public > 0).mean():.3f}", ""]
os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True); open(a.out, "w", encoding="utf-8").write("\n".join(md) + "\n"); print("\n".join(md))
