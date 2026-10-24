"""P1 step 1: frozen, unused evaluation molecules and provenance-aware candidate recall (class-2 proxy, [M+H]+).

Evaluation molecules (two strata, N each): (A) enveda-180 identity-fold-0 molecules (timsTOF) and (B) molecules of the public
NP libraries (gnps/riken/mona/massbank/msdial), both restricted to molecules with [M+H]+ spectra, NOT in MassSpecGym (raw or
official key), and NOT used in any earlier experiment (enveda-np-examples panel, E2b/E2c sets, same identity group).
No label-derived ppm filter is applied to the selection; the measured precursor is used as-is.

Candidate retrieval per molecule (label-free): neutral mass = median [M+H]+ precursor (electron-corrected for enveda-180)
- PROTON; window +-10 ppm over three sources with provenance:
  pool_meta (public v2 pool: src 1 = train structures, 2 = COCONUT, 3 = both), PubChem tier.
Recall is recorded by the OFFICIAL scorer key: pool keys are already scorer keys; PubChem window candidates are canonicalised
only when their formula equals the truth's (cheap pre-filter) to decide presence.

Usage: python -X utf8 p1_select_and_recall.py <processed_dir> <folds_dir> <msg_tsv> <pool_meta.parquet> <pubchem_tier_dir> <exclude_csvs...> --out <dir> [--n 300] [--seed 1]
"""
import argparse, json, os, sys, time
import numpy as np, pandas as pd, polars as pl
from rdkit import Chem, RDLogger
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem.rdMolDescriptors import CalcMolFormula
RDLogger.DisableLog("rdApp.*")

ap = argparse.ArgumentParser()
ap.add_argument("processed"); ap.add_argument("folds"); ap.add_argument("msg"); ap.add_argument("pool"); ap.add_argument("tier")
ap.add_argument("exclude", nargs="*"); ap.add_argument("--out", required=True); ap.add_argument("--n", type=int, default=300); ap.add_argument("--seed", type=int, default=1)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
PROTON, ELECTRON, PPM = 1.007276, 0.000548, 10.0
TAUT = rdMolStandardize.TautomerEnumerator()
t0 = time.time()


def skey(mol):
    try:
        m = Chem.Mol(mol); Chem.RemoveStereochemistry(m); return Chem.MolToInchiKey(TAUT.Canonicalize(m))[:14]
    except Exception:
        return None


# --- identities to exclude: MSG (raw + scorer), panel, earlier experiment molecules (by scorer key) and their identity groups
msg = pl.read_csv(a.msg, separator="\t", columns=["inchikey", "smiles"], infer_schema_length=10000, ignore_errors=True)
msg_raw = set(msg["inchikey"].str.slice(0, 14).drop_nulls().to_list())
msg_keys = set(k for smi in msg["smiles"].drop_nulls().unique().to_list() for k in [skey(Chem.MolFromSmiles(smi)) if Chem.MolFromSmiles(smi) else None] if k)
keys = pl.read_parquet(f"{a.processed}/train_scorer_keys.parquet").select("normalized_smiles", "inchikey14", "scorer_ik14")
meta = pl.read_parquet(f"{a.processed}/train_meta.parquet").join(keys.select("normalized_smiles", "scorer_ik14"), on="normalized_smiles", how="left")
folds = pd.read_parquet(f"{a.folds}/structures.parquet")[["inchikey14", "scorer_key", "identity_group", "fold_identity"]].drop_duplicates("inchikey14")
group_of = folds.set_index("inchikey14").identity_group
used_keys = set(meta.filter(pl.col("ingest_lib") == "enveda-np-examples")["scorer_ik14"].to_list())
for f in a.exclude:
    try:
        df = pd.read_csv(f)
        col = "scorer_key" if "scorer_key" in df.columns else "molecule"
        used_keys |= set(df[col].astype(str))
        if "molecule" in df.columns: used_keys |= set(df["molecule"].astype(str))
    except Exception as e:
        print("exclude read failed", f, e)
used_groups = set(folds[folds.inchikey14.isin(used_keys) | folds.scorer_key.isin(used_keys)].identity_group)
print(f"exclusions: MSG raw {len(msg_raw)}, MSG scorer {len(msg_keys)}, used keys {len(used_keys)}, used identity groups {len(used_groups)} ({time.time()-t0:.0f}s)", flush=True)

pos = meta.filter((pl.col("adduct") == "[M+H]+") & (pl.col("ionization_mode") == "positive"))
pos = pos.with_columns(pl.col("inchikey14").map_elements(lambda k: int(group_of.get(k, -1)), return_dtype=pl.Int64).alias("identity_group"))
pos = pos.filter(~pl.col("inchikey14").is_in(list(msg_raw)) & ~pl.col("scorer_ik14").is_in(list(msg_keys)) & ~pl.col("scorer_ik14").is_in(list(used_keys)) & ~pl.col("identity_group").is_in(list(used_groups)))
fold0 = set(folds[folds.fold_identity == 0].inchikey14)


def pick(lib_filter, name):
    d = pos.filter(lib_filter)
    g = (d.group_by("inchikey14").agg(pl.col("normalized_smiles").first(), pl.col("scorer_ik14").first(), pl.col("molecular_formula").first(), pl.col("ingest_lib").first(),
                                      pl.col("precursor_mz").median().alias("prec_median"), pl.len().alias("n_spec"), pl.col("identity_group").first())
         .sort("inchikey14").to_pandas())
    if name == "A_timstof": g = g[g.inchikey14.isin(fold0)]
    g = g.drop_duplicates("identity_group").sample(n=min(a.n, len(g)), random_state=a.seed)
    print(f"{name}: eligible identity groups {d['identity_group'].n_unique()}, sampled {len(g)}; libs {g.ingest_lib.value_counts().to_dict()}", flush=True)
    return g


sets = {"A_timstof": pick(pl.col("ingest_lib") == "enveda-180", "A_timstof"),
        "B_nplib": pick(pl.col("ingest_lib").is_in(["gnps", "riken", "mona", "massbank", "msdial"]), "B_nplib")}

pool = pl.read_parquet(a.pool).select("key", "smiles", "formula", "mass", "src").sort("mass")
pmass = pool["mass"].to_numpy(); pkey = pool["key"].to_numpy(); psrc = pool["src"].to_numpy(); pform = pool["formula"].to_numpy()
tmass = np.load(f"{a.tier}/pc_mass.npy", mmap_mode="r"); toff = np.load(f"{a.tier}/pc_off.npy", mmap_mode="r"); tbuf = np.load(f"{a.tier}/pc_smiles.npy", mmap_mode="r")


def tier_window(target):
    tol = target * PPM * 1e-6
    lo = int(np.searchsorted(tmass, target - tol, "left")); hi = int(np.searchsorted(tmass, target + tol, "right"))
    if hi <= lo: return []
    o = np.asarray(toff[lo:hi + 1]).astype(np.int64); raw = bytes(tbuf[o[0]:o[-1]]); base = o[0]
    return [raw[o[i] - base:o[i + 1] - base].decode("ascii") for i in range(hi - lo)]


rows = []
for name, g in sets.items():
    for j, r in enumerate(g.itertuples(index=False)):
        tm = Chem.MolFromSmiles(r.normalized_smiles)
        if tm is None: continue
        truth_key = skey(tm); f_truth = CalcMolFormula(tm)
        shift = ELECTRON if r.ingest_lib == "enveda-180" else 0.0
        neutral = float(r.prec_median) - shift - PROTON
        tol = neutral * PPM * 1e-6
        lo = int(np.searchsorted(pmass, neutral - tol, "left")); hi = int(np.searchsorted(pmass, neutral + tol, "right"))
        pk = pkey[lo:hi]; ps = psrc[lo:hi]; pf = pform[lo:hi]
        in_pool = truth_key in set(pk.tolist())
        src_hit = sorted({int(s) for k, s in zip(pk, ps) if k == truth_key})
        in_coconut = any(s in (2, 3) for s in src_hit); in_train_only = (src_hit == [1])
        n_pool = len(set(pk.tolist())); n_pool_same_formula = len({k for k, f in zip(pk, pf) if f == f_truth})
        n_pool_ext = len({k for k, s in zip(pk, ps) if s in (2, 3)})
        # PubChem tier: official-key presence checked among same-formula candidates only
        smis = tier_window(neutral); n_tier = len(smis); same_f = 0; in_tier = False; seen_f = set()
        for s in smis:
            m = Chem.MolFromSmiles(s)
            if m is None or CalcMolFormula(m) != f_truth: continue
            same_f += 1
            if not in_tier and skey(m) == truth_key: in_tier = True
        rows.append(dict(set=name, molecule=r.inchikey14, scorer_key=truth_key, lib=r.ingest_lib, formula=f_truth, n_spectra=r.n_spec, neutral_mass=neutral,
                         n_pool_window=n_pool, n_pool_external=n_pool_ext, n_pool_same_formula=n_pool_same_formula, truth_in_pool=in_pool, truth_in_coconut=in_coconut, truth_train_only=in_train_only,
                         n_tier_window=n_tier, n_tier_same_formula=same_f, truth_in_tier=in_tier, truth_reachable_external=(in_coconut or in_tier)))
        if (j + 1) % 50 == 0: print(f"  {name}: {j+1}/{len(g)} ({time.time()-t0:.0f}s)", flush=True)
df = pd.DataFrame(rows)
df.to_csv(f"{a.out}/p1_eval_molecules_recall.csv", index=False)
for name, d in df.groupby("set"):
    print(f"\n== {name}: N={len(d)} | window sizes (median): pool {d.n_pool_window.median():.0f}, pool external {d.n_pool_external.median():.0f}, tier {d.n_tier_window.median():.0f}, "
          f"same-formula pool {d.n_pool_same_formula.median():.0f}, tier {d.n_tier_same_formula.median():.0f}")
    print(f"   truth in pool (any src) {d.truth_in_pool.mean():.3f} | in COCONUT {d.truth_in_coconut.mean():.3f} | train-only {d.truth_train_only.mean():.3f} | in PubChem tier {d.truth_in_tier.mean():.3f} | reachable from external DBs {d.truth_reachable_external.mean():.3f}")
json.dump(dict(seed=a.seed, n=a.n, excluded_keys=len(used_keys), excluded_groups=len(used_groups), msg_scorer_keys=len(msg_keys)), open(f"{a.out}/p1_manifest.json", "w"), indent=1)
print(f"done {time.time()-t0:.0f}s")
