"""143 E2 step 3: train the second engine E2 = pointwise LightGBM binary on the fold-3 / fold-4 pool E-window tables, both views
(e2_common.view_frame / train_groups). Fixed before any E2 result was read:
  rows: C1 + C2 groups of train_pool_f{3,4}a, train_pool_f{3,4}b, np061_f{3,4}pool (fold-safe FPNet of the molecule's own fold);
        a molecule that appears in two dirs of one fold is kept once (first dir in that order); weight 1 / (group size) per row;
  params: PARAMS below; number of rounds chosen from GRID by a two-way cross-fit inside the training folds (fold 3 -> fold 4 and
        fold 4 -> fold 3), criterion = mean MRR@25 over the four (direction, view) cells; the development folds 1 / 2 and the panel
        are never read here. Final model = all training rows with the chosen rounds.
Outputs: <out>/e2_lgb.txt, <out>/e2_train_manifest.json, <out>/e2_crossfit.csv.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/e2/e2_train.py --out experiments/e2/model_v1"""
import argparse, hashlib, json, os, sys, time
import numpy as np, pandas as pd, lightgbm as lgb
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
from e2_common import FEATS, view_frame, train_groups, rank_lists, rr_of
S5 = ["C_np_crosslib", "D_np_single", "E_np_negonly", "F_np_uncovered", "G_tims_crosslib"]; S3 = ["NP_H", "NP_X", "NP_N"]
FOLD_DIRS = {3: [("train_pool_f3a", S5), ("train_pool_f3b", S5), ("np061_f3pool", S3)], 4: [("train_pool_f4a", S5), ("train_pool_f4b", S5), ("np061_f4pool", S3)]}
PARAMS = dict(objective="binary", learning_rate=0.05, num_leaves=63, min_data_in_leaf=50, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1,
              lambda_l2=1.0, verbose=-1, seed=7, num_threads=8, deterministic=True, force_row_wise=True)
GRID = [100, 200, 400, 800]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def load_fold(ew, f, log):
    parts, seen, hashes = [], set(), {}
    for d, sets in FOLD_DIRS[f]:
        for s in sets:
            pe, pf = f"{ew}/{d}/ewin_{s}.parquet", f"{ew}/{d}/e2f_{s}.parquet"; hashes[f"{d}/{s}"] = [sha(pe)[:16], sha(pf)[:16]]
            E = pd.read_parquet(pe); F = pd.read_parquet(pf); E["molecule"] = E.molecule.astype(str); F["molecule"] = F.molecule.astype(str)
            dup = set(E.molecule) & seen
            if dup: E = E[~E.molecule.isin(dup)]; F = F[~F.molecule.isin(dup)]
            seen |= set(E.molecule)
            for v in ("c1", "c2"):
                X = train_groups(view_frame(E, F, v)); X["gk"] = f"{d}|{v}|" + X.gk; X["fold"] = f; parts.append(X)
                log(f"  fold {f} {d} {s} {v}: groups {X.gk.nunique()}, rows {len(X)} (dup molecules dropped {len(dup)})")
    return pd.concat(parts, ignore_index=True), hashes


def weights(X): return (1.0 / X.groupby("gk").gk.transform("size")).values


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--ewin", default="experiments/e2/ewin"); a = ap.parse_args()
    P_ = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p); out = P_(a.out); os.makedirs(out, exist_ok=True); t0 = time.time()
    log = lambda *x: print(*x, flush=True)
    X3, h3 = load_fold(P_(a.ewin), 3, log); X4, h4 = load_fold(P_(a.ewin), 4, log)
    log(f"fold 3: {X3.gk.nunique()} groups / {len(X3)} rows; fold 4: {X4.gk.nunique()} groups / {len(X4)} rows ({time.time()-t0:.0f}s)")
    cf = []
    for tr, te, name in ((X3, X4, "3to4"), (X4, X3, "4to3")):
        m = lgb.train(PARAMS, lgb.Dataset(tr[FEATS], tr.is_truth.astype(int), weight=weights(tr)), num_boost_round=max(GRID))
        for k in GRID + ["fp_only"]:
            R = rank_lists(te, te.fp.values if k == "fp_only" else m.predict(te[FEATS], num_iteration=k)); rr = rr_of(R)
            for v in ("c1", "c2"):
                sel = rr[[g.split("|")[1] == v for g in rr.index]]
                cf.append(dict(direction=name, rounds=str(k), view=v, groups=len(sel), mrr=float(sel.mean()), top1=float((sel == 1).mean())))
        log(f"  cross-fit {name} done ({time.time()-t0:.0f}s)")
    CF = pd.DataFrame(cf); CF.to_csv(f"{out}/e2_crossfit.csv", index=False)
    crit = CF[CF.rounds != "fp_only"].groupby("rounds").mrr.mean(); best = int(crit.idxmax())
    log(CF.pivot_table(index="rounds", columns=["direction", "view"], values="mrr").round(4).to_string()); log(f"chosen rounds {best} (criterion {crit.round(4).to_dict()})")
    XA = pd.concat([X3, X4], ignore_index=True)
    m = lgb.train(PARAMS, lgb.Dataset(XA[FEATS], XA.is_truth.astype(int), weight=weights(XA)), num_boost_round=best); m.save_model(f"{out}/e2_lgb.txt")
    imp = dict(zip(FEATS, [round(float(x), 1) for x in m.feature_importance("gain")]))
    man = dict(feats=FEATS, params=PARAMS, grid=GRID, rounds=best, criterion={str(k): float(v) for k, v in crit.items()}, groups=int(XA.gk.nunique()), rows=int(len(XA)),
               groups_by_view={v: int(XA[XA.view == v].gk.nunique()) for v in ("c1", "c2")}, inputs={**h3, **h4}, script=sha(os.path.abspath(__file__))[:16],
               common=sha(os.path.join(HERE, "e2_common.py"))[:16], model=sha(f"{out}/e2_lgb.txt"), gain=imp, seconds=round(time.time() - t0))
    json.dump(man, open(f"{out}/e2_train_manifest.json", "w"), indent=1); log(json.dumps(imp)); log(f"E2_TRAIN_DONE {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
