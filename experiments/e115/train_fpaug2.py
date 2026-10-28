"""115 v2 (Codex 118 / 119): FPNet fine-tuning from a fold-safe checkpoint, R (--sim_frac 0) or A (a fixed share --sim_frac of the POSITIVE [M+H]+ /
[M+Na]+ real slots of every batch replaced by GLACIER-simulated spectra taken IN ORDER from a fixed plan, make_simplan.py).
DETERMINISTIC SCHEDULE (Codex 119): before any worker starts, every training batch ID b = 0 .. S-1 gets its real spectrum IDs (the public
sample_ids with RNG [seed, 1, b]), its H/Na-eligible slots, n_rep(b) = round(alpha * eligible), the replaced slots (RNG [seed, 7, b]) and its
simulated plan positions [sum_{b'<b} n_rep(b'), ... + n_rep(b)). Worker w builds batches b = w, w + W, ... (item RNG [seed, 2, b], simulated
augmentation [seed, 11, b, slot], negatives [seed, 13, b, slot]) into ITS OWN queue; the main loop consumes batch b from queue b mod W, in order.
Hence R and A see the same real items and the same negatives for every non-replaced slot of every batch ID, whatever the worker timing, and the
plan is consumed exactly in order. A dead worker stops training (its queue times out); nothing is refilled from other workers.
Identical between R and A: initial weights, updates, batch, optimizer (fresh AdamW), LR / warmup / cosine schedule, losses (public: f.z ranking CE
over 1 positive + K negatives, FP BCE, elements), negatives and augmentation rules.
Negatives (Codex 118 / 119): the PUBLIC rule on the FULL pool, evaluation-independent: the raw +-10 ppm window (window of <= 1 row -> global random;
< 8 raw rows -> the second half global random), sampled uniformly from the window rows that are NOT the positive's identity (canonical row, second
official keys of its identity group, alias spellings); an empty valid window -> global random. Held-out REAL spectra stay out (Data's holdout).
Identity of pool rows: official keys first (structures scorer_key, train_structs key = pool key), raw keys only where not an official key of
another identity (same rule as make_simplan.py); STOP on conflicting official keys, on a pool row whose training structures disagree on the identity,
or on an alias / second row of the plan's audit that does not share its canonical row's identity.
Simulated inputs (Codex 119): every generation part (prefix) must carry the plan's jobs sha256; ranges 0 <= start <= stop <= requested_stop <= jobs,
together covering the job list exactly once; per part: shard indices inside its range, ok + failed + rejected = its range exactly, ok count = its
meta; NPZ structure (offsets start at 0, strictly increase, end at len(mz) = len(it)), finite positive intensities; planned jobs are QTOF, H / Na,
CE 20 / 40 / 60. Plan positions whose job is a RECORDED failure / rejection are dropped (at most --max_fail); anything else missing -> STOP.
Simulated item: GLACIER peaks -> the public augmentation (peak dropout, intensity / ppm jitter; with p 0.1 ce_known = 0 while the CE VALUE is kept,
as in the public Data.item) -> fpnet.prep_peaks with the THEORETICAL precursor m/z = pool mass - ADDUCT_SHIFT[adduct]; n_merged 1, mode +1.
Input gate: --init sha256 == --init_sha, work/fp_bits.npy sha256 == --bits_sha, the run's split audits passed (split_audit.json / check_inputs.json),
no existing <tag>_final.pt / <tag>_receipt.json in the run. The ledger counts simulated items AFTER a successful optimizer step only.
Usage: python train_fpaug2.py --code C --run R --init CK --init_sha SHA --bits_sha SHA --folds F --tag T --steps S
       [--sim_dir PLAN_DIR --sim_out GEN_PREFIX[,GEN_PREFIX2..] --sim_frac 0.25] [--device cuda] [--smoke_steps n] [--bs 256] [--workers 6]"""
import argparse, glob, hashlib, json, math, os, sys, time, signal, pathlib
os.environ['OMP_NUM_THREADS'] = '1'; os.environ['NUMBA_NUM_THREADS'] = '1'; os.environ['OPENBLAS_NUM_THREADS'] = '1'; os.environ['MKL_NUM_THREADS'] = '1'
sys.dont_write_bytecode = True
import multiprocessing as mp
import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('--code', required=True); ap.add_argument('--run', required=True); ap.add_argument('--init', required=True); ap.add_argument('--folds', required=True)
ap.add_argument('--init_sha', required=True); ap.add_argument('--bits_sha', required=True)
ap.add_argument('--tag', required=True); ap.add_argument('--steps', type=int, required=True)
ap.add_argument('--bs', type=int, default=256); ap.add_argument('--K', type=int, default=63); ap.add_argument('--lr', type=float, default=1e-4); ap.add_argument('--wd', type=float, default=0.01)
ap.add_argument('--warmup', type=int, default=500); ap.add_argument('--merge_p', type=float, default=0.3); ap.add_argument('--w_bce', type=float, default=1.0); ap.add_argument('--w_el', type=float, default=0.1)
ap.add_argument('--workers', type=int, default=6); ap.add_argument('--seed', type=int, default=0); ap.add_argument('--holdout', default='hold,np')
ap.add_argument('--sim_dir', default=''); ap.add_argument('--sim_out', default=''); ap.add_argument('--sim_frac', type=float, default=0.0)
ap.add_argument('--device', default='cuda'); ap.add_argument('--smoke_steps', type=int, default=0); ap.add_argument('--max_fail', type=float, default=0.01)
ap.add_argument('--dump_batches', type=int, default=0)   # technical tests only: save positives / negatives / real IDs of the first n consumed batches
args = ap.parse_args()
A = args.sim_frac > 0
if A and not (args.sim_dir and args.sim_out): sys.exit('STOP: A needs --sim_dir (plan) and --sim_out (generation prefix)')
# absolute paths BEFORE chdir (Codex 119)
CODE = os.path.abspath(args.code); INIT = os.path.abspath(args.init); FOLDS = os.path.abspath(args.folds); RUN = os.path.abspath(args.run)
SIMD = os.path.abspath(args.sim_dir) if args.sim_dir else ''; SIMO = [os.path.abspath(p) for p in args.sim_out.split(',') if p]
sys.path.insert(0, CODE); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'b1_baseline'))
os.chdir(RUN)
import torch
import torch.nn.functional as F
from casmi import fpnet, traindata, chem
from b1_common import ADDUCT_SHIFT

G = {}
STOP = False
COND = {(ad, ce) for ad in ('[M+H]+', '[M+Na]+') for ce in (20.0, 40.0, 60.0)}


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


def die(msg):
    sys.exit(f'STOP: {msg}')


def negatives(D, pos, K, b):
    IDN = G['ident']; n_pool = len(D.pmass)
    out = np.empty((len(pos), K), np.int64)
    for r in range(len(pos)):
        rng = np.random.default_rng([args.seed, 13, b, r]); p = int(pos[r]); idp = IDN[p]

        def glob_(n):   # global random decoys, never the positive's identity
            x = rng.integers(0, n_pool, n); bad = IDN[x] == idp
            while bad.any(): x[bad] = rng.integers(0, n_pool, int(bad.sum())); bad = IDN[x] == idp
            return x
        m = D.pmass[p]; tol = m * 10e-6
        lo = int(np.searchsorted(D.pmass, m - tol, 'left')); hi = int(np.searchsorted(D.pmass, m + tol, 'right'))
        if hi - lo <= 1: out[r] = glob_(K); continue
        win = np.arange(lo, hi); valid = win[IDN[lo:hi] != idp]
        c = valid[rng.integers(0, len(valid), K)] if len(valid) else glob_(K)
        if hi - lo < 8:   # tiny RAW windows: the second half global random (public rule)
            k = K // 2; c[k:] = glob_(K - k)
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
    if rng.random() < 0.1: ce_known = 0.0   # the CE value is kept (public Data.item), only the flag is hidden
    prec = float(D.pmass[int(SIM['pid'][j])]) - ADDUCT_SHIFT[ad]
    pm, pi = fpnet.prep_peaks(mz, it, prec)
    return dict(mz=pm, it=pi, prec=prec, adduct_ix=chem.adduct_index(ad), ce=ce, ce_known=ce_known, n_merged=1, mode=1.0)


def worker(wid, q, n_batches):
    signal.signal(signal.SIGTERM, signal.SIG_DFL); signal.signal(signal.SIGHUP, signal.SIG_DFL)
    torch.set_num_threads(1)
    D = G['D']; S = G['sched']
    for b in range(wid, n_batches, args.workers):
        ids = S['ids'][b]; D.rng = np.random.default_rng([args.seed, 2, b])
        items = [D.item(int(i), args.merge_p, True) for i in ids]   # the real stream of batch b is identical in R and A
        pos = D.sid2pid[D.sid[ids]].copy(); sim_jobs = []
        for k, p_ in zip(S['slots'][b], range(int(S['start'][b]), int(S['start'][b]) + len(S['slots'][b]))):
            j = int(G['plan'][p_ % len(G['plan'])])
            items[k] = sim_item(D, j, np.random.default_rng([args.seed, 11, b, int(k)])); pos[k] = int(G['sim']['pid'][j]); sim_jobs.append(j)
        negs = negatives(D, pos, args.K, b)
        q.put((tuple(t.numpy() for t in fpnet.collate(items, 'cpu')), pos, negs, dict(b=b, n_elig=int(S['n_elig'][b]), n_rep=len(sim_jobs), sim_jobs=sim_jobs)))


def identity_map(D):
    ts = pd.read_parquet('work/train_structs.parquet', columns=['sid', 'inchikey14', 'key', 'rawkey'])
    if not (ts.sid.values == np.arange(len(ts))).all(): die('train_structs sid is not the row index')
    st = pd.read_parquet(FOLDS, columns=['inchikey14', 'scorer_key', 'identity_group'])
    ik2g = dict(zip(st.inchikey14.astype(str), st.identity_group.astype(np.int64)))
    tg = ts.inchikey14.astype(str).map(ik2g)
    if tg.isna().any(): die(f'{int(tg.isna().sum())} training structures without an identity')
    tg = tg.values.astype(np.int64)
    k2g = {}
    for k, g in [(str(k), int(g)) for k, g in zip(st.scorer_key, st.identity_group)] + [(str(k), int(g)) for k, g in zip(ts.key, tg)]:
        if k2g.setdefault(k, g) != g: die(f'official key {k} maps to identities {k2g[k]} and {g}')
    official = set(k2g); raw = {}
    for k, g in [(str(k), int(g)) for k, g in zip(st.inchikey14, st.identity_group)] + [(str(k), int(g)) for k, g in zip(ts.rawkey, tg)]:
        if k in official: continue
        if raw.setdefault(k, g) != g: die(f'raw key {k} maps to identities {raw[k]} and {g}')
    k2g.update(raw)
    pkeys = pd.read_parquet('work/pool_meta.parquet', columns=['key']).key.astype(str).values
    ident = np.array([k2g.get(k, -(i + 1)) for i, k in enumerate(pkeys)], np.int64)
    pid = D.sid2pid; has = pid >= 0
    chk = pd.DataFrame(dict(pid=pid[has], g=tg[has])).groupby('pid').g.nunique()
    if (chk > 1).any(): die(f'{int((chk > 1).sum())} pool rows whose training structures disagree on the identity')
    ident[pid[has]] = tg[has]
    return ident, pkeys


def load_sim(pkeys):
    pm = json.load(open(os.path.join(SIMD, 'plan_manifest.json')))
    for f, h in pm['outputs'].items():
        if fsha(os.path.join(SIMD, f)) != h: die(f'plan file {f} changed since make_simplan')
    pool_in = [h for p, h in pm.get('inputs', {}).items() if p.endswith('pool_meta.parquet')]
    if pool_in and pool_in[0] != fsha('work/pool_meta.parquet'): die("the run's pool_meta differs from the plan's input pool")
    jobs = json.load(open(os.path.join(SIMD, 'jobs.json'))); nj = len(jobs)
    jpid = np.load(os.path.join(SIMD, 'jobs_pid.npy'), allow_pickle=False).astype(np.int64); plan = np.load(os.path.join(SIMD, 'plan.npy'), allow_pickle=False).astype(np.int64)
    if len(jpid) != nj or plan.min() < 0 or plan.max() >= nj: die('jobs_pid / plan inconsistent with the job list')
    if (jpid[plan] < 0).any() or jpid[plan].max() >= len(pkeys): die('a planned job has no pool row')
    for j in np.unique(plan):
        jb = jobs[int(j)]
        if str(jb[2]) != 'QTOF' or (str(jb[1]), float(jb[3])) not in COND: die(f'planned job {int(j)} is not QTOF x H/Na x CE 20/40/60')
    cover = np.zeros(nj, np.int32); start = np.full(nj, -1, np.int64); ln = np.zeros(nj, np.int32); MZ, IT = [], []; base = 0
    recorded_fail = np.zeros(nj, bool); parts = []
    for pf in SIMO:
        m = json.load(open(pf + '_meta.json'))
        if m.get('hashes', {}).get('jobs') != pm['outputs']['jobs.json']: die(f'{pf}: generated from a different job list')
        s_, e_, rq = int(m['start']), int(m['stop']), int(m['requested_stop'])
        if not (0 <= s_ <= e_ <= rq <= nj) or int(m['n_jobs']) != e_ - s_: die(f'{pf}: bad range [{s_}, {e_}) / {rq} / {nj}')
        cover[s_:e_] += 1; seen = np.zeros(nj, bool); n_ok = 0
        for k in range(int(m['chunks'])):
            f = f'{pf}_{k:04d}.npz'
            with np.load(f, allow_pickle=False) as Z:
                idx = Z['idx'].astype(np.int64); off = Z['off'].astype(np.int64); mz = Z['mz']; it = Z['it']   # each array read ONCE
            if len(off) != len(idx) + 1 or off[0] != 0 or (len(idx) and (np.diff(off) <= 0).any()) or off[-1] != len(mz) or len(mz) != len(it):
                die(f'{f}: malformed offsets')
            if len(idx) and (idx.min() < s_ or idx.max() >= e_): die(f'{f}: job index outside its part range')
            if seen[idx].any() or len(np.unique(idx)) != len(idx) or (start[idx] >= 0).any(): die(f'{f}: duplicate job index')
            if not (np.isfinite(mz).all() and np.isfinite(it).all() and (it > 0).all()): die(f'{f}: non-finite or non-positive peaks')
            seen[idx] = True; start[idx] = base + off[:-1]; ln[idx] = np.diff(off).astype(np.int32); MZ.append(mz); IT.append(it); base += len(mz); n_ok += len(idx)
        fr = np.asarray(list(m.get('failed_idx', [])) + list(m.get('rejected_idx', [])), np.int64)
        if n_ok != int(m['n_ok']) or len(fr) != int(m['n_fail']) + sum(m.get('rejected', {}).values()): die(f'{pf}: counts differ from its meta')
        if len(fr) and (fr.min() < s_ or fr.max() >= e_ or seen[fr].any()): die(f'{pf}: failed / rejected indices inconsistent')
        if n_ok + len(fr) != e_ - s_: die(f'{pf}: ok + failed + rejected != its range')
        recorded_fail[fr] = True; parts.append(dict(prefix=pf, start=s_, stop=e_, complete=m.get('complete'), n_ok=n_ok, n_fail=len(fr), hashes=m.get('hashes')))
    if not (cover == 1).all(): die(f'generation parts do not cover the job list exactly once (missing {(cover == 0).sum()}, overlapping {(cover > 1).sum()})')
    ok = start >= 0
    miss = ~ok[plan]
    if (miss & ~recorded_fail[plan]).any(): die('a planned job is neither generated nor a recorded failure')
    if miss.mean() > args.max_fail: die(f'{miss.mean():.4f} of the plan positions are recorded failures (> {args.max_fail})')
    G['plan'] = plan[~miss]
    G['sim'] = dict(start=start, len=ln, mz=np.concatenate(MZ) if MZ else np.zeros(0, np.float32), it=np.concatenate(IT) if IT else np.zeros(0, np.float32),
                    pid=jpid, adduct=np.array([j[1] for j in jobs], dtype=object), ce=np.array([float(j[3]) for j in jobs], np.float64))
    return dict(jobs=nj, ok=int(ok.sum()), plan=len(plan), plan_used=int(len(G['plan'])), plan_positions_dropped_failed=int(miss.sum()), parts=parts,
                plan_sha256=pm['outputs']['plan.npy'], jobs_sha256=pm['outputs']['jobs.json'], catalog_sha256=pm['outputs']['catalog.parquet'])


def audit_aliases(ident):
    p = os.path.join(SIMD, 'alias_audit.csv')
    if not os.path.exists(p): return dict(alias_audit='absent (existing-mode plan)')
    al = pd.read_csv(p)
    bad = [int(r.row_pid) for r in al.itertuples() if ident[int(r.row_pid)] != ident[int(r.canonical_pid)]]
    if bad: die(f'alias / second rows not sharing their canonical identity: {bad[:5]}')
    return dict(alias_audit_rows=len(al))


def main():
    torch.set_num_threads(1)
    # input gate (Codex 119)
    if os.path.exists(f'{args.tag}_final.pt') or os.path.exists(f'{args.tag}_receipt.json'): die('the run already holds this tag (fresh output only)')
    if fsha(INIT) != args.init_sha: die('init checkpoint sha256 differs from the registered one')
    if fsha('work/fp_bits.npy') != args.bits_sha: die('fp_bits sha256 differs from the registered one')
    for f in ('split_audit.json', 'check_inputs.json'):
        if not (os.path.exists(f) and json.load(open(f)).get('passed') is True): die(f'{f} missing or not passed in the run')
    hold = tuple(args.holdout.split(','))
    D = traindata.Data('cpu', seed=args.seed, holdout_folds=hold); G['D'] = D
    if np.isin(D.fold[D.sid[D.tr]], hold).any(): die('a held-out real spectrum is in the training stream')
    ident, pkeys = identity_map(D); G['ident'] = ident
    hna = {chem.adduct_index('[M+H]+'), chem.adduct_index('[M+Na]+')}
    sim_audit = load_sim(pkeys) if A else None
    al_audit = audit_aliases(ident) if A else None
    G.setdefault('plan', np.zeros(1, np.int64))
    # deterministic schedule: real IDs, eligible slots, replaced slots, plan positions per batch ID
    n_batches = args.smoke_steps or args.steps
    ids, n_elig, slots, start = [], np.zeros(n_batches, np.int64), [], np.zeros(n_batches, np.int64); cum = 0
    for b in range(n_batches):
        D.rng = np.random.default_rng([args.seed, 1, b]); x = D.sample_ids(args.bs); ids.append(x)
        el = [k for k, i in enumerate(x) if D.mode[i] > 0 and int(D.adduct[i]) in hna]; n_elig[b] = len(el)
        n_rep = int(round(args.sim_frac * len(el))) if A else 0
        sl = np.random.default_rng([args.seed, 7, b]).choice(el, size=n_rep, replace=False) if n_rep else np.zeros(0, np.int64)
        slots.append(np.asarray(sl, np.int64)); start[b] = cum; cum += n_rep
    G['sched'] = dict(ids=ids, n_elig=n_elig, slots=slots, start=start)
    sched = dict(batches=n_batches, eligible_share=float(n_elig.sum() / (n_batches * args.bs)), planned_sim_items=int(cum),
                 planned_wrap_positions=int(max(0, cum - len(G['plan']))) if A else 0)
    setup = dict(pool=int(len(pkeys)), rows_with_known_identity=int((ident >= 0).sum()), schedule=sched, sim=sim_audit, aliases=al_audit,
                 init_sha256=args.init_sha, bits_sha256=args.bits_sha, split_sha256=fsha('work/split.parquet'), pool_fp_sha256=fsha('work/pool_fp.npy'))
    log('setup', json.dumps(sched), json.dumps({k: v for k, v in (sim_audit or {}).items() if k != 'parts'}))
    ctx = mp.get_context('fork'); queues = [ctx.Queue(maxsize=8) for _ in range(args.workers)]
    procs = [ctx.Process(target=worker, args=(w, queues[w], n_batches), daemon=True) for w in range(args.workers)]
    for p in procs: p.start()
    dev = args.device; torch.manual_seed(args.seed)
    PFP = D.PFP.to(dev); ELEM = D.elem.to(dev)
    ck = torch.load(INIT, map_location='cpu', weights_only=True)
    model = fpnet.FPNet(ck['nbits'], d=ck['d'], layers=ck['layers'], heads=ck.get('heads', 8)); model.load_state_dict(ck['model']); model = model.to(dev)
    decay = [p for n, p in model.named_parameters() if p.ndim >= 2]; no_decay = [p for n, p in model.named_parameters() if p.ndim < 2]
    opt = torch.optim.AdamW([dict(params=decay, weight_decay=args.wd), dict(params=no_decay, weight_decay=0.0)], lr=args.lr, betas=(0.9, 0.98))
    use_amp = dev == 'cuda'; dtype = fpnet.autocast_dtype(dev) if use_amp else torch.float32
    nj = sim_audit['jobs'] if A else 0; consumed = np.zeros(nj, np.int32)
    t0 = time.time(); step = 0; ema = {}; st_ = dict(elig=0, rep=0, rows=0); DUMP = {}
    while step < n_batches and not STOP:
        prog = step / args.steps; f = min(1.0, (step + 1) / args.warmup) * (0.02 + 0.98 * 0.5 * (1 + math.cos(math.pi * prog)))
        for g in opt.param_groups: g['lr'] = args.lr * f
        w = step % args.workers
        try:
            arrs, pos, negs, info = queues[w].get(timeout=300)
        except Exception:
            die(f'worker {w} produced no batch {step} within 300 s (alive: {procs[w].is_alive()})')
        if info['b'] != step: die(f'batch order broken: got {info["b"]}, expected {step}')
        inp = tuple(torch.as_tensor(a_, device=dev) for a_ in arrs); pos_t = torch.as_tensor(pos, device=dev)
        cand = torch.as_tensor(np.concatenate([pos[:, None], negs], 1), device=dev)
        with torch.autocast('cuda', dtype=dtype, enabled=use_amp):
            z, el = model(*inp)
        z = z.float(); el = el.float(); fpb = fpnet.unpack_gpu(PFP[cand], D.nbits)
        sc = torch.einsum('bkn,bn->bk', fpb, z)
        target = torch.zeros(len(pos), dtype=torch.long, device=dev)
        l_rank = F.cross_entropy(sc, target); l_bce = F.binary_cross_entropy_with_logits(z, fpb[:, 0]); l_el = F.smooth_l1_loss(el, ELEM[pos_t])
        loss = l_rank + args.w_bce * l_bce + args.w_el * l_el
        if not math.isfinite(loss.item()): raise RuntimeError(f'non-finite loss at step {step + 1}')
        opt.zero_grad(set_to_none=True); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); step += 1
        st_['elig'] += info['n_elig']; st_['rep'] += info['n_rep']; st_['rows'] += len(pos)
        if info['sim_jobs']: np.add.at(consumed, np.asarray(info['sim_jobs'], np.int64), 1)   # counted AFTER a successful update only
        if step <= args.dump_batches:
            DUMP.setdefault('pos', []).append(np.asarray(pos, np.int64)); DUMP.setdefault('negs', []).append(np.asarray(negs, np.int64))
            DUMP.setdefault('ids', []).append(np.asarray(G['sched']['ids'][step - 1], np.int64)); DUMP.setdefault('slots', []).append(np.pad(G['sched']['slots'][step - 1], (0, args.bs - len(G['sched']['slots'][step - 1])), constant_values=-1))
            DUMP.setdefault('sim_jobs', []).append(np.pad(np.asarray(info['sim_jobs'], np.int64), (0, args.bs - len(info['sim_jobs'])), constant_values=-1))
        vals = dict(loss=loss.item(), rank=l_rank.item(), bce=l_bce.item(), el=l_el.item(), acc=(sc.argmax(1) == 0).float().mean().item())
        for k, v in vals.items(): ema[k] = v if step == 1 else 0.98 * ema[k] + 0.02 * v
        if step % 200 == 0 or step == n_batches:
            log(f"step {step} lr {opt.param_groups[0]['lr']:.2e} " + ' '.join(f'{k} {v:.4f}' for k, v in ema.items()) +
                f" | eligible share {st_['elig'] / max(1, st_['rows']):.3f} sim share {st_['rep'] / max(1, st_['rows']):.4f} | {step / (time.time() - t0):.2f} it/s")
    if DUMP: np.savez(f'{args.tag}_dump.npz', **{k: np.stack(v) for k, v in DUMP.items()})
    led = {}
    if A:
        np.save(f'{args.tag}_consumed_jobs.npy', consumed)
        cp = np.bincount(np.asarray(G['sim']['pid'][G['plan']], np.int64), minlength=len(pkeys)) > 0
        exp_ = np.bincount(np.asarray(G['sim']['pid'], np.int64)[consumed > 0], weights=consumed[consumed > 0].astype(np.float64), minlength=len(pkeys))[cp]
        led = dict(consumed_sim_items=int(consumed.sum()), distinct_jobs=int((consumed > 0).sum()), plan_structures=int(cp.sum()),
                   structures_exposure={'0': int((exp_ == 0).sum()), '1': int((exp_ == 1).sum()), '2': int((exp_ == 2).sum()), '3+': int((exp_ >= 3).sum())},
                   consumed_jobs_file=f'{args.tag}_consumed_jobs.npy', consumed_jobs_sha256=fsha(f'{args.tag}_consumed_jobs.npy'))
    receipt = dict(step=step, complete=(step == args.steps and not args.smoke_steps), elapsed_seconds=time.time() - t0, setup=setup, ledger=led,
                   eligible_share_of_rows=st_['elig'] / max(1, st_['rows']), sim_share_of_rows=st_['rep'] / max(1, st_['rows']),
                   sim_share_of_eligible=st_['rep'] / max(1, st_['elig']), args=vars(args), init=INIT, code_sha256=fsha(os.path.abspath(__file__)))
    if receipt['complete'] or args.smoke_steps:
        fn = f'{args.tag}_final.pt' if receipt['complete'] else f'{args.tag}_smoke.pt'
        fpnet.save_ckpt(fn, model, step, extra=dict(args=vars(args), init=INIT)); receipt['checkpoint'] = fn; receipt['checkpoint_sha256'] = fsha(fn)
    pathlib.Path(f'{args.tag}_receipt.json').write_text(json.dumps(receipt, indent=2, default=str))
    log('DONE', json.dumps({k: v for k, v in receipt.items() if k not in ('args', 'setup')}, default=str)[:1500])
    for p in procs: p.terminate()
    for p in procs: p.join()


if __name__ == '__main__':
    main()
