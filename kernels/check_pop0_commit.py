"""pop0 commit-run check (written before the kernel is pushed): the frozen-LAM reference lists of the pop0 commit run must equal, row by row
(content, not file bytes: the pipeline's row order comes from polars unique() and differs between runs), the lists of the two v8w7a commit
runs already on disk (kernels/b1-probe-tv8w7a/output_v1 and b1-probe-bv8w7a/output_v1, same notebook, same smoke molecules), for the files both
sides wrote: submission_fixed.csv and submission_probe_{train,nontrain}.csv (the v8w7a main list itself was replaced there by the probe extraction).
Also printed: the processed molecules, the POP0_RECORD line, and how many pop0 lists / rank-1 differ from the frozen-LAM main list (descriptive).
Usage: python -X utf8 kernels/check_pop0_commit.py kernels/b1-pop0/output_v1"""
import os, sys, json
import pandas as pd
out = sys.argv[1]; REF = ["kernels/b1-probe-tv8w7a/output_v1", "kernels/b1-probe-bv8w7a/output_v1"]
def load(p):
    s = pd.read_csv(p); assert s.molecule_id.is_unique; return s.set_index("molecule_id").smiles.astype(str)
ok = True
for mine, theirs in (("submission_lamref_fixed.csv", "submission_fixed.csv"), ("submission_lamref_probe_train.csv", "submission_probe_train.csv"),
                     ("submission_lamref_probe_nontrain.csv", "submission_probe_nontrain.csv")):
    a = load(os.path.join(out, mine))
    for r in REF:
        b = load(os.path.join(r, theirs)); assert set(a.index) == set(b.index), (mine, r, "ids")
        b = b.loc[a.index]; diff = [m for m in a.index if a[m] != b[m]]
        print(f"{mine} vs {r}/{theirs}: rows {len(a)}, processed {(a != 'CCO').sum()}, differing {len(diff)}"); ok &= not diff
m = load(os.path.join(out, "submission.csv")); r = load(os.path.join(out, "submission_lamref.csv")).loc[m.index]
proc = [k for k in m.index if m[k] != "CCO" or r[k] != "CCO"]
print("pop0 vs frozen-LAM main (this run): processed", len(proc), "lists changed", sum(m[k] != r[k] for k in proc), "rank-1 changed", sum(m[k].split(";")[0] != r[k].split(";")[0] for k in proc))
log = open(next(os.path.join(out, f) for f in os.listdir(out) if f.endswith(".log") and f.startswith("casmi26-b1-pop0")), encoding="utf-8", errors="replace").read()
rec = [l for l in log.splitlines() if "POP0_RECORD" in l]; print("record:", rec[-1][:600] if rec else "MISSING"); ok &= bool(rec)
meta = json.load(open(os.path.join(out, "submission_meta.json"))); print("pipeline_rc", meta["pipeline_rc"], "smoke", meta["smoke"], "processed", meta["n_processed"], "args", meta["pipeline_args"][-6:])
ok &= meta["pipeline_rc"] == 0 and "--lam_fixed" in meta["pipeline_args"]
print("POP0_COMMIT_CHECK", "PASS" if ok else "FAIL")
