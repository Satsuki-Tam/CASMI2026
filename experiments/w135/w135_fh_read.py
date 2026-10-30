"""153 FH v0 registered reader (153 registration; written before any FH number is read).
Inputs: <x>_queries.parquet of the two directions (w135_fh_fit.py): d2c (train design, test confirm) and c2d (train confirm, test design).
Primary (per direction): pi3 = 0.3 worlds, all queries, mean RR difference gen - P; 95% interval = batch-pair bootstrap (3 pairs per side,
ratio estimator, 4000 draws, seed 20261030; exploratory as in 139); the family bootstrap is reported as auxiliary. d2c primary worlds = cF1/cR1/cF2/cR2/cF3/cR3 _p30 (as 139),
cU1_p30 reported separately; c2d primary worlds = dF1/dR1/dF2/dR2/dF3/dR3 _p30.
Gate (153): in BOTH directions gen - P >= +0.02 and the lower bound > 0; protections (lower bound >= -0.01): C1 and C2 queries of the pi 0.3
worlds, C1 and C2 queries of the pi 0 worlds, all queries of the pi 0 worlds.
Also reported (not gate): gen - db (the products' contribution), db - P (the connection change), per class (C1 / C2 / C3) means, C3 reach
(truth among U's products), truth in the final top 25 / at rank 1, mean RR when reached, and the c2d pi 0.6 worlds (real worlds, sensitivity).
Usage: python -X utf8 experiments/w135/w135_fh_read.py --d2c experiments/w135/fh/x153_d2c --c2d experiments/w135/fh/x153_c2d"""
import argparse, json, os, sys
import numpy as np, pandas as pd

PRIMARY = dict(d2c=[f"{b}_p30" for b in ("cF1", "cR1", "cF2", "cR2", "cF3", "cR3")], c2d=[f"{b}_p30" for b in ("dF1", "dR1", "dF2", "dR2", "dF3", "dR3")])
PI0 = dict(d2c=[f"{b}_p0" for b in ("cF1", "cR1", "cF2", "cR2", "cF3", "cR3")], c2d=[f"{b}_p0" for b in ("dF1", "dR1", "dF2", "dR2", "dF3", "dR3")])
NB, SEED = 4000, 20261030


def boot(D, a, b, mask, unit="pair"):
    """bootstrap of the registered all-query mean of (rr_a - rr_b) over rows in mask (ratio estimator: sum of differences / count of the drawn
    units). unit 'pair' = the batch pair j (xFj + xRj, the 139 exploratory unit; 3 per side); 'fam' = (batch, family) (auxiliary)."""
    X = D[mask]
    if not len(X): return np.nan, np.nan, np.nan, 0
    d = (X[f"rr_{a}"] - X[f"rr_{b}"]).values
    u = (X.batch.astype(str).str[-1]).values if unit == "pair" else (X.batch.astype(str) + "|" + X.fam.astype(str)).values
    units, inv = np.unique(u, return_inverse=True); s = np.bincount(inv, weights=d); c = np.bincount(inv).astype(float)
    rng = np.random.default_rng(SEED); est = d.mean(); bs = np.empty(NB)
    for i in range(NB):
        k = rng.integers(0, len(units), len(units)); bs[i] = s[k].sum() / c[k].sum()
    lo, hi = np.percentile(bs, [2.5, 97.5]); return est, lo, hi, len(X)


def fmt(t): return f"{t[0]:+.4f} [{t[1]:+.4f}, {t[2]:+.4f}] (n {t[3]})"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--d2c", required=True); ap.add_argument("--c2d", required=True); a = ap.parse_args()
    gate_ok = True; lines = []
    for dn, x in (("d2c", a.d2c), ("c2d", a.c2d)):
        D = pd.read_parquet(x + "_queries.parquet"); meta = json.load(open(x + "_meta.json"))
        prim = D.world.isin(PRIMARY[dn]); pi0 = D.world.isin(PI0[dn])
        g = boot(D, "gen", "P", prim); lines.append(f"## {dn} (train {meta['train']} -> test {meta['test']})")
        lines.append(f"PRIMARY gen - P (pi 0.3, all): {fmt(g)}")
        lines.append(f"  auxiliary family bootstrap: {fmt(boot(D, 'gen', 'P', prim, unit='fam'))}")
        ok = (g[0] >= 0.02) and (g[1] > 0)
        prot = {"C1 @ pi0.3": prim & (D.wclass == "C1"), "C2 @ pi0.3": prim & (D.wclass == "C2"), "C1 @ pi0": pi0 & (D.wclass == "C1"),
                "C2 @ pi0": pi0 & (D.wclass == "C2"), "all @ pi0": pi0}
        for nm, msk in prot.items():
            t = boot(D, "gen", "P", msk); pk = (not np.isfinite(t[1])) or t[1] >= -0.01; ok = ok and pk
            lines.append(f"protection {nm}: {fmt(t)} -> {'ok' if pk else 'FAIL'}")
        lines.append(f"gate ({dn}): {'PASS' if ok else 'NO'}"); gate_ok = gate_ok and ok
        lines.append(f"gen - db (pi 0.3, all): {fmt(boot(D, 'gen', 'db', prim))} | db - P (pi 0.3, all): {fmt(boot(D, 'db', 'P', prim))}")
        for wc in ("C1", "C2", "C3"):
            m = prim & (D.wclass == wc)
            if m.any(): lines.append(f"  pi0.3 {wc} (n {int(m.sum())}): P {D[m].rr_P.mean():.4f} db {D[m].rr_db.mean():.4f} gen {D[m].rr_gen.mean():.4f}")
        if dn == "d2c":
            mu = D.world == "cU1_p30"
            if mu.any(): lines.append(f"cU1_p30 (separate): gen - P {fmt(boot(D, 'gen', 'P', mu))}")
        if dn == "c2d":
            m6 = D.world.str.endswith("_p60")
            if m6.any(): lines.append(f"pi 0.6 worlds (sensitivity, real worlds): gen - P {fmt(boot(D, 'gen', 'P', m6))}")
        c3 = D[prim & (D.wclass == "C3")]
        if len(c3):
            inB = c3.apply(lambda r: r.truth in json.loads(r.top25_gen) or False, axis=1)
            lines.append(f"  C3 (pi0.3): n {len(c3)}, truth in gen top-25 {int(inB.sum())}, at rank 1 {int((c3.rr_gen == 1).sum())}, mean RR | in top-25 "
                         f"{c3[inB].rr_gen.mean() if inB.any() else float('nan'):.3f}")
        # false promotions: queries whose P rank-1 was correct and gen moved a product above it
        pr = D[prim & (D.rr_P == 1)]
        lines.append(f"  P rank-1 correct (pi0.3): n {len(pr)}, gen keeps rank 1 {int((pr.rr_gen == 1).sum())}, db keeps {int((pr.rr_db == 1).sum())}")
    lines.append(f"GATE (both directions): {'PASS' if gate_ok else 'NO'}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
