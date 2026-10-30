"""159 decision D, remaining item (technical, no label or metric is read): independent check of the flag formulas on the tables EXPORTED into
the v2 workspace (what the model sees), dev and hold. Per query (uid):
  T1 keys unique; rows = Q.n_u2 <= 100; T2 sum in_P = Q.n_p <= 25 and rP of the P rows is the permutation 1..n_p;
  T3 in_E25 => in_Ewin; in_E25 == in_Ewin & e2_rank <= 25; sum in_E25 = Q.n_e25 = min(25, n_e); e_miss == 1 - in_Ewin; 1 <= e2_rank <= n_e on
     the E-window rows; e_empty == (n_e == 0);
  T4 gen_only == in_B & !in_P & !in_Ewin; in_B_added == in_B & !in_P & !in_E25; every row is in_P | in_E25 | in_B;
  T5 f_applied (U and Q) == (n_p > 0 & n_e25 > 0); in_F_pool == (in_P | in_E25) when n_p > 0, else 0;
  T6 f_score == in_P / (10 + rP) + 0.5 * in_Ewin / (10 + e2_rank) (atol 1e-12) on the F-pool rows; f_rank of the F-pool rows ordered by
     (-f_score, rP, e2_rank, key) is 1 .. min(25, pool) and 26 elsewhere (P-empty queries: all 26).
  T0 every U uid is in Q; a Q uid without U rows must have n_u2 = n_p = n_e25 = f_applied = 0 (empty U2), counted separately.
  T7 (Codex 160) every numeric U and Q value is finite (NaN or Inf = failure); an empty-U2 query also has n_b = n_e = 0 and e_empty = 1.
Usage: python -X utf8 experiments/w135/x160_flags.py --ws C:/kaggle/competitions/casmi-harness-v2"""
import argparse, glob, os, sys
import numpy as np, pandas as pd


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ws", required=True); a = ap.parse_args()
    fails = []; nq = 0; nr = 0; nan = {}; n_empty = 0; nq_all = 0
    for sub in ("w135_u2_dev_v1", "w135_u2_hold_e_v1"):
        for pu in sorted(glob.glob(os.path.join(a.ws, "data/raw", sub, "U_*.parquet"))):
            tag = os.path.basename(pu)[2:-8]; U = pd.read_parquet(pu); Q = pd.read_parquet(os.path.join(os.path.dirname(pu), f"Q_{tag}.parquet")).set_index("uid")
            nq_all += len(Q); su = set(U.uid)
            if su - set(Q.index): fails.append(f"{sub}/{tag}: T0 U uid outside Q")
            for u in sorted(set(Q.index) - su):
                q = Q.loc[u]; n_empty += 1
                if (int(q.n_u2), int(q.n_p), int(q.n_e25), int(q.f_applied)) != (0, 0, 0, 0): fails.append(f"{sub}/{tag}/{u}: T0 empty U2 with non-zero counts")
                if (int(q.n_b), int(q.n_e), int(q.e_empty)) != (0, 0, 1): fails.append(f"{sub}/{tag}/{u}: T7 empty U2 needs n_b = n_e = 0 and e_empty = 1")
            for D_, nm in ((U, "U"), (Q, "Q")):
                for c in D_.columns:
                    if D_[c].dtype.kind in "fiu":
                        k = int((~np.isfinite(D_[c].astype(float))).sum())
                        if k: nan[f"{nm}.{c}"] = nan.get(f"{nm}.{c}", 0) + k
            for u, g in U.groupby("uid", sort=False):
                q = Q.loc[u]; nq += 1; nr += len(g); bad = lambda m: fails.append(f"{sub}/{tag}/{u}: {m}")
                n_p, n_e, n_e25 = int(q.n_p), int(q.n_e), int(q.n_e25)
                if g.key.duplicated().any(): bad("T1 duplicate key")
                if len(g) != int(q.n_u2) or len(g) > 100: bad("T1 row count")
                P = g[g.in_P == 1]
                if len(P) != n_p or n_p > 25 or sorted(P.rP.tolist()) != list(range(1, n_p + 1)): bad("T2 P rows / ranks")
                ew = g.in_Ewin == 1
                if ((g.in_E25 == 1) & ~ew).any(): bad("T3 E25 outside the E window")
                if not ((g.in_E25 == 1) == (ew & (g.e2_rank <= 25))).all(): bad("T3 in_E25 != E window & rank <= 25")
                if int(g.in_E25.sum()) != n_e25 or n_e25 != min(25, n_e): bad("T3 n_e25")
                if not (g.e_miss == 1 - g.in_Ewin).all(): bad("T3 e_miss")
                if ew.any() and not g[ew].e2_rank.between(1, n_e).all(): bad("T3 e2_rank range")
                if int(q.e_empty) != int(n_e == 0): bad("T3 e_empty")
                if not (g.gen_only == ((g.in_B == 1) & (g.in_P == 0) & (g.in_Ewin == 0)).astype(int)).all(): bad("T4 gen_only")
                if not (g.in_B_added == ((g.in_B == 1) & (g.in_P == 0) & (g.in_E25 == 0)).astype(int)).all(): bad("T4 in_B_added")
                if not ((g.in_P == 1) | (g.in_E25 == 1) | (g.in_B == 1)).all(): bad("T4 row outside P25 | E25 | B")
                fa = int(n_p > 0 and n_e25 > 0)
                if not (g.f_applied == fa).all() or int(q.f_applied) != fa: bad("T5 f_applied")
                pool = ((g.in_P == 1) | (g.in_E25 == 1)).astype(int) if n_p > 0 else pd.Series(0, index=g.index)
                if not (g.in_F_pool == pool).all(): bad("T5 in_F_pool")
                F = g[g.in_F_pool == 1]
                if len(F):
                    fs = F.in_P / (10 + F.rP.where(F.in_P == 1, 1)) * (F.in_P == 1) + 0.5 * (F.in_Ewin == 1) / (10 + F.e2_rank.where(F.in_Ewin == 1, 1))
                    if not np.allclose(F.f_score.values, fs.values, rtol=0, atol=1e-12): bad("T6 f_score formula")
                    o = F.assign(_k=F.key.astype(str)).sort_values(["f_score", "rP", "e2_rank", "_k"], ascending=[False, True, True, True])
                    exp = list(range(1, min(25, len(o)) + 1)) + [26] * max(0, len(o) - 25)
                    if o.f_rank.tolist() != exp: bad("T6 f_rank order")
                if (g[g.in_F_pool == 0].f_rank != 26).any(): bad("T6 f_rank outside the pool")
    print(f"X160_FLAGS {'PASS' if not fails else 'FAIL'}: {nq_all} queries in Q (dev + hold) = {nq} with U2 rows ({nr} rows) + {n_empty} with an empty U2; {len(fails)} failures")
    if nan: fails.append(f"T7 non-finite values {nan}")
    print("  non-finite per numeric column (U and Q):", nan or "none")
    for f in fails[:10]: print("  -", f)
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
