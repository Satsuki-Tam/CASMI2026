"""Technical test of the casmi-harness-v2 src (cv / metrics / adapter / aux reader) -- every check is an assert. Temporary copy: dev = the 30
exported worlds except cU1_p30; a fake feature-only hold = cU1_p30 (y / iid removed; its uids become the test ids); the copied cv.py has its
expected counts adapted. No real holdout data is used.
  P1 P reference == RR from P's ranks; P2 a truth among the E-only / products scores 0 in the P reference; P3 a missing U file stops it;
  F1 the F reference reproduces the stored F lists (RR from fref == RR from f_top25); F2 P-empty queries have an empty F;
  A1 FH-PEB: finite, every real slot scored; A2 other arms / fixed-param overrides refused; A3 tampered table refused; A4 a label column
  refused with an updated manifest; A5 missing Q row refused; C1 cv.py stops on a truth row labelled 0 and writes nothing."""
import glob, hashlib, importlib.util, json, os, shutil, sys, tempfile
import numpy as np, pandas as pd

WS = r"C:\kaggle\competitions\casmi-harness-v2"
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def build_tmp():
    tmp = tempfile.mkdtemp(prefix="casmi_ws2_test_")
    for d in ("data/raw/w135_u2_dev_v1", "data/raw/w135_u2_hold_e_v1", "data/folds", "src", "state", "experiments", "refs"):
        os.makedirs(os.path.join(tmp, d), exist_ok=True)
    for f in ("metrics.py", "cv.py", "adapter.py", "aux_reader.py"):
        shutil.copy(os.path.join(WS, "src", f), os.path.join(tmp, "src", f))
    src = os.path.join(WS, "data/raw/w135_u2_dev_v1")
    for f in os.listdir(src):
        if "cU1_p30" in f or f in ("units_dev.parquet", "fref_dev.parquet"): continue
        shutil.copy(os.path.join(src, f), os.path.join(tmp, "data/raw/w135_u2_dev_v1", f))
    units = pd.read_parquet(os.path.join(src, "units_dev.parquet")); fref = pd.read_parquet(os.path.join(src, "fref_dev.parquet"))
    keep = set(units[units.batch != "cU1"].uid)
    units[units.uid.isin(keep)].to_parquet(os.path.join(tmp, "data/raw/w135_u2_dev_v1/units_dev.parquet"), index=False)
    fref[fref.uid.isin(keep)].to_parquet(os.path.join(tmp, "data/raw/w135_u2_dev_v1/fref_dev.parquet"), index=False)
    U = pd.read_parquet(os.path.join(src, "U_cU1_p30.parquet")); Q = pd.read_parquet(os.path.join(src, "Q_cU1_p30.parquet"))
    U.drop(columns=["y"]).to_parquet(os.path.join(tmp, "data/raw/w135_u2_hold_e_v1/U_00.parquet"), index=False)
    Q.drop(columns=["iid"]).to_parquet(os.path.join(tmp, "data/raw/w135_u2_hold_e_v1/Q_00.parquet"), index=False)
    pd.DataFrame(dict(uid=Q.uid)).to_csv(os.path.join(tmp, "data/raw/hold_ids.csv"), index=False)
    cvp = os.path.join(tmp, "src/cv.py"); s = open(cvp, encoding="utf-8").read()
    s = s.replace('EXPECT = dict(units=3095, primary=1198, test=596, folds={0: 600, 1: 600, 2: 600, 3: 396, 4: 400, 5: 400, 6: 99}, hold_files=6)',
                  f'EXPECT = dict(units={len(keep)}, primary=1198, test={len(Q)}, folds={{0: 600, 1: 600, 2: 600, 3: 396, 4: 400, 5: 400}}, hold_files=1)')
    s = s.replace(' + ["cU1_p30"]\nEXPECT', '\nEXPECT'); open(cvp, "w", encoding="utf-8").write(s)
    return tmp, U, Q


def mod(tmp, name):
    spec = importlib.util.spec_from_file_location(f"{name}_{os.path.basename(tmp)}", os.path.join(tmp, "src", f"{name}.py"))
    m = importlib.util.module_from_spec(spec); sys.path.insert(0, os.path.join(tmp, "src")); spec.loader.exec_module(m); return m


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except (RuntimeError, ValueError, SystemExit) as e:
        return str(e)
    raise AssertionError("expected an error, none raised")


def main():
    tmp, U_c, Q_c = build_tmp(); cv = mod(tmp, "cv"); cv.main()
    M = mod(tmp, "metrics"); A = mod(tmp, "adapter"); R = mod(tmp, "aux_reader")
    V = {k: v for k, v in np.load(os.path.join(tmp, "data/folds/validation.npz"), allow_pickle=False).items()}
    vm = {k[6:]: v for k, v in V.items() if k.startswith("meta__")}
    Ud = pd.concat([pd.read_parquet(p) for p in glob.glob(os.path.join(tmp, "data/raw/w135_u2_dev_v1/U_*.parquet"))])
    rrP = M.reciprocal_ranks(V["y"], R.p_reference(V), vm)
    t = Ud[(Ud.y == 1) & (Ud.in_P == 1)].set_index("uid").rP
    assert np.allclose(rrP, [1.0 / t[u] if u in t.index and t[u] <= 25 else 0.0 for u in V["ids"]]); print("P1 P reference == RR from P's ranks: ok")
    outP = set(Ud[(Ud.y == 1) & (Ud.in_P == 0)].uid); mo = np.array([u in outP for u in V["ids"]]); assert mo.sum() > 0 and rrP[mo].sum() == 0; print(f"P2 P reference ignores {int(mo.sum())} truths outside P25: ok")
    fu = sorted(glob.glob(os.path.join(tmp, "data/raw/w135_u2_dev_v1/U_*.parquet")))[-1]; keep_u = open(fu, "rb").read(); os.remove(fu)
    assert "differ" in raises(R.p_reference, V); open(fu, "wb").write(keep_u); print("P3 P reference stops when a U file is missing: ok")
    rrF = M.reciprocal_ranks(V["y"], R.f_reference(V), vm)
    fr = pd.read_parquet(os.path.join(tmp, "data/raw/w135_u2_dev_v1/fref_dev.parquet")).set_index("uid")
    direct = np.array([next((1.0 / (i + 1) for i, k in enumerate(json.loads(fr.loc[u, "f_top25"])[:25]) if k == y), 0.0) for u, y in zip(V["ids"], V["y"])])
    assert np.allclose(rrF, direct); print("F1 F reference == RR of the stored F lists: ok")
    pe = V["meta__n_p"] == 0; assert (rrF[pe] == 0).all() and all(len(json.loads(fr.loc[u, "f_top25"])) == 0 for u in V["ids"][pe]); print(f"F2 P-empty queries ({int(pe.sum())}) have an empty F: ok")
    fold = V["fold"]; va = np.flatnonzero(fold == 0); tr = np.flatnonzero(fold != 0)
    ctx = dict(workspace=tmp, validation_path=os.path.join(tmp, "data/folds/validation.npz"), train_indices=tr, valid_indices=va, seed=11, smoke=False,
               config=dict(mode="fh", arm="peb", rounds=30), resource_ids=[], output_dir=None, fold=0)
    r = A.run_fold(ctx); G = r["valid_predictions"]; vv = V["meta__cand_valid"][va]
    assert G.shape == (len(va), 100) and np.isfinite(G).all() and np.isfinite(r["test_predictions"]).all() and (G[vv] > M.NOT_SUBMITTED).all(); print("A1 FH-PEB finite, every real slot scored: ok")
    for bad in (dict(mode="fh", arm="pe"), dict(mode="p_order"), dict(mode="fh", arm="peb", params=dict(num_threads=32))): raises(A.run_fold, dict(ctx, config=bad))
    print("A2 other arms / fixed-param override refused: ok")
    f0 = sorted(glob.glob(os.path.join(tmp, "data/raw/w135_u2_dev_v1/U_*.parquet")))[0]; keep = open(f0, "rb").read()
    pd.read_parquet(f0).assign(fz=lambda d: d.fz + 1e-6).to_parquet(f0, index=False); raises(A.run_fold, ctx); open(f0, "wb").write(keep); print("A3 tampered table refused: ok")
    hq = os.path.join(tmp, "data/raw/w135_u2_hold_e_v1/Q_00.parquet"); keep_h = open(hq, "rb").read(); man_p = os.path.join(tmp, "data/folds/data_manifest.json"); keep_m = open(man_p, "rb").read()
    pd.read_parquet(hq).assign(wclass="C2").to_parquet(hq, index=False); man = json.load(open(man_p)); man["w135_u2_hold_e_v1/Q_00.parquet"] = sha(hq); json.dump(man, open(man_p, "w"))
    assert "label" in raises(A.run_fold, ctx); open(hq, "wb").write(keep_h); open(man_p, "wb").write(keep_m); print("A4 label column refused with an updated manifest: ok")
    fq = sorted(glob.glob(os.path.join(tmp, "data/raw/w135_u2_dev_v1/Q_*.parquet")))[0]; keep_q = open(fq, "rb").read()
    pd.read_parquet(fq).iloc[1:].to_parquet(fq, index=False); man = json.load(open(man_p)); man[f"w135_u2_dev_v1/{os.path.basename(fq)}"] = sha(fq); json.dump(man, open(man_p, "w"))
    raises(A.run_fold, ctx); open(fq, "wb").write(keep_q); open(man_p, "wb").write(keep_m); print("A5 missing Q row refused: ok")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp2, _, _ = build_tmp(); f = sorted(glob.glob(os.path.join(tmp2, "data/raw/w135_u2_dev_v1/U_*.parquet")))[0]
    d = pd.read_parquet(f); i = int(np.flatnonzero(d.y.values == 1)[0]); d.loc[d.index[i], "y"] = 0; d.to_parquet(f, index=False)
    assert "labels disagree" in raises(mod(tmp2, "cv").main) and not os.path.exists(os.path.join(tmp2, "data/folds/validation.npz")); shutil.rmtree(tmp2, ignore_errors=True)
    print("C1 cv.py stops on a truth row labelled 0 and writes nothing: ok"); print("TECH_TEST_V2WS_PASS")


if __name__ == "__main__":
    main()
