"""115 v2 (Codex 118 / 119): fixed simulated-positive plan = catalog + GLACIER job list + cycle order, decided before any generation or performance.
Catalog (mode 'all', the registered main comparison M_all): every IDENTITY with public COCONUT membership -- pool rows with src 2 (COCONUT only) or
3 (training structure and COCONUT) -- represented by ONE canonical pool row chosen by ONE function: a known identity (structures inchikey14 /
scorer_key, train_structs key / rawkey -> identity_group) is represented by the LOWEST pid among the pool rows of its train_structs keys; a src-2
row whose key belongs to a known identity is an alias spelling and maps to that canonical row (the identity keeps its COCONUT membership through
the alias; Codex 118); every other src-2 row is its own identity. Order of rules (fixed): unify to the canonical row -> neutral mass 150-1,200 Da
-> accepted by the runner's structure rules (gl_classify.accepted). No label, evaluation membership or score is read.
Every pool row of a known identity group maps to that group's canonical row (2 groups carry two official keys, e.g. pralidoxime's cation and
neutral tautomer; recorded in alias_audit.csv). STOP conditions (Codex 119): an official key (scorer_key / pool key) or a raw key mapping to two identities (a raw key equal to
ANOTHER identity's official key is shadowed by the official mapping and recorded); an alias row without a
canonical row; a cycle that does not visit every catalog pid exactly once; a pid whose cycle conditions repeat (2 cycles <= 6 conditions); job
tuples / jobs_pid inconsistent with the catalog; (existing mode) duplicate job tuples or a non-QTOF job.
Conditions: [M+H]+ / [M+Na]+ x CE 20 / 40 / 60 eV, QTOF token. Each identity has a fixed permutation of the 6 conditions (sha256(salt|key|cond));
cycle r (r = 0 .. R-1) visits every identity once, in the order sha256(salt|r|key), with condition perm[r mod 6]. With R = 2 an identity gets
its first two permuted conditions: about 40% of identities get the same adduct twice (not 'both adducts for every structure').
Only the (identity, condition) pairs the plan uses are written as jobs (generation on demand). Mode 'existing': the catalog and jobs.json of an
existing directory (e.g. cat15k, all 6 conditions generated) and a plan over those job indices (technical tests only).
Writes <out>/catalog.parquet, jobs.json ([smiles, adduct, 'QTOF', ce]), jobs_pid.npy, plan.npy, alias_audit.csv (mode all), plan_manifest.json
(counts, hashes of inputs, code and outputs). Usage:
  .venv/bin/python make_simplan.py all <pool_meta.parquet> <structures.parquet> <train_structs.parquet> <out> [--cycles 2] [--salt e115v2] [--limit N]
  .venv/bin/python make_simplan.py existing <dir with catalog.parquet + jobs.json> <out> [--cycles 2] [--salt e115v2] [--limit N]"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B1 = os.path.join(HERE, "..", "b1_baseline"); sys.path.insert(0, B1)
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
def stop(msg): sys.exit(f"STOP: {msg}")
if a.cycles > 6: stop("more than 6 cycles would repeat a condition")
man = dict(mode=a.mode, cycles=a.cycles, salt=a.salt, limit=a.limit, conditions=[list(c) for c in COND], inputs={},
           code={p: fsha(p) for p in (os.path.abspath(__file__), os.path.join(B1, "gl_classify.py"))})
if a.mode == "all":
    pool_p, st_p, ts_p, out = a.paths
    for p in (pool_p, st_p, ts_p): man["inputs"][p] = fsha(p)
    import gl_classify as GC
    P = pd.read_parquet(pool_p, columns=["pid", "key", "smiles", "mass", "formula", "src"])
    if not (P.pid.values == np.arange(len(P))).all(): stop("pid must be the row index")
    if P.key.duplicated().any(): stop("duplicate pool keys")
    st = pd.read_parquet(st_p, columns=["inchikey14", "scorer_key", "identity_group"])
    ts = pd.read_parquet(ts_p, columns=["key", "rawkey", "inchikey14"])
    ik2g = dict(zip(st.inchikey14.astype(str), st.identity_group.astype(int)))
    ts["g"] = ts.inchikey14.astype(str).map(ik2g)
    if ts.g.isna().any(): stop(f"{int(ts.g.isna().sum())} train_structs rows without an identity")
    # OFFICIAL scorer keys first (structures scorer_key, train_structs key = the pool key); raw InChIKey14 spellings only fill keys that are not
    # an official key of another identity (non-idempotent tautomer canonicalisation: a raw key can equal another identity's scorer key, e.g.
    # UWVKGDFRNQQIBO); conflicts among official keys, or among raw keys of different identities, STOP.
    k2g, shadowed = {}, []
    for k, g in [(str(k), int(g)) for k, g in zip(st.scorer_key, st.identity_group)] + [(str(k), int(g)) for k, g in zip(ts.key, ts.g)]:
        if k2g.setdefault(k, g) != g: stop(f"official key {k} maps to identities {k2g[k]} and {g}")
    official = set(k2g); raw = {}
    for k, g in [(str(k), int(g)) for k, g in zip(st.inchikey14, st.identity_group)] + [(str(k), int(g)) for k, g in zip(ts.rawkey, ts.g)]:
        if k in official:
            if k2g[k] != g: shadowed.append(dict(key=k, raw_of=g, official_of=k2g[k]))
            continue
        if raw.setdefault(k, g) != g: stop(f"raw key {k} maps to identities {raw[k]} and {g}")
    k2g.update(raw)
    key2pid = dict(zip(P.key.astype(str), P.pid.astype(int)))
    canon = {}
    for k, g in zip(ts.key.astype(str), ts.g.astype(int)):
        if k in key2pid: canon[g] = min(canon.get(g, 1 << 62), key2pid[k])   # fixed tie rule: lowest pid
    coco = P[P.src.isin([2, 3])]
    rows, alias = {}, []
    for r in coco.itertuples(index=False):
        k = str(r.key); g = k2g.get(k)
        if g is None:
            if int(r.src) == 3: stop(f"src-3 row {r.pid} without a known identity")
            rows[("c", k)] = int(r.pid)
        else:
            if g not in canon: stop(f"row {r.pid} ({k}) of identity {g} has no canonical row")
            if canon[g] != int(r.pid):   # an alias spelling (src 2) or a second official key of the same identity group (src 3; 2 groups)
                alias.append(dict(kind="alias_src2" if int(r.src) == 2 else "same_group_second_row_src3", row_pid=int(r.pid), row_key=k, identity=g,
                                  canonical_pid=canon[g], canonical_key=str(P.key.iloc[canon[g]]), canonical_src=int(P.src.iloc[canon[g]])))
            rows[("g", g)] = canon[g]
    pids = np.array(sorted(set(rows.values())), np.int64)
    C = P.iloc[pids].copy(); n_canon = len(C); C = C[C.mass.between(150, 1200)]
    ok = np.array([GC.accepted(str(s)) is True for s in C.smiles], bool); n_rej = int((~ok).sum()); C = C[ok]
    os.makedirs(out, exist_ok=True); pd.DataFrame(alias).to_csv(os.path.join(out, "alias_audit.csv"), index=False)
    man.update(coconut_rows=len(coco), alias_rows_mapped=len(alias), raw_keys_shadowed_by_official=shadowed, identities=len(rows), canonical_rows=n_canon, in_mass_range=int(len(ok)), rejected_by_runner_rules=n_rej)
    if a.limit: C = C.assign(h=[H(a.salt + "|" + str(k)) for k in C.key]).sort_values("h").head(a.limit).drop(columns=["h"])
    C = C.sort_values("pid").reset_index(drop=True)
else:
    src, out = a.paths
    C = pd.read_parquet(os.path.join(src, "catalog.parquet")); old_jobs = json.load(open(os.path.join(src, "jobs.json")))
    man["inputs"] = {os.path.join(src, f): fsha(os.path.join(src, f)) for f in ("catalog.parquet", "jobs.json")}
    tup = [(str(j[0]), str(j[1]), str(j[2]), float(j[3])) for j in old_jobs]
    if len(set(tup)) != len(tup): stop("duplicate job tuples in the existing job list")
    if any(t[2] != "QTOF" for t in tup): stop("a non-QTOF job in the existing job list")
    jmap = {(t[0], t[1], t[3]): n for n, t in enumerate(tup)}
    if a.limit: C = C.assign(h=[H(a.salt + "|" + str(k)) for k in C.key]).sort_values("h").head(a.limit).drop(columns=["h"]).sort_values("pid").reset_index(drop=True)
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
    C.to_parquet(os.path.join(out, "catalog.parquet"), index=False)
else:
    s2p = dict(zip(C.smiles.astype(str), C.pid.astype(int)))
    plan = np.array([jmap[(str(C.smiles.iloc[i]), COND[c][0], COND[c][1])] for i, c in plan_pairs], np.int64)
    jobs = old_jobs; jpid = [s2p.get(str(j[0]), -1) for j in jobs]   # jobs outside a --limit subset get -1 and are never in the plan
    C.to_parquet(os.path.join(out, "catalog.parquet"), index=False)
jpid = np.asarray(jpid, np.int64)
# checks (Codex 119)
cat_pid = C.pid.values.astype(np.int64); smi_of = dict(zip(cat_pid, C.smiles.astype(str)))
for r in range(a.cycles):
    cyc = jpid[plan[r * N:(r + 1) * N]]
    if len(cyc) != N or len(np.unique(cyc)) != N or set(cyc.tolist()) != set(cat_pid.tolist()): stop(f"cycle {r} does not visit every catalog pid exactly once")
conds = {}
for pos, j in enumerate(plan):
    jb = jobs[int(j)]; p_ = int(jpid[j])
    if p_ < 0 or smi_of.get(p_) != str(jb[0]) or str(jb[2]) != "QTOF" or (str(jb[1]), float(jb[3])) not in COND: stop(f"plan position {pos}: job {int(j)} inconsistent with the catalog")
    conds.setdefault(p_, []).append((str(jb[1]), float(jb[3])))
if any(len(set(v)) != len(v) for v in conds.values()): stop("a pid repeats a condition across cycles")
same_adduct = float(np.mean([len({c[0] for c in v}) == 1 for v in conds.values()])) if a.cycles == 2 else None
json.dump(jobs, open(os.path.join(out, "jobs.json"), "w")); np.save(os.path.join(out, "jobs_pid.npy"), jpid); np.save(os.path.join(out, "plan.npy"), plan)
man.update(catalog=N, jobs=len(jobs), plan=len(plan), share_same_adduct_both_cycles=same_adduct,
           outputs={f: fsha(os.path.join(out, f)) for f in ("catalog.parquet", "jobs.json", "jobs_pid.npy", "plan.npy")})
json.dump(man, open(os.path.join(out, "plan_manifest.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in man.items() if k not in ("outputs", "inputs", "conditions", "code")}))
