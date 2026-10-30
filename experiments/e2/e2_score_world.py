"""156 (v2 prep): E2 scores on a WORLD E-window table. The world tables (b1_ewin_world.py + e2_feats_world.py) carry identical c1 / c2
columns (the world view), so e2_common.view_frame(E, F, 'c1') keeps every world-window row and builds the 21 frozen E2 features; the frozen
E2 model (experiments/e2/model_v1/e2_lgb.txt, trained on the fold-3/4 np061 pools; no W135 identity) scores them; ranks inside each query
follow e2_common.rank_lists (score desc, f.z desc, official key). Writes <ewin dir>/e2s_<set>.parquet: set, molecule, official_key, smiles,
e2_score, e2_rank, n_e, fp, in_train (world), in_coconut, in_pcl, in_bio, lib_sim (world), ana_ap (world), frag, is_truth (label; used only by
the development table builder). No metric is computed.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/e2/e2_score_world.py --ewin DIR --sets SET [--model experiments/e2/model_v1/e2_lgb.txt]"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
import e2_common as C
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
MODEL_SHA_PREFIX = "fba8e860"


def main():
    import lightgbm as lgb
    ap = argparse.ArgumentParser(); ap.add_argument("--ewin", required=True); ap.add_argument("--sets", nargs="+", required=True)
    ap.add_argument("--model", default="experiments/e2/model_v1/e2_lgb.txt"); a = ap.parse_args()
    P_ = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p)
    mp = P_(a.model); msha = sha(mp)
    if not msha.startswith(MODEL_SHA_PREFIX): sys.exit(f"STOP: E2 model sha {msha[:16]} is not the frozen model_v1")
    bst = lgb.Booster(model_file=mp)
    if bst.feature_name() != C.FEATS: sys.exit("STOP: model features differ from e2_common.FEATS")
    man = dict(model_sha256=msha, model_rounds=bst.num_trees(), script=sha(os.path.abspath(__file__)), common=sha(os.path.join(HERE, "e2_common.py")), version="2.1", sets={})
    for s in a.sets:
        out = os.path.join(P_(a.ewin), f"e2s_{s}.parquet")
        if os.path.exists(out): sys.exit(f"STOP: {out} exists (no overwrite)")
        pe, pf = os.path.join(P_(a.ewin), f"ewin_{s}.parquet"), os.path.join(P_(a.ewin), f"e2f_{s}.parquet")
        E = pd.read_parquet(pe); F = pd.read_parquet(pf)
        fm = json.load(open(os.path.join(P_(a.ewin), "e2f_world_manifest.json")))
        if fm["sets"][s]["input_ewin"] != sha(pe) or fm["sets"][s]["output"] != sha(pf): sys.exit(f"STOP: {s}: e2f was not built from this ewin table (v2.1 chain)")
        if set(zip(E.molecule.astype(str), E.official_key)) != set(zip(F.molecule.astype(str), F.official_key)): sys.exit(f"STOP: {s}: E / F key sets differ")
        cols = ["set", "molecule", "official_key", "smiles", "e2_score", "e2_rank", "n_e", "fp", "in_train", "in_coconut", "in_pcl", "in_bio", "lib_sim", "ana_ap", "frag", "is_truth"]
        if not len(E):   # v2.1: a legal all-empty set -> typed empty table, no predict
            pd.DataFrame(columns=cols).to_parquet(out, index=False); man["sets"][s] = dict(rows=0, queries=0, sha=sha(out), input_ewin=sha(pe), input_e2f=sha(pf)); continue
        for c in ("in_train", "lib_sim", "lib_same", "lib_nref"):
            if not (E[f"{c}_c1"] == E[f"{c}_c2"]).all(): sys.exit(f"STOP: {c} c1 / c2 columns differ (not a world table)")
        X = C.view_frame(E, F, "c1")
        if len(X) != len(E): sys.exit("STOP: the c1 view dropped world rows")
        sc = bst.predict(X[C.FEATS].values.astype(float))
        if not np.isfinite(sc).all(): sys.exit("STOP: non-finite E2 score")
        R = C.rank_lists(X, sc)
        D = E.set_index(["molecule", "official_key"])
        out_df = pd.DataFrame(dict(set=R.set.values, molecule=R.molecule.values, official_key=R.official_key.values, smiles=R.smiles.values,
                                   e2_score=R.score.values, e2_rank=R["rank"].values, n_e=np.exp(R.log_n.values).round().astype(int), fp=R.fp.values,
                                   in_train=R.in_train.values, in_coconut=R.in_coconut.values, in_pcl=R.in_pcl.values, in_bio=R.in_bio.values,
                                   lib_sim=R.lib_sim.values, ana_ap=R.ana_ap.values, frag=R.frag.values, is_truth=R.is_truth.values))
        tmp_ = out + ".tmp"; out_df[cols].to_parquet(tmp_, index=False); os.replace(tmp_, out)
        man["sets"][s] = dict(rows=int(len(out_df)), queries=int(out_df.molecule.nunique()), sha=sha(out), input_ewin=sha(pe), input_e2f=sha(pf))
        print(f"{s}: {len(out_df)} rows, {out_df.molecule.nunique()} queries -> {out} (no metric)", flush=True)
    json.dump(man, open(os.path.join(P_(a.ewin), "e2s_manifest.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
