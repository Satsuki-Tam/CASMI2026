"""Reproduction bundle for a locally trained FPNet (Codex 022): copies the exact code used into <dataset>/code/ and writes
<dataset>/TRAINING_MANIFEST.json with file hashes (code, inputs, split, dropped rows, audit groups), the full training arguments stored in the
checkpoint, environment versions, final evaluation and the git commit of the repository at bundling time.
Usage: python -X utf8 make_training_manifest.py --run experiments/fpnet_full/full_eval --ckpt full_eval_final.pt --dataset kernels/fpnet-fulleval-dataset
"""
import argparse, glob, hashlib, json, os, platform, shutil, subprocess, sys
ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--ckpt", required=True); ap.add_argument("--dataset", required=True)
ap.add_argument("--code_dir", default="data/external/v3_models/code"); ap.add_argument("--public_trainer", default="data/external/fold_safe_fpnet/train_fivefold.py")
ap.add_argument("--train", default="data/raw/train.parquet"); ap.add_argument("--folds", default="data/external/identity_folds/structures.parquet")
ap.add_argument("--extra_code", nargs="*", default=["experiments/fpnet_full/prep_full_eval.py", "experiments/fpnet_full/make_win_trainer.py", "experiments/fpnet_full/train_fivefold_win.py",
                "experiments/fpnet_full/gocheck_full_rk.py", "experiments/fpnet_full/full_eval_dropped_rows.py", "experiments/fpnet_full/audit_panel_dups.py", "experiments/b1_baseline/b1_common.py"])
ap.add_argument("--extra_files", nargs="*", default=["experiments/fpnet_full/full_eval_audit/panel_molecule_audit_groups.csv", "experiments/fpnet_full/full_eval_audit/panel_dup_audit_summary.json",
                "experiments/b1_baseline/eval_set2/v2/p2_molecules.csv", "experiments/b1_baseline/locked_eval2/v2/p2_molecules.csv"])
a = ap.parse_args()
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
D = a.dataset; os.makedirs(os.path.join(D, "code", "casmi"), exist_ok=True); os.makedirs(os.path.join(D, "records"), exist_ok=True)
code = {}
for p in a.extra_code + [a.public_trainer]:
    dst = os.path.join(D, "code", os.path.basename(p)); shutil.copy2(p, dst); code[p] = sha(p)
for p in sorted(glob.glob(os.path.join(a.code_dir, "casmi", "*.py"))):
    shutil.copy2(p, os.path.join(D, "code", "casmi", os.path.basename(p))); code[p.replace("\\", "/")] = sha(p)
for lic in glob.glob(os.path.join(a.code_dir, "**", "LICENSE*"), recursive=True) + glob.glob(os.path.join(os.path.dirname(a.code_dir), "LICENSE*")):
    shutil.copy2(lic, os.path.join(D, "code", "casmi", "LICENSE_" + os.path.basename(os.path.dirname(lic)))); code[lic.replace("\\", "/")] = sha(lic)
records = {}
for p in [os.path.join(a.run, f) for f in ("check_inputs.json", "check_inputs.prep.json", "gocheck.json", "launch.json", "dropped_train_rows.json", "query_identity_exposure.csv")] + \
         [os.path.join(a.run, "work", "split.parquet")] + glob.glob(os.path.join(a.run, "*_history.json")) + glob.glob(os.path.join(a.run, "*_progress.json")) + a.extra_files:
    if os.path.exists(p):
        nm = os.path.basename(p) if os.path.basename(p) != "p2_molecules.csv" else os.path.basename(os.path.dirname(os.path.dirname(p))) + "_" + os.path.basename(os.path.dirname(p)) + "_p2_molecules.csv"
        shutil.copy2(p, os.path.join(D, "records", nm)); records[p.replace("\\", "/")] = sha(p)
inputs = {p: sha(p) for p in (a.train, a.folds)}
for f in ("train_structs.parquet", "pool_meta.parquet", "fp_bits.npy", "pool_fp.npy"):
    p = os.path.join(a.run, "work", f); inputs[p.replace("\\", "/")] = sha(p)
import torch, numpy
ck = torch.load(os.path.join(a.run, a.ckpt), map_location="cpu", weights_only=False)
hist = sorted(glob.glob(os.path.join(a.run, "*_history.json")))
final = json.load(open(hist[0]))[-1] if hist else None
try: commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
except Exception: commit = None
man = dict(checkpoint=a.ckpt, checkpoint_sha256=sha(os.path.join(a.run, a.ckpt)), checkpoint_step=ck.get("step"), checkpoint_arch=dict(nbits=ck.get("nbits"), d=ck.get("d"), layers=ck.get("layers"), heads=ck.get("heads")),
           training_args=ck.get("args") or (ck.get("extra") or {}).get("args"), final_eval=final, repository="https://github.com/Satsuki-Tam/CASMI2026", repository_commit_at_bundling=commit,
           code_sha256=code, input_sha256=inputs, record_sha256=records,
           environment=dict(python=platform.python_version(), torch=torch.__version__, numpy=numpy.__version__, platform=platform.platform(),
                            gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None),
           negatives_note="traindata.Data.negatives() samples decoys from the whole v2 pool (training structures + COCONUT-derived structures, ahmedberatozer/casmi26-v2-pool); MS/MS supervision comes only from competition train.parquet",
           attribution=dict(trainer="dmitriigluzdov/casmi26-fold-safe-fpnet train_fivefold.py (Dmitrii Gluzdov)", windows_port="experiments/fpnet_full/make_win_trainer.py (this repository)",
                            model_and_data_access="casmi package of ahmedberatozer/casmi26-v3-models (Ahmed Berat Ozer)", fingerprint_bits="fp_bits.npy of ahmedberatozer/casmi26-v2-pool (unchanged)"))
json.dump(man, open(os.path.join(D, "TRAINING_MANIFEST.json"), "w"), indent=1, default=str)
print("manifest written:", os.path.join(D, "TRAINING_MANIFEST.json"), "| code files", len(code), "| records", len(records), "| ckpt sha", man["checkpoint_sha256"][:16], "| commit", commit)
