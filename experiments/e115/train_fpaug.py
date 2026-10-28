"""115 pilot (Codex 115 Q3): FPNet fine-tuning from a fold-safe checkpoint, R (real spectra only, --sim_frac 0) or A (the same, but a fixed share
--sim_frac of the POSITIVE [M+H]+ / [M+Na]+ real slots of every batch is replaced by GLACIER-simulated spectra of the fixed catalog). Everything
else is identical between R and A: initial weights, updates, batch, optimizer, schedule, losses (the public ones: f.z ranking CE over 1 positive +
K negatives, FP BCE, elements), negatives (uniform from the +-10 ppm window of the ALLOWED pool: held-out identity groups and alias rows removed,
the positive's own group removed), augmentation (the public peak dropout / intensity / ppm jitter, also applied to simulated spectra).
Simulated item: GLACIER peaks (gl_simulate.py output; post-processed top-100, max 1) -> fpnet.prep_peaks with the THEORETICAL precursor
m/z = pool mass - ADDUCT_SHIFT[adduct] (no electron correction, never GLACIER's internal precursor 0), CE = the job's CE (known), n_merged 1,
mode +1; positive = the catalog structure's pool row. The realised simulated share of every batch is logged and stored in the receipt.
No evaluation inside training; checkpoints only at --steps. Usage: python train_fpaug.py --code C --run R --init CK --folds F --tag T --steps S
[--sim_dir DIR --sim_frac 0.25] [--smoke_steps n]"""
import argparse, glob, json, math, os, sys, time, signal, pathlib
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
ap.add_argument('--sim_dir', default=''); ap.add_argument('--sim_frac', type=float, default=0.0); ap.add_argument('--smoke_steps', type=int, default=0)
args = ap.parse_args()
INIT = os.path.abspath(args.init); FOLDS = os.path.abspath(args.folds); SIMD = os.path.abspath(args.sim_dir) if args.sim_dir else ''
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


def negatives(D, pos, K, rng):
    OKP, OKM, GRP = G['okpid'], G['okmass'], G['grp']
    m = D.pmass[pos]; tol = m * 10e-6
    lo = np.searchsorted(OKM, m - tol, 'left'); hi = np.searchsorted(OKM, m + tol, 'right')
    out = np.empty((len(pos), K), np.int64)
    for r in range(len(pos)):
        c = OKP[lo[r]:hi[r]]; gp = GRP[pos[r]]
        c = c[(c != pos[r]) & ((GRP[c] != gp) | (gp < 0))]
        def rand(n):
            x = OKP[rng.integers(0, len(OKP), n)]
            bad = (x == pos[r]) | ((GRP[x] == gp) & (gp >= 0))
            while bad.any():
                x[bad] = OKP[rng.integers(0, len(OKP), int(bad.sum()))]; bad = (x == pos[r]) | ((GRP[x] == gp) & (gp >= 0))
            return x
        if len(c) == 0: out[r] = rand(K)
        elif len(c) < 8: k = K // 2; out[r, :k] = c[rng.integers(0, len(c), k)]; out[r, k:] = rand(K - k)
        else: out[r] = c[rng.integers(0, len(c), K)]
    return out


def sim_item(D, rec, rng):
    pid, ad, ce, mz, it = rec
    mz = mz.astype(np.float64).copy(); it = it.astype(np.float64).copy()
    if len(mz) > 4:   # the public augmentation (traindata.Data.item, aug=True)
        keep = rng.random(len(mz)) > rng.uniform(0.0, 0.3)
        if keep.sum() >= 3: mz, it = mz[keep], it[keep]
    it = it * np.exp(rng.normal(0.0, 0.3, size=len(it))); mz = mz * (1.0 + rng.normal(0.0, 4e-6, size=len(mz)))
    prec = float(D.pmass[pid]) - ADDUCT_SHIFT[ad]
    pm, pi = fpnet.prep_peaks(mz, it, prec)
    return dict(mz=pm, it=pi, prec=prec, adduct_ix=chem.adduct_index(ad), ce=float(ce), ce_known=1.0, n_merged=1, mode=1.0)


def worker(wid, q):
    signal.signal(signal.SIGTERM, signal.SIG_DFL); signal.signal(signal.SIGHUP, signal.SIG_DFL)
    torch.set_num_threads(1)
    D = G['D']; D.rng = np.random.default_rng(args.seed * 1000 + wid + 1); SIM = G['sim']; HNA = G['hna']
    while True:
        ids = D.sample_ids(args.bs)
        items = [D.item(int(i), args.merge_p, True) for i in ids]
        pos = D.sid2pid[D.sid[ids]].copy()
        elig = [k for k, i in enumerate(ids) if D.mode[i] > 0 and int(D.adduct[i]) in HNA]; n_rep = 0
        if SIM and args.sim_frac > 0 and elig:
            n_rep = int(round(args.sim_frac * len(elig)))
            for k in D.rng.choice(elig, size=n_rep, replace=False):
                rec = SIM[int(D.rng.integers(0, len(SIM)))]; items[k] = sim_item(D, rec, D.rng); pos[k] = rec[0]
        negs = negatives(D, pos, args.K, D.rng)
        q.put((tuple(t.numpy() for t in fpnet.collate(items, 'cpu')), pos, negs, dict(n_elig=len(elig), n_rep=n_rep)))


def load_sim(D):
    if not SIMD or args.sim_frac <= 0: return []
    cat = pd.read_parquet(os.path.join(SIMD, 'catalog.parquet'), columns=['pid', 'smiles']); s2p = dict(zip(cat.smiles.astype(str), cat.pid.astype(int)))
    jobs = json.load(open(os.path.join(SIMD, 'jobs.json'))); recs = []
    for f in sorted(glob.glob(os.path.join(SIMD, 'sim_*.npz'))):
        Z = np.load(f, allow_pickle=False)
        for n, j in enumerate(Z['idx']):
            smi, ad, ins, ce = jobs[int(j)]; o0, o1 = int(Z['off'][n]), int(Z['off'][n + 1])
            if smi in s2p and o1 > o0: recs.append((s2p[smi], ad, float(ce), Z['mz'][o0:o1], Z['it'][o0:o1]))
    assert all(np.isfinite(D.pmass[r[0]]) for r in recs)
    return recs


def main():
    torch.set_num_threads(1)
    hold = tuple(args.holdout.split(','))
    D = traindata.Data('cpu', seed=args.seed, holdout_folds=hold); G['D'] = D
    ts = pd.read_parquet('work/train_structs.parquet', columns=['sid', 'inchikey14', 'key', 'rawkey'])
    st = pd.read_parquet(FOLDS, columns=['inchikey14', 'identity_group', 'scorer_key']).drop_duplicates('inchikey14')
    gsid = ts[['inchikey14']].merge(st[['inchikey14', 'identity_group']], on='inchikey14', how='left', validate='many_to_one').identity_group.values.astype(np.int64)
    npool = len(D.pmass); grp = np.full(npool, -1, np.int64); pid = D.sid2pid; has = pid >= 0; grp[pid[has]] = gsid[has]
    held_groups = np.unique(gsid[np.isin(D.fold, hold)])
    bad = np.zeros(npool, bool); bad[pid[has & np.isin(D.fold, hold)]] = True; bad |= (grp >= 0) & np.isin(grp, held_groups)
    known = set(ts.key.astype(str)) | set(ts.rawkey.astype(str)) | set(st.inchikey14.astype(str)) | set(st.scorer_key.astype(str))
    pkeys = pd.read_parquet('work/pool_meta.parquet', columns=['key']).key.astype(str).values
    bad |= (grp < 0) & np.fromiter((k in known for k in pkeys), bool, npool)
    okpid = np.flatnonzero(~bad); G['okpid'], G['okmass'], G['grp'] = okpid, D.pmass[okpid], grp
    G['hna'] = {chem.adduct_index('[M+H]+'), chem.adduct_index('[M+Na]+')}
    SIM = load_sim(D); G['sim'] = SIM
    held_pids = set(np.flatnonzero(bad).tolist()); n_sim_held = sum(1 for r in SIM if r[0] in held_pids)
    neg_audit = dict(pool=int(npool), excluded=int(bad.sum()), allowed=int(len(okpid)), sim_records=len(SIM), sim_structures=len({r[0] for r in SIM}), sim_records_on_excluded_rows=n_sim_held)
    log('setup', json.dumps(neg_audit))
    q = mp.get_context('fork').Queue(maxsize=64)
    procs = [mp.get_context('fork').Process(target=worker, args=(w, q), daemon=True) for w in range(args.workers)]
    for p in procs: p.start()
    dev = 'cuda'; torch.manual_seed(args.seed)
    PFP = D.PFP.to(dev); ELEM = D.elem.to(dev)
    ck = torch.load(INIT, map_location='cpu', weights_only=True)
    model = fpnet.FPNet(ck['nbits'], d=ck['d'], layers=ck['layers'], heads=ck.get('heads', 8)); model.load_state_dict(ck['model']); model = model.to(dev)
    decay = [p for n, p in model.named_parameters() if p.ndim >= 2]; no_decay = [p for n, p in model.named_parameters() if p.ndim < 2]
    opt = torch.optim.AdamW([dict(params=decay, weight_decay=args.wd), dict(params=no_decay, weight_decay=0.0)], lr=args.lr, betas=(0.9, 0.98))
    dtype = fpnet.autocast_dtype(dev); target = torch.zeros(args.bs, dtype=torch.long, device=dev)
    t0 = time.time(); step = 0; ema = {}; st_ = dict(elig=0, rep=0, rows=0)
    stop_at = args.smoke_steps or args.steps
    while step < stop_at and not STOP:
        prog = step / args.steps; f = min(1.0, (step + 1) / args.warmup) * (0.02 + 0.98 * 0.5 * (1 + math.cos(math.pi * prog)))
        for g in opt.param_groups: g['lr'] = args.lr * f
        arrs, pos, negs, info = q.get(timeout=300)
        st_['elig'] += info['n_elig']; st_['rep'] += info['n_rep']; st_['rows'] += len(pos)
        inp = tuple(torch.as_tensor(a_, device=dev) for a_ in arrs); pos_t = torch.as_tensor(pos, device=dev)
        cand = torch.as_tensor(np.concatenate([pos[:, None], negs], 1), device=dev)
        with torch.autocast('cuda', dtype=dtype):
            z, el = model(*inp)
        z = z.float(); el = el.float(); fpb = fpnet.unpack_gpu(PFP[cand], D.nbits)
        sc = torch.einsum('bkn,bn->bk', fpb, z)
        l_rank = F.cross_entropy(sc, target); l_bce = F.binary_cross_entropy_with_logits(z, fpb[:, 0]); l_el = F.smooth_l1_loss(el, ELEM[pos_t])
        loss = l_rank + args.w_bce * l_bce + args.w_el * l_el
        opt.zero_grad(set_to_none=True); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); step += 1
        vals = dict(loss=loss.item(), rank=l_rank.item(), bce=l_bce.item(), el=l_el.item(), acc=(sc.argmax(1) == 0).float().mean().item())
        if not math.isfinite(vals['loss']): raise RuntimeError(f'non-finite loss at step {step}')
        for k, v in vals.items(): ema[k] = v if step == 1 else 0.98 * ema[k] + 0.02 * v
        if step % 200 == 0 or step == stop_at:
            log(f"step {step} lr {opt.param_groups[0]['lr']:.2e} " + ' '.join(f'{k} {v:.4f}' for k, v in ema.items()) +
                f" | sim share of batches {st_['rep'] / max(1, st_['rows']):.4f} (of eligible {st_['rep'] / max(1, st_['elig']):.3f}) | {step / (time.time() - t0):.2f} it/s queue {q.qsize()}")
    receipt = dict(step=step, complete=(step == args.steps and not args.smoke_steps), elapsed_seconds=time.time() - t0, setup=neg_audit,
                   sim_share_of_rows=st_['rep'] / max(1, st_['rows']), sim_share_of_eligible=st_['rep'] / max(1, st_['elig']), args=vars(args), init=INIT)
    if receipt['complete'] or args.smoke_steps:
        fpnet.save_ckpt(f'{args.tag}_final.pt' if receipt['complete'] else f'{args.tag}_smoke.pt', model, step, extra=dict(args=vars(args), init=INIT))
    pathlib.Path(f'{args.tag}_receipt.json').write_text(json.dumps(receipt, indent=2)); log('DONE', json.dumps({k: v for k, v in receipt.items() if k != 'args'}))
    for p in procs: p.terminate()
    for p in procs: p.join()


if __name__ == '__main__':
    main()
