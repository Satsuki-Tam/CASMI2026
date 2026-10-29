"""Codex 131 Q2 (MIST-feature ranker pair, step 1): how many ranker-training identities remain after excluding the MassSpecGym (MSG) molecules the
public MIST checkpoint was trained / selected on, by polarity and reference condition; and the same counts for the development tables.
Identity = the official scorer key (RemoveStereochemistry -> TautomerEnumerator().Canonicalize -> InChIKey[:14]) recomputed from the MSG SMILES;
the CASMI side uses scorer_key of the molecule CSVs. MSG folds: train (MIST training positives), val (checkpoint selection), test (unseen by the
checkpoint). Exposure classes per CASMI identity: msg_train_or_val (excluded from the pair's training rows), msg_test_only, not_in_msg.
Rows: the v8w7a training runs (b1_rank_train --runs of spark_e102.sh / v8w7a: run_v3_p1 fit, run_v3_eval, run_v3_c1, run_tp_f3a fit, run_tp_f4a fit)
with their group (fit / tune / eval after the :fit override), and the development tables used by 102 / 128. Polarity from the molecule tables'
adducts (positive only / negative only / both); reference condition = c1_usable. Counts only (no model output is read).
Usage (Spark, repo root): python -X utf8 experiments/mist/x_msg_overlap.py [--workers 16]"""
import argparse, glob, json, os
from multiprocessing import Pool
import numpy as np, pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
B = f"{ROOT}/experiments/b1_baseline"


def _keys(smiles):
    from rdkit import Chem, RDLogger
    from rdkit.Chem.MolStandardize import rdMolStandardize
    RDLogger.DisableLog("rdApp.*"); T = rdMolStandardize.TautomerEnumerator(); out = []
    for s in smiles:
        try:
            m = Chem.MolFromSmiles(s)
            if m is None: out.append(None); continue
            Chem.RemoveStereochemistry(m); out.append(Chem.MolToInchiKey(T.Canonicalize(m))[:14])
        except Exception: out.append(None)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=16); a = ap.parse_args()
    msg = pd.read_csv(f"{ROOT}/data/external/massspecgym/MassSpecGym.tsv", sep="\t", usecols=["identifier", "smiles", "inchikey", "fold", "adduct", "instrument_type"])
    us = sorted(set(msg.smiles.astype(str)))
    with Pool(a.workers) as p: ks = [k for ch in p.imap(_keys, [us[i:i + 300] for i in range(0, len(us), 300)], chunksize=1) for k in ch]
    key_of = dict(zip(us, ks)); msg["okey"] = msg.smiles.astype(str).map(key_of)
    folds = msg.dropna(subset=["okey"]).groupby("okey").fold.apply(set).to_dict()
    raw14 = msg.groupby(msg.inchikey.astype(str).str[:14]).fold.apply(set).to_dict()
    exp = lambda k: ("msg_train_or_val" if (folds.get(k, set()) & {"train", "val"}) else ("msg_test_only" if k in folds else "not_in_msg"))
    stats = dict(msg_spectra=len(msg), msg_smiles=len(us), msg_smiles_unparsed=sum(k is None for k in ks), msg_official_keys=len(folds),
                 msg_keys_by_fold={f: int(sum(f in v for v in folds.values())) for f in ("train", "val", "test")})
    RUNS = [("run_v3_p1", f"{ROOT}/experiments/p1_baseline/run1/p1_molecules.csv", "fit"), ("run_v3_eval", f"{B}/eval_set/p1_molecules.csv", None),
            ("run_v3_c1", f"{B}/eval_c1/p1_molecules.csv", None), ("run_tp_f3a", f"{B}/train_pool_f3a/p2_molecules.csv", "fit"), ("run_tp_f4a", f"{B}/train_pool_f4a/p2_molecules.csv", "fit")]
    DEV = [("np053f1dev", "run_np053_f1dev", f"{B}/np053_f1dev/p2_molecules.csv"), ("np053f2dev", "run_np053_f2dev", f"{B}/np053_f2dev/p2_molecules.csv"),
           ("f1dev", "run_f1dev", f"{B}/eval_set_f1/p2_molecules.csv"), ("f2dev", "run_f2dev", f"{B}/eval_set_f2/p2_molecules.csv"), ("panel", "run_panel_fe", f"{B}/panel_np250/p1_molecules.csv")]
    def mol_info(run):
        fs = sorted(glob.glob(f"{B}/{run}/b1_molecules_*.csv"))
        if not fs: return pd.DataFrame(columns=["molecule", "adducts", "c1_usable"])
        d = pd.concat([pd.read_csv(f, usecols=lambda c: c in ("molecule", "adducts", "c1_usable")) for f in fs], ignore_index=True); d["molecule"] = d.molecule.astype(str)
        return d.drop_duplicates("molecule")
    def pol(ad):
        s = [x for x in str(ad).split("|") if x and x != "nan"]
        if not s: return "unknown"
        p_, n_ = any(x.endswith("+") for x in s), any(x.endswith("-") for x in s)
        return "both" if (p_ and n_) else ("positive" if p_ else "negative")
    rows = []
    for name, csv, override in RUNS:
        m = pd.read_csv(csv, usecols=lambda c: c in ("set", "group", "molecule", "scorer_key", "lib")); m["molecule"] = m.molecule.astype(str)
        if override: m["group"] = override
        mi = mol_info(name); m = m.merge(mi, on="molecule", how="left")
        for r in m.itertuples(index=False):
            rows.append(dict(table=name, kind="train_run", group=r.group, molecule=r.molecule, key=str(r.scorer_key), lib=r.lib, polarity=pol(getattr(r, "adducts", "")),
                             c1_usable=bool(getattr(r, "c1_usable", False)) if pd.notna(getattr(r, "c1_usable", np.nan)) else False, exposure=exp(str(r.scorer_key)),
                             raw14_in_msg=r.molecule in raw14))
    for name, run, csv in DEV:
        if not os.path.exists(csv): continue
        m = pd.read_csv(csv, usecols=lambda c: c in ("set", "group", "molecule", "scorer_key", "lib")); m["molecule"] = m.molecule.astype(str)
        mi = mol_info(run); m = m.merge(mi, on="molecule", how="left")
        for r in m.itertuples(index=False):
            rows.append(dict(table=name, kind="dev", group=getattr(r, "set", ""), molecule=r.molecule, key=str(r.scorer_key), lib=r.lib, polarity=pol(getattr(r, "adducts", "")),
                             c1_usable=bool(getattr(r, "c1_usable", False)) if pd.notna(getattr(r, "c1_usable", np.nan)) else False, exposure=exp(str(r.scorer_key)),
                             raw14_in_msg=r.molecule in raw14))
    R = pd.DataFrame(rows); os.makedirs(f"{ROOT}/experiments/mist/out", exist_ok=True); R.to_csv(f"{ROOT}/experiments/mist/out/msg_overlap_rows.csv", index=False)
    md = ["# MSG exposure of the ranker-training and development identities (Codex 131 Q2, counts only)", "", "```", json.dumps(stats, indent=1), "```", ""]
    tr = R[R.kind == "train_run"]
    fit_ids = tr[tr.group == "fit"].drop_duplicates("key")
    md += ["## training runs: unique identities (official key) by group and exposure", "", "| group | identities | msg_train_or_val | msg_test_only | not_in_msg | kept (not train/val) share |", "|---|---:|---:|---:|---:|---:|"]
    for gname, gg in tr.drop_duplicates(["group", "key"]).groupby("group"):
        c = gg.exposure.value_counts(); n = len(gg)
        md.append(f"| {gname} | {n} | {c.get('msg_train_or_val', 0)} | {c.get('msg_test_only', 0)} | {c.get('not_in_msg', 0)} | {(n - c.get('msg_train_or_val', 0)) / max(n, 1):.3f} |")
    md += ["", "## fit identities by polarity / reference condition / library and exposure", "", "| stratum | value | identities | msg_train_or_val | kept |", "|---|---|---:|---:|---:|"]
    for col in ("polarity", "c1_usable", "lib"):
        for val, gg in fit_ids.groupby(col):
            c = int((gg.exposure == "msg_train_or_val").sum()); md.append(f"| {col} | {val} | {len(gg)} | {c} | {len(gg) - c} |")
    md += ["", "## development tables: identities by exposure", "", "| table | set | identities | msg_train_or_val | msg_test_only | not_in_msg | positive-capable (pos/both) |", "|---|---|---:|---:|---:|---:|---:|"]
    for (t, s), gg in R[R.kind == "dev"].drop_duplicates(["table", "group", "key"]).groupby(["table", "group"]):
        c = gg.exposure.value_counts(); md.append(f"| {t} | {s} | {len(gg)} | {c.get('msg_train_or_val', 0)} | {c.get('msg_test_only', 0)} | {c.get('not_in_msg', 0)} | {int(gg.polarity.isin(['positive', 'both']).sum())} |")
    md += ["", f"raw IK14 vs official-key agreement on the MSG membership (train runs): {float((tr.raw14_in_msg == (tr.exposure != 'not_in_msg')).mean()):.4f}"]
    open(f"{ROOT}/experiments/mist/out/msg_overlap.md", "w", encoding="utf-8").write("\n".join(md) + "\n"); print("\n".join(md))
