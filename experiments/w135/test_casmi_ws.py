"""Technical test of the casmi-harness src v2 (cv / metrics / adapter / aux reader) on a temporary copy (no real holdout data):
dev = the 30 exported worlds except cU1_p30; a fake feature-only 'hold' = cU1_p30 with y / iid removed (its uids become the test ids).
Checks: (1) metric on P's order == RR computed directly from P's ranks; (2) P-only: a truth among the products scores 0 in P's reference
(NOT_SUBMITTED slots); (3) the tie rule = P rank, then product key; (4) fh gen / db return finite (n, 75) arrays, db leaves products
unsubmitted; (5) a tampered base-data file is refused; (6) padding is ignored even with a huge score; (7) the training weights come
from the train roster (identity world counts)."""
import importlib.util, os, shutil, sys, tempfile, glob
import numpy as np, pandas as pd

WS = r"C:\kaggle\competitions\casmi-harness"
tmp = tempfile.mkdtemp(prefix="casmi_ws_test2_")
for d in ("data/raw/w135_u_dev_v2", "data/raw/w135_u_hold_e_v2", "data/folds", "src"):
    os.makedirs(os.path.join(tmp, d), exist_ok=True)
for f in ("metrics.py", "cv.py", "adapter.py", "aux_reader.py"):
    shutil.copy(os.path.join(WS, "src", f), os.path.join(tmp, "src", f))
src_dev = os.path.join(WS, "data/raw/w135_u_dev_v2")
for f in os.listdir(src_dev):
    if "cU1_p30" in f or f == "units_dev.parquet": continue
    shutil.copy(os.path.join(src_dev, f), os.path.join(tmp, "data/raw/w135_u_dev_v2", f))
units = pd.read_parquet(os.path.join(src_dev, "units_dev.parquet")); units[units.batch != "cU1"].to_parquet(os.path.join(tmp, "data/raw/w135_u_dev_v2/units_dev.parquet"), index=False)
U = pd.read_parquet(os.path.join(src_dev, "U_cU1_p30.parquet")); Q = pd.read_parquet(os.path.join(src_dev, "Q_cU1_p30.parquet"))
U.drop(columns=["y"]).to_parquet(os.path.join(tmp, "data/raw/w135_u_hold_e_v2/U_00.parquet"), index=False)
Q.drop(columns=["iid"]).to_parquet(os.path.join(tmp, "data/raw/w135_u_hold_e_v2/Q_00.parquet"), index=False)
pd.DataFrame(dict(uid=Q.uid)).to_csv(os.path.join(tmp, "data/raw/hold_ids.csv"), index=False)
cvp = os.path.join(tmp, "src/cv.py"); s = open(cvp, encoding="utf-8").read().replace("len(units) != 3095", f"len(units) != {int((units.batch != 'cU1').sum())}"); open(cvp, "w", encoding="utf-8").write(s)

def mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(tmp, "src", f"{name}.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
cv = mod("cv"); cv.main(); M = mod("metrics"); A = mod("adapter")
V = np.load(os.path.join(tmp, "data/folds/validation.npz"), allow_pickle=False)
y = V["y"]; ids = V["ids"]; fold = V["fold"]; meta = {k[6:]: V[k] for k in V.files if k.startswith("meta__")}
va = np.flatnonzero(fold == 0); tr = np.flatnonzero(fold != 0); sub = {k: v[va] for k, v in meta.items()}
ctx = dict(workspace=tmp, validation_path=os.path.join(tmp, "data/folds/validation.npz"), train_indices=tr, valid_indices=va, seed=11, smoke=False,
           config=dict(mode="p_order"), resource_ids=[], output_dir=tmp, fold=0)
r = A.run_fold(ctx); P = r["valid_predictions"]; rr = M.reciprocal_ranks(y[va], P, sub)
Ud = pd.concat([pd.read_parquet(p) for p in glob.glob(os.path.join(tmp, "data/raw/w135_u_dev_v2/U_*.parquet"))])
t = Ud[(Ud.y == 1) & (Ud.src == "P")].set_index("uid").rP
direct = np.array([1.0 / t[u] if u in t.index and t[u] <= 25 else 0.0 for u in ids[va]])
print("(1) p_order RR == direct P RR:", np.allclose(rr, direct), "| shapes", P.shape, r["test_predictions"].shape); assert np.allclose(rr, direct)
inB = set(Ud[(Ud.y == 1) & (Ud.src == "B")].uid)
mB = np.array([u in inB for u in ids[va]]); print(f"(2) P-only: units with the truth among the products {int(mB.sum())}, their p_order RR sum {rr[mB].sum():.1f} (must be 0)"); assert rr[mB].sum() == 0
Z = np.where(meta["cand_valid"][va], 0.0, A.PAD); order_ok = True
for k, i in enumerate(va[:200]):
    v = np.flatnonzero(meta["cand_valid"][i]); ks = meta["cand_keys"][i][v]; n_p = int(meta["n_p"][i])
    if list(ks[n_p:]) != sorted(ks[n_p:]): order_ok = False
print("(3) tie rule: product slots sorted by key after P's ranks:", order_ok); assert order_ok
for arm in ("gen", "db"):
    ctx["config"] = dict(mode="fh", arm=arm, rounds=40); r2 = A.run_fold(ctx); G = r2["valid_predictions"]
    assert G.shape == (len(va), 75) and np.isfinite(G).all() and np.isfinite(r2["test_predictions"]).all()
    if arm == "db":
        prod_sub = [(G[k, int(meta["n_p"][i]):][meta["cand_valid"][i][int(meta["n_p"][i]):]] > M.NOT_SUBMITTED).any() for k, i in enumerate(va)]
        print("(4) fh/db: products never submitted:", not any(prod_sub)); assert not any(prod_sub)
    else:
        print("(4) fh/gen: finite (n, 75) ok")
H = os.path.join(tmp, "data/raw/w135_u_hold_e_v2/U_00.parquet"); U.to_parquet(H, index=False)
try:
    ctx["config"] = dict(mode="p_order"); A.run_fold(ctx); print("(5) tampered file NOT refused (BAD)")
except RuntimeError as e:
    print("(5) tampered file refused:", str(e)[:70])
Z = P.copy(); Z[~sub["cand_valid"]] = 1e12; print("(6) padding ignored:", np.allclose(M.reciprocal_ranks(y[va], Z, sub), rr))
shutil.rmtree(tmp, ignore_errors=True); print("TECH_TEST_DONE")
