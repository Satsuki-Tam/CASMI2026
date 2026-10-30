"""Technical test v3 of the casmi-harness src (cv / metrics / adapter / aux reader) -- every check is an assert (155 decision C).
Temporary copy: dev = the 30 exported worlds except cU1_p30; a fake feature-only hold = cU1_p30 (y / iid removed; its uids become the test
ids); the copied cv.py has its expected counts adapted to this copy. No real holdout data is used.
Checks:
  M1 ties: equal scores -> P by rank, then products by key; M2 P empty / products only; M3 no candidate -> RR 0; M4 NOT_SUBMITTED boundary
  (-1e8 excluded, just above included); M5 rank 25 counts, rank 26 does not; M6 a non-finite valid prediction raises; M7 padding ignored.
  P1 the aux reader's P reference == RR from P's ranks; P2 a truth among the products scores 0 in the P reference.
  A1 FH-gen runs, every real slot is scored, outputs finite; A2 p_order / db / fixed-param overrides are refused; A3 a tampered table is
  refused; A4 a label column is refused even with an updated manifest; A5 a missing Q row is refused; A6 training weights =
  1/|U| x 1/(roster units of the identity), empty units included."""
import glob, hashlib, importlib.util, json, os, shutil, sys, tempfile
import numpy as np, pandas as pd

WS = r"C:\kaggle\competitions\casmi-harness"
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def build_tmp():
    tmp = tempfile.mkdtemp(prefix="casmi_ws_test3_")
    for d in ("data/raw/w135_u_dev_v2", "data/raw/w135_u_hold_e_v2", "data/folds", "src", "state", "experiments"):
        os.makedirs(os.path.join(tmp, d), exist_ok=True)
    for f in ("metrics.py", "cv.py", "adapter.py", "aux_reader.py"):
        shutil.copy(os.path.join(WS, "src", f), os.path.join(tmp, "src", f))
    src = os.path.join(WS, "data/raw/w135_u_dev_v2")
    for f in os.listdir(src):
        if "cU1_p30" in f or f == "units_dev.parquet": continue
        shutil.copy(os.path.join(src, f), os.path.join(tmp, "data/raw/w135_u_dev_v2", f))
    units = pd.read_parquet(os.path.join(src, "units_dev.parquet")); units[units.batch != "cU1"].to_parquet(os.path.join(tmp, "data/raw/w135_u_dev_v2/units_dev.parquet"), index=False)
    U = pd.read_parquet(os.path.join(src, "U_cU1_p30.parquet")); Q = pd.read_parquet(os.path.join(src, "Q_cU1_p30.parquet"))
    U.drop(columns=["y"]).to_parquet(os.path.join(tmp, "data/raw/w135_u_hold_e_v2/U_00.parquet"), index=False)
    Q.drop(columns=["iid"]).to_parquet(os.path.join(tmp, "data/raw/w135_u_hold_e_v2/Q_00.parquet"), index=False)
    pd.DataFrame(dict(uid=Q.uid)).to_csv(os.path.join(tmp, "data/raw/hold_ids.csv"), index=False)
    cvp = os.path.join(tmp, "src/cv.py"); s = open(cvp, encoding="utf-8").read()
    s = s.replace('EXPECT = dict(units=3095, primary=1198, test=596, folds={0: 600, 1: 600, 2: 600, 3: 396, 4: 400, 5: 400, 6: 99}, hold_files=6)',
                  f'EXPECT = dict(units={int((units.batch != "cU1").sum())}, primary=1198, test={len(Q)}, folds={{0: 600, 1: 600, 2: 600, 3: 396, 4: 400, 5: 400}}, hold_files=1)')
    s = s.replace(' + ["cU1_p30"]\nEXPECT', '\nEXPECT')
    open(cvp, "w", encoding="utf-8").write(s)
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
    tmp, U_c, Q_c = build_tmp()
    cv = mod(tmp, "cv"); cv.main()
    M = mod(tmp, "metrics"); A = mod(tmp, "adapter"); R = mod(tmp, "aux_reader")
    # ---- metric (synthetic)
    keys = np.array([["PPPPPPPPPPPPPA", "PPPPPPPPPPPPPB", "BBBBBBBBBBBBBA", "BBBBBBBBBBBBBB"] + [""] * 26,
                     ["BBBBBBBBBBBBBA", "BBBBBBBBBBBBBB"] + [""] * 28, [""] * 30], dtype="<U14")
    valid = keys != ""; meta = dict(cand_keys=keys, cand_valid=valid, primary=np.array([True, True, True]))
    y = np.array(["BBBBBBBBBBBBBA", "BBBBBBBBBBBBBA", "PPPPPPPPPPPPPA"])
    pred = np.zeros(keys.shape); pred[1, :2] = [0.1, 0.9]
    rr = M.reciprocal_ranks(y, pred, meta)
    assert np.allclose(rr, [1 / 3, 1 / 2, 0.0]), rr; print("M1 ties / M2 P empty / M3 no candidate: ok")
    p4 = pred.copy(); p4[0, 2] = -1e8; assert M.reciprocal_ranks(y, p4, meta)[0] == 0.0
    p4[0, 2] = -0.99e8; p4[0, :2] = -0.995e8; p4[0, 3] = -0.999e8; assert M.reciprocal_ranks(y, p4, meta)[0] == 1.0; print("M4 NOT_SUBMITTED boundary: ok")
    k5 = np.array([[f"{chr(65 + i // 26)}{chr(65 + i % 26)}" + "A" * 12 for i in range(30)]], dtype="<U14"); v5 = np.ones((1, 30), bool)
    for pos_, exp in ((24, 1 / 25), (25, 0.0)):
        p5 = -np.arange(30, dtype=float)[None, :]; y5 = np.array([k5[0, pos_]])
        assert np.isclose(M.reciprocal_ranks(y5, p5, dict(cand_keys=k5, cand_valid=v5, primary=np.array([True])))[0], exp)
    print("M5 rank 25 / 26: ok")
    p6 = pred.copy(); p6[0, 0] = np.nan; raises(M.reciprocal_ranks, y, p6, meta); p6[0, 0] = np.inf; raises(M.reciprocal_ranks, y, p6, meta); print("M6 non-finite raises: ok")
    p7 = pred.copy(); p7[~valid] = 1e12; assert np.allclose(M.reciprocal_ranks(y, p7, meta), rr); print("M7 padding ignored: ok")
    # ---- P reference
    V = {k: v for k, v in np.load(os.path.join(tmp, "data/folds/validation.npz"), allow_pickle=False).items()}
    vm = {k[6:]: v for k, v in V.items() if k.startswith("meta__")}
    Pref = R.p_reference(V); rrP = M.reciprocal_ranks(V["y"], Pref, vm)
    Ud = pd.concat([pd.read_parquet(p) for p in glob.glob(os.path.join(tmp, "data/raw/w135_u_dev_v2/U_*.parquet"))])
    t = Ud[(Ud.y == 1) & (Ud.src == "P")].set_index("uid").rP
    direct = np.array([1.0 / t[u] if u in t.index and t[u] <= 25 else 0.0 for u in V["ids"]])
    assert np.allclose(rrP, direct); print("P1 aux reader P reference == RR from P's ranks: ok")
    inB = set(Ud[(Ud.y == 1) & (Ud.src == "B")].uid); mB = np.array([u in inB for u in V["ids"]])
    assert mB.sum() > 0 and rrP[mB].sum() == 0; print(f"P2 P reference ignores {int(mB.sum())} truths among the products: ok")
    # ---- adapter
    fold = V["fold"]; va = np.flatnonzero(fold == 0); tr = np.flatnonzero(fold != 0)
    ctx = dict(workspace=tmp, validation_path=os.path.join(tmp, "data/folds/validation.npz"), train_indices=tr, valid_indices=va, seed=11, smoke=False,
               config=dict(mode="fh", arm="gen", rounds=30), resource_ids=[], output_dir=None, fold=0)
    r = A.run_fold(ctx); G = r["valid_predictions"]; T = r["test_predictions"]
    vv = V["meta__cand_valid"][va]
    assert G.shape == (len(va), 75) and np.isfinite(G).all() and np.isfinite(T).all() and (G[vv] > M.NOT_SUBMITTED).all()
    print("A1 FH-gen: finite, every real slot scored: ok")
    for bad in (dict(mode="p_order"), dict(mode="fh", arm="db"), dict(mode="fh", arm="gen", params=dict(num_threads=32))):
        c2 = dict(ctx, config=bad); raises(A.run_fold, c2)
    print("A2 p_order / db / fixed-param override refused: ok")
    f0 = sorted(glob.glob(os.path.join(tmp, "data/raw/w135_u_dev_v2/U_*.parquet")))[0]; keep = open(f0, "rb").read()
    pd.read_parquet(f0).assign(fz=lambda d: d.fz + 1e-6).to_parquet(f0, index=False); raises(A.run_fold, ctx); open(f0, "wb").write(keep); print("A3 tampered table refused: ok")
    hq = os.path.join(tmp, "data/raw/w135_u_hold_e_v2/Q_00.parquet"); keep_h = open(hq, "rb").read(); man_p = os.path.join(tmp, "data/folds/data_manifest.json"); keep_m = open(man_p, "rb").read()
    pd.read_parquet(hq).assign(wclass="C2").to_parquet(hq, index=False); man = json.load(open(man_p)); man["w135_u_hold_e_v2/Q_00.parquet"] = sha(hq); json.dump(man, open(man_p, "w"))
    msg = raises(A.run_fold, ctx); assert "label" in msg, msg; open(hq, "wb").write(keep_h); open(man_p, "wb").write(keep_m); print("A4 label column refused with an updated manifest: ok")
    fq = sorted(glob.glob(os.path.join(tmp, "data/raw/w135_u_dev_v2/Q_*.parquet")))[0]; keep_q = open(fq, "rb").read()
    pd.read_parquet(fq).iloc[1:].to_parquet(fq, index=False); man = json.load(open(man_p)); man[f"w135_u_dev_v2/{os.path.basename(fq)}"] = sha(fq); json.dump(man, open(man_p, "w"))
    raises(A.run_fold, ctx); open(fq, "wb").write(keep_q); open(man_p, "wb").write(keep_m); print("A5 missing Q row refused: ok")
    Rw = pd.DataFrame(dict(uid=["u1", "u1", "u2", "u3"], nU=[2, 2, 1, 1])); Qw = pd.DataFrame(dict(uid=["u1", "u2", "u3", "u4"], iid=["i1", "i1", "i2", "i1"]))
    w = A.train_weights(Rw, Qw); assert np.allclose(w, [1 / 2 / 3, 1 / 2 / 3, 1 / 3, 1.0]), w; print("A6 roster-based weights (empty unit u4 counted): ok")
    shutil.rmtree(tmp, ignore_errors=True); print("TECH_TEST_V3_PASS")


if __name__ == "__main__":
    main()
