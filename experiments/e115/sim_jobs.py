"""115 (pilot, Codex 115 'fixed public catalog' version): a label-independent catalog subset and its GLACIER jobs.
Catalog = pool rows that are COCONUT-only structures (src == 2: not training structures), neutral mass 150-1200 Da, accepted by the runner's
structure rules (gl_classify.accepted; run in .venv because .venv-ice has no pyarrow -- gl_simulate.py re-checks every structure with the
runner's own smiles_ok in .venv-ice and records rejections); ordered by sha256(salt + key) and the first N taken (no label, score or evaluation
membership is read; overlap with evaluation truths is recorded afterwards, never used to select). Rows whose key is a known identity key or alias
(--known: train_structs key / rawkey / inchikey14 and structures inchikey14 / scorer_key; stage-2 check after Codex 112's alias rows) are skipped. Jobs = every structure x [M+H]+ / [M+Na]+ x
CE 20 / 40 / 60 eV (stored separately, not summed) x instrument token QTOF. Writes <out>/catalog.parquet (pid, key, smiles, mass, formula, hash)
and <out>/jobs.json ([smiles, adduct, 'QTOF', ce]); prints counts. Usage: .venv/bin/python sim_jobs.py <pool_meta.parquet> <out_dir> [--n 15000] [--salt e115]"""
import argparse, hashlib, json, os, sys
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "b1_baseline"))
import gl_classify as GC
ap = argparse.ArgumentParser(); ap.add_argument("pool"); ap.add_argument("out"); ap.add_argument("--n", type=int, default=15000); ap.add_argument("--salt", default="e115")
ap.add_argument("--known", nargs=2, metavar=("TRAIN_STRUCTS", "STRUCTURES"), default=None)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
P = pd.read_parquet(a.pool, columns=["pid", "key", "smiles", "mass", "formula", "src"])
P = P[(P.src == 2) & P.mass.between(150, 1200)].copy(); n_alias = 0
if a.known:
    ts = pd.read_parquet(a.known[0], columns=["key", "rawkey", "inchikey14"]); st = pd.read_parquet(a.known[1], columns=["inchikey14", "scorer_key"])
    known = set(ts.key.astype(str)) | set(ts.rawkey.astype(str)) | set(ts.inchikey14.astype(str)) | set(st.inchikey14.astype(str)) | set(st.scorer_key.astype(str))
    al = P.key.astype(str).isin(known); n_alias = int(al.sum()); P = P[~al]
P["hash"] = [hashlib.sha256((a.salt + str(k)).encode()).hexdigest() for k in P.key]
P = P.sort_values("hash"); keep, n_rej = [], 0
for r in P.itertuples(index=False):
    if GC.accepted(str(r.smiles)) is True: keep.append(r)
    else: n_rej += 1
    if len(keep) >= a.n: break
C = pd.DataFrame(keep)[["pid", "key", "smiles", "mass", "formula", "hash"]]; C.to_parquet(os.path.join(a.out, "catalog.parquet"), index=False)
jobs = [[s, ad, "QTOF", ce] for s in C.smiles.astype(str) for ad in ("[M+H]+", "[M+Na]+") for ce in (20.0, 40.0, 60.0)]
json.dump(jobs, open(os.path.join(a.out, "jobs.json"), "w"))
print(f"COCONUT-only pool rows in mass range {len(P)} (known-identity aliases skipped {n_alias}), catalog {len(C)} (rejected while scanning {n_rej}), jobs {len(jobs)}")
