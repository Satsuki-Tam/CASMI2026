"""153 FH v0 data assembly (153_draft_fh.md; Codex 152 Q3): the unified candidate table U(q) = P's top 25 + the generated products B of every
query of a W135 world, with observable features computed on the same code paths as the 139 selector (w135_selector.load_world):
  common (every candidate) : fz (f.z: the view row's fp for a P candidate -- max over the official key's rows; the product's own f.z for B),
                             gl (released GLACIER, by SMILES; + gl_miss), frag (b1_frag, 0 when not computable);
  P side                   : rP (P's rank 1..25; 26 for products), sP (P's score; NaN for products, sP_miss = 1);
  product side             : apsc, log_npar, src_peer, src_train, n_steps, off_mass and the five edit groups of the 139 fixed edit table
                             (0 for P candidates; is_gen separates them); in_db = the product's official key is in the world's view list
                             (a DB structure outside P's top 25 that was also generated);
  query                    : p_gap12, gl_ok, lib_max, log_ncand, best_analog, n_peer_struct, n_train, n_b, n_p (= |P top 25|).
Labels: y = (official key == the batch's scorer key); joined only to write the table (no metric is computed or printed here).
Invariants (STOP): every check of w135_selector.check_world / load_world (world manifest, generation meta, product GL meta, B invariants,
B disjoint from P's top 25), a P candidate absent from the view list, duplicated keys in U, non-finite required values.
Writes experiments/w135/fh/U_<world>.parquet + U_<world>.meta.json (input hashes, script hash, row / query counts).
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_fh.py --worlds dF1_p30 [...] | --all"""
import argparse, hashlib, json, os, sys, time
from multiprocessing import Pool
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); B = os.path.join(ROOT, "experiments/b1_baseline"); sys.path.insert(0, B)
import w135_selector as S

OUTD = os.path.join(ROOT, "experiments/w135/fh")
EDITS = ["e_sugar", "e_methyl", "e_redox", "e_acyl", "e_other"]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
def stop(m): sys.exit(f"STOP (w135_fh): {m}")


def build(wname):
    from b1_features import heavy_ok
    W = S.check_world(wname); b, p = wname.split("_p")
    G = pd.read_parquet(os.path.join(W, "gen_full_v2.parquet")); G["molecule"] = G.molecule.astype(str)
    P = pd.read_parquet(os.path.join(W, "P.parquet")); P["molecule"] = P.molecule.astype(str)
    M = pd.read_csv(os.path.join(W, f"b1_molecules_{b}.csv")); M["molecule"] = M.molecule.astype(str)
    bt = pd.read_csv(os.path.join(ROOT, "experiments/w135/batches", f"{b}.csv")); bt["molecule"] = bt.molecule.astype(str)
    for nm, ids in (("generation", G.molecule), ("P", P.molecule), ("molecules table", M.molecule)):
        if ids.duplicated().any() or set(ids) != set(bt.molecule): stop(f"{wname}: {nm} ids are not one-to-one with the batch")
    G = G.set_index("molecule"); P = P.set_index("molecule"); M = M.set_index("molecule"); bt = bt.set_index("molecule")
    F = pd.read_parquet(os.path.join(W, f"b1_features_{b}.parquet")); F["molecule"] = F.molecule.astype(str)
    gl = json.load(open(os.path.join(W, "work", f"gl_{b}.json"))); pgl = json.load(open(os.path.join(W, "prod_gl.json")))
    runner = {d["mid"]: d for d in json.load(open(os.path.join(W, "prod_runner_in.json")))}
    if set(runner) != set(bt.index): stop(f"{wname}: product runner molecules != batch")
    tasks = []
    for m in bt.index:
        det = json.loads(G.loc[m, "B_detail_both"]); Bl = json.loads(G.loc[m, "B_both"]); t25 = json.loads(P.loc[m, "top25"]); keys = [d[0] for d in det]
        if keys != Bl or hashlib.sha1(";".join(Bl).encode()).hexdigest()[:16] != G.loc[m, "B_hash_both"] or len(set(Bl)) != len(Bl) or len(Bl) > 50: stop(f"{wname} {m}: B invariant")
        if set(Bl) & {e[1] for e in t25}: stop(f"{wname} {m}: B intersects P's top 25")
        if runner[m]["cands"] != [d[1] for d in det if heavy_ok(d[1])]: stop(f"{wname} {m}: product runner candidates != B")
        if int(P.loc[m, "n_cand"]) > 0 and not t25: stop(f"{wname} {m}: non-empty list without top 25")
        sm = [d[1] for d in det] + [e[2] for e in t25]
        sp = [dict(mz=np.asarray(s["mz"]), it=np.asarray(s["it"]), prec=s["prec"], mode=s["mode"]) for s in runner[m]["spectra"]]
        tasks.append((m, sm, sp))
    with Pool(12) as pool_: FR = dict(pool_.map(S._frag_job, tasks, chunksize=2))
    rows, qrows = [], []
    T = bt["scorer_key"].astype(str).to_dict()
    for m in bt.index:
        det = json.loads(G.loc[m, "B_detail_both"]); t25 = json.loads(P.loc[m, "top25"]); gq = gl.get(m) or {}; pq = pgl.get(m) or {}
        n_cand = int(P.loc[m, "n_cand"]); empty = n_cand == 0
        if empty:
            lib_max, gap = 0.0, 0.0; view = F.iloc[0:0]
        else:
            lib_max = float(M.loc[m, "lib_max_c2"])
            if not np.isfinite(lib_max): stop(f"{wname} {m}: lib_max missing for a non-empty list")
            view = F[(F.molecule == m) & F.in_short_c2.astype(bool) & (F.in_tier | F.in_coconut | F.in_train_c2).astype(bool)]
            sc = [e[3] for e in t25]; gap = float(sc[0] - sc[1]) if len(sc) >= 2 else 0.0
        vkeys = set(view.official_key.astype(str))
        an = json.loads(P.loc[m, "analogs"])
        q = dict(world=wname, batch=b, pi=int(p), molecule=m, fam=int(bt.loc[m, "fam"]), wclass=str(bt.loc[m, f"wclass_p{p}"]), used=bool(bt.loc[m, "used"]),
                 gl_ok=int(P.loc[m, "gl_ok"]), lib_max=lib_max, n_cand=n_cand, n_b=len(det), n_p=len(t25), p_gap12=gap, log_ncand=float(np.log1p(n_cand)),
                 best_analog=float(an[0][1]) if an else 0.0, n_peer_struct=int(G.loc[m, "n_peer_struct"]), n_train=int(G.loc[m, "n_train"]), truth=T[m])
        qrows.append(q)
        seen = set(); n_dup = 0
        for e in t25:   # e = [rank, official key, smiles, score, is_truth]; e[4] is a label and is never read here
            rank, key, smi, score = int(e[0]), str(e[1]), str(e[2]), float(e[3])
            if key in seen:   # an alias row of a key already listed: the scorer counts the first occurrence only
                n_dup += 1; continue
            tv = view[view.official_key.astype(str) == key]
            if not len(tv): stop(f"{wname} {m}: P candidate {key} not in the view list")
            fz = float(tv.fp.astype(float).max()); g_ = gq.get(smi)
            if not np.isfinite(fz) or not np.isfinite(score): stop(f"{wname} {m}: non-finite P value")
            rows.append(dict(world=wname, molecule=m, key=key, smiles=smi, src="P", is_gen=0, in_db=1, rP=rank, sP=score, sP_miss=0, fz=fz,
                             gl=0.0 if g_ is None else float(g_), gl_miss=int(g_ is None), frag=float(FR[m].get(smi, 0.0)), apsc=0.0, log_npar=0.0,
                             src_peer=0, src_train=0, n_steps=0, off_mass=0, **{k: 0 for k in EDITS}))
            seen.add(key)
        q["n_p_dup"] = n_dup
        for i, d in enumerate(det):
            key, smi, fz, apsc, npar, srcs, combo, loc, off = d; g_ = pq.get(smi)
            if key in seen: stop(f"{wname} {m}: duplicated key in U")
            seen.add(key)
            rows.append(dict(world=wname, molecule=m, key=str(key), smiles=str(smi), src="B", is_gen=1, in_db=int(str(key) in vkeys), rP=26, sP=0.0, sP_miss=1, fz=float(fz),
                             gl=0.0 if g_ is None else float(g_), gl_miss=int(g_ is None), frag=float(FR[m].get(smi, 0.0)), apsc=float(apsc), log_npar=float(np.log1p(npar)),
                             src_peer=int("peer" in srcs), src_train=int("train" in srcs), n_steps=(combo or "").count("+") + 1, off_mass=int(bool(off)), **S.edit_groups(combo)))
    R = pd.DataFrame(rows); Q = pd.DataFrame(qrows)
    num = ["rP", "sP", "fz", "gl", "frag", "apsc", "log_npar"]
    if len(R) and not np.isfinite(R[num].values.astype(float)).all(): stop(f"{wname}: non-finite feature")
    R["y"] = (R.key == R.molecule.map(T)).astype(int)
    if R.groupby("molecule").y.sum().max() > 1: stop(f"{wname}: more than one positive row in a query")
    return R, Q


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--worlds", nargs="*", default=[]); ap.add_argument("--all", action="store_true")
    a = ap.parse_args(); t0 = time.time(); os.makedirs(OUTD, exist_ok=True)
    worlds = (S.DESIGN + S.CONFIRM) if a.all else a.worlds
    if not worlds: stop("no worlds")
    for w in worlds:
        out = os.path.join(OUTD, f"U_{w}.parquet")
        if os.path.exists(out): stop(f"{out} exists (no overwrite)")
        R, Q = build(w)
        R.to_parquet(out, index=False); Q.to_parquet(os.path.join(OUTD, f"Q_{w}.parquet"), index=False)
        Wd = os.path.join(ROOT, "experiments/w135/worlds", w)
        meta = dict(world=w, script_sha256=sha(os.path.abspath(__file__)), selector_sha256=sha(os.path.join(HERE, "w135_selector.py")), b1_frag_sha256=sha(os.path.join(B, "b1_frag.py")),
                    inputs=dict(gen=sha(os.path.join(Wd, "gen_full_v2.parquet")), P=sha(os.path.join(Wd, "P.parquet")), prod_gl=sha(os.path.join(Wd, "prod_gl.json")),
                                world_manifest=sha(os.path.join(Wd, "manifest.txt"))),
                    n_rows=int(len(R)), n_queries=int(len(Q)), n_P_rows=int((R.src == "P").sum()), n_B_rows=int((R.src == "B").sum()), n_B_in_db=int(R.in_db[R.src == "B"].sum()),
                    U_sha256=sha(out), Q_sha256=sha(os.path.join(OUTD, f"Q_{w}.parquet")))
        json.dump(meta, open(os.path.join(OUTD, f"U_{w}.meta.json"), "w"), indent=1)
        print(f"[{time.time()-t0:5.0f}s] {w}: {len(Q)} queries, {len(R)} rows (P {meta['n_P_rows']}, B {meta['n_B_rows']}, B in_db {meta['n_B_in_db']}) -- no metric printed", flush=True)
