"""105 stage 2 reading tool: GLACIER-only retrieval of two forward-model runs A (C0' = released weights) and B (adapted) scored on the SAME runner
input (same molecules, candidates, spectra, batching), per (set, view, molecule) of a B1 feature table:
  rr_gl   : 1 / rank of the truth by the GL score among the view's candidates (missing GL = worst; ties pessimistic), 0 beyond rank 25;
  rr_form : the same among the candidates that share the truth's neutral formula (wf_common.neutral_formula) and have a finite GL score;
  top1_form, margin_form = GL(truth) - max GL(same-formula decoys) (NaN without a decoy or a truth score), covered = truth has a GL score.
Only molecules of the selection CSV with a non-empty view list; the same rows for A and B (checked). Paired differences B - A with an
identity bootstrap (4,000). Writes <out>.csv (per row) and <out>.md.
Usage: python gl_only_eval.py --run RUN --set SET --eval_csv CSV --gl_a A.json --gl_b B.json --views c2 [c1] --out OUT"""
import argparse, json, os, sys
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, os.path.join(ROOT, "experiments", "b1_baseline"))
from wf_common import neutral_formula
ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--set", required=True); ap.add_argument("--eval_csv", required=True)
ap.add_argument("--gl_a", required=True); ap.add_argument("--gl_b", required=True); ap.add_argument("--views", nargs="+", default=["c2"]); ap.add_argument("--out", required=True); a = ap.parse_args()
F = pd.read_parquet(os.path.join(a.run, f"b1_features_{a.set}.parquet")); F["molecule"] = F.molecule.astype(str)
M = pd.read_csv(os.path.join(a.run, f"b1_molecules_{a.set}.csv")); M["molecule"] = M.molecule.astype(str); M = M.set_index("molecule")
ev = pd.read_csv(a.eval_csv); ev["molecule"] = ev.molecule.astype(str); mols = ev[ev.set.astype(str) == a.set].molecule.tolist()
GA, GB = json.load(open(a.gl_a)), json.load(open(a.gl_b))
if set(GA) != set(GB): sys.exit("A / B runs cover different molecules")


def rank_pess(vals, i):
    v = np.where(np.isfinite(vals), vals, -np.inf); return int(np.sum(v >= v[i])) if np.isfinite(v[i]) else len(v)


rows = []
for v in a.views:
    keep = F[f"in_short_{v}"].astype(bool)
    if v == "c2": keep &= (F.in_tier | F.in_coconut | F[f"in_train_{v}"]).astype(bool)
    Fv = F[keep]
    for mid in mols:
        if v == "c1" and not bool(M.loc[mid, "c1_usable"]): continue
        g = Fv[Fv.molecule == mid].drop_duplicates("official_key")
        if not len(g) or not g.is_truth.any(): continue
        sm = g.smiles.astype(str).values; tr = np.flatnonzero(g.is_truth.values.astype(bool))[0]; forms = [neutral_formula(s) for s in sm]
        rec = dict(set=a.set, view=v, molecule=mid, n_cand=len(g), n_same_form=int(sum(f == forms[tr] for f in forms)) if forms[tr] else 0)
        for k, G in (("A", GA), ("B", GB)):
            d = G.get(mid) or {}; gl = np.array([np.nan if d.get(s) is None else float(d.get(s)) for s in sm], float)
            r = rank_pess(gl, tr); rec[f"rr_gl_{k}"] = 1.0 / r if r <= 25 else 0.0; rec[f"covered_{k}"] = bool(np.isfinite(gl[tr]))
            same = [j for j in range(len(sm)) if forms[tr] and forms[j] == forms[tr] and np.isfinite(gl[j])]
            if np.isfinite(gl[tr]) and len(same) >= 1:
                sv = gl[same]; ti = same.index(tr); rf = int(np.sum(sv >= sv[ti])); rec[f"rr_form_{k}"] = 1.0 / rf; rec[f"top1_form_{k}"] = float(rf == 1)
                dec = [gl[j] for j in same if j != tr]; rec[f"margin_form_{k}"] = float(gl[tr] - max(dec)) if dec else np.nan
            else: rec[f"rr_form_{k}"] = 0.0; rec[f"top1_form_{k}"] = 0.0; rec[f"margin_form_{k}"] = np.nan
        rows.append(rec)
R = pd.DataFrame(rows); R.to_csv(a.out + ".csv", index=False)
rng = np.random.default_rng(105)
L = [f"# GL-only A vs B: {a.run} {a.set} ({', '.join(a.views)}), A = {a.gl_a}, B = {a.gl_b}", "", "| view | n | metric | A | B | B - A [95%] |", "|---|---:|---|---:|---:|---|"]
for v, r in R.groupby("view"):
    for met in ("rr_gl", "rr_form", "top1_form", "margin_form"):
        x, y = r[f"{met}_A"].values.astype(float), r[f"{met}_B"].values.astype(float); ok = np.isfinite(x) & np.isfinite(y); d = (y - x)[ok]
        if not len(d): continue
        bs = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(4000)]); lo, hi = np.percentile(bs, [2.5, 97.5])
        L.append(f"| {v} | {int(ok.sum())} | {met} | {np.nanmean(x[ok]):.4f} | {np.nanmean(y[ok]):.4f} | {d.mean():+.4f} [{lo:+.4f}, {hi:+.4f}] |")
L.append(""); L.append(f"truth covered A / B: {R.covered_A.mean():.3f} / {R.covered_B.mean():.3f}; median same-formula candidates {R.n_same_form.median():.0f}")
open(a.out + ".md", "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
