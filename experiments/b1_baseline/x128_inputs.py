"""128 v3 input record (Codex 129): sha256 of every input the fold's 128 evaluation reads - evaluator, wf_common, ranker, MIST v3 manifests and
score tables, selection CSVs, feature tables, molecule ledgers, stored GLACIER outputs, frozen-P baselines - written at the start of the job and
compared at the end (the job fails if anything changed). The reader verifies the record against the files and the registered versions.
Usage (Spark, experiments/b1_baseline): python -X utf8 x128_inputs.py --fold 1 --out diag/x128v3_inputs.json [--check]"""
import argparse, glob, hashlib, json, os, sys
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ap = argparse.ArgumentParser(); ap.add_argument("--fold", type=int, required=True, choices=[1, 2]); ap.add_argument("--out", required=True); ap.add_argument("--check", action="store_true"); a = ap.parse_args()
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
K = a.fold
TAGS = {f"f{K}dev": (f"run_f{K}dev", f"eval_set_f{K}/p2_molecules.csv", f"diag/r102_f{K}dev.csv"), f"np053f{K}dev": (f"run_np053_f{K}dev", f"np053_f{K}dev/p2_molecules.csv", f"diag/r102_np053f{K}dev.csv")}
if K == 1: TAGS["c1bankdev"] = ("run_c1bankdev_f1", "c1bank_f1/c1dev/p2_molecules.csv", "diag/r111_base_c1bankdev.csv")
F = {"gen_eval2fd_n128v3.py": "gen_eval2fd_n128v3.py", "wf_common.py": "wf_common.py", "ranker": "rank_v8w7a/lambdarank.txt", "x128v3_summary.py": "x128v3_summary.py"}
MS = os.path.join(ROOT, "experiments", "mist", "scores_v3")
for t, (run, csv, base) in TAGS.items():
    F[f"{t}:eval_csv"] = csv; F[f"{t}:baseline"] = base; F[f"{t}:mist_manifest"] = os.path.join(MS, f"mist_{t}_manifest.json")
    for s in sorted(pd.read_csv(os.path.join(HERE, csv)).set.unique()):
        F[f"{t}:{s}:features"] = os.path.join(run, f"b1_features_{s}.parquet"); F[f"{t}:{s}:ledger"] = os.path.join(run, f"b1_molecules_{s}.csv")
        F[f"{t}:{s}:mist"] = os.path.join(MS, f"mist_{t}_{s}.parquet")
        for g in sorted(glob.glob(os.path.join(HERE, run, "work", f"gl_{s}.json*"))): F[f"{t}:{s}:gl:{os.path.basename(g)}"] = os.path.relpath(g, HERE)
rec = {k: dict(path=v, sha256=sha(v if os.path.isabs(v) else os.path.join(HERE, v))) for k, v in sorted(F.items())}
if a.check:
    old = json.load(open(os.path.join(HERE, a.out)))
    diff = sorted(k for k in set(old) | set(rec) if old.get(k, {}).get("sha256") != rec.get(k, {}).get("sha256"))
    if diff: sys.exit(f"inputs changed during the run: {diff[:10]}")
    print(f"inputs unchanged ({len(rec)} files)")
else:
    json.dump(rec, open(os.path.join(HERE, a.out), "w"), indent=1); print(f"input record: {len(rec)} files -> {a.out}")
