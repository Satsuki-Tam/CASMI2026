"""Evidence-family audit v2 (Codex 103 Q1; descriptive, after the 102 reading). Fixes of v1: (1) FULL denominators = every registered evaluation row
of diag/r102_<tag>.csv (molecules without candidate rows count as unreached), cell-weighted blocks reported next to row means; (2) explicit ties --
'pure' single evidences rank ties by a neutral fixed identity order (official key), missing values last; GL is reported with its coverage, and the
'GL + FP tie' policy is shown separately; (3) increments on the MAIN list's errors: for rows where the main list (v8w7a, top-25 dump) has a wrong
rank-1 but the truth in its list, the share of rows in which an evidence scores the truth ABOVE the main rank-1 decoy (rescue potential), and for
rows where the main rank-1 is the truth, the share in which the evidence scores the main rank-2 candidate above the truth (damage potential);
same-formula decoys are reported separately (98% of DB-route errors are same-formula isomers).
Inputs: diag/r102_<tag>.csv, diag/top102_<tag>.parquet (gen_eval2fd --dump_top of the same main), the run tables and GL JSON.
Usage: python -X utf8 fam_audit2.py"""
import json, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "panel": "run_panel_fe"}
NP = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered"]
CLEAN = set(pd.read_csv(os.path.join(HERE, "..", "fpnet_full", "full_eval_audit", "panel_molecule_audit_groups.csv")).query("audit_group == 'clean_nearest_lt_0.90'").molecule.astype(str))
EV = ["fp", "gl", "pop", "lib", "S"]


def zl(x):
    x = np.asarray(x, float); ok = np.isfinite(x)
    if ok.sum() < 2 or np.nanstd(x) == 0: return np.zeros(len(x))
    out = (x - np.nanmean(x)) / np.nanstd(x); out[~ok] = np.nanmin(out[ok]); return out


def trank_neutral(score, tr, keys):
    """rank of the best truth row under score desc; ties by the official key (neutral), missing (nan) values last; 0 if no truth row."""
    if not tr.any(): return 0
    s = np.asarray(score, float); miss = ~np.isfinite(s); s2 = np.where(miss, -np.inf, s)
    order = np.lexsort((np.asarray(keys), -s2)); pos = np.empty(len(s), int); pos[order] = np.arange(1, len(s) + 1)
    return int(pos[tr].min())


def formula_of(smiles):
    from rdkit import Chem
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula
    m = Chem.MolFromSmiles(smiles); return CalcMolFormula(m) if m is not None else None


rows = []
for tag, run in RUN_OF.items():
    R = pd.read_csv(os.path.join(HERE, f"diag/r102_{tag}.csv")); R["molecule"] = R.molecule.astype(str)
    TP = pd.read_parquet(os.path.join(HERE, f"diag/top102_{tag}.parquet")); TP["molecule"] = TP.molecule.astype(str)
    TOP = {(s, v, m): g.sort_values("rank") for (s, v, m), g in TP.groupby(["set", "view", "molecule"])}
    T = {}
    for f in sorted(os.listdir(os.path.join(HERE, run))):
        if not (f.startswith("b1_features_") and f.endswith(".parquet")): continue
        s = f[len("b1_features_"):-len(".parquet")]
        F = pd.read_parquet(os.path.join(HERE, run, f)); F["molecule"] = F.molecule.astype(str)
        pth = os.path.join(HERE, run, "work", f"gl_{s}.json")
        try: ok = json.load(open(pth + ".meta.json")).get("status") in ("ok", "partial")
        except Exception: ok = False
        gl = json.load(open(pth)) if ok else {}
        for mid, g0 in F.groupby("molecule", sort=False): T[(s, mid)] = (g0, gl.get(mid) or {})
    for r in R.itertuples(index=False):
        s, v, mid = r.set, r.view, r.molecule
        base = dict(tag=tag, set=s, view=v, molecule=mid, main=float(r.main), rP=int(np.nan_to_num(getattr(r, "rP", 0))))
        if (s, mid) not in T: rows.append(dict(base, n=0)); continue
        g0, glm = T[(s, mid)]
        keep = g0[f"in_short_{v}"].values.astype(bool)
        if v == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
        g = g0[keep].reset_index(drop=True); tr = g.is_truth.values.astype(bool); keys = g.official_key.astype(str).values
        if not len(g): rows.append(dict(base, n=0)); continue
        sc = dict(fp=g.fp.values.astype(float), pop=g.pop_public.values.astype(float), lib=g[f"lib_sim_{v}"].values.astype(float),
                  gl=np.array([np.nan if glm.get(sm) is None else float(glm.get(sm)) for sm in g.smiles], float))
        sc["S"] = zl(sc["fp"]) + 2 * zl(sc["gl"]) + 0.5 * sc["pop"]
        out = dict(base, n=len(g), gl_cov=float(np.isfinite(sc["gl"]).mean()), **{f"r_{k}": trank_neutral(sc[k], tr, keys) for k in EV})
        out["r_glfp"] = trank_neutral(np.where(np.isfinite(sc["gl"]), sc["gl"], -np.inf) * 1.0 + 1e-6 * zl(sc["fp"]), tr, keys) if np.isfinite(sc["gl"]).any() else 0
        tp = TOP.get((s, v, mid))
        if tp is not None and len(tp) and tr.any():
            idx = {k: i for i, k in enumerate(keys)}; ti = int(np.flatnonzero(tr)[0])
            top1 = idx.get(str(tp.okey.iloc[0])); top2 = idx.get(str(tp.okey.iloc[1])) if len(tp) > 1 else None
            ftruth = formula_of(str(g.smiles.values[ti]))
            if out["main"] < 1 and top1 is not None and top1 != ti:   # main wrong at rank 1, truth in the list: does x prefer the truth over the main rank-1 decoy?
                out["same_formula_top1"] = formula_of(str(g.smiles.values[top1])) == ftruth
                for k in EV: out[f"rescue_{k}"] = (np.isfinite(sc[k][ti]) and (not np.isfinite(sc[k][top1]) or sc[k][ti] > sc[k][top1])) if np.isfinite(sc[k][ti]) or np.isfinite(sc[k][top1]) else np.nan
            if out["main"] == 1 and top2 is not None:   # main right at rank 1: does x prefer the main rank-2 candidate over the truth?
                for k in EV: out[f"damage_{k}"] = (np.isfinite(sc[k][top2]) and (not np.isfinite(sc[k][ti]) or sc[k][top2] > sc[k][ti])) if np.isfinite(sc[k][ti]) or np.isfinite(sc[k][top2]) else np.nan
        rows.append(out)
A = pd.DataFrame(rows); A.to_csv(os.path.join(HERE, "diag/fam_audit2.csv"), index=False)
rr = lambda r: np.where((r >= 1) & (r <= 25), 1.0 / np.maximum(r, 1), 0.0)
LAY = {"A 053 NP C2 (H/N)": lambda d: d.tag.str.startswith("np053") & (d.view == "c2") & d.set.isin(["NP_H", "NP_N"]),
       "B_D f1/f2 D C2": lambda d: d.tag.isin(["f1dev", "f2dev"]) & (d.view == "c2") & (d.set == "D_np_single"),
       "old B f1/f2 NP C2": lambda d: d.tag.isin(["f1dev", "f2dev"]) & (d.view == "c2") & d.set.isin(NP),
       "G C1": lambda d: d.tag.isin(["f1dev", "f2dev"]) & (d.view == "c1") & (d.set == "G_tims_crosslib"),
       "panel C1 clean": lambda d: (d.tag == "panel") & (d.view == "c1") & d.molecule.isin(CLEAN)}
L = ["# evidence-family audit v2 (full denominators, neutral ties, increments on the main list's errors)", "",
     "| layer | n (rows) | main MRR | " + " | ".join(f"{k} MRR" for k in EV + ["glfp"]) + " | GL coverage (mean) |", "|---|---:|---:|" + "---:|" * (len(EV) + 2)]
for lab, f in LAY.items():
    d = A[f(A)]
    L.append(f"| {lab} | {len(d)} | {d.main.mean():.4f} | " + " | ".join(f"{rr(d[f'r_{k}'].fillna(0).values).mean():.4f}" for k in EV + ["glfp"]) + f" | {d.gl_cov.mean():.3f} |")
L += ["", "Rescue potential: rows with a wrong main rank-1 and the truth in the list; share in which the evidence scores the truth above the main rank-1 (all / same-formula decoy). Damage potential: rows with a correct main rank-1; share in which the evidence scores the main rank-2 above the truth.", "",
      "| layer | n wrong@1 (same formula) | " + " | ".join(f"rescue {k}" for k in EV) + " | n right@1 | " + " | ".join(f"damage {k}" for k in EV) + " |", "|---|---|" + "---|" * len(EV) + "---:|" + "---|" * len(EV)]
for lab, f in LAY.items():
    d = A[f(A)]
    w = d[d.columns[d.columns.str.startswith("rescue_")]].notna().any(axis=1) if any(d.columns.str.startswith("rescue_")) else pd.Series(False, index=d.index)
    dw = d[w]; sf = dw.same_formula_top1.fillna(False).astype(bool) if "same_formula_top1" in dw else pd.Series(False, index=dw.index)
    cells = [f"{dw[f'rescue_{k}'].mean():.2f} / {dw[sf][f'rescue_{k}'].mean():.2f}" if f"rescue_{k}" in dw and len(dw) else "-" for k in EV]
    rgt = d[d[d.columns[d.columns.str.startswith("damage_")]].notna().any(axis=1)] if any(d.columns.str.startswith("damage_")) else d.iloc[:0]
    dmg = [f"{rgt[f'damage_{k}'].mean():.2f}" if f"damage_{k}" in rgt and len(rgt) else "-" for k in EV]
    L.append(f"| {lab} | {len(dw)} ({int(sf.sum())}) | " + " | ".join(cells) + f" | {len(rgt)} | " + " | ".join(dmg) + " |")
open(os.path.join(HERE, "diag/fam_audit2.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
