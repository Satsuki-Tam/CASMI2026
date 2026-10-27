"""089 stage (a) evaluation under the Codex 088 contract (separate from training; the head is read from dreams_fp_f<k>/head.pt).
Evaluation units: fold-k identities (identity_folds fold_identity == k, not panel, structure in the v2 pool) x library x polarity; per unit the query
spectra are chosen as in production (test adducts only, select_queries round-robin, max 8, store-row order). Candidate set: pool structures inside the
union of +-10 ppm windows around each adduct's median neutral mass (query-derived, the truth may be outside = 'unreached', RR 0 for every method).
Scores (all on the same candidate set, raw f.z = packed pool FP . logits):
  F  = fold-safe FPNet fold k on the production input (spectra of the unit merged with merge_spectra, median precursor, most common adduct, mean CE,
       n_merged = min(n, 8)) -- the PRIMARY control (F_current)
  Fs = the same FPNet, single-spectrum inputs, logits averaged (diagnostic)
  D  = DreaMS-FP head, per-spectrum logits averaged
  E  = z(F) + z(D) (PRIMARY fusion; z over the candidate set, std 0 -> 0); diagnostics E05 = z(F) + 0.5 z(D), ES = z(Fs) + z(D), D alone
Ranks: score descending, ties broken by pool index ascending (truth-independent); RR@25. Same-formula rank (candidates with the truth's formula) is a
diagnostic only. Missing D (no embedded spectrum in the unit) -> E = F (fixed beforehand; counted).
Evaluation set (fixed before results): every COCONUT-truth identity of fold k + 5,000 non-COCONUT identities drawn with seed 0.
Identity score = mean RR over its units (equal unit weight). Output: <out>/units.csv, <out>/summary.json.
Usage: python -X utf8 dreams_fp_eval.py --fold 1 --head dreams_fp_f1/head.pt --out dreams_fp_eval_f1
"""
import argparse, json, os, sys, time
from collections import Counter
import numpy as np, polars as pl, torch, torch.nn as nn
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries
sys.path.insert(0, f"{ROOT}/data/external/v3_models/code")
from casmi import fpnet as FPN, chem as CH
from casmi.spectra import merge_spectra
ap = argparse.ArgumentParser(); ap.add_argument("--fold", type=int, required=True); ap.add_argument("--head", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--fpnet", default=""); ap.add_argument("--emb_dir", default=f"{ROOT}/data/processed/dreams_emb"); ap.add_argument("--n_noncoco", type=int, default=5000)
ap.add_argument("--max_spectra", type=int, default=8); ap.add_argument("--limit", type=int, default=0)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); dev = "cuda"; t0 = time.time()
def log(*x): print(time.strftime("%H:%M:%S"), *x, flush=True)
HW = f"{ROOT}/data/external/harness_work"; ST = f"{ROOT}/data/processed/spectra_store"
meta = pl.read_parquet(f"{ST}/spec_meta.parquet", columns=["row", "scorer_ik14", "ingest_lib", "adduct", "ionization_mode", "ce_mean", "precursor_mz"]).sort("row")
folds = pl.read_parquet(f"{ROOT}/data/external/identity_folds/spectra_folds.parquet", columns=["row", "fold_identity", "identity_group"])
meta = meta.join(folds, on="row", how="left").sort("row")
pool = pl.read_parquet(f"{HW}/pool_meta.parquet", columns=["key", "mass", "src", "formula"]); pmass = pool["mass"].to_numpy().astype(np.float64)
psrc = pool["src"].to_numpy(); pform = pool["formula"].to_numpy(); k2p = dict(zip(pool["key"].to_list(), range(pool.height)))
key = meta["scorer_ik14"].to_list(); pid = np.array([k2p.get(k, -1) for k in key], np.int64)
fold = meta["fold_identity"].to_numpy(); lib = meta["ingest_lib"].to_numpy(); add = meta["adduct"].to_numpy(); modes = meta["ionization_mode"].to_numpy()
ce = meta["ce_mean"].to_numpy().astype(np.float64); prec = meta["precursor_mz"].to_numpy().astype(np.float64); igrp = meta["identity_group"].to_numpy()
panel_g = set(meta.filter(pl.col("ingest_lib") == "enveda-np-examples")["identity_group"].to_list())
OK = np.load(f"{a.emb_dir}/ok.npy"); EMB = np.load(f"{a.emb_dir}/emb_f16.npy", mmap_mode="r")
MZ = np.load(f"{ST}/spec_mz.npy", mmap_mode="r"); IT = np.load(f"{ST}/spec_int.npy", mmap_mode="r"); OFF = np.load(f"{ST}/spec_off.npy")
# ---- evaluation identities (fixed rule): all COCONUT truths of fold k + n_noncoco others (seed 0)
elig = np.where((fold == a.fold) & (pid >= 0) & ~np.isin(igrp, np.array(sorted(panel_g))) & np.isin(add, list(ADDUCT_SHIFT)))[0]
ids = np.unique(pid[elig]); coco = np.isin(psrc[ids], [2, 3])
rng = np.random.default_rng(0); nonc = ids[~coco]; nonc = np.sort(rng.choice(nonc, min(a.n_noncoco, len(nonc)), replace=False))
EV = set(ids[coco].tolist()) | set(nonc.tolist())
if a.limit: EV = set(sorted(EV)[:a.limit])
units = {}
for r in elig:
    p_ = int(pid[r])
    if p_ in EV: units.setdefault((p_, str(lib[r]), str(modes[r])), []).append(int(r))
log(f"fold {a.fold}: identities {len(EV)} (COCONUT {int(coco.sum())}, non-COCONUT sample {len(nonc)}), units {len(units)}")
# ---- models
ck = torch.load(a.head, map_location="cpu", weights_only=True)
class Head(nn.Module):
    def __init__(s, din, h, nout, drop):
        super().__init__(); s.ln = nn.LayerNorm(din)
        s.net = nn.Sequential(nn.Linear(din, h), nn.GELU(), nn.Dropout(drop), nn.Linear(h, h), nn.GELU(), nn.Dropout(drop), nn.Linear(h, nout))
    def forward(s, x): return s.net(s.ln(x))
head = Head(ck["din"], ck["hidden"], ck["nbits"], ck["drop"]); head.load_state_dict(ck["state"]); head.to(dev).eval()
ADD = list(ck["adducts"]); assert ADD == list(ADDUCT_SHIFT) and ck["holdout_fold"] == a.fold, (ck["holdout_fold"], a.fold)
fp_model = FPN.load_model(a.fpnet or f"{ROOT}/data/external/fold_safe_fpnet/fpnet_fold{a.fold}.pt", dev); dt = FPN.autocast_dtype(dev)
PFP = torch.from_numpy(np.load(f"{HW}/pool_fp.npy")).to(dev); nbits = int(ck["nbits"])
SH = torch.arange(7, -1, -1, device=dev, dtype=torch.uint8)
def unpack(p): return ((p.unsqueeze(-1) >> SH) & 1).reshape(*p.shape[:-1], -1)[..., :nbits].float()
def side(rows):
    S = np.zeros((len(rows), len(ADD) + 4), np.float32)
    for j, r in enumerate(rows):
        S[j, ADD.index(add[r]) if add[r] in ADD else len(ADD)] = 1.0; S[j, len(ADD) + 1] = -1.0 if modes[r] == "negative" else 1.0
        if np.isfinite(ce[r]): S[j, len(ADD) + 2] = 1.0; S[j, len(ADD) + 3] = ce[r] / 100.0
    return S
def spec(r, sh): return np.asarray(MZ[OFF[r]:OFF[r + 1]], np.float64) - sh, np.asarray(IT[OFF[r]:OFF[r + 1]], np.float64)
def zs(x):
    s = x.std(); return (x - x.mean()) / s if s > 0 else np.zeros_like(x)
def rank_of(score, t, order_pid):
    # descending score, ties -> smaller pool index first (truth-independent)
    better = (score > score[t]) | ((score == score[t]) & (order_pid < order_pid[t]))
    return int(better.sum() + 1)
rows_out = []
with torch.no_grad():
    for n_u, ((p_, lb, md), rr) in enumerate(sorted(units.items())):
        q = select_queries(sorted(rr), a.max_spectra, lambda x: add[x], lambda x: float(ce[x]))
        sh = ELECTRON if (lb == "enveda-180" and md == "positive") else 0.0
        # query-derived windows (per-adduct median neutral mass), union over adducts
        Mb = {}
        for x in q: Mb.setdefault(add[x], []).append(prec[x] - sh + ADDUCT_SHIFT[add[x]])
        cand = set()
        for M in (float(np.median(v)) for v in Mb.values()):
            tol = M * 10e-6; lo = int(np.searchsorted(pmass, M - tol, "left")); hi = int(np.searchsorted(pmass, M + tol, "right")); cand.update(range(lo, hi))
        cand = np.array(sorted(cand), np.int64); reached = p_ in set(cand.tolist())
        row = dict(pid=p_, lib=lb, mode=md, n_q=len(q), n_cand=len(cand), reached=reached, coco=bool(psrc[p_] in (2, 3)),
                   addcls=("H" if add[q[0]] in ("[M+H]+", "[M-H]-") else ("Na" if add[q[0]] == "[M+Na]+" else "other")))
        if not reached or len(cand) == 0:
            for c in ("F", "Fs", "D", "E", "E05", "ES"): row[f"rr_{c}"] = 0.0
            row["d_ok"] = False; rows_out.append(row); continue
        # F (production merged input)
        pairs = [spec(x, sh) for x in q]; mz, it = pairs[0] if len(pairs) == 1 else merge_spectra(pairs)
        pr = float(np.median([prec[x] - sh for x in q])); ces = [ce[x] for x in q if np.isfinite(ce[x])]
        ad = Counter(add[x] for x in q).most_common(1)[0][0]; pm, pi = FPN.prep_peaks(mz, it, pr)
        items = [dict(mz=pm, it=pi, prec=pr, adduct_ix=CH.adduct_index(ad), ce=float(np.mean(ces)) if ces else 0.0, ce_known=1.0 if ces else 0.0,
                      n_merged=min(len(q), 8), mode=1.0 if md == "positive" else -1.0)]
        for x in q:   # Fs singles
            m1, i1 = spec(x, sh); pm1, pi1 = FPN.prep_peaks(m1, i1, prec[x] - sh); ck_ = bool(np.isfinite(ce[x]))
            items.append(dict(mz=pm1, it=pi1, prec=prec[x] - sh, adduct_ix=CH.adduct_index(add[x]), ce=float(ce[x]) if ck_ else 0.0, ce_known=1.0 if ck_ else 0.0, n_merged=1,
                              mode=1.0 if md == "positive" else -1.0))
        inp = FPN.collate(items, dev)
        with torch.autocast("cuda", dtype=dt): Z = fp_model(*inp)[0].float()
        zF = Z[0]; zFs = Z[1:].mean(0)
        qd = [x for x in q if OK[x]]; row["d_ok"] = bool(qd)
        W = unpack(PFP[torch.as_tensor(cand, device=dev)]); t = int(np.flatnonzero(cand == p_)[0])
        sF = (W @ zF).cpu().numpy(); sFs = (W @ zFs).cpu().numpy()
        if qd:
            x_ = torch.cat([torch.from_numpy(np.asarray(EMB[qd], np.float32)), torch.from_numpy(side(qd))], 1).to(dev)
            sD = (W @ head(x_).float().mean(0)).cpu().numpy()
            sc = dict(F=sF, Fs=sFs, D=sD, E=zs(sF) + zs(sD), E05=zs(sF) + 0.5 * zs(sD), ES=zs(sFs) + zs(sD))
        else:
            sc = dict(F=sF, Fs=sFs, D=np.zeros_like(sF), E=zs(sF), E05=zs(sF), ES=zs(sFs))
        for c, s_ in sc.items():
            r_ = rank_of(s_, t, cand); row[f"rr_{c}"] = 1.0 / r_ if r_ <= 25 else 0.0; row[f"rank_{c}"] = r_
        sf = pform[cand] == pform[p_]; idx = np.flatnonzero(sf); tt = int(np.flatnonzero(idx == t)[0]); row["n_sameform"] = int(sf.sum())
        for c in ("F", "D", "E"):
            r_ = rank_of(sc[c][idx], tt, cand[idx]); row[f"rrsf_{c}"] = 1.0 / r_ if r_ <= 25 else 0.0
        rows_out.append(row)
        if n_u % 2000 == 0: log(f"{n_u}/{len(units)} units ({time.time() - t0:.0f}s)")
U = pl.DataFrame(rows_out); U.write_csv(f"{a.out}/units.csv")
I = U.group_by("pid").agg(pl.col("coco").first(), *[pl.col(f"rr_{c}").mean() for c in ("F", "Fs", "D", "E", "E05", "ES")], pl.len().alias("n_units"))
summ = dict(fold=a.fold, identities=I.height, units=U.height, spectra=int(U["n_q"].sum()), reached_units=int(U["reached"].sum()), d_missing_units=int((~U["d_ok"]).sum()),
            seconds=round(time.time() - t0))
for name, f in (("coco", pl.col("coco")), ("noncoco", ~pl.col("coco"))):
    J = I.filter(f); summ[name] = dict(n=J.height, **{c: round(float(J[f"rr_{c}"].mean()), 4) for c in ("F", "Fs", "D", "E", "E05", "ES")})
json.dump(summ, open(f"{a.out}/summary.json", "w"), indent=1); log(json.dumps(summ))
