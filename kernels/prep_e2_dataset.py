"""145: fill kernels/e2-model-dataset (private dataset hayatetaf/casmi26-e2-model) from the trained E2 model fetched from the Spark:
e2_lgb.txt (copied byte for byte) + e2_model_manifest.json (sha256, bytes, provenance, training-data description, cross-fit choice).
Usage: python -X utf8 kernels/prep_e2_dataset.py experiments/e2/model_v1"""
import hashlib, json, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); src = sys.argv[1]; dst = os.path.join(HERE, "e2-model-dataset")
m = os.path.join(src, "e2_lgb.txt"); tm = json.load(open(os.path.join(src, "e2_train_manifest.json")))
shutil.copyfile(m, os.path.join(dst, "e2_lgb.txt")); shutil.copyfile(os.path.join(src, "e2_ik14_to_scorer.parquet"), os.path.join(dst, "e2_ik14_to_scorer.parquet"))
sha = hashlib.sha256(open(os.path.join(dst, "e2_lgb.txt"), "rb").read()).hexdigest()
assert sha == tm["model"], ("model hash differs from the training manifest", sha, tm["model"])
man = dict(purpose="145 / 144_prereg_e2.md v2: the second engine E2 of the fusion F (identity RRF K 10, alpha 0.5) in the B1 pipeline (experiments/b1_e2k)",
           files={"e2_lgb.txt": dict(sha256=sha, bytes=os.path.getsize(os.path.join(dst, "e2_lgb.txt"))),
                  "e2_ik14_to_scorer.parquet": dict(sha256=hashlib.sha256(open(os.path.join(dst, "e2_ik14_to_scorer.parquet"), "rb").read()).hexdigest(), bytes=os.path.getsize(os.path.join(dst, "e2_ik14_to_scorer.parquet")),
                                                    what="inchikey14 -> official scorer key of every train structure (computed from train.parquet SMILES with RDKit 2026.03.3; = the development library index of E2)")},
           trainer="experiments/e2/e2_train.py (LightGBM binary, fixed parameters, rounds chosen by the fold 3 <-> 4 cross-fit only)",
           features=tm["feats"], params=tm["params"], rounds=tm["rounds"], groups=tm["groups"], rows=tm["rows"], groups_by_view=tm["groups_by_view"],
           training_data=("E-window tables (experiments/e2/b1_ewin.py + e2_feats.py) of the fold 3 / 4 pool molecules (train_pool_f3a/f3b/f4a/f4b, np061_f3pool/f4pool) "
                          "built from the competition train.parquet spectra, the v2 pool / COCONUT / PubChemLite / ChEBI-LIPID MAPS structures of the public Kaggle datasets, "
                          "and the fold-safe FPNet of each molecule's fold (public dataset casmi26-fold-safe-fpnet); no NIST-derived data"),
           code="experiments/e2/{b1_ewin,e2_feats,e2_common,e2_train}.py in the team repository (training code available)")
json.dump(man, open(os.path.join(dst, "e2_model_manifest.json"), "w"), indent=1)
print("dataset ready:", sorted(os.listdir(dst)), sha[:16])
