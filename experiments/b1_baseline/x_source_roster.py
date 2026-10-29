"""Codex 131 Q3 (1): source roster of every development molecule -- for each (table, set, molecule) of the used development tables, the truth's
official key and its membership in the candidate sources, separated into ORIGINAL-ASSET membership (key level) and VIEW-LEVEL eligibility:
  key level  : in_train (train structures, v2 pool src 1/3), in_coconut (pool src 2/3 or the COCONUT store via the feature table), in_pcl /
               in_bio (E key v2), group T / B / L / O by the priority T (train) > B (COCONUT) > L (PubChemLite or BIO) > O (other = only the
               PubChem tier or unresolved);
  view level : the truth row in the C2 / C1 view list (in_short_<view> and, for C2, the B1 source condition), its E membership in that view
               (in_coconut | in_train_<view> | E key), and the C2 view's train hiding (in_train_c2).
Molecules whose truth has no row in the feature table (empty window / not reached) keep key-level flags from the pool and E keys and are
marked absent at view level. Counts only (no model output is read). Writes diag/source_roster.parquet and diag/source_roster.md.
Usage (Spark, experiments/b1_baseline): python -X utf8 x_source_roster.py"""
import glob, os
import numpy as np, pandas as pd, polars as pl
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TABLES = {"np053f1dev": ("run_np053_f1dev", "np053_f1dev/p2_molecules.csv"), "np053f2dev": ("run_np053_f2dev", "np053_f2dev/p2_molecules.csv"),
          "f1dev": ("run_f1dev", "eval_set_f1/p2_molecules.csv"), "f2dev": ("run_f2dev", "eval_set_f2/p2_molecules.csv"), "panel": ("run_panel_fe", "panel_np250/p1_molecules.csv"),
          "c1bankdev": ("run_c1bankdev_f1", "c1bank_f1/c1dev/p2_molecules.csv")}
EK = pd.read_parquet(os.path.join(HERE, "diag/e_window_keys_v2.parquet")); PCL = set(EK[EK.in_pcl].key.astype(str)); BIO = set(EK[EK.in_bio].key.astype(str))
pool = pl.read_parquet(os.path.join(ROOT, "data/external/v2_pool/pool_meta.parquet"), columns=["key", "src"]).to_pandas(); pool["key"] = pool.key.astype(str)
SRC = pool.groupby("key").src.apply(lambda s: int(np.bitwise_or.reduce(s.astype(int).values))).to_dict()
rows = []
for t, (run, csv) in TABLES.items():
    ev = pd.read_csv(os.path.join(HERE, csv)); ev["molecule"] = ev.molecule.astype(str)
    for s, g in ev.groupby("set"):
        fp = os.path.join(HERE, run, f"b1_features_{s}.parquet")
        if not os.path.exists(fp): continue
        F = pd.read_parquet(fp); F["molecule"] = F.molecule.astype(str); T = F[F.is_truth.astype(bool)]
        for r in g.itertuples(index=False):
            k = str(r.scorer_key); src = SRC.get(k, 0); tr = T[T.molecule == r.molecule]
            in_train = bool(src & 1); in_coco = bool(src & 2) or (bool(tr.in_coconut.any()) if len(tr) else False); in_pcl, in_bio = k in PCL, k in BIO
            grp = "T" if in_train else ("B" if in_coco else ("L" if (in_pcl or in_bio) else "O"))
            rec = dict(table=t, set=s, molecule=r.molecule, key=k, in_train=in_train, in_coconut=in_coco, in_pcl=in_pcl, in_bio=in_bio, group=grp, truth_row=len(tr) > 0)
            for v in ("c2", "c1"):
                if len(tr):
                    x = tr.iloc[0]; inv = bool(x.get(f"in_short_{v}", True)) and (v == "c1" or bool(x.in_tier or x.in_coconut or x[f"in_train_{v}"]))
                    rec[f"in_list_{v}"] = inv; rec[f"in_E_{v}"] = inv and bool(x.in_coconut or x[f"in_train_{v}"] or k in PCL or k in BIO)
                    rec[f"train_visible_{v}"] = bool(x[f"in_train_{v}"])
                else: rec[f"in_list_{v}"] = False; rec[f"in_E_{v}"] = False; rec[f"train_visible_{v}"] = False
            rows.append(rec)
R = pd.DataFrame(rows); R.to_parquet(os.path.join(HERE, "diag/source_roster.parquet"), index=False)
L = ["# Development source roster (key-level group T > B > L > O; view-level C2 list / E membership)", "", "| table | set | n | T | B | L | O | C2 truth in list | C2 truth in E | C2 in list but outside E |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
for (t, s), g in R.groupby(["table", "set"], sort=False):
    c = g.group.value_counts()
    L.append(f"| {t} | {s} | {len(g)} | {c.get('T', 0)} | {c.get('B', 0)} | {c.get('L', 0)} | {c.get('O', 0)} | {int(g.in_list_c2.sum())} | {int(g.in_E_c2.sum())} | {int((g.in_list_c2 & ~g.in_E_c2).sum())} |")
open(os.path.join(HERE, "diag/source_roster.md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
