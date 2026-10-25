"""Work directory for a FULL-DATA FPNet training run ('full_np'): every identity fold is trained, only the NP-example panel groups are held
out (so the panel stays an unseen evaluation set). Same recipe as the public fold-safe training (train_fivefold.py / make_split.py of
dmitriigluzdov/casmi26-fold-safe-fpnet) with the held-out identity fold removed.

Steps: (1) hard-link the public structure / pool files (unchanged) into <run>/work; (2) rebuild the spectrum cache from the full competition
train.parquet with the public builder casmi.build.build_spec_cache (the cache copied from the E0 run was a class-2-proxy cache without the
600 evaluation molecules, so it is NOT reused); (3) split.parquet = make_split.py logic with no held-out fold ('np' rows only);
(4) check_inputs.json gate computed from the data (panel groups absent from the training rows).
Usage: python -X utf8 prep_full_np.py --run <abs run dir> --src data/external/harness_work --train data/raw/train.parquet
       --folds data/external/identity_folds/structures.parquet --code data/external/v3_models/code
"""
import argparse, hashlib, json, os, sys, time
import numpy as np, pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--src", required=True); ap.add_argument("--train", required=True)
ap.add_argument("--folds", required=True); ap.add_argument("--code", required=True); ap.add_argument("--expect_spectra", type=int, default=2539608)
a = ap.parse_args(); t0 = time.time()
wd = os.path.join(a.run, "work"); os.makedirs(wd, exist_ok=True)
STATIC = ["train_structs.parquet", "pool_meta.parquet", "pool_fp.npy", "fp_bits.npy", "train_fp_sel.npy", "pool_frag_mass.npy", "pool_frag_off.npy"]
for f in STATIC:
    src, dst = os.path.join(a.src, f), os.path.join(wd, f)
    if not os.path.exists(dst):
        try: os.link(src, dst)
        except OSError: import shutil; shutil.copy2(src, dst)
print("static files linked", round(time.time() - t0), "s", flush=True)
sys.path.insert(0, os.path.abspath(a.code))
from casmi import build
if not os.path.exists(os.path.join(wd, "spec_off.npy")):
    build.build_spec_cache(train_parquet=os.path.abspath(a.train), workdir=wd)
meta = pd.read_parquet(os.path.join(wd, "spec_meta.parquet"), columns=["sid"])
n_spec = len(meta); print("spectra in rebuilt cache", n_spec, "expected", a.expect_spectra, flush=True)
assert n_spec == a.expect_spectra, "rebuilt cache does not hold every training spectrum"
# split: make_split.py with no held-out identity fold
ts = pd.read_parquet(os.path.join(wd, "train_structs.parquet"))
st = pd.read_parquet(a.folds, columns=["inchikey14", "identity_group", "fold_identity"]).drop_duplicates("inchikey14")
j = ts.merge(st, on="inchikey14", how="left")
assert j.fold_identity.notna().all() and (j.sid.values == np.arange(len(j))).all()
assert j.groupby("key").fold_identity.nunique().max() == 1
is_np = (j.libmask.astype("int64") & (1 << 9)) != 0
np_groups = set(j.identity_group[is_np])
fold = np.where(j.identity_group.isin(np_groups), "np", "train")
out = pd.DataFrame(dict(sid=j.sid.values, fold=fold))
out[out.fold != "train"].to_parquet(os.path.join(wd, "split.parquet"), index=False)
counts = out.fold.value_counts().to_dict(); print("split", counts, flush=True)
# gate: panel identity groups must not appear among training rows; there is no held-out fold in this recipe
train_groups = set(j.identity_group[fold == "train"])
panel_overlap = len(np_groups & train_groups)
sid_of_spec = meta.sid.values; spec_train = int(np.isin(sid_of_spec, j.sid.values[fold == "train"]).sum())
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
gate = dict(passed=panel_overlap == 0, recipe="public fold-safe recipe with NO held-out identity fold (full_np): all folds trained, NP-example panel groups held out",
            spectra_total=n_spec, structures_total=len(ts), training_structure_rows=int((fold == "train").sum()), excluded_np_structure_rows=int((fold == "np").sum()),
            training_spectra_with_structure=spec_train, panel_identity_groups=len(np_groups), panel_training_overlap=panel_overlap, fold_training_overlap=0,
            held_out_fold=None, train_parquet_sha256=sha(a.train), folds_sha256=sha(a.folds), structs_sha256=sha(os.path.join(wd, "train_structs.parquet")),
            built=time.strftime("%Y-%m-%dT%H:%M:%S"))
json.dump(gate, open(os.path.join(a.run, "check_inputs.json"), "w"), indent=2)
print(json.dumps({k: v for k, v in gate.items() if not k.endswith("sha256")}), f"({time.time() - t0:.0f}s)")
