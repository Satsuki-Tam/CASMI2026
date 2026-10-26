"""Learned spectral similarity (own MS2DeepScore-type model, 040): spectrum -> embedding whose cosine approximates the Morgan (r2, 2048)
Tanimoto similarity of the two structures. Trained on train.parquet spectra only; every identity group of the evaluation / confirmation /
ranker-fit files is excluded (and recorded), so evaluation molecules are unseen by this model.

Input: 0.1 Da bins over m/z [10, 1000) of the top-100 peaks (sqrt of relative intensity, L2-normalised) + a polarity flag.
Pairs: anchor spectrum of a random training key; partner = a spectrum (same polarity) of one of the anchor key's 32 nearest structures
(probability P_NEAR) or of a random key; loss = MSE(cos, Tanimoto) re-weighted towards uniform over 10 Tanimoto bins.
Validation: fixed pairs among held-out training keys (never used for fitting): Pearson / Spearman of predicted vs true Tanimoto, and the
same statistics for the entropy similarity (+ precursor shift, b1_analog) on a subset — the 040 sanity condition.
Usage: python -X utf8 ls_train.py --out_dir experiments/b1_baseline/ls_v1 --exclude CSV ... [--steps 60000]
"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
from b1_common import ADDUCT_SHIFT, ELECTRON  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--store", default="data/processed/spectra_store")
ap.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
ap.add_argument("--folds", default="data/external/identity_folds/structures.parquet")
ap.add_argument("--exclude", nargs="+", required=True); ap.add_argument("--out_dir", required=True)
ap.add_argument("--steps", type=int, default=60000); ap.add_argument("--bs", type=int, default=512); ap.add_argument("--lr", type=float, default=1e-3)
ap.add_argument("--cap_per_key", type=int, default=5); ap.add_argument("--val_frac", type=float, default=0.02); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--p_near", type=float, default=0.6); ap.add_argument("--eval_every", type=int, default=2000)
a = ap.parse_args()
os.makedirs(a.out_dir, exist_ok=True); T0 = time.time(); rng = np.random.default_rng(a.seed)
def log(*x): print(f"[ls {time.time() - T0:6.0f}s]", *x, flush=True)
NB, MZ0, BW, TOPK = 9900, 10.0, 0.1, 100

# ---------------------------------------------------------------- exclusions (identity groups of every evaluation file)
idf = pd.read_parquet(f"{ROOT}/{a.folds}", columns=["inchikey14", "scorer_key", "identity_group"]).dropna()
used = set()
for f in a.exclude:
    d = pd.read_csv(f if os.path.isabs(f) else os.path.join(ROOT, f))
    for c in ("molecule", "scorer_key", "raw_key", "inchikey14"):
        if c in d.columns: used |= set(d[c].dropna().astype(str))
grp_used = set(idf[idf.inchikey14.astype(str).isin(used) | idf.scorer_key.astype(str).isin(used)].identity_group)
excl_keys = set(idf[idf.identity_group.isin(grp_used)].scorer_key.astype(str)) | used
log(f"exclusion: {len(used):,} listed identities -> {len(grp_used):,} identity groups -> {len(excl_keys):,} excluded keys")

# ---------------------------------------------------------------- spectra and structures
meta = pl.read_parquet(f"{ROOT}/{a.store}/spec_meta.parquet", columns=["row", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "scorer_ik14", "n_peaks"])
meta = meta.filter(pl.col("scorer_ik14").is_not_null() & pl.col("adduct").is_in(list(ADDUCT_SHIFT)) & (pl.col("n_peaks") >= 3) & ~pl.col("scorer_ik14").is_in(list(excl_keys)))
ts = pd.read_parquet(f"{ROOT}/{a.structs}", columns=["key", "smiles"]).drop_duplicates("key"); KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
meta = meta.filter(pl.col("scorer_ik14").is_in(list(KEY_SMI)))
# cap spectra per (key, polarity) at random
meta = meta.with_columns(pl.Series("r", rng.random(meta.height))).sort(["scorer_ik14", "ionization_mode", "r"]).group_by(["scorer_ik14", "ionization_mode"], maintain_order=True).head(a.cap_per_key)
keys = sorted(set(meta["scorer_ik14"].to_list())); KIX = {k: i for i, k in enumerate(keys)}
log(f"training spectra {meta.height:,} for {len(keys):,} keys")
from rdkit import Chem, RDLogger, DataStructs  # noqa: E402
from rdkit.Chem import rdFingerprintGenerator  # noqa: E402
RDLogger.DisableLog("rdApp.*"); GEN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
FPB = np.zeros((len(keys), 2048), np.uint8); ok_key = np.ones(len(keys), bool)
for i, k in enumerate(keys):
    m = Chem.MolFromSmiles(KEY_SMI[k])
    if m is None: ok_key[i] = False; continue
    arr = np.zeros((2048,), np.uint8); DataStructs.ConvertToNumpyArray(GEN.GetFingerprint(m), arr); FPB[i] = arr
log(f"fingerprints {ok_key.sum():,} / {len(keys):,}")
S_MZ = np.load(f"{ROOT}/{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{ROOT}/{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{ROOT}/{a.store}/spec_off.npy")
rows = meta["row"].to_numpy(); kix = np.array([KIX[k] for k in meta["scorer_ik14"].to_list()]); pol = (meta["ionization_mode"].to_numpy() == "positive").astype(np.int8)
libs = meta["ingest_lib"].to_numpy(); precs = meta["precursor_mz"].to_numpy().astype(np.float64)
keep = ok_key[kix]; rows, kix, pol, libs, precs = rows[keep], kix[keep], pol[keep], libs[keep], precs[keep]
ptr = [0]; idx_l, val_l = [], []
for x, lb, po in zip(rows, libs, pol):
    o0, o1 = S_OFF[x], S_OFF[x + 1]; mz = np.asarray(S_MZ[o0:o1], np.float64); it = np.asarray(S_IT[o0:o1], np.float64)
    if lb == "enveda-180" and po == 1: mz = mz - ELECTRON
    ok = (mz >= MZ0) & (mz < MZ0 + NB * BW) & (it > 0); mz, it = mz[ok], it[ok]
    if len(it) > TOPK:
        o = np.argsort(-it)[:TOPK]; mz, it = mz[o], it[o]
    b = ((mz - MZ0) / BW).astype(np.int64); v = np.sqrt(it / it.max()) if len(it) else it
    # merge duplicate bins (max), L2-normalise
    if len(b):
        ub, inv = np.unique(b, return_inverse=True); vv = np.zeros(len(ub)); np.maximum.at(vv, inv, v); v = vv / (np.linalg.norm(vv) + 1e-9); b = ub
    idx_l.append(b.astype(np.int32)); val_l.append(v.astype(np.float32)); ptr.append(ptr[-1] + len(b))
PTR = np.array(ptr, np.int64); IDX = np.concatenate(idx_l); VAL = np.concatenate(val_l)
log(f"binned {len(rows):,} spectra, {len(IDX):,} non-zero bins")

import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
import torch.nn.functional as F  # noqa: E402
dev = "cuda"; torch.manual_seed(a.seed)
FP_T = torch.tensor(FPB, dtype=torch.float16, device=dev); FP_N = FP_T.float().sum(1)
# 32 nearest structures per key (Tanimoto), chunked on the GPU
K_NN = 32; NN = np.zeros((len(keys), K_NN), np.int64)
for s0 in range(0, len(keys), 2048):
    q = FP_T[s0:s0 + 2048]; inter = (q @ FP_T.T).float(); tan = inter / (FP_N[s0:s0 + 2048, None] + FP_N[None, :] - inter + 1e-9)
    tan[torch.arange(len(q)), torch.arange(s0, s0 + len(q))] = -1.0
    NN[s0:s0 + len(q)] = torch.topk(tan, K_NN, dim=1).indices.cpu().numpy()
log("nearest structures done")
# key -> spectra indices per polarity
spec_of = {}
for i, (k, p) in enumerate(zip(kix, pol)): spec_of.setdefault((int(k), int(p)), []).append(i)
key_ids = np.unique(kix); vmask = rng.random(len(key_ids)) < a.val_frac; VAL_KEYS = set(key_ids[vmask].tolist()); TR_KEYS = key_ids[~vmask]
tr_spec = np.array([i for i, k in enumerate(kix) if int(k) not in VAL_KEYS]); va_spec = np.array([i for i, k in enumerate(kix) if int(k) in VAL_KEYS])
log(f"train spectra {len(tr_spec):,} / val spectra {len(va_spec):,} ({len(VAL_KEYS):,} val keys)")
PTR_T = torch.tensor(PTR, device=dev); IDX_T = torch.tensor(IDX, device=dev, dtype=torch.int64); VAL_T = torch.tensor(VAL, device=dev); POL_T = torch.tensor(pol, device=dev, dtype=torch.float32)


def dense(ix):
    """spectrum indices (tensor) -> dense (len, NB + 1) batch on the GPU."""
    st = PTR_T[ix]; en = PTR_T[ix + 1]; ln = en - st
    rep = torch.repeat_interleave(torch.arange(len(ix), device=dev), ln)
    off = torch.arange(int(ln.sum()), device=dev) - torch.repeat_interleave(torch.cumsum(ln, 0) - ln, ln)
    flat = torch.repeat_interleave(st, ln) + off
    X = torch.zeros((len(ix), NB + 1), device=dev); X[rep, IDX_T[flat]] = VAL_T[flat]; X[:, NB] = POL_T[ix]
    return X


class Enc(nn.Module):
    def __init__(s):
        super().__init__(); s.net = nn.Sequential(nn.Linear(NB + 1, 1024), nn.BatchNorm1d(1024), nn.LeakyReLU(), nn.Dropout(0.2), nn.Linear(1024, 512), nn.BatchNorm1d(512), nn.LeakyReLU(), nn.Dropout(0.2), nn.Linear(512, 256))
    def forward(s, x): return F.normalize(s.net(x), dim=1)


def tanimoto(ka, kb):
    fa, fb = FP_T[ka].float(), FP_T[kb].float(); inter = (fa * fb).sum(1); return inter / (FP_N[ka] + FP_N[kb] - inter + 1e-9)


def sample_pairs(pool_spec, n, near_ok=True, partner_any=False):
    """training: both keys outside the validation keys; validation (partner_any): held-out anchor, partner from any key (the analog-search use: unseen query vs known library)."""
    a_ = rng.choice(pool_spec, n); pa = []
    for i in a_:
        k = int(kix[i]); p = int(pol[i])
        for _ in range(4):
            if near_ok and rng.random() < a.p_near: kb = int(NN[k, rng.integers(K_NN)])
            else: kb = int(kix[rng.choice(pool_spec)])
            if not partner_any and kb in VAL_KEYS: continue
            lst = spec_of.get((kb, p))
            if lst: pa.append(int(rng.choice(lst))); break
        else: pa.append(int(rng.choice(tr_spec)))
    return np.array(a_), np.array(pa)


enc = Enc().to(dev); opt = torch.optim.AdamW(enc.parameters(), lr=a.lr, weight_decay=1e-4)
sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=a.steps, pct_start=0.05)
va_a, va_b = sample_pairs(va_spec, 20000, partner_any=True); va_t = tanimoto(torch.tensor(kix[va_a], device=dev), torch.tensor(kix[va_b], device=dev)).cpu().numpy()
log(f"validation pairs {len(va_a):,}: Tanimoto mean {va_t.mean():.3f}, share > 0.6 {(va_t > 0.6).mean():.3f}")
hist = np.ones(10); best = -1.0
for step in range(1, a.steps + 1):
    enc.train(); ia, ib = sample_pairs(tr_spec, a.bs)
    ta = torch.tensor(ia, device=dev); tb = torch.tensor(ib, device=dev)
    y = tanimoto(torch.tensor(kix[ia], device=dev), torch.tensor(kix[ib], device=dev))
    bins = torch.clamp((y * 10).long(), 0, 9); hb = np.bincount(bins.cpu().numpy(), minlength=10); hist = 0.99 * hist + 0.01 * hb
    w = torch.tensor((hist.sum() / (10 * hist))[bins.cpu().numpy()], device=dev, dtype=torch.float32)
    ea, eb = enc(dense(ta)), enc(dense(tb)); pred = (ea * eb).sum(1)
    loss = (w * (pred - y) ** 2).mean(); opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    if step % a.eval_every == 0 or step == a.steps:
        enc.eval(); preds = []
        with torch.no_grad():
            for s0 in range(0, len(va_a), 2048):
                xa = enc(dense(torch.tensor(va_a[s0:s0 + 2048], device=dev))); xb = enc(dense(torch.tensor(va_b[s0:s0 + 2048], device=dev))); preds.append((xa * xb).sum(1).cpu().numpy())
        pv = np.concatenate(preds); pr = float(np.corrcoef(pv, va_t)[0, 1]); sr = float(pd.Series(pv).corr(pd.Series(va_t), method="spearman")); rmse = float(np.sqrt(((pv - va_t) ** 2).mean()))
        log(f"step {step}: loss {loss.item():.4f} | val pearson {pr:.3f} spearman {sr:.3f} rmse {rmse:.3f}")
        if pr > best:
            best = pr; torch.save(dict(state=enc.state_dict(), nb=NB, mz0=MZ0, bw=BW, topk=TOPK, step=step, val_pearson=pr, val_spearman=sr), f"{a.out_dir}/ls_model.pt")
# entropy baseline on a subset of the same validation pairs (040 sanity condition)
import b1_analog as BA  # noqa: E402
from b1_common import clean_peaks, entropy_weight  # noqa: E402
def prep(i):
    x = int(rows[i]); o0, o1 = S_OFF[x], S_OFF[x + 1]; mz = np.asarray(S_MZ[o0:o1], np.float64); it = np.asarray(S_IT[o0:o1], np.float64)
    sh = ELECTRON if (libs[i] == "enveda-180" and pol[i] == 1) else 0.0; prec = float(precs[i]) - sh
    cm, ci = clean_peaks(mz - sh, it, prec, floor=0.005, top=64)
    if not len(ci): return None
    p = entropy_weight(ci); return (cm, p, float(-(p[p > 0] * np.log(p[p > 0])).sum()), prec)
sub = rng.choice(len(va_a), 3000, replace=False); es, et, lp = [], [], []
pv_all = np.concatenate(preds)
for j in sub:
    qa, qb = prep(int(va_a[j])), prep(int(va_b[j]))
    if qa is None or qb is None: continue
    es.append(BA.sim_pair(qa, qb)); et.append(va_t[j]); lp.append(pv_all[j])
es, et, lp = np.array(es), np.array(et), np.array(lp)
res = dict(best_val_pearson=best, entropy_pearson=float(np.corrcoef(es, et)[0, 1]), learned_pearson_same_subset=float(np.corrcoef(lp, et)[0, 1]),
           entropy_spearman=float(pd.Series(es).corr(pd.Series(et), method="spearman")), learned_spearman_same_subset=float(pd.Series(lp).corr(pd.Series(et), method="spearman")),
           n_subset=int(len(es)), excluded_groups=len(grp_used), train_spectra=int(len(tr_spec)), keys=len(keys), steps=a.steps)
json.dump(res, open(f"{a.out_dir}/ls_summary.json", "w"), indent=1); log("summary", res)
