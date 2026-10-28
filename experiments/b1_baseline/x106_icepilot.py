"""106 (iii) ICEBERG pilot, step 3 (exploratory; written before the ICE run). Inputs: diag/icepilot106/out_<tag>_<set>.json (ice_runner: {mid: {smiles:
ice_ex_mean}}), the GL JSON of the run, diag/top102_<tag>.parquet (main top 25 with scores), diag/r102_<tag>.csv, the run tables, subset.csv.
Fixed before the run:
  (1) isomer discrimination: for view-list rows whose truth has >= 1 same-formula competitor with an ICE score, the truth's rank inside its formula group
      under the main order, under GL alone and under ICE alone (ties by official key, missing last); reported as within-group MRR and pairwise wins.
  (2) connection: in the main top 25, every same-formula group (>= 2 members with ICE) is re-ordered among its OWN slots by z(main score) + 0.5 z(ICE)
      (z inside the group); other positions unchanged; vs the main order (paired bootstrap, rows, 4,000, seed 107).
Views: C2 rows of NP_H / NP_N / C / D, C1 rows of G and panel. Usage: python -X utf8 x106_icepilot.py"""
import json, os, sys
import numpy as np, pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem.rdMolDescriptors import CalcMolFormula
RDLogger.DisableLog("rdApp.*")
HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.join(HERE, "diag", "icepilot106"); NB = 4000
RUN_OF = {"f1dev": "run_f1dev", "f2dev": "run_f2dev", "np053f1dev": "run_np053_f1dev", "np053f2dev": "run_np053_f2dev", "panel": "run_panel_fe"}
SUB = pd.read_csv(os.path.join(HERE, "diag", "glpilot106", "subset.csv")); SUB["molecule"] = SUB.molecule.astype(str)
FORM = {}
def formula(smi):
    if smi not in FORM:
        m = Chem.MolFromSmiles(smi); FORM[smi] = CalcMolFormula(m) if m is not None else None
    return FORM[smi]
def zl(x):
    x = np.asarray(x, float); ok = np.isfinite(x)
    if ok.sum() < 2 or np.std(x[ok]) == 0: return np.where(ok, 0.0, np.nan)
    return (x - x[ok].mean()) / x[ok].std()
def grank(score, ti, members, keys):
    s = np.array([score[i] if np.isfinite(score[i]) else -np.inf for i in members]); k = np.array([keys[i] for i in members])
    o = np.lexsort((k, -s)); pos = {members[j]: r + 1 for r, j in enumerate(o)}; return pos[ti]
rows, conn = [], []
for (tag, s), sub in SUB.groupby(["tag", "set"]):
    run = os.path.join(HERE, RUN_OF[tag]); op = os.path.join(P, f"out_{tag}_{s}.json")
    if not os.path.exists(op): sys.exit(f"STOP: missing {op}")
    ice = json.load(open(op)); gl = json.load(open(os.path.join(run, "work", f"gl_{s}.json")))
    F = pd.read_parquet(os.path.join(run, f"b1_features_{s}.parquet")); F["molecule"] = F.molecule.astype(str)
    M = pd.read_csv(os.path.join(run, f"b1_molecules_{s}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
    TP = pd.read_parquet(os.path.join(HERE, f"diag/top102_{tag}.parquet")); TP["molecule"] = TP.molecule.astype(str)
    R = pd.read_csv(os.path.join(HERE, f"diag/r102_{tag}.csv")); R["molecule"] = R.molecule.astype(str); R = R.set_index(["set", "view", "molecule"])
    for mid in sub.molecule:
        g0 = F[F.molecule == mid]; im = ice.get(mid) or {}; gm = gl.get(mid) or {}
        for view in ("c2", "c1"):
            if view == "c1" and not bool(M.loc[mid, "c1_usable"]): continue
            keep = g0[f"in_short_{view}"].values.astype(bool)
            if view == "c2": keep &= (g0.in_tier.values | g0.in_coconut.values | g0.in_train_c2.values).astype(bool)
            g = g0[keep].reset_index(drop=True); tr = np.flatnonzero(g.is_truth.values.astype(bool)); keys = g.official_key.astype(str).values; smi = g.smiles.astype(str).values
            iv = np.array([np.nan if im.get(x) is None else float(im[x]) for x in smi]); gv = np.array([np.nan if gm.get(x) is None else float(gm[x]) for x in smi])
            main = float(R.loc[(s, view, mid), "main"]) if (s, view, mid) in R.index else 0.0
            tp = TP[(TP.set == s) & (TP.view == view) & (TP.molecule == mid)].sort_values("rank")
            if len(tr):
                ti = int(tr[0]); ft = formula(smi[ti]); mem = [i for i in range(len(g)) if formula(smi[i]) == ft]
                if len(mem) >= 2 and np.isfinite(iv[mem]).sum() >= 2:
                    pos_main = {k: r for r, k in enumerate(tp.okey.astype(str))}; pm = np.array([-pos_main.get(keys[i], 10 ** 6) for i in range(len(g))], float)
                    rows.append(dict(tag=tag, set=s, view=view, molecule=mid, n_group=len(mem), r_main=grank(pm, ti, mem, keys), r_gl=grank(gv, ti, mem, keys), r_ice=grank(iv, ti, mem, keys)))
            if len(tp):   # (2) connection inside the main top 25
                order = list(range(len(tp))); sm_ = tp.smiles.astype(str).values; scz = tp.score.values.astype(float)
                ivt = np.array([np.nan if im.get(x) is None else float(im[x]) for x in sm_]); ft_ = [formula(x) for x in sm_]
                new = list(order)
                for f_ in set(ft_):
                    slots = [k for k in order if ft_[k] == f_]
                    if len(slots) < 2 or np.isfinite(ivt[slots]).sum() < 2: continue
                    sc = zl(scz[slots]) + 0.5 * np.nan_to_num(zl(ivt[slots]), nan=0.0)
                    srt = [slots[j] for j in np.lexsort((np.array(slots), -sc))]
                    for k_, i_ in zip(sorted(slots), srt): new[k_] = i_
                tpos = [k for k, i in enumerate(new) if bool(tp.is_truth.values[i])]
                conn.append(dict(tag=tag, set=s, view=view, molecule=mid, main=main, ice_grp=(1.0 / (tpos[0] + 1)) if tpos else 0.0))
A = pd.DataFrame(rows); C = pd.DataFrame(conn); A.to_csv(os.path.join(P, "x106_ice_rows.csv"), index=False); C.to_csv(os.path.join(P, "x106_ice_conn.csv"), index=False)
rng = np.random.default_rng(107)
def ci(d):
    d = np.asarray(d, float); bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(NB)]; return f"{d.mean():+.4f} [{np.percentile(bs, 2.5):+.4f}, {np.percentile(bs, 97.5):+.4f}]"
inv = lambda r: 1.0 / np.asarray(r, float)
LAY = {"C2 NP_H/NP_N (053)": lambda d: (d.view == "c2") & d.set.isin(["NP_H", "NP_N"]), "C2 C/D (f1/f2)": lambda d: (d.view == "c2") & d.set.isin(["C_np_crosslib", "D_np_single"]),
       "C1 G (f1/f2)": lambda d: (d.view == "c1") & (d.set == "G_tims_crosslib"), "C1 panel": lambda d: (d.view == "c1") & (d.set == "P_np250")}
L = ["# 106 ICEBERG pilot (exploratory; fixed before the run)", "", "## (1) truth's rank inside its formula group (rows with >= 2 ICE-scored group members)", "",
     "| layer | rows | group size (median) | within-group MRR main / GL / ICE | ICE beats main (rows) | main beats ICE |", "|---|---:|---:|---|---:|---:|"]
for lab, f in LAY.items():
    d = A[f(A)] if len(A) else A
    if not len(d): continue
    L.append(f"| {lab} | {len(d)} | {d.n_group.median():.0f} | {inv(d.r_main).mean():.3f} / {inv(d.r_gl).mean():.3f} / {inv(d.r_ice).mean():.3f} | {int((d.r_ice < d.r_main).sum())} | {int((d.r_main < d.r_ice).sum())} |")
L += ["", "## (2) main top 25 with formula groups re-ordered by z(main) + 0.5 z(ICE) inside their own slots", "", "| layer | rows | main | delta | rescued / lost |", "|---|---:|---:|---|---|"]
for lab, f in LAY.items():
    d = C[f(C)] if len(C) else C
    if not len(d): continue
    dd = d.ice_grp - d.main
    L.append(f"| {lab} | {len(d)} | {d.main.mean():.4f} | {ci(dd)} | {int((dd > 1e-12).sum())} / {int((dd < -1e-12).sum())} |")
open(os.path.join(P, "x106_icepilot.md"), "w", encoding="utf-8").write(chr(10).join(L) + chr(10)); print(chr(10).join(L))
