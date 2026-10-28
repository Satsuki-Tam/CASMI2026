"""Descriptive, label-using stratification (not a gate, no model change): are development truths whose SCAFFOLD the fold-safe FPNet has seen
(another identity of the same scaffold_group outside the held-out fold) easier than novel-scaffold truths, and does each single evidence degrade
alike? Literature (reports/research/seen_analog_bias_2026-10-29.md): fingerprint predictors collapse on novel scaffolds while forward models
hold up. Per molecule (C2 view): P's main RR (diag/r102_<tag>.csv), FP-only RR over the C2 shortlist (table fp, pessimistic ties), GL-only RR
over the C2 shortlist candidates with a finite GLACIER score (pessimistic ties; molecules without GL listed separately), prior-only RR
(pop_public). Truth unreached in the C2 shortlist -> RR 0 for every evidence. Usage (Spark, experiments/b1_baseline): python -X utf8 x_scafseen.py"""
import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import b1_locked_eval as LE
TAGS = {"f1dev": ("run_f1dev", 1, ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]),
        "np053f1dev": ("run_np053_f1dev", 1, ["NP_H", "NP_X", "NP_N"]),
        "f2dev": ("run_f2dev", 2, ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]),
        "np053f2dev": ("run_np053_f2dev", 2, ["NP_H", "NP_X", "NP_N"])}
ST = pd.read_parquet(os.path.join(ROOT, "data/external/identity_folds/structures.parquet"), columns=["inchikey14", "scaffold_group", "fold_identity", "identity_group"])
sg_of = dict(zip(ST.inchikey14.astype(str), ST.scaffold_group)); ig_of = dict(zip(ST.inchikey14.astype(str), ST.identity_group))
folds_of_sg = ST.groupby("scaffold_group").fold_identity.agg(lambda x: set(x.astype(str))).to_dict()
def rr_of(vals, ti):
    v = np.nan_to_num(np.asarray(vals, float), nan=-1e18); r = int((v >= v[ti]).sum()); return 1.0 / r if r <= 25 else 0.0
rows = []
for tag, (run, K, sets) in TAGS.items():
    R = pd.read_csv(os.path.join(HERE, f"diag/r102_{tag}.csv"), usecols=["set", "view", "molecule", "main"]); R = R[R.view == "c2"]; R["molecule"] = R.molecule.astype(str)
    main = dict(zip(zip(R.set, R.molecule), R.main))
    for s in sets:
        F = pd.read_parquet(os.path.join(HERE, run, f"b1_features_{s}.parquet"), columns=["molecule", "smiles", "is_truth", "in_short_c2", "fp", "pop_public"]); F["molecule"] = F.molecule.astype(str)
        gl, meta, p = LE.runner(os.path.join(HERE, run), s, "gl"); gl = gl or {}
        for mid, f in F.groupby("molecule"):
            sg = sg_of.get(mid); seen = None if sg is None else bool(folds_of_sg.get(sg, set()) - {str(K), "np"})
            f = f[f.in_short_c2.astype(bool)].reset_index(drop=True)
            t = np.flatnonzero(f.is_truth.astype(bool).values)
            rec = dict(tag=tag, set=s, molecule=mid, scaffold_seen=seen, main=main.get((s, mid), np.nan), reached=len(t) > 0)
            if len(t):
                ti = int(t[0]); g = gl.get(mid) or {}
                glv = [g.get(sm) if g.get(sm) is not None else np.nan for sm in f.smiles.astype(str)]
                rec.update(fp_rr=rr_of(f.fp.values, ti), pop_rr=rr_of(f.pop_public.values, ti),
                           gl_rr=(rr_of(glv, ti) if np.isfinite(glv[ti]) else np.nan), has_gl=bool(np.isfinite(glv[ti])))
            else:
                rec.update(fp_rr=0.0, pop_rr=0.0, gl_rr=np.nan, has_gl=False)
            rows.append(rec)
D = pd.DataFrame(rows); D.to_csv(os.path.join(HERE, "diag/x_scafseen.csv"), index=False)
NP = ["NP_H", "NP_X", "NP_N", "D_np_single"]
L = ["# Development truths by scaffold novelty for the fold-safe FPNet (C2 view; descriptive, label-using)", "",
     "scaffold seen = another identity of the truth's scaffold_group sits in a training fold of that FPNet (fold_identity not the held-out fold, not 'np').", "",
     "| strata | scaffold | n | reached | P main | FP-only | prior-only | GL-only (rows with GL) | rows with GL |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
for lab, g0 in (("NP (np053 H/X/N, D)", D[D.set.isin(NP)]), ("other (C, E, F, G)", D[~D.set.isin(NP)])):
    for k, g in g0.groupby(g0.scaffold_seen.map({True: "seen", False: "novel", None: "unknown"})):
        hg = g[g.has_gl]
        L.append(f"| {lab} | {k} | {len(g)} | {g.reached.mean():.2f} | {g.main.mean():.3f} | {g.fp_rr.mean():.3f} | {g.pop_rr.mean():.3f} | {hg.gl_rr.mean():.3f} (P {hg.main.mean():.3f}, FP {hg.fp_rr.mean():.3f}) | {len(hg)} |")
open(os.path.join(HERE, "diag/x_scafseen.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
