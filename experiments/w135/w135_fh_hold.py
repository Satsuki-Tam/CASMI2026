"""Harness test resource (154 G0 proposal): from the U / Q tables of the fold-0 e-worlds (built by w135_fh.py), write
  (1) FEATURE-ONLY copies for the casmi-harness workspace (res-w135-u-hold-e-v1): U without y; Q without truth / wclass / used / fam;
  (2) the label file kept OUTSIDE the workspace (hold_e_labels.parquet: world, molecule, truth, wclass) for the one human-approved
      holdout evaluation.
No metric is computed. Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_fh_hold.py"""
import glob, hashlib, json, os, sys
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FH = os.path.join(ROOT, "experiments/w135/fh")
OUT = os.path.join(FH, "hold_e_features"); LAB = os.path.join(FH, "hold_e_labels.parquet")
WORLDS = [f"{b}_p{p}" for b in ("eF1", "eF2", "eF3", "eR1", "eR2", "eR3") for p in (30, 0)]
DROP_U = ["y"]; DROP_Q = ["truth", "wclass", "used", "fam"]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    if os.path.exists(OUT) or os.path.exists(LAB): sys.exit("STOP: outputs exist (no overwrite)")
    os.makedirs(OUT); labs = []; man = dict(worlds={}, script_sha256=sha(os.path.abspath(__file__)))
    for w in WORLDS:
        mt = json.load(open(os.path.join(FH, f"U_{w}.meta.json")))
        U = pd.read_parquet(os.path.join(FH, f"U_{w}.parquet")); Q = pd.read_parquet(os.path.join(FH, f"Q_{w}.parquet"))
        if sha(os.path.join(FH, f"U_{w}.parquet")) != mt["U_sha256"] or sha(os.path.join(FH, f"Q_{w}.parquet")) != mt["Q_sha256"]: sys.exit(f"STOP: {w} tables differ from their meta")
        labs.append(Q[["world", "molecule", "truth", "wclass"]].copy())
        U.drop(columns=DROP_U).to_parquet(os.path.join(OUT, f"U_{w}.parquet"), index=False)
        Q.drop(columns=DROP_Q).to_parquet(os.path.join(OUT, f"Q_{w}.parquet"), index=False)
        man["worlds"][w] = dict(U=sha(os.path.join(OUT, f"U_{w}.parquet")), Q=sha(os.path.join(OUT, f"Q_{w}.parquet")), source_U=mt["U_sha256"], source_Q=mt["Q_sha256"])
    pd.concat(labs, ignore_index=True).to_parquet(LAB, index=False); man["labels_sha256"] = sha(LAB)
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
    print(f"feature-only tables for {len(WORLDS)} worlds -> {OUT}; labels kept at {LAB} (not for the workspace)")


if __name__ == "__main__":
    main()
