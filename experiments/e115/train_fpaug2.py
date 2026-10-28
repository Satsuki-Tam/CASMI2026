"""115 v2 (Codex 118): FPNet fine-tuning from a fold-safe checkpoint, R (--sim_frac 0) or A (a fixed share --sim_frac of the POSITIVE [M+H]+ /
[M+Na]+ real slots of every batch replaced by GLACIER-simulated spectra taken IN ORDER from a fixed plan, make_simplan.py). Identical between R and A:
initial weights, updates, batch, optimizer (fresh AdamW), LR / warmup / cosine schedule, losses (public: f.z ranking CE over 1 positive + K
negatives, FP BCE, elements), the real-sample stream (per worker, the public Data RNG), negatives and augmentation rules.
Changes from v1 (Codex 118): (1) negatives follow the PUBLIC rule on the FULL pool (uniform from the +-10 ppm window, tiny windows (< 8) half random
decoys), evaluation-independent: no held-out-structure exclusion; only the positive's own identity (canonical row and alias spellings, via public
identity definitions) is excluded. Held-out REAL spectra stay out of training (Data's holdout). (2) Simulated positives follow ONE global cycle (a
shared counter over the plan; no per-worker cycles); every consumed simulated item is counted in the main loop (ledger), prefetched-only items are
not. (3) Simulated data are read once per shard into flat arrays + offsets; generation must be complete (meta) and every plan job either predicted
or recorded as failed (failed jobs are dropped from the cycle, at most --max_fail); otherwise STOP. A with no simulated input is a STOP, never a
silent R. (4) Separate RNG streams keyed by (seed, purpose, worker, batch, slot) for replacement choice, simulated augmentation and negatives.
Simulated item: GLACIER peaks -> the public augmentation (peak dropout, intensity / ppm jitter, CE dropped with p 0.1) -> fpnet.prep_peaks with the
THEORETICAL precursor m/z = pool mass - ADDUCT_SHIFT[adduct]; CE known (the job's), n_merged 1, mode +1; positive = the plan job's canonical pool row.
No evaluation inside training; only the final checkpoint is saved (plus a smoke checkpoint in smoke mode).
Usage: python train_fpaug2.py --code C --run R --init CK --folds F --tag T --steps S [--sim_dir PLAN_DIR --sim_out GEN_PREFIX --sim_frac 0.25]
       [--device cuda] [--smoke_steps n] [--bs 256] [--workers 6]"""
import argparse, glob, hashlib, json, math, os, sys, time, signal, pathlib
os.environ['OMP_NUM_THREADS'] = '1'; os.environ['NUMBA_NUM_THREADS'] = '1'; os.environ['OPENBLAS_NUM_THREADS'] = '1'; os.environ['MKL_NUM_THREADS'] = '1'
sys.dont_write_bytecode = True
import multiprocessing as mp
import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('--code', required=True); ap.add_argument('--run', required=True); ap.add_argument('--init', required=True); ap.add_argument('--folds', required=True)
ap.add_argument('--tag', required=True); ap.add_argument('--steps', type=int, required=True)
ap.add_argument('--bs', type=int, default=256); ap.add_argument('--K', type=int, default=63); ap.add_argument('--lr', type=float, default=1e-4); ap.add_argument('--wd', type=float, default=0.01)
ap.add_argument('--warmup', type=int, default=500); ap.add_argument('--merge_p', type=float, default=0.3); ap.add_argument('--w_bce', type=float, default=1.0); ap.add_argument('--w_el', type=float, default=0.1)
ap.add_argument('--workers', type=int, default=6); ap.add_argument('--seed', type=int, default=0); ap.add_argument('--holdout', default='hold,np')
ap.add_argument('--sim_dir', default=''); ap.add_argument('--sim_out', default=''); ap.add_argument('--sim_frac', type=float, default=0.0)
ap.add_argument('--device', default='cuda'); ap.add_argument('--smoke_steps', type=int, default=0); ap.add_argument('--max_fail', type=float, default=0.01)
args = ap.parse_args()
A = args.sim_frac > 0
if A and not (args.sim_dir and args.sim_out): sys.exit('STOP: A needs --sim_dir (plan) and --sim_out (generation prefix)')
INIT = os.path.abspath(args.init); FOLDS = os.path.abspath(args.folds)
SIMD = os.path.abspath(args.sim_dir) if args.sim_dir else ''; SIMO = os.path.abspath(args.sim_out) if args.sim_out else ''
sys.path.insert(0, args.code); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'b1_baseline'))
os.chdir(args.run)
import torch
import torch.nn.functional as F
from casmi import fpnet, traindata, chem
from b1_common import ADDUCT_SHIFT

G = {}
STOP = False


def stop_requested(signum, frame):
    global STOP
    STOP = True


signal.signal(signal.SIGTERM, stop_requested); signal.signal(signal.SIGHUP, stop_requested)


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def fsha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()


def negatives(D, pos, K, wid, b):
    """Public rule (traindata.Data.negatives) on the full pool + exclusion of the positive's own identity; one RNG per slot."""
    IDN = G['ident']; n_pool = len(D.pmass)
    out = np.empty((len(pos), K), np.int64)
    for r in range(len(pos)):
        rng = np.random.default_rng([args.seed, 13, wid, b, r]); p = int(pos[r]); idp = IDN[p]
        m = D.pmass[p]; tol = m * 10e-6
        lo = int(np.searchsorted(D.pmass, m - tol, 'left')); hi = int(np.searchsorted(D.pmass, m + tol, 'right'))

        def fix(c, lo_, hi_):
            bad = (c == p) | (IDN[c] == idp)
            for _ in range(8):
                if not bad.any(): break
                c[bad] = rng.integers(lo_, hi_, int(bad.sum())); bad = (c == p) | (IDN[c] == idp)
            while bad.any():   # the window holds only the positive's identity: global random decoys
                c[bad] = rng.integers(0, n_pool, int(bad.sum())); bad = (c == p) | (IDN[c] == idp)
            return c
        if hi - lo <= 1:
            out[r] = fix(rng.integers(0, n_pool, K), 0, n_pool)
        else:
            c = fix(rng.integers(lo, hi, K), lo, hi)
            if hi - lo < 8:   # tiny windows: mix in random decoys (public rule)
                k = K // 2; c[k:] = fix(rng.integers(0, n_pool, K - k), 0, n_pool)
            out[r] = c
    return out


def sim_item(D, j, rng):
    SIM = G['sim']; s0, n = int(SIM['start'][j]), int(SIM['len'][j])
    mz = SIM['mz'][s0:s0 + n].astype(np.float64); it = SIM['it'][s0:s0 + n].astype(np.float64)
    ad, ce = str(SIM['adduct'][j]), float(SIM['ce'][j]); ce_known = 1.0
    if len(mz) > 4:   # the public augmentation (traindata.Data.item, aug=True)
        keep = rng.random(len(mz)) > rng.uniform(0.0, 0.3)
        if keep.sum() >= 3: mz, it = mz[keep], it[keep]
    it = it * np.exp(rng.normal(0.0, 0.3, size=len(it))); mz = mz * (1.0 + rng.normal(0.0, 4e-6, size=len(mz)))
    if rng.random() < 0.1: ce_known = 0.0
    prec = float(D.pmass[int(SIM['pid'][j])]) - ADDUCT_SHIFT[ad]
    pm, pi = fpnet.prep_peaks(mz, it, prec)
    return dict(mz=pm, it=pi, prec=prec, adduct_ix=chem.adduct_index(ad), ce=ce if ce_known else 0.0, ce_known=ce_known, n_merged=1, mode=1.0)


def worker(wid, q, counter, lock):
    signal.signal(signal.SIGTERM, signal.SIG_DFL); signal.signal(signal.SIGHUP, signal.SIG_DFL)
    torch.set_num_threads(1)
    D = G['D']; D.rng = np.random.default_rng(args.seed * 1000 + wid + 1); HNA = G['hna']; PLAN = G.get('plan')
    b = 0
    while True:
        ids = D.sample_ids(args.bs)
        items = [D.item(int(i), args.merge_p, True) for i in ids]   # the real stream is drawn identically in R and A
        pos = D.sid2pid[D.sid[ids]].copy()
        elig = [k for k, i in enumerate(ids) if D.mode[i] > 0 and int(D.adduct[i]) in HNA]; sim_jobs = []
        if A and elig:
            rr = np.random.default_rng([args.seed, 7, wid, b]); n_rep = int(round(args.sim_frac * len(elig)))
            if n_rep:
                slots = rr.choice(elig, size=n_rep, replace=False)
                with lock:
                    start = counter.value; counter.value += n_rep
                for k, p_ in zip(slots, range(start, start + n_rep)):
                    j = int(PLAN[p_ % len(PLAN)])
                    items[k] = sim_item(D, j, np.random.default_rng([args.seed, 11, wid, b, int(k)])); pos[k] = int(G['sim']['pid'][j]); sim_jobs.append(j)
        negs = negatives(D, pos, args.K, wid, b)
        q.put((tuple(t.numpy() for t in fpnet.collate(items, 'cpu')), pos, negs, dict(n_elig=len(elig), n_rep=len(sim_jobs), sim_jobs=sim_jobs, wid=wid, b=b)))
        b += 1


def load_sim():
    """Plan + complete generation -> flat arrays; STOP on anything missing (Codex 118)."""
    pm = json.load(open(os.path.join(SIMD, 'plan_manifest.json')))
    for f, h in pm['outputs'].items():
        if fsha(os.path.join(SIMD, f)) != h: sys.exit(f'STOP: plan file {f} changed since make_simplan')
    jobs = json.load(open(os.path.join(SIMD, 'jobs.json'))); jpid = np.load(os.path.join(SIMD, 'jobs_pid.npy'), allow_pickle=False)
    plan = np.load(os.path.join(SIMD, 'plan.npy'), allow_pickle=False); nj = len(jobs)
    meta = json.load(open(SIMO + '_meta.json'))
    if meta.get('n_jobs') != nj or meta['n_ok'] + meta['n_fail'] + sum(meta.get('rejected', {}).values()) != nj:
        sys.exit(f"STOP: generation meta does not cover the job list ({meta.get('n_jobs')} / {nj})")
    start = np.full(nj, -1, np.int64); ln = np.zeros(nj, np.int32); MZ, IT = [], []; base = 0
    for f in sorted(glob.glob(SIMO + '_[0-9]*.npz')):
        with np.load(f, allow_pickle=False) as Z:
            idx = Z['idx']; off = Z['off']; mz = Z['mz']; it = Z['it']   # each array read ONCE
        if len(idx) and (idx.min() < 0 or idx.max() >= nj): sys.exit(f'STOP: job index out of range in {f}')
        if (start[idx] >= 0).any() or len(np.unique(idx)) != len(idx): sys.exit(f'STOP: duplicate job index in {f}')
        if not (np.isfinite(mz).all() and np.isfinite(it).all()): sys.exit(f'STOP: non-finite peaks in {f}')
        start[idx] = base + off[:-1]; ln[idx] = np.diff(off).astype(np.int32); MZ.append(mz); IT.append(it); base += len(mz)
    ok = start >= 0
    if int(ok.sum()) != meta['n_ok']: sys.exit(f"STOP: shards hold {int(ok.sum())} predictions, meta says {meta['n_ok']}")
    if (ln[ok] <= 0).any(): sys.exit('STOP: an ok job has no peaks')
    failed_plan = ~ok[plan]
    if failed_plan.mean() > args.max_fail: sys.exit(f'STOP: {failed_plan.mean():.4f} of the plan positions have no prediction (> {args.max_fail})')
    G['plan'] = plan[~failed_plan]
    G['sim'] = dict(start=start, len=ln, mz=np.concatenate(MZ) if MZ else np.zeros(0, np.float32), it=np.concatenate(IT) if IT else np.zeros(0, np.float32),
                    pid=jpid.astype(np.int64), adduct=np.array([j[1] for j in jobs], dtype=object), ce=np.array([float(j[3]) for j in jobs], np.float64))
    return dict(jobs=nj, ok=int(ok.sum()), plan=len(plan), plan_used=int(len(G['plan'])), plan_positions_dropped_failed=int(failed_plan.sum()),
                plan_sha256=pm['outputs']['plan.npy'], jobs_sha256=pm['outputs']['jobs.json'], catalog_sha256=pm['outputs']['catalog.parquet'], gen_meta=meta)


def main():
    torch.set_num_threads(1)
    hold = tuple(args.holdout.split(','))
    D = traindata.Data('cpu', seed=args.seed, holdout_folds=hold); G['D'] = D
    # identity of every pool row (public definitions only): training rows -> identity_group of their structure; other rows whose key is a known
    # identity key / alias -> that identity; all other rows -> their own id. Used ONLY to keep the positive's own identity out of its negatives.
    ts = pd.read_parquet('work/train_structs.parquet', columns=['sid', 'inchikey14', 'key', 'rawkey'])
    st = pd.read_parquet(FOLDS, columns=['inchikey14', 'scorer_key', 'identity_group'])
    ik2g = dict(zip(st.inchikey14.astype(str), st.identity_group.astype(np.int64)))
    k2g = dict(ik2g); k2g.update(dict(zip(st.scorer_key.astype(str), st.identity_group.astype(np.int64))))
    tg = ts.inchikey14.astype(str).map(ik2g)
    for c in ('key', 'rawkey'): k2g.update({k: int(g) for k, g in zip(ts[c].astype(str), tg) if pd.notna(g)})
    pkeys = pd.read_parquet('work/pool_meta.parquet', columns=['key']).key.astype(str).values
    ident = np.array([k2g.get(k, -(i + 1)) for i, k in enumerate(pkeys)], np.int64)
    pid = D.sid2pid; has = (pid >= 0) & tg.notna().values
    ident[pid[has]] = tg.values[has].astype(np.int64)
    G['ident'] = ident; G['hna'] = {chem.adduct_index('[M+H]+'), chem.adduct_index('[M+Na]+')}
    sim_audit = load_sim() if A else None
    setup = dict(pool=int(len(pkeys)), rows_with_known_identity=int((ident >= 0).sum()), sim=sim_audit)
    log('setup', json.dumps({k: v for k, v in setup.items() if k != 'sim'}), json.dumps({k: v for k, v in (sim_audit or {}).items() if k != 'gen_meta'}))
    ctx = mp.get_context('fork'); q = ctx.Queue(maxsize=64); counter = ctx.Value('q', 0, lock=False); lock = ctx.Lock()
    procs = [ctx.Process(target=worker, args=(w, q, counter, lock), daemon=True) for w in range(args.workers)]
    for p in procs: p.start()
    dev = args.device; torch.manual_seed(args.seed)
    PFP = D.PFP.to(dev); ELEM = D.elem.to(dev)
    ck = torch.load(INIT, map_location='cpu', weights_only=True)
    model = fpnet.FPNet(ck['nbits'], d=ck['d'], layers=ck['layers'], heads=ck.get('heads', 8)); model.load_state_dict(ck['model']); model = model.to(dev)
    decay = [p for n, p in model.named_parameters() if p.ndim >= 2]; no_decay = [p for n, p in model.named_parameters() if p.ndim < 2]
    opt = torch.optim.AdamW([dict(params=decay, weight_decay=args.wd), dict(params=no_decay, weight_decay=0.0)], lr=args.lr, betas=(0.9, 0.98))
    use_amp = dev == 'cuda'; dtype = fpnet.autocast_dtype(dev) if use_amp else torch.float32
    nj = sim_audit['jobs'] if A else 0; consumed = np.zeros(nj, np.int32)
    t0 = time.time(); step = 0; ema = {}; st_ = dict(elig=0, rep=0, rows=0)
    stop_at = args.smoke_steps or args.steps
    while step < stop_at and not STOP:
        prog = step / args.steps; f = min(1.0, (step + 1) / args.warmup) * (0.02 + 0.98 * 0.5 * (1 + math.cos(math.pi * prog)))
        for g in opt.param_groups: g['lr'] = args.lr * f
        arrs, pos, negs, info = q.get(timeout=300)
        st_['elig'] += info['n_elig']; st_['rep'] += info['n_rep']; st_['rows'] += len(pos)
        if info['sim_jobs']: np.add.at(consumed, np.asarray(info['sim_jobs'], np.int64), 1)   # the ledger counts CONSUMED items only
        inp = tuple(torch.as_tensor(a_, device=dev) for a_ in arrs); pos_t = torch.as_tensor(pos, device=dev)
        cand = torch.as_tensor(np.concatenate([pos[:, None], negs], 1), device=dev)
        with torch.autocast('cuda', dtype=dtype, enabled=use_amp):
            z, el = model(*inp)
        z = z.float(); el = el.float(); fpb = fpnet.unpack_gpu(PFP[cand], D.nbits)
        sc = torch.einsum('bkn,bn->bk', fpb, z)
        target = torch.zeros(len(pos), dtype=torch.long, device=dev)
        l_rank = F.cross_entropy(sc, target); l_bce = F.binary_cross_entropy_with_logits(z, fpb[:, 0]); l_el = F.smooth_l1_loss(el, ELEM[pos_t])
        loss = l_rank + args.w_bce * l_bce + args.w_el * l_el
        opt.zero_grad(set_to_none=True); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); step += 1
        vals = dict(loss=loss.item(), rank=l_rank.item(), bce=l_bce.item(), el=l_el.item(), acc=(sc.argmax(1) == 0).float().mean().item())
        if not math.isfinite(vals['loss']): raise RuntimeError(f'non-finite loss at step {step}')
        for k, v in vals.items(): ema[k] = v if step == 1 else 0.98 * ema[k] + 0.02 * v
        if step % 200 == 0 or step == stop_at:
            log(f"step {step} lr {opt.param_groups[0]['lr']:.2e} " + ' '.join(f'{k} {v:.4f}' for k, v in ema.items()) +
                f" | eligible share {st_['elig'] / max(1, st_['rows']):.3f} sim share {st_['rep'] / max(1, st_['rows']):.4f} | {step / (time.time() - t0):.2f} it/s queue {q.qsize()}")
    led = {}
    if A:
        np.save(f'{args.tag}_consumed_jobs.npy', consumed)
        cp = np.bincount(np.asarray(G['sim']['pid'], np.int64), weights=consumed.astype(np.float64), minlength=len(pkeys))
        cat_pids = np.unique(np.asarray(G['sim']['pid'], np.int64)); e = cp[cat_pids]
        led = dict(consumed_sim_items=int(consumed.sum()), distinct_jobs=int((consumed > 0).sum()), catalog_structures=int(len(cat_pids)),
                   structures_exposure={'0': int((e == 0).sum()), '1': int((e == 1).sum()), '2': int((e == 2).sum()), '3+': int((e >= 3).sum())},
                   plan_wraps=int(counter.value // max(1, len(G['plan']))), counter=int(counter.value), consumed_jobs_file=f'{args.tag}_consumed_jobs.npy')
    receipt = dict(step=step, complete=(step == args.steps and not args.smoke_steps), elapsed_seconds=time.time() - t0, setup=setup, ledger=led,
                   eligible_share_of_rows=st_['elig'] / max(1, st_['rows']), sim_share_of_rows=st_['rep'] / max(1, st_['rows']),
                   sim_share_of_eligible=st_['rep'] / max(1, st_['elig']), args=vars(args), init=INIT, init_sha256=fsha(INIT))
    if receipt['complete'] or args.smoke_steps:
        fpnet.save_ckpt(f'{args.tag}_final.pt' if receipt['complete'] else f'{args.tag}_smoke.pt', model, step, extra=dict(args=vars(args), init=INIT))
    pathlib.Path(f'{args.tag}_receipt.json').write_text(json.dumps(receipt, indent=2, default=str))
    log('DONE', json.dumps({k: v for k, v in receipt.items() if k not in ('args', 'setup')}, default=str)[:1500])
    for p in procs: p.terminate()
    for p in procs: p.join()


if __name__ == '__main__':
    main()
