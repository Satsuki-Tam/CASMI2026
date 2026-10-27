"""DreaMS-FP head: frozen DreaMS embedding (dreams_embed.py) + adduct / polarity / CE -> fingerprint logits over the FPNet bit set
(10,226 bits, packed pool FPs of data/external/harness_work), trained like train_fpnet.py: softmax ranking CE of the positive against K pool
negatives inside +-10 ppm of the positive mass (+ BCE on the positive bits). Identity-fold-safe: --holdout_fold k removes every spectrum of
an identity in fold k (identity_folds/spectra_folds.parquet) and of the 250 panel identities (as the public fold-safe FPNets do).
Evaluation on fold-k molecules (one row per molecule, up to 8 spectra, logits averaged): rank of the truth in its FULL +-10 ppm pool window,
DreaMS head vs the fold-safe FPNet fold k on the same spectra (single-spectrum inputs, logits averaged) vs their z-sum.
Usage: python -X utf8 dreams_fp_train.py --emb_dir data/processed/dreams_emb --holdout_fold 1 --out experiments/b1_baseline/dreams_fp_f1
"""
import argparse, json, math, os, sys, time
import numpy as np, polars as pl, torch, torch.nn as nn, torch.nn.functional as F
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from b1_common import ADDUCT_SHIFT
ap = argparse.ArgumentParser(); ap.add_argument("--emb_dir", default=f"{ROOT}/data/processed/dreams_emb"); ap.add_argument("--holdout_fold", type=int, required=True)
ap.add_argument("--out", required=True); ap.add_argument("--steps", type=int, default=30000); ap.add_argument("--bs", type=int, default=512); ap.add_argument("--K", type=int, default=63)
ap.add_argument("--lr", type=float, default=1e-3); ap.add_argument("--wd", type=float, default=0.01); ap.add_argument("--hidden", type=int, default=2048); ap.add_argument("--drop", type=float, default=0.1)
ap.add_argument("--w_bce", type=float, default=1.0); ap.add_argument("--seed", type=int, default=0); ap.add_argument("--eval_n", type=int, default=0, help="0 = every fold-k molecule"); ap.add_argument("--warmup", type=int, default=1000)
ap.add_argument("--exclude_keys", default="", help="text file of scorer keys never used for training (e.g. dev2 hold / locked2 lock for a production head)")
ap.add_argument("--fpnet_eval", type=int, default=1, help="also score the eval molecules with the fold-safe FPNet fold k")
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
torch.manual_seed(a.seed); rng = np.random.default_rng(a.seed); dev = "cuda"
def log(*x): print(time.strftime("%H:%M:%S"), *x, flush=True)
HW = f"{ROOT}/data/external/harness_work"; ST = f"{ROOT}/data/processed/spectra_store"
meta = pl.read_parquet(f"{ST}/spec_meta.parquet", columns=["row", "scorer_ik14", "ingest_lib", "adduct", "ionization_mode", "ce_mean", "precursor_mz"])
folds = pl.read_parquet(f"{ROOT}/data/external/identity_folds/spectra_folds.parquet", columns=["row", "fold_identity"])
meta = meta.join(folds, on="row", how="left").sort("row")
pool = pl.read_parquet(f"{HW}/pool_meta.parquet", columns=["key", "mass", "src", "np_likeness"]); pmass = pool["mass"].to_numpy().astype(np.float64)
psrc = pool["src"].to_numpy(); pnpl = pool["np_likeness"].to_numpy().astype(np.float64)
k2p = dict(zip(pool["key"].to_list(), range(pool.height)))
key = meta["scorer_ik14"].to_list(); pid = np.array([k2p.get(k, -1) for k in key], np.int64)
fold = meta["fold_identity"].fill_null(-1).to_numpy(); lib = meta["ingest_lib"].to_numpy()
ok = np.load(f"{a.emb_dir}/ok.npy"); assert len(ok) == meta.height
panel = set(meta.filter(pl.col("ingest_lib") == "enveda-np-examples")["scorer_ik14"].to_list())
excl = set(open(a.exclude_keys).read().split()) if a.exclude_keys else set()
is_panel = np.array([k in panel for k in key]); is_excl = np.array([k in excl for k in key]) if excl else np.zeros(len(key), bool)
tr = np.where(ok & (pid >= 0) & (fold != a.holdout_fold) & ~is_panel & ~is_excl)[0]
ev_rows = np.where(ok & (pid >= 0) & (fold == a.holdout_fold) & ~is_panel)[0]
log(f"train spectra {len(tr):,} ({len(np.unique(pid[tr])):,} structures), eval-fold spectra {len(ev_rows):,}")
# side inputs: adduct one-hot (10 test adducts + other), polarity, CE
ADD = list(ADDUCT_SHIFT); add_ix = np.array([ADD.index(x) if x in ADD else len(ADD) for x in meta["adduct"].to_list()], np.int64)
mode = np.where(meta["ionization_mode"].to_numpy() == "negative", -1.0, 1.0).astype(np.float32)
ce = meta["ce_mean"].to_numpy().astype(np.float32); ce_known = np.isfinite(ce).astype(np.float32); ce = np.where(np.isfinite(ce), ce / 100.0, 0.0).astype(np.float32)
SIDE = np.zeros((meta.height, len(ADD) + 1 + 3), np.float32); SIDE[np.arange(meta.height), add_ix] = 1.0
SIDE[:, len(ADD) + 1] = mode; SIDE[:, len(ADD) + 2] = ce_known; SIDE[:, len(ADD) + 3] = ce
log("loading embeddings"); EMB = torch.from_numpy(np.load(f"{a.emb_dir}/emb_f16.npy")).to(dev)
SIDE_T = torch.from_numpy(SIDE).to(dev)
pfp = np.load(f"{HW}/pool_fp.npy"); nbits = int(np.load(f"{HW}/fp_bits.npy").shape[0]); PFP = torch.from_numpy(pfp).to(dev)
SH = torch.arange(7, -1, -1, device=dev, dtype=torch.uint8)
def unpack(p): return ((p.unsqueeze(-1) >> SH) & 1).reshape(*p.shape[:-1], -1)[..., :nbits].float()
class Head(nn.Module):
    def __init__(s, din, h, nout, drop):
        super().__init__(); s.ln = nn.LayerNorm(din)
        s.net = nn.Sequential(nn.Linear(din, h), nn.GELU(), nn.Dropout(drop), nn.Linear(h, h), nn.GELU(), nn.Dropout(drop), nn.Linear(h, nout))
    def forward(s, x): return s.net(s.ln(x))
model = Head(1024 + SIDE.shape[1], a.hidden, nbits, a.drop).to(dev)
dec = [p for n, p in model.named_parameters() if p.ndim >= 2]; nod = [p for n, p in model.named_parameters() if p.ndim < 2]
opt = torch.optim.AdamW([dict(params=dec, weight_decay=a.wd), dict(params=nod, weight_decay=0.0)], lr=a.lr, betas=(0.9, 0.98))
# structure-uniform sampling: train rows grouped by pool id
o = np.argsort(pid[tr], kind="mergesort"); trs = tr[o]; ps = pid[trs]; st = np.flatnonzero(np.r_[True, ps[1:] != ps[:-1]]); en = np.r_[st[1:], len(ps)]
def sample(B):
    h = B // 2; x1 = rng.choice(tr, h)
    g = rng.integers(0, len(st), B - h); x2 = trs[st[g] + (rng.random(B - h) * (en[g] - st[g])).astype(np.int64)]
    return np.concatenate([x1, x2])
def negatives(pos):
    m = pmass[pos]; tol = m * 10e-6
    lo = np.searchsorted(pmass, m - tol, "left"); hi = np.searchsorted(pmass, m + tol, "right"); n = hi - lo
    c = lo[:, None] + (rng.random((len(pos), a.K)) * np.maximum(n, 1)[:, None]).astype(np.int64)
    bad = c == pos[:, None]; c = np.where(bad, np.where(c + 1 < hi[:, None], c + 1, lo[:, None]), c)
    rnd = rng.integers(0, len(pmass), (len(pos), a.K))
    small = n <= 1; c[small] = rnd[small]
    tiny = (n > 1) & (n < 8); k2 = a.K // 2
    c[tiny, k2:] = rnd[tiny, k2:]
    same = c == pos[:, None]; c[same] = (np.broadcast_to(pos[:, None], c.shape)[same] + 1) % len(pmass)
    return c
def feats(rows):
    r = torch.as_tensor(rows, device=dev)
    return torch.cat([EMB[r].float(), SIDE_T[r]], 1)
t0 = time.time(); ema = dict(loss=0.0, rank=0.0, bce=0.0, acc=0.0); tgt = torch.zeros(a.bs, dtype=torch.long, device=dev)
model.train()
for step in range(a.steps):
    prog = step / a.steps; lr = a.lr * min(1.0, (step + 1) / a.warmup) * (0.02 + 0.98 * 0.5 * (1 + math.cos(math.pi * prog)))
    for g_ in opt.param_groups: g_["lr"] = lr
    rows = sample(a.bs); pos = pid[rows]; cand = torch.as_tensor(np.concatenate([pos[:, None], negatives(pos)], 1), device=dev)
    with torch.autocast("cuda", dtype=torch.bfloat16): z = model(feats(rows))
    z = z.float(); fp = unpack(PFP[cand]); sc = torch.einsum("bkn,bn->bk", fp, z)
    l_rank = F.cross_entropy(sc, tgt); l_bce = F.binary_cross_entropy_with_logits(z, fp[:, 0]); loss = l_rank + a.w_bce * l_bce
    opt.zero_grad(set_to_none=True); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
    v = dict(loss=loss.item(), rank=l_rank.item(), bce=l_bce.item(), acc=(sc.argmax(1) == 0).float().mean().item())
    for k_ in ema: ema[k_] = v[k_] if step == 0 else 0.99 * ema[k_] + 0.01 * v[k_]
    if step % 1000 == 0 or step == a.steps - 1:
        log(f"step {step} lr {lr:.2e} " + " ".join(f"{k_} {x:.4f}" for k_, x in ema.items()) + f" {(step + 1) / (time.time() - t0):.1f} it/s")
torch.save(dict(state=model.state_dict(), din=1024 + SIDE.shape[1], hidden=a.hidden, nbits=nbits, drop=a.drop, adducts=ADD, holdout_fold=a.holdout_fold,
                n_train=int(len(tr)), steps=a.steps), f"{a.out}/head.pt")
# ---- evaluation on fold-k molecules: up to 8 spectra per molecule (logits averaged), full +-10 ppm pool window
model.eval()
mol_rows = {}
for r in ev_rows: mol_rows.setdefault(int(pid[r]), []).append(int(r))
mols = sorted(mol_rows); rng2 = np.random.default_rng(123)
if a.eval_n > 0: mols = [mols[i] for i in np.sort(rng2.choice(len(mols), min(a.eval_n, len(mols)), replace=False))]
fpnet = None
if a.fpnet_eval:
    sys.path.insert(0, f"{ROOT}/data/external/v3_models/code")
    from casmi import fpnet as FPN, chem as CH
    fpnet = FPN.load_model(f"{ROOT}/data/external/fold_safe_fpnet/fpnet_fold{a.holdout_fold}.pt", dev)
    MZ = np.load(f"{ST}/spec_mz.npy", mmap_mode="r"); IT = np.load(f"{ST}/spec_int.npy", mmap_mode="r"); OFF = np.load(f"{ST}/spec_off.npy")
    prec_all = meta["precursor_mz"].to_numpy(); add_all = meta["adduct"].to_list(); ce_all = meta["ce_mean"].to_numpy()
def zs(x):
    s = x.std(); return (x - x.mean()) / s if s > 0 else x * 0
res = []
with torch.no_grad():
    for p_ in mols:
        rr = mol_rows[p_]; rr = [rr[i] for i in rng2.permutation(len(rr))[:8]]
        zD = model(feats(np.array(rr))).float().mean(0)
        m = pmass[p_]; tol = m * 10e-6; lo = int(np.searchsorted(pmass, m - tol, "left")); hi = int(np.searchsorted(pmass, m + tol, "right"))
        W = unpack(PFP[lo:hi]); sD = (W @ zD).cpu().numpy(); t = p_ - lo
        row = dict(pid=p_, lib=str(lib[rr[0]]), coco=bool(psrc[p_] in (2, 3)), npl=float(pnpl[p_]), n_win=hi - lo, rD=int((sD > sD[t]).sum() + 1))
        if fpnet is not None:
            items = []
            for r in rr:
                mz = np.asarray(MZ[OFF[r]:OFF[r + 1]], np.float64); it = np.asarray(IT[OFF[r]:OFF[r + 1]], np.float64)
                pm, pi = FPN.prep_peaks(mz, it, float(prec_all[r]))
                ck = bool(np.isfinite(ce_all[r]))
                items.append(dict(mz=pm, it=pi, prec=float(prec_all[r]), adduct_ix=CH.adduct_index(add_all[r]), ce=float(ce_all[r]) if ck else 0.0, ce_known=1.0 if ck else 0.0,
                                  n_merged=1, mode=float(mode[r])))
            inp = FPN.collate(items, dev)
            with torch.autocast("cuda", dtype=FPN.autocast_dtype(dev)): zF = fpnet(*inp)[0].float().mean(0)
            sF = (W @ zF).cpu().numpy()
            row["rF"] = int((sF > sF[t]).sum() + 1)
            for w in (0.5, 1.0):
                sE = zs(sF) + w * zs(sD); row[f"rE{w}"] = int((sE > sE[t]).sum() + 1)
        res.append(row)
R = pl.DataFrame(res); out = dict(holdout_fold=a.holdout_fold, n_eval=R.height, train_spectra=int(len(tr)), steps=a.steps, seconds=round(time.time() - t0))
def summ(df):
    d = {}
    for c in [c for c in df.columns if c in ("rD", "rF") or c.startswith("rE")]:
        r_ = df[c].to_numpy(); d[c] = dict(top1=round(float((r_ == 1).mean()), 4), mrr25=round(float(np.where(r_ <= 25, 1.0 / r_, 0).mean()), 4))
    return d
out["all"] = summ(R); out["coco"] = dict(n=int(R["coco"].sum()), **summ(R.filter(pl.col("coco")))); out["noncoco"] = summ(R.filter(~pl.col("coco")))
out["by_lib"] = {str(l): dict(n=int(g.height), **summ(g)) for (l,), g in R.group_by("lib")}
R.write_csv(f"{a.out}/eval_rows.csv"); json.dump(out, open(f"{a.out}/eval.json", "w"), indent=1)
log(json.dumps(out["all"])); log("coco:", json.dumps(out["coco"])); log("by lib:", json.dumps({k: (v["n"], v["rD"]["top1"], v.get("rF", {}).get("top1")) for k, v in out["by_lib"].items()}))
