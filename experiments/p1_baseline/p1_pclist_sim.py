"""P1 add-on (v2, after Codex 004) -- simulate the public notebook's PubChem-only channel list on the P1 shortlists and compare
list-ordering rules with the REAL public rerank function.

Public notebook (casmi26-baseline-v18, PubChem-only channel): K = 25 structures whose official scorer key is NOT in the candidate pool
(train structures AND COCONUT, 710,701 keys), ordered by z(f.z) + 0.15 * pop; GLACIER/ICEBERG re-score only same-formula groups inside
the top 25, slot-preserving (gl_fuse.rerank_multi); the list is then interleaved into the base list at slots [2,4,6,8,10,24] or
[4,8,12,16,20,24] (promotion to rank 1 when S > 6 and pop >= 5 or rel > 150), so only the PC top-6 can reach the final list.
Here: PC list = P1 shortlist candidates whose official key is not in the v2 pool (the truth's own TRAIN membership is hidden, but a truth
that is in the pool's COCONUT part would be a pool candidate in the notebook and is therefore NOT in the PC list -> PC RR 0, flagged),
ordered by z(fp) + 0.15 pop (z over the PC-eligible shortlist rows -- not the notebook's pass-2 set; documented limitation), cut at K.
Rules compared on the SAME list: base order, the real gl_fuse.rerank_multi (gl / ice+gl, top 25), whole-list z-sum fusions.
RR@25 by official identity, worst-case ties; strict class-2: molecules whose truth is reachable only via train structures = 0.
Also reports top-1 and hit@6 (the PC positions that can enter the final list through the slots).
Usage: python -X utf8 p1_pclist_sim.py --run DIR --set A_timstof --pool pool_meta.parquet --glacier DIR [--out DIR] [--exclude_v1 CSV ...]
"""
import argparse, json, os, sys
import numpy as np, pandas as pd, polars as pl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p1_evaluate import z, formula_of, boot, LAM

ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--set", required=True); ap.add_argument("--out", default=None)
ap.add_argument("--pool", required=True); ap.add_argument("--glacier", required=True); ap.add_argument("--exclude_v1", nargs="*", default=[])
a = ap.parse_args(); out = a.out or f"{a.run}/results"; os.makedirs(out, exist_ok=True)
sys.path.insert(0, a.glacier); import gl_fuse  # noqa: E402  (the real public rerank function)
sl = pd.read_parquet(f"{a.run}/p1_shortlist_{a.set}.parquet"); fun = pd.read_csv(f"{a.run}/p1_funnel_{a.set}.csv").set_index("molecule")
mols = pd.read_csv(f"{a.run}/p1_molecules.csv").set_index("molecule")
pool = pl.read_parquet(a.pool, columns=["key", "src"])
pool_keys = set(pool["key"].to_list()); pool_ext_keys = set(pool.filter(pl.col("src").is_in([2, 3]))["key"].to_list())
used_v1 = set()
for f in a.exclude_v1:
    d = pd.read_csv(f); used_v1 |= set(d["molecule"].astype(str)) if "molecule" in d.columns else set()
gl = json.load(open(f"{a.run}/work/gl_{a.set}.json")) if os.path.exists(f"{a.run}/work/gl_{a.set}.json") else {}
ice = json.load(open(f"{a.run}/work/ice_{a.set}.json")) if os.path.exists(f"{a.run}/work/ice_{a.set}.json") else {}


def complete(path):
    try: return json.load(open(path + ".meta.json")).get("status") == "ok"
    except Exception: return False


gl_ok = complete(f"{a.run}/work/gl_{a.set}.json"); ice_ok = complete(f"{a.run}/work/ice_{a.set}.json")
if not ice_ok: ice = {}


def getv(d, mid, smiles):
    dd = d.get(mid) or {}
    return np.array([np.nan if dd.get(s) is None else float(dd.get(s)) for s in smiles], float)


def rr_scores(scores, is_t):
    s = np.nan_to_num(np.asarray(scores, float), nan=-1e18)
    if not is_t.any(): return 0.0, None
    rank = int(np.sum(s >= s[is_t][0])); return (1.0 / rank if rank <= 25 else 0.0), rank


def rr_order(order, is_t):
    pos = [i for i, c in enumerate(order) if is_t[c]]
    if not pos: return 0.0, None
    return (1.0 / (pos[0] + 1) if pos[0] < 25 else 0.0), pos[0] + 1


sl["_in_pool"] = sl.official_key.isin(pool_keys); sl["_in_pool_ext"] = sl.official_key.isin(pool_ext_keys)   # once (isin with a 710k set per molecule is very slow)
rows = []
for mid, g0 in sl.groupby("molecule", sort=False):
    in_pool = g0._in_pool.values; in_ext = g0._in_pool_ext.values; is_truth0 = g0.is_truth.values.astype(bool)
    truth_in_pool_coconut = bool((is_truth0 & in_ext).any())
    keep = ~in_pool | (is_truth0 & ~in_ext)      # truth: hide its train membership only
    g = g0[keep].reset_index(drop=True)
    rec = dict(molecule=mid, n_pc_eligible=len(g), truth_in_pc_eligible=bool(g.is_truth.any()), truth_in_pool_coconut=truth_in_pool_coconut,
               n_shortlist_in_pool_nontruth=int((in_pool & ~is_truth0).sum()), used_in_e2b_v1=mid in used_v1)
    if len(g) == 0: rows.append(rec); continue
    fp = g.fp.values.astype(float); pop = g.pop_public.values.astype(float); is_t_all = g.is_truth.values.astype(bool)
    glv = getv(gl, mid, g.smiles); icv = getv(ice, mid, g.smiles) if ice else None
    base_all = z(fp) + LAM * pop
    order0 = np.argsort(-base_all, kind="stable")
    for K in (25, 60, 100):
        idx = order0[:K]; is_t = is_t_all[idx]; b = base_all[idx]; gv = glv[idx]; iv = icv[idx] if icv is not None else None
        smis = [str(s) for s in g.smiles.values[idx]]; keys = [str(k) for k in g.official_key.values[idx]]; forms = [formula_of(s) for s in smis]
        gl_list = [None if not np.isfinite(v) else float(v) for v in gv]
        ice_list = [None if not np.isfinite(v) else float(v) for v in iv] if iv is not None else None
        rec[f"K{K} truth_in_list"] = bool(is_t.any()); rec[f"K{K} gl_covered"] = float(np.isfinite(gv).mean())
        res = {}
        res["base fp+0.15pop"] = rr_scores(b, is_t)
        res["public rerank_multi(gl)"] = rr_order(gl_fuse.rerank_multi(smis, keys, list(map(float, b)), forms, [gl_list], [1.0], top_n=25), is_t)
        if ice_list is not None:
            res["public rerank_multi(ice,gl) = E0"] = rr_order(gl_fuse.rerank_multi(smis, keys, list(map(float, b)), forms, [ice_list, gl_list], [1.0, 1.0], top_n=25), is_t)
        for w in (1.0, 1.5, 2.0, 3.0):
            res[f"global z(base)+{w:g}z(gl)"] = rr_scores(z(b) + w * z(gv), is_t)
        if iv is not None:
            for wg, wi in ((1.0, 1.0), (2.0, 1.0), (2.0, 2.0), (1.5, 1.0)):
                res[f"global z(base)+{wg:g}z(gl)+{wi:g}z(ice)"] = rr_scores(z(b) + wg * z(gv) + wi * z(iv), is_t)
        for name, (rr, rank) in res.items():
            rec[f"K{K} {name}"] = rr; rec[f"K{K} {name} @top1"] = float(rank == 1) if rank else 0.0; rec[f"K{K} {name} @hit6"] = float(rank is not None and rank <= 6)
    rows.append(rec)
df = pd.DataFrame(rows).set_index("molecule").reindex(fun.index)
reach = mols.loc[df.index, "window_external"].astype(bool).values
fresh = ~df.used_in_e2b_v1.fillna(False).astype(bool).values
rule_cols = [c for c in df.columns if c.startswith("K") and not c.endswith(("truth_in_list", "gl_covered", "@top1", "@hit6"))]
for c in [c for c in df.columns if c.startswith("K") and (c.endswith(("@top1", "@hit6")) or c in rule_cols)]: df[c] = df[c].fillna(0.0)
N = len(df)
md = [f"## PC-list simulation v2 {a.set} (N={N}; pool condition = official key not in the 710,701-key v2 pool; real gl_fuse.rerank_multi; GL complete {gl_ok}, ICE complete {ice_ok})",
      f"truth in the PC-eligible set {int(df.truth_in_pc_eligible.fillna(False).sum())}/{N}; truth is a pool-COCONUT structure (handled by the pool route, PC RR = 0) {int(df.truth_in_pool_coconut.fillna(False).sum())}; "
      f"molecules used in E2b v1 {int((~fresh).sum())} (excluded from the 'fresh' column); n reachable (strict) {int(reach.sum())}", "",
      "| K | rule | MRR@25 | 95% CI | strict | fresh | top-1 | hit@6 | Δ vs E0 rule | Δ strict |", "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
res_out = {}
for K in (25, 60, 100):
    refname = f"K{K} public rerank_multi(ice,gl) = E0" if f"K{K} public rerank_multi(ice,gl) = E0" in df.columns else f"K{K} public rerank_multi(gl)"
    ref = df[refname].values.astype(float)
    md.append(f"| {K} | truth in list {df[f'K{K} truth_in_list'].fillna(False).astype(bool).mean():.3f}; GL covered {df[f'K{K} gl_covered'].mean():.3f} | | | | | | | | |")
    for c in [c for c in rule_cols if c.startswith(f"K{K} ")]:
        v = df[c].values.astype(float); d = v - ref; ci = boot(v); dci = boot(d); ds = boot(d * reach)
        res_out[c] = dict(mrr25=float(v.mean()), ci95=ci, strict=float((v * reach).mean()), fresh=float(v[fresh].mean()), top1=float(df[c + " @top1"].mean()), hit6=float(df[c + " @hit6"].mean()),
                          delta_vs_e0=float(d.mean()), delta_ci95=dci, delta_strict=float((d * reach).mean()), delta_strict_ci95=ds, reference=refname)
        md.append(f"| {K} | {c[len(f'K{K} '):]} | {v.mean():.3f} | [{ci[0]:.3f},{ci[1]:.3f}] | {(v * reach).mean():.3f} | {v[fresh].mean():.3f} | {df[c + ' @top1'].mean():.3f} | {df[c + ' @hit6'].mean():.3f} | "
                  f"{d.mean():+.3f} [{dci[0]:+.3f},{dci[1]:+.3f}] | {(d * reach).mean():+.3f} [{ds[0]:+.3f},{ds[1]:+.3f}] |")
json.dump(res_out, open(f"{out}/pclist_v2_{a.set}.json", "w"), indent=1); df.to_csv(f"{out}/pclist_v2_{a.set}_per_molecule.csv")
open(f"{out}/pclist_v2_{a.set}.md", "w", encoding="utf-8").write("\n".join(md)); print("\n".join(md))
