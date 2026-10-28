"""111 (Codex 111): training of the own dual-encoder head (n111_model.N111) on the fold-safe FPNet.
Loop and data access follow the public fold-safe trainer (train_fivefold.py, Apache-2.0; casmi/traindata.Data reads <run>/work/), with these
own changes:
  - init: the FPNet part from a fold-safe checkpoint (--init; loaded with weights_only=True); new heads (spectrum projection, molecule MLP, scale);
  - loss: w_cos * CE over cos-scores (1 positive + K mass-window negatives) + the public losses as auxiliaries (f.z ranking CE, FP BCE, elements);
  - negatives (Codex 111 (2)(3)): from the +-10 ppm pool window AFTER removing (a) every pool structure of a held-out identity group (split labels
    hold / np = evaluation fold + NP-example groups; their structures are never shown as negatives) and (b) every structure of the positive's own
    identity group; when >= 8 valid same-formula structures exist, K_F (48) of the K (63) are drawn from them and the rest from the whole valid
    window (fixed ratio); windows with < 8 valid structures are half filled with random valid decoys, empty windows fully (rates are logged);
  - schedule: linear warmup, cosine to 2% at --steps; checkpoints only at the fixed --save_at steps and at --steps (no evaluation inside training,
    no selection by training metrics); no resume (a failed run is restarted from scratch with the same seed).
Usage: python train_n111.py --code <casmi code> --run <run dir with work/> --init <fpnet ckpt> --tag T --steps S --save_at a,b [--smoke_steps n]"""
import argparse, json, math, os, sys, time, signal, pathlib
os.environ['OMP_NUM_THREADS'] = '1'; os.environ['NUMBA_NUM_THREADS'] = '1'; os.environ['OPENBLAS_NUM_THREADS'] = '1'; os.environ['MKL_NUM_THREADS'] = '1'
sys.dont_write_bytecode = True
import multiprocessing as mp
import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('--code', required=True); ap.add_argument('--run', required=True); ap.add_argument('--init', required=True); ap.add_argument('--folds', required=True)
ap.add_argument('--tag', required=True); ap.add_argument('--steps', type=int, required=True); ap.add_argument('--save_at', default='')
ap.add_argument('--bs', type=int, default=256); ap.add_argument('--K', type=int, default=63); ap.add_argument('--K_F', type=int, default=48, help='same-formula negatives per row when the window has >= 8 valid same-formula structures')
ap.add_argument('--lr_fp', type=float, default=1e-4); ap.add_argument('--lr_head', type=float, default=5e-4); ap.add_argument('--wd', type=float, default=0.01)
ap.add_argument('--warmup', type=int, default=500); ap.add_argument('--merge_p', type=float, default=0.3)
ap.add_argument('--w_cos', type=float, default=1.0); ap.add_argument('--w_rank', type=float, default=1.0); ap.add_argument('--w_bce', type=float, default=1.0); ap.add_argument('--w_el', type=float, default=0.1)
ap.add_argument('--d_out', type=int, default=256); ap.add_argument('--hid', type=int, default=1024)
ap.add_argument('--workers', type=int, default=12); ap.add_argument('--seed', type=int, default=0); ap.add_argument('--holdout', default='hold,np')
ap.add_argument('--smoke_steps', type=int, default=0)
args = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__)); INIT = os.path.abspath(args.init); FOLDS = os.path.abspath(args.folds)
sys.path.insert(0, args.code); sys.path.insert(0, HERE)
os.chdir(args.run)
import torch
import torch.nn.functional as F
from casmi import fpnet, traindata
import n111_model as NM

G = {}
STOP = False
def stop_requested(signum, frame):
    global STOP
    STOP = True
signal.signal(signal.SIGTERM, stop_requested); signal.signal(signal.SIGHUP, stop_requested)


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def negatives(D, pos, K, rng):
    """K negatives per positive pool id from the +-10 ppm window of the ALLOWED pool structures, the positive's identity group removed.
    Same-formula concentration (fixed ratio): if the window has >= 8 valid same-formula structures, K_F of the K come from them and K - K_F from
    the whole valid window; otherwise K from the valid window; windows with < 8 valid structures are half filled with random valid decoys,
    empty windows fully (all uniform with replacement; counts logged)."""
    OKP, OKM, GRP, FORM = G['okpid'], G['okmass'], G['grp'], G['formula']
    m = D.pmass[pos]; tol = m * 10e-6
    lo = np.searchsorted(OKM, m - tol, 'left'); hi = np.searchsorted(OKM, m + tol, 'right')
    out = np.empty((len(pos), K), np.int64); n_small = n_empty = n_conc = 0
    for r in range(len(pos)):
        c = OKP[lo[r]:hi[r]]; gp = GRP[pos[r]]
        c = c[(c != pos[r]) & ((GRP[c] != gp) | (gp < 0))]
        def rand(n):
            x = OKP[rng.integers(0, len(OKP), n)]
            bad = (x == pos[r]) | ((GRP[x] == gp) & (gp >= 0))
            while bad.any():
                x[bad] = OKP[rng.integers(0, len(OKP), int(bad.sum()))]; bad = (x == pos[r]) | ((GRP[x] == gp) & (gp >= 0))
            return x
        if len(c) == 0:
            out[r] = rand(K); n_empty += 1
        elif len(c) < 8:
            k = K // 2; out[r, :k] = c[rng.integers(0, len(c), k)]; out[r, k:] = rand(K - k); n_small += 1
        else:
            cf = c[FORM[c] == FORM[pos[r]]]
            if len(cf) >= 8:
                out[r, :args.K_F] = cf[rng.integers(0, len(cf), args.K_F)]; out[r, args.K_F:] = c[rng.integers(0, len(c), K - args.K_F)]; n_conc += 1
            else:
                out[r] = c[rng.integers(0, len(c), K)]
    return out, n_small, n_empty, n_conc


def worker(wid, q):
    signal.signal(signal.SIGTERM, signal.SIG_DFL); signal.signal(signal.SIGHUP, signal.SIG_DFL)
    torch.set_num_threads(1)
    D = G['D']; D.rng = np.random.default_rng(args.seed * 1000 + wid + 1); FORM = G['formula']
    while True:
        ids = D.sample_ids(args.bs)
        items = [D.item(int(i), args.merge_p, True) for i in ids]
        pos = D.sid2pid[D.sid[ids]]
        negs, n_small, n_empty, n_conc = negatives(D, pos, args.K, D.rng)
        same_f = float((FORM[negs] == FORM[pos][:, None]).mean())
        q.put((tuple(t.numpy() for t in fpnet.collate(items, 'cpu')), pos, negs, dict(small=n_small, empty=n_empty, conc=n_conc, same_formula=same_f)))


def main():
    torch.set_num_threads(1)
    hold = tuple(args.holdout.split(','))
    D = traindata.Data('cpu', seed=args.seed, holdout_folds=hold); G['D'] = D
    # ---- negative pool: drop every structure of a held-out identity group, map pool ids to identity groups
    ts = pd.read_parquet('work/train_structs.parquet', columns=['sid', 'inchikey14'])
    st = pd.read_parquet(FOLDS, columns=['inchikey14', 'identity_group']).drop_duplicates('inchikey14')
    gsid = ts.merge(st, on='inchikey14', how='left', validate='many_to_one').identity_group.values
    assert not np.isnan(gsid.astype(float)).any(), 'train structure without an identity group'
    gsid = gsid.astype(np.int64); npool = len(D.pmass)
    grp = np.full(npool, -1, np.int64); pid = D.sid2pid; has = pid >= 0
    grp[pid[has]] = gsid[has]
    held_groups = np.unique(gsid[np.isin(D.fold, hold)])
    bad = np.zeros(npool, bool); bad[pid[has & np.isin(D.fold, hold)]] = True
    bad |= (grp >= 0) & np.isin(grp, held_groups)
    okpid = np.flatnonzero(~bad); assert (np.diff(D.pmass[okpid]) >= 0).all(), 'pool not sorted by mass'
    G['okpid'], G['okmass'], G['grp'] = okpid, D.pmass[okpid], grp
    G['formula'] = pd.factorize(pd.read_parquet('work/pool_meta.parquet', columns=['formula']).formula.astype(str).to_numpy(dtype=object))[0].astype(np.int64)
    tr_groups = np.unique(gsid[~np.isin(D.fold, hold)])
    assert not np.isin(tr_groups, held_groups).any(), 'an identity group is both training and held out'
    neg_audit = dict(pool=int(npool), excluded=int(bad.sum()), held_groups=int(len(held_groups)), allowed=int(len(okpid)))
    log('negative pool', json.dumps(neg_audit))
    q = mp.get_context('fork').Queue(maxsize=64)
    procs = [mp.get_context('fork').Process(target=worker, args=(w, q), daemon=True) for w in range(args.workers)]
    for p in procs: p.start()
    dev = 'cuda'; torch.manual_seed(args.seed)
    PFP = D.PFP.to(dev); ELEM = D.elem.to(dev)
    ck = torch.load(INIT, map_location='cpu', weights_only=True)
    base = fpnet.FPNet(ck['nbits'], d=ck['d'], layers=ck['layers'], heads=ck.get('heads', 8)); base.load_state_dict(ck['model'])
    assert base.nbits == D.nbits
    model = NM.N111(fpnet, base, d_out=args.d_out, hid=args.hid).to(dev)
    fp_params = list(model.fp.named_parameters()); head_params = [(n, p) for n, p in model.named_parameters() if not n.startswith('fp.')]
    groups = [dict(params=[p for n, p in fp_params if p.ndim >= 2], weight_decay=args.wd, base_lr=args.lr_fp),
              dict(params=[p for n, p in fp_params if p.ndim < 2], weight_decay=0.0, base_lr=args.lr_fp),
              dict(params=[p for n, p in head_params if p.ndim >= 2], weight_decay=args.wd, base_lr=args.lr_head),
              dict(params=[p for n, p in head_params if p.ndim < 2], weight_decay=0.0, base_lr=args.lr_head)]
    opt = torch.optim.AdamW(groups, lr=args.lr_fp, betas=(0.9, 0.98))
    log('parameters', sum(p.numel() for p in model.parameters()), 'new', sum(p.numel() for n, p in head_params), 'init', INIT)
    dtype = fpnet.autocast_dtype(dev)
    save_at = sorted({int(x) for x in args.save_at.split(',') if x} | {args.steps})
    t0 = time.time(); step = 0; ema = {}; stats = dict(small=0, empty=0, conc=0, rows=0, same_formula=0.0, batches=0)
    target = torch.zeros(args.bs, dtype=torch.long, device=dev)
    stop_at = args.smoke_steps or args.steps
    while step < stop_at and not STOP:
        prog = step / args.steps
        f = min(1.0, (step + 1) / args.warmup) * (0.02 + 0.98 * 0.5 * (1 + math.cos(math.pi * prog)))
        for g in opt.param_groups: g['lr'] = g['base_lr'] * f
        arrs, pos, negs, st_ = q.get(timeout=300)   # a dead worker pool raises instead of hanging
        stats['small'] += st_['small']; stats['empty'] += st_['empty']; stats['conc'] += st_['conc']; stats['rows'] += len(pos); stats['same_formula'] += st_['same_formula']; stats['batches'] += 1
        inp = tuple(torch.as_tensor(a, device=dev) for a in arrs)
        pos_t = torch.as_tensor(pos, device=dev); cand = torch.as_tensor(np.concatenate([pos[:, None], negs], 1), device=dev)
        fpb = fpnet.unpack_gpu(PFP[cand], D.nbits)
        with torch.autocast('cuda', dtype=dtype):
            z, el, s = model.spectrum(*inp)
            m = model.molecule(fpb)
        z = z.float(); el = el.float(); s = s.float(); m = m.float()
        sc_cos = torch.einsum('bkd,bd->bk', m, s) * model.scale()
        sc_fp = torch.einsum('bkn,bn->bk', fpb, z)
        l_cos = F.cross_entropy(sc_cos, target); l_rank = F.cross_entropy(sc_fp, target)
        l_bce = F.binary_cross_entropy_with_logits(z, fpb[:, 0]); l_el = F.smooth_l1_loss(el, ELEM[pos_t])
        loss = args.w_cos * l_cos + args.w_rank * l_rank + args.w_bce * l_bce + args.w_el * l_el
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); step += 1
        vals = dict(loss=loss.item(), cos=l_cos.item(), rank=l_rank.item(), bce=l_bce.item(), el=l_el.item(),
                    acc_cos=(sc_cos.argmax(1) == 0).float().mean().item(), acc_fp=(sc_fp.argmax(1) == 0).float().mean().item(), scale=float(model.scale().item()))
        if not math.isfinite(vals['loss']): raise RuntimeError(f'non-finite loss at step {step}')
        for k, v in vals.items(): ema[k] = v if step == 1 else 0.98 * ema[k] + 0.02 * v
        if step % 200 == 0 or step == stop_at:
            log(f"step {step} lr_fp {opt.param_groups[0]['lr']:.2e} " + ' '.join(f'{k} {v:.4f}' for k, v in ema.items()) +
                f" | neg small {stats['small'] / max(1, stats['rows']):.4f} empty {stats['empty'] / max(1, stats['rows']):.4f} concentrated {stats['conc'] / max(1, stats['rows']):.3f} same-formula {stats['same_formula'] / max(1, stats['batches']):.3f}"
                f" | {step / (time.time() - t0):.2f} it/s queue {q.qsize()} mem {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB")
        if step in save_at and not args.smoke_steps:
            NM.save(f'{args.tag}_s{step}.pt', model, step, extra=dict(args=vars(args), neg_audit=neg_audit, init=INIT))
            log('saved', f'{args.tag}_s{step}.pt')
    receipt = dict(step=step, complete=(step == args.steps and not args.smoke_steps), elapsed_seconds=time.time() - t0, neg_audit=neg_audit,
                   neg_small_rate=stats['small'] / max(1, stats['rows']), neg_empty_rate=stats['empty'] / max(1, stats['rows']), neg_concentrated_rate=stats['conc'] / max(1, stats['rows']),
                   same_formula_rate=stats['same_formula'] / max(1, stats['batches']), device=torch.cuda.get_device_name(), peak_gib=torch.cuda.max_memory_allocated() / 2**30, args=vars(args))
    if args.smoke_steps:   # save / reload / re-score check on the last batch
        model.eval(); NM.save(f'{args.tag}_smoke.pt', model, step, extra=dict(args=vars(args)))
        with torch.no_grad(), torch.autocast('cuda', dtype=dtype):
            _, _, s1 = model.spectrum(*inp); m1 = model.molecule(fpb[:4])
            m2, _ = NM.load(f'{args.tag}_smoke.pt', fpnet, dev); _, _, s2 = m2.spectrum(*inp); mm2 = m2.molecule(fpb[:4])
        receipt['reload_max_abs_diff'] = float(max((s1.float() - s2.float()).abs().max().item(), (m1.float() - mm2.float()).abs().max().item()))
        log('smoke reload max abs diff', receipt['reload_max_abs_diff'])
    pathlib.Path(f'{args.tag}_receipt.json').write_text(json.dumps(receipt, indent=2)); log('DONE', json.dumps({k: v for k, v in receipt.items() if k != 'args'}))
    for p in procs: p.terminate()
    for p in procs: p.join()


if __name__ == '__main__':
    main()
