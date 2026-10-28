"""109 (a): input gate for the public fold-safe recipe (train_fivefold.py reads <run>/check_inputs.json). Computed from the run's work/split.parquet
(make_split.py of the public package) and the identity folds: training sids whose identity group is an NP-example group (panel_training_overlap)
or whose identity fold is the held-out fold (fold_training_overlap) must both be 0.
Usage: python fold_check.py <run_dir> <folds structures.parquet> <held_out_fold>"""
import json, os, sys
import numpy as np, pandas as pd
RUN, FOLDS, FOLD = sys.argv[1], sys.argv[2], int(sys.argv[3]); wd = os.path.join(RUN, "work")
ts = pd.read_parquet(os.path.join(wd, "train_structs.parquet")); sp = pd.read_parquet(os.path.join(wd, "split.parquet"))
st = pd.read_parquet(FOLDS, columns=["inchikey14", "identity_group", "fold_identity"]).drop_duplicates("inchikey14")
j = ts.merge(st, on="inchikey14", how="left"); fold = np.array(["train"] * len(j), dtype=object); fold[sp.sid.values] = sp.fold.values
is_np = (j.libmask.astype("int64") & (1 << 9)) != 0; np_groups = set(j.identity_group[is_np])
tr = fold == "train"
gate = dict(passed=True, recipe_variant=f"public fold recipe, held-out fold {FOLD}, new seed (109 a)", held_out_fold=FOLD,
            split_counts={k: int(v) for k, v in pd.Series(fold).value_counts().items()},
            panel_training_overlap=int((tr & j.identity_group.isin(np_groups).values).sum()), fold_training_overlap=int((tr & (j.fold_identity.values == FOLD)).sum()))
gate["passed"] = gate["panel_training_overlap"] == 0 and gate["fold_training_overlap"] == 0
json.dump(gate, open(os.path.join(RUN, "check_inputs.json"), "w"), indent=2); print(json.dumps(gate))
