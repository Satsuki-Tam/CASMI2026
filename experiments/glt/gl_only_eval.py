"""105 stage 2 reading tool: GLACIER-only retrieval of two forward-model runs A (C0' = released weights) and B (adapted) scored on the SAME runner
input (same molecules, candidates, spectra, batch plan), per (set, view, molecule) of a B1 feature table.
v2 (Codex 134, before any stage-2 result):
  - denominator = the FULL selection roster of the set: a molecule with an empty view list or whose truth is not in the view list stays with
    0 for both runs (flags empty / truth_absent); nothing is dropped;
  - rr_gl   = 1 / rank of the truth by the GL score among the view's candidates (ties pessimistic), 0 beyond rank 25, and 0 when the truth has
              no GL score (v1 returned rank = len(list) there);
  - rr_form = 1 / rank of the truth among the candidates of the truth's neutral formula (wf_common.neutral_formula) with a finite GL score, NOT
              truncated (a capability diagnostic that uses the truth's formula; not a retrieval MRR), 0 when the truth has no GL score;
  - comparability: the (molecule, SMILES) pairs with a non-null score must be IDENTICAL in A and B and both runs must have the same runner
    status / scored-molecule counts (meta), else STOP -- a decoy that B failed to score must not raise rr_form;
  - the view list must have unique official keys per molecule (no silent de-duplication); rows = molecules = identities (bootstrap unit).
v2.1 (2026-10-29 23:20 JST, technical fix after the first 134 reader run stopped while WRITING the summary table, before any result was read): r.empty is
pandas DataFrame.empty (a bool), so the column is read as r["empty"]; the per-molecule table (written before that line) is unchanged.
Reported per view: n, rr_gl / rr_form / top1_form / margin_form for A and B with B - A and an identity bootstrap (4,000, seed 105), molecules
with >= 2 same-formula competitors, singletons, truth / decoy GL coverage. Writes <out>.csv and <out>.md.
Usage: python gl_only_eval.py --run RUN --set SET --eval_csv CSV --gl_a A.json --gl_b B.json --views c2 [c1] --out OUT"""
import argparse, json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, os.path.join(ROOT, "experiments", "b1_baseline"))
from wf_common import neutral_formula
ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--set", required=True); ap.add_argument("--eval_csv", required=True)
ap.add_argument("--gl_a", required=True); ap.add_argument("--gl_b", required=True); ap.add_argument("--views", nargs="+", default=["c2"]); ap.add_argument("--out", required=True); a = ap.parse_args()
def stop(m): sys.exit(f"STOP (gl_only_eval): {m}")
F = pd.read_parquet(os.path.join(a.run, f"b1_features_{a.set}.parquet")); F["molecule"] = F.molecule.astype(str)
M = pd.read_csv(os.path.join(a.run, f"b1_molecules_{a.set}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
ev = pd.read_csv(a.eval_csv); ev["molecule"] = ev.molecule.astype(str); mols = ev[ev.set.astype(str) == a.set].molecule.tolist()
if len(mols) != len(set(mols)): stop("duplicate molecules in the selection")
GA, GB = json.load(open(a.gl_a)), json.load(open(a.gl_b))
for p_ in (a.gl_a, a.gl_b):   # runner meta of both runs
    if not os.path.exists(p_ + ".meta.json"): stop(f"runner meta missing for {p_}")
MA, MB = json.load(open(a.gl_a + ".meta.json")), json.load(open(a.gl_b + ".meta.json"))
for k in ("n_mols", "n_mols_scored"):
    if MA.get(k) != MB.get(k): stop(f"runner meta differs in {k}: {MA.get(k)} vs {MB.get(k)}")
if MA.get("status") not in ("ok", "partial") or MB.get("status") not in ("ok", "partial"): stop(f"runner status {MA.get('status')} / {MB.get('status')}")
nonnull = lambda G: {(m, s) for m, d in G.items() for s, v in (d or {}).items() if v is not None}
if set(GA) != set(GB) or nonnull(GA) != nonnull(GB): stop("A and B do not score the same (molecule, SMILES) pairs")


def rank_pess(vals, i):
    v = np.where(np.isfinite(vals), vals, -np.inf)
    return int(np.sum(v >= v[i])) if np.isfinite(vals[i]) else None   # None = the truth has no score


rows = []
for v in a.views:
    keep = F[f"in_short_{v}"].astype(bool)
    if v == "c2": keep &= (F.in_tier | F.in_coconut | F[f"in_train_{v}"]).astype(bool)
    Fv = F[keep]
    for mid in mols:
        if v == "c1" and not bool(M.loc[mid, "c1_usable"]): continue
        g = Fv[Fv.molecule == mid]
        if g.official_key.astype(str).duplicated().any(): stop(f"{mid}: duplicate official keys in the view list")
        rec = dict(set=a.set, view=v, molecule=mid, n_cand=len(g), empty=len(g) == 0, truth_absent=bool(len(g)) and not g.is_truth.any())
        if rec["empty"] or rec["truth_absent"]:
            rec.update(n_same_form=0, rr_gl_A=0.0, rr_gl_B=0.0, rr_form_A=0.0, rr_form_B=0.0, top1_form_A=0.0, top1_form_B=0.0, margin_form_A=np.nan, margin_form_B=np.nan, covered_A=False, covered_B=False,
                       decoy_cov_A=np.nan, decoy_cov_B=np.nan); rows.append(rec); continue
        sm = g.smiles.astype(str).values; tr = int(np.flatnonzero(g.is_truth.values.astype(bool))[0]); forms = [neutral_formula(s) for s in sm]
        rec["n_same_form"] = int(sum(f == forms[tr] for f in forms)) if forms[tr] else 0
        for k, G in (("A", GA), ("B", GB)):
            d = G.get(mid) or {}; gl = np.array([np.nan if d.get(s) is None else float(d.get(s)) for s in sm], float)
            r = rank_pess(gl, tr); rec[f"rr_gl_{k}"] = (1.0 / r if r <= 25 else 0.0) if r is not None else 0.0; rec[f"covered_{k}"] = r is not None
            same = [j for j in range(len(sm)) if forms[tr] and forms[j] == forms[tr]]; rec[f"decoy_cov_{k}"] = float(np.mean([np.isfinite(gl[j]) for j in same if j != tr])) if len(same) > 1 else np.nan
            fin = [j for j in same if np.isfinite(gl[j])]
            if r is not None and fin:
                sv = gl[fin]; ti = fin.index(tr); rf = int(np.sum(sv >= sv[ti])); rec[f"rr_form_{k}"] = 1.0 / rf; rec[f"top1_form_{k}"] = float(rf == 1)
                dec = [gl[j] for j in fin if j != tr]; rec[f"margin_form_{k}"] = float(gl[tr] - max(dec)) if dec else np.nan
            else: rec[f"rr_form_{k}"] = 0.0; rec[f"top1_form_{k}"] = 0.0; rec[f"margin_form_{k}"] = np.nan
        rows.append(rec)
R = pd.DataFrame(rows); R.to_csv(a.out + ".csv", index=False)
rng = np.random.default_rng(105)
L = [f"# GL-only A vs B: {os.path.basename(a.run)} {a.set} ({', '.join(a.views)}), A = {os.path.basename(a.gl_a)}, B = {os.path.basename(a.gl_b)}", "",
     "| view | n | metric | A | B | B - A [95%] |", "|---|---:|---|---:|---:|---|"]
for v, r in R.groupby("view"):
    for met in ("rr_gl", "rr_form", "top1_form", "margin_form"):
        x, y = r[f"{met}_A"].values.astype(float), r[f"{met}_B"].values.astype(float); ok = np.isfinite(x) & np.isfinite(y); d = (y - x)[ok]
        if not len(d): continue
        bs = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]); lo, hi = np.percentile(bs, [2.5, 97.5])
        L.append(f"| {v} | {int(ok.sum())} | {met} | {np.nanmean(x[ok]):.4f} | {np.nanmean(y[ok]):.4f} | {d.mean():+.4f} [{lo:+.4f}, {hi:+.4f}] |")
    L.append(f"| {v} | {len(r)} | roster: empty {int(r['empty'].sum())}, truth absent {int(r.truth_absent.sum())}, truth covered A / B {int(r.covered_A.sum())} / {int(r.covered_B.sum())}, "
             f">= 2 same-formula competitors {int((r.n_same_form >= 3).sum())}, singletons {int((r.n_same_form == 1).sum())}, decoy GL coverage A / B {r.decoy_cov_A.mean():.3f} / {r.decoy_cov_B.mean():.3f} | | | |")
open(a.out + ".md", "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
