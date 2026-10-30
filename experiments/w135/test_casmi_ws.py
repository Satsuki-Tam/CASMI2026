"""Technical test of the casmi-harness src (metrics / cv / adapter) on a temporary copy: dev = 30 worlds, a fake feature-only 'hold' resource
= cU1_p30 with labels stripped (its ids become the test ids). Checks: (1) metric on P's order == RR computed directly from the U tables;
(2) adapter p_order reproduces it through to_slots; (3) fh / gen and fh / db run, return finite (n, 75) arrays, products can reach rank 1;
(4) a label column in the hold resource is refused; (5) padding slots are ignored by the metric."""
import importlib.util, os, shutil, sys, tempfile
import numpy as np, pandas as pd

WS = r"C:\kaggle\competitions\casmi-harness"
tmp = tempfile.mkdtemp(prefix="casmi_ws_test_")
for d in ("data/raw/w135_u_dev_v1", "data/raw/w135_u_hold_e_v1", "data/folds", "src"):
    os.makedirs(os.path.join(tmp, d), exist_ok=True)
for f in ("metrics.py", "cv.py", "adapter.py"):
    shutil.copy(os.path.join(WS, "src", f), os.path.join(tmp, "src", f))
src_dev = os.path.join(WS, "data/raw/w135_u_dev_v1")
for f in os.listdir(src_dev):
    if "cU1_p30" in f: continue
    shutil.copy(os.path.join(src_dev, f), os.path.join(tmp, "data/raw/w135_u_dev_v1", f))
U = pd.read_parquet(os.path.join(src_dev, "U_cU1_p30.parquet")); Q = pd.read_parquet(os.path.join(src_dev, "Q_cU1_p30.parquet"))
U.drop(columns=["y"]).to_parquet(os.path.join(tmp, "data/raw/w135_u_hold_e_v1/U_cU1_p30.parquet"), index=False)
Q.drop(columns=["truth", "wclass", "used", "fam"]).to_parquet(os.path.join(tmp, "data/raw/w135_u_hold_e_v1/Q_cU1_p30.parquet"), index=False)
pd.DataFrame(dict(world=Q.world, molecule=Q.molecule.astype(str))).to_csv(os.path.join(tmp, "data/raw/hold_e_ids.csv"), index=False)

def mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(tmp, "src", f"{name}.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
cv = mod("cv"); cv.worlds = lambda: sorted(os.path.basename(p)[2:-8] for p in __import__("glob").glob(os.path.join(cv.DEV, "U_*.parquet")))
cv.main()
M = mod("metrics"); A = mod("adapter")
V = np.load(os.path.join(tmp, "data/folds/validation.npz"), allow_pickle=False)
y = V["y"]; ids = V["ids"]; fold = V["fold"]; meta = {k[6:]: V[k] for k in V.files if k.startswith("meta__")}
va = np.flatnonzero(fold == 0); tr = np.flatnonzero(fold != 0)
ctx = dict(workspace=tmp, validation_path=os.path.join(tmp, "data/folds/validation.npz"), train_indices=tr, valid_indices=va, seed=11, smoke=False,
           config=dict(mode="p_order"), resource_ids=["res-w135-u-dev-v1", "res-w135-u-hold-e-v1"], output_dir=tmp, fold=0)
r = A.run_fold(ctx); P = r["valid_predictions"]
sub = {k: v[va] for k, v in meta.items()}
rr_metric = M.reciprocal_ranks(y[va], P, sub)
Ud = pd.concat([pd.read_parquet(p) for p in __import__("glob").glob(os.path.join(tmp, "data/raw/w135_u_dev_v1/U_*.parquet"))]); Ud["uid"] = Ud.world + "|" + Ud.molecule.astype(str)
t = Ud[(Ud.y == 1) & (Ud.src == "P")].set_index("uid").rP
rr_direct = np.array([1.0 / t[u] if u in t.index and t[u] <= 25 else 0.0 for u in ids[va]])
print("(1)(2) p_order metric RR == direct RR from U:", np.allclose(rr_metric, rr_direct), "| fold-0 primary MRR", round(M.score(y[va], P, sub), 4), "| shapes", P.shape, r["test_predictions"].shape)
assert np.allclose(rr_metric, rr_direct) and np.isfinite(P).all() and np.isfinite(r["test_predictions"]).all()
for arm in ("gen", "db"):
    ctx["config"] = dict(mode="fh", arm=arm, rounds=50); r2 = A.run_fold(ctx); G = r2["valid_predictions"]
    assert G.shape == (len(va), 75) and np.isfinite(G).all() and np.isfinite(r2["test_predictions"]).all()
    top1_slot = np.array([np.flatnonzero(meta["cand_valid"][i])[np.argmax(G[k, meta["cand_valid"][i]])] if meta["cand_valid"][i].any() else -1 for k, i in enumerate(va)])
    n_p = meta["n_p"][va]
    print(f"(3) fh/{arm}: finite (n, 75) ok | queries whose top-1 is a product slot: {int(((top1_slot >= n_p) & (top1_slot >= 0)).sum())} (descriptive, technical)")
H = os.path.join(tmp, "data/raw/w135_u_hold_e_v1/U_cU1_p30.parquet"); U.to_parquet(H, index=False)   # label column back -> hash change
try:
    ctx["config"] = dict(mode="p_order"); A.run_fold(ctx); print("(4) label column NOT refused (BAD)")
except RuntimeError as e:
    print("(4) label column refused:", str(e)[:80])
Z = P.copy(); pad = ~sub["cand_valid"]; Z[pad] = 1e12
print("(5) padding ignored:", np.allclose(M.reciprocal_ranks(y[va], Z, sub), rr_metric))
shutil.rmtree(tmp, ignore_errors=True); print("TECH_TEST_DONE")
