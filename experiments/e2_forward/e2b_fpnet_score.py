"""E2b-fp: score the E2b candidate sets with the fold-safe FPNet (the model that never saw each molecule) and compare
fingerprint ranking with the forward models (ICEBERG / GLACIER) on identical same-formula candidate sets.

Usage: python -X utf8 e2b_fpnet_score.py <set_name> <e2_dir> <fold_safe_dir> <v3_code_dir> <folds_dir> <out_json>

Protocol (follows eval_ckpt.py of the fold-safe dataset): up to 8 [M+H]+ spectra of a molecule are merged
(casmi.spectra.merge_spectra), cleaned with fpnet.prep_peaks, encoded by FPNet fold k (k = the molecule's identity fold,
so the model never trained on it); candidate score = f_c . z over the 10,226 selected bits. Ranks use worst-case ties.
Fusions: z-standardised sums within each molecule's candidate set.
"""
import json, math, sys, time
import numpy as np, pandas as pd, torch

NAME, E, FS, V3, FOLDS, OUT = sys.argv[1:7]
sys.path.insert(0, V3)
from casmi import fpnet, chem                      # noqa: E402
from casmi.spectra import merge_spectra           # noqa: E402

t0 = time.time()
bits = np.load(f"{FS}/fp_bits.npy")
fold_of = pd.read_parquet(f"{FOLDS}/structures.parquet")[["inchikey14", "fold_identity"]].drop_duplicates("inchikey14").set_index("inchikey14").fold_identity
items = json.load(open(f"{E}/e2b_{NAME}_in.json"))
ice = json.load(open(f"{E}/e2b_work/ice_{NAME}.json")) if True else {}
gl = json.load(open(f"{E}/e2b_work/gl_{NAME}.json"))
models = {}
dtype = fpnet.autocast_dtype("cuda")


def model_for(k):
    if k not in models:
        models[k] = fpnet.load_model(f"{FS}/fpnet_fold{k}.pt", "cuda")
    return models[k]


def z(x):
    x = np.asarray(x, float); ok = np.isfinite(x); out = np.zeros_like(x)
    if ok.sum() >= 2 and x[ok].std(ddof=1) > 0:
        out[ok] = (x[ok] - x[ok].mean()) / x[ok].std(ddof=1)
    return out


def rr(scores):
    s = np.asarray(scores, float); t = s[0]
    if not np.isfinite(t): return 0.0
    rank = 1 + int(np.sum(s[1:] >= t))
    return 1.0 / rank if rank <= 25 else 0.0


rows, fp_cache, fp_out = [], {}, {}
with torch.no_grad():
    for n, it in enumerate(items):
        mid, cands, spectra = it["mid"], it["cands"], it["spectra"][:8]
        k = int(fold_of.get(mid, 0)) if mid in fold_of.index else 0
        model = model_for(k)
        pairs = [(np.asarray(s["mz"], float), np.asarray(s["it"], float)) for s in spectra]
        if len(pairs) == 1:
            mz, inten = pairs[0]
        else:
            mz, inten = merge_spectra(pairs)
        prec = float(np.median([s["prec"] for s in spectra]))
        ces = [float(np.mean(s["ce_ev"])) for s in spectra if s.get("ce_ev")]
        nm = int(sum(max(1, len(s["ce_ev"] or [])) for s in spectra))
        pm, pi = fpnet.prep_peaks(mz, inten, prec)
        inp = fpnet.collate([dict(mz=pm, it=pi, prec=prec, adduct_ix=chem.adduct_index("[M+H]+"), ce=float(np.mean(ces)) if ces else 0.0,
                                  ce_known=1.0 if ces else 0.0, n_merged=min(nm, 8), mode=1.0)], "cuda")
        with torch.autocast("cuda", dtype=dtype):
            zlog = model(*inp)[0].float()[0].cpu().numpy()
        fps = []
        for s in cands:
            if s not in fp_cache:
                f = chem.raw_fingerprint(s)
                fp_cache[s] = f[bits].astype(np.float32) if f is not None else None
            fps.append(fp_cache[s])
        fp_score = np.array([float(f @ zlog) if f is not None else np.nan for f in fps])
        fp_out[mid] = {s: (float(v) if np.isfinite(v) else None) for s, v in zip(cands, fp_score)}
        ice_s = np.array([(ice.get(mid, {}) or {}).get(s, np.nan) if (ice.get(mid, {}) or {}).get(s) is not None else np.nan for s in cands], float)
        gl_s = np.array([(gl.get(mid, {}) or {}).get(s, np.nan) if (gl.get(mid, {}) or {}).get(s) is not None else np.nan for s in cands], float)
        rows.append(dict(molecule=mid, fold=k, n=len(cands),
                         fp=rr(np.nan_to_num(fp_score, nan=-1e9)), gl=rr(np.nan_to_num(gl_s, nan=-1e9)), ice=rr(np.nan_to_num(ice_s, nan=-1e9)),
                         fp_gl=rr(z(fp_score) + z(gl_s)), fp_ice_gl=rr(z(fp_score) + z(ice_s) + z(gl_s)),
                         fp_2gl=rr(z(fp_score) + 2 * z(gl_s)), gl_ice=rr(z(gl_s) + z(ice_s)),
                         fp_rank=1 + int(np.sum(np.nan_to_num(fp_score[1:], nan=-1e9) >= fp_score[0])) if np.isfinite(fp_score[0]) else None))
        if (n + 1) % 50 == 0:
            print(f"  {n+1}/{len(items)} ({time.time()-t0:.0f}s)", flush=True)
df = pd.DataFrame(rows)
import os
os.makedirs(os.path.join(E, 'e2b_work'), exist_ok=True)
json.dump(fp_out, open(os.path.join(E, 'e2b_work', f'fp_{NAME}.json'), 'w'))
df.to_csv(OUT.replace(".json", "_per_molecule.csv"), index=False)
rng = np.random.default_rng(0)
res = {"set": NAME, "n": len(df), "folds_used": sorted(df.fold.unique().tolist()), "rules": {}}
print(f"{NAME}: {len(df)} molecules | folds used {res['folds_used']} | fp truth rank median {df.fp_rank.median()}")
for rule in ("fp", "ice", "gl", "fp_gl", "fp_2gl", "gl_ice", "fp_ice_gl"):
    v = df[rule].values.astype(float)
    bs = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(4000)]
    res["rules"][rule] = dict(mrr25=float(v.mean()), ci95=[float(np.quantile(bs, .025)), float(np.quantile(bs, .975))], top1=float((v == 1).mean()), hit25=float((v > 0).mean()))
    print(f"  {rule:10s} MRR {v.mean():.4f} CI [{np.quantile(bs,.025):.3f},{np.quantile(bs,.975):.3f}] top1 {(v==1).mean():.3f} hit25 {(v>0).mean():.3f}")
json.dump(res, open(OUT, "w"), indent=1)
print("saved", OUT, f"({time.time()-t0:.0f}s)")
