"""115 v2 (Codex 118): fixed simulated-positive plan = catalog + GLACIER job list + cycle order, decided before any generation or performance.
Catalog (mode 'all', the registered main comparison M_all): every IDENTITY with public COCONUT membership -- pool rows with src 2 (COCONUT only) or
3 (training structure and COCONUT) -- represented by its CANONICAL pool row: a src-2 row whose key is a known identity key / alias (structures
inchikey14 / scorer_key, train_structs key / rawkey) is mapped to that identity's canonical row (its training pool row via train_structs key) and is
not a separate identity (Codex 118: map aliases, do not drop the identity). Neutral mass 150-1,200 Da, accepted by the runner's structure rules
(gl_classify.accepted). No label, evaluation membership or score is read (the same rule for every structure).
Conditions: [M+H]+ / [M+Na]+ x CE 20 / 40 / 60 eV, QTOF token. Each identity has a fixed permutation of the 6 conditions (sha256(salt|key|cond)).
Cycle r (r = 0 .. R-1) visits every identity once, in the order sha256(salt|r|key), with condition perm[r mod 6] -> plan = R x N job indices.
Only the (identity, condition) pairs the plan uses are written as jobs (generation on demand; Codex 118). Mode 'existing': the catalog and
jobs.json of an existing directory (e.g. cat15k, all 6 conditions generated) and a plan over those job indices (technical tests).
Writes <out>/catalog.parquet, jobs.json ([smiles, adduct, 'QTOF', ce]), jobs_pid.npy (canonical pool row per job), plan.npy (int64 job index per
plan position), plan_manifest.json (counts, hashes of inputs and outputs, alias mapping counts).
Usage: .venv/bin/python make_simplan.py all <pool_meta.parquet> <structures.parquet> <train_structs.parquet> <out> [--cycles 2] [--salt e115v2] [--limit N]
       .venv/bin/python make_simplan.py existing <dir with catalog.parquet + jobs.json> <out> [--cycles 2] [--salt e115v2]"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "b1_baseline"))
COND = [(ad, ce) for ad in ("[M+H]+", "[M+Na]+") for ce in (20.0, 40.0, 60.0)]
ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["all", "existing"]); ap.add_argument("paths", nargs="+")
ap.add_argument("--cycles", type=int, default=2); ap.add_argument("--salt", default="e115v2"); ap.add_argument("--limit", type=int, default=0)
a = ap.parse_args()
H = lambda s: hashlib.sha256(s.encode()).hexdigest()
def fsha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
man = dict(mode=a.mode, cycles=a.cycles, salt=a.salt, conditions=[list(c) for c in COND], inputs={})
if a.mode == "all":
    pool_p, st_p, ts_p, out = a.paths
    for p in (pool_p, st_p, ts_p): man["inputs"][p] = fsha(p)
    import gl_classify as GC
    P = pd.read_parquet(pool_p, columns=["pid", "key", "smiles", "mass", "formula", "src"])
    assert (P.pid.values == np.arange(len(P))).all(), "pid must be the row index"
    st = pd.read_parquet(st_p, columns=["inchikey14", "scorer_key", "identity_group"])
    ts = pd.read_parquet(ts_p, columns=["key", "rawkey", "inchikey14"])
    # identity of every known key; canonical pool row of every training identity = the pool row of its train_structs key
    k2g = {}
    for c in ("inchikey14", "scorer_key"):
        k2g.update(dict(zip(st[c].astype(str), st.identity_group.astype(int))))
    ik2g = dict(zip(st.inchikey14.astype(str), st.identity_group.astype(int)))
    ts["g"] = ts.inchikey14.astype(str).map(ik2g)
    for c in ("key", "rawkey"):
        k2g.update({k: int(g) for k, g in zip(ts[c].astype(str), ts.g) if pd.notna(g)})
    key2pid = dict(zip(P.key.astype(str), P.pid.astype(int)))
    canon = {}   # identity -> canonical pool row (the training row)
    for k, g in zip(ts.key.astype(str), ts.g):
        if pd.notna(g) and k in key2pid: canon.setdefault(int(g), key2pid[k])
    coco = P[P.src.isin([2, 3])]
    rows, n_alias, n_alias_no_canon = {}, 0, 0
    for r in coco.itertuples(index=False):
        k = str(r.key); g = k2g.get(k)
        if g is None:                       # a COCONUT-only identity of its own
            rows[("c", k)] = int(r.pid)
        elif int(r.src) == 3 or canon.get(int(g)) == int(r.pid):   # the canonical training row itself (src 3)
            rows[("g", int(g))] = int(r.pid)
        else:                               # an alias spelling of a known identity -> its canonical row
            n_alias += 1
            if int(g) in canon: rows.setdefault(("g", int(g)), canon[int(g)])
            else: n_alias_no_canon += 1
    pids = np.array(sorted(set(rows.values())), np.int64)
    C = P.iloc[pids].copy(); C = C[C.mass.between(150, 1200)]
    ok = np.array([GC.accepted(str(s)) is True for s in C.smiles], bool); n_rej = int((~ok).sum()); C = C[ok]
    man.update(coconut_rows=len(coco), alias_rows_mapped=n_alias, alias_rows_without_canonical=n_alias_no_canon, identities=len(rows), canonical_rows=len(pids),
               in_mass_range=int(len(ok)), rejected_by_runner_rules=n_rej)
    C["ident"] = [H(a.salt + "|" + str(k)) for k in C.key]
    if a.limit: C = C.sort_values("ident").head(a.limit)
    C = C.sort_values("pid").reset_index(drop=True)
else:
    src, out = a.paths
    C = pd.read_parquet(os.path.join(src, "catalog.parquet")); old_jobs = json.load(open(os.path.join(src, "jobs.json")))
    man["inputs"] = {os.path.join(src, f): fsha(os.path.join(src, f)) for f in ("catalog.parquet", "jobs.json")}
    jmap = {(str(j[0]), str(j[1]), float(j[3])): n for n, j in enumerate(old_jobs)}
os.makedirs(out, exist_ok=True)
keys = C.key.astype(str).tolist(); N = len(C)
perm = [sorted(range(6), key=lambda c, k=k: H(f"{a.salt}|{k}|{COND[c][0]}|{COND[c][1]}")) for k in keys]
plan_pairs = []
for r in range(a.cycles):
    order = sorted(range(N), key=lambda i: H(f"{a.salt}|{r}|{keys[i]}"))
    plan_pairs += [(i, perm[i][r % 6]) for i in order]
if a.mode == "all":
    jid, jobs, jpid = {}, [], []
    for i, c in plan_pairs:
        if (i, c) not in jid:
            jid[(i, c)] = len(jobs); jobs.append([str(C.smiles.iloc[i]), COND[c][0], "QTOF", COND[c][1]]); jpid.append(int(C.pid.iloc[i]))
    plan = np.array([jid[p] for p in plan_pairs], np.int64)
    C.drop(columns=["ident"]).to_parquet(os.path.join(out, "catalog.parquet"), index=False)
else:
    jobs = old_jobs; s2p = dict(zip(C.smiles.astype(str), C.pid.astype(int)))
    plan = np.array([jmap[(str(C.smiles.iloc[i]), COND[c][0], COND[c][1])] for i, c in plan_pairs], np.int64)
    jpid = [s2p.get(str(j[0]), -1) for j in jobs]
    assert min(jpid) >= 0, "a job SMILES has no catalog row"
    if os.path.abspath(out) != os.path.abspath(src):
        C.to_parquet(os.path.join(out, "catalog.parquet"), index=False)
json.dump(jobs, open(os.path.join(out, "jobs.json"), "w")); np.save(os.path.join(out, "jobs_pid.npy"), np.asarray(jpid, np.int64)); np.save(os.path.join(out, "plan.npy"), plan)
assert len(np.unique(plan[:N])) == N, "the first cycle must visit every identity once"
man.update(catalog=N, jobs=len(jobs), plan=len(plan), outputs={f: fsha(os.path.join(out, f)) for f in ("catalog.parquet", "jobs.json", "jobs_pid.npy", "plan.npy")})
json.dump(man, open(os.path.join(out, "plan_manifest.json"), "w"), indent=1); print(json.dumps({k: v for k, v in man.items() if k not in ("outputs", "inputs", "conditions")}))
