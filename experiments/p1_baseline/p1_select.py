"""P1 step 1 -- frozen, previously unused evaluation molecules (class-2 proxy, [M+H]+) with spectra, and a label-free candidate
recall table by stage and source.

Selection (per set, N molecules, seed fixed):
  A_timstof : enveda-180 molecules (timsTOF, synthetic-library chemistry)
  B_nplib   : molecules of the public natural-product libraries (gnps / riken / mona / massbank / msdial)
Common filters: has positive-mode [M+H]+ spectra in the selection library; identity fold 0 (so ONE fixed fold-safe FPNet
checkpoint, fold 0, never trained on them); not in MassSpecGym (raw InChIKey14 or official scorer key); not in any identity group
already used for development (enveda-np-examples panel, E2b/E2c molecules, passed as CSVs); one molecule per identity group.
No label-derived precursor-error filter is applied; the measured median precursor is used as-is and the error is only RECORDED.
Each set is split by identity group into fit / tune / eval thirds (for the later fusion work; this step treats them alike).

Candidate sources (provenance kept separately):
  pool_meta.parquet (public v2 pool; src 1 = train structures only, 2 = COCONUT only, 3 = both; keys are official scorer keys),
  coco_* (prvsiyan COCONUT candidate dataset; key type is checked and recorded), PubChem tier (105.9M rows, mass-sorted SMILES).
Recall stages per molecule (truth identity = official scorer key; tier/coco presence by raw InChIKey14 with an official-key
fallback over same-formula candidates when the raw key is absent, since equal raw keys imply equal official keys but not vice versa):
  db_present_external : truth exists in COCONUT (pool src 2/3 or coco) or in the PubChem tier at its THEORETICAL mass (+-2 mDa)
  window_external     : truth inside the +-10 ppm window around the MEASURED neutral mass in COCONUT or the PubChem tier
  window_train        : truth inside the window among train structures (pool src 1/3) -- a class-1 route, masked in the class-2 proxy
Usage: python -X utf8 p1_select.py --processed DIR --raw DIR --folds DIR --msg_dir DIR --pool pool_meta.parquet --coco DIR --tier DIR
                                   --exclude CSV [CSV ...] --out DIR [--n 300] [--seed 1] [--workers 8]
"""
import argparse, hashlib, json, os, pickle, time
from multiprocessing import Pool
import numpy as np, pandas as pd, polars as pl

PROTON, ELECTRON, PPM, EXACT_TOL = 1.007276, 0.000548, 10.0, 0.002
NP_LIBS = ["gnps", "riken", "mona", "massbank", "msdial"]


def _init(tier):
    global Chem, TAUT, CalcMolFormula, tmass, toff, tbuf
    from rdkit import Chem, RDLogger
    from rdkit.Chem.MolStandardize import rdMolStandardize
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula
    RDLogger.DisableLog("rdApp.*"); TAUT = rdMolStandardize.TautomerEnumerator()
    tmass = np.load(f"{tier}/pc_mass.npy", mmap_mode="r"); toff = np.load(f"{tier}/pc_off.npy", mmap_mode="r"); tbuf = np.load(f"{tier}/pc_smiles.npy", mmap_mode="r")


def _skey(m):
    try:
        m = Chem.Mol(m); Chem.RemoveStereochemistry(m); return Chem.MolToInchiKey(TAUT.Canonicalize(m))[:14]
    except Exception:
        return None


def _tier_smiles(lo_mass, hi_mass):
    lo = int(np.searchsorted(tmass, lo_mass, "left")); hi = int(np.searchsorted(tmass, hi_mass, "right"))
    if hi <= lo: return []
    o = np.asarray(toff[lo:hi + 1]).astype(np.int64); raw = bytes(tbuf[o[0]:o[-1]]); base = o[0]
    return [raw[o[i] - base:o[i + 1] - base].decode("ascii") for i in range(hi - lo)]


def _alias_keys(truth_smiles, truth_raw):
    """raw InChIKey14 of every RDKit-enumerated tautomer of the (stereo-stripped) truth: a window structure whose raw key is in this
    set has the same official scorer key as the truth (the official key is the canonical member of this tautomer class)."""
    keys = {truth_raw}
    try:
        m = Chem.MolFromSmiles(truth_smiles); Chem.RemoveStereochemistry(m)
        for t in TAUT.Enumerate(m):
            try: keys.add(Chem.MolToInchiKey(t)[:14])
            except Exception: pass
    except Exception:
        pass
    return keys


def _presence(smis, truth_raw, alias_keys, formula):
    """(n_valid_unique_raw, n_same_formula, present, how) over a list of SMILES; presence by raw key or tautomer alias."""
    seen, same_f, hit_raw, hit_alias = set(), 0, False, False
    for s in smis:
        m = Chem.MolFromSmiles(s)
        if m is None: continue
        k = Chem.MolToInchiKey(m)[:14]
        if k in seen: continue
        seen.add(k)
        if k == truth_raw: hit_raw = True
        elif k in alias_keys: hit_alias = True
        if CalcMolFormula(m) == formula: same_f += 1
    return len(seen), same_f, hit_raw or hit_alias, ("raw" if hit_raw else "official" if hit_alias else "")


def _tier_job(args):
    neutral, exact, truth_raw, truth_smiles, formula = args
    alias = _alias_keys(truth_smiles, truth_raw)
    tol = neutral * PPM * 1e-6
    n_win, n_sf, in_win, how_win = _presence(_tier_smiles(neutral - tol, neutral + tol), truth_raw, alias, formula)
    n_ex, _, in_ex, how_ex = _presence(_tier_smiles(exact - EXACT_TOL, exact + EXACT_TOL), truth_raw, alias, formula)
    return dict(n_tier_window=n_win, n_tier_same_formula=n_sf, truth_in_tier_window=in_win, tier_window_match=how_win,
                truth_in_tier_exact=in_ex, tier_exact_match=how_ex, n_tier_exact=n_ex, n_truth_tautomer_keys=len(alias))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""): h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    for k in ("processed", "raw", "folds", "msg_dir", "pool", "coco", "tier", "out"): ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--exclude", nargs="*", default=[]); ap.add_argument("--n", type=int, default=300); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=8); ap.add_argument("--max_spectra", type=int, default=8)
    ap.add_argument("--require_other_lib", action="store_true", help="keep only molecules with spectra in >= 2 libraries (class-1 scenario possible)")
    ap.add_argument("--sets", nargs="*", default=["A_timstof", "B_nplib"])
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); t0 = time.time()
    from rdkit import Chem, RDLogger
    from rdkit.Chem.MolStandardize import rdMolStandardize
    from rdkit.Chem.rdMolDescriptors import CalcMolFormula
    from rdkit.Chem.Descriptors import ExactMolWt
    RDLogger.DisableLog("rdApp.*"); TAUT = rdMolStandardize.TautomerEnumerator()

    def skey(m):
        m = Chem.Mol(m); Chem.RemoveStereochemistry(m); return Chem.MolToInchiKey(TAUT.Canonicalize(m))[:14]

    # ---------------------------------------------------------------- exclusions
    msg_raw = set(open(f"{a.msg_dir}/msg_raw_keys.txt").read().split()); msg_keys = set(open(f"{a.msg_dir}/msg_scorer_keys.txt").read().split())
    keys = pl.read_parquet(f"{a.processed}/train_scorer_keys.parquet").select("normalized_smiles", "scorer_ik14")
    meta = pl.read_parquet(f"{a.processed}/train_meta.parquet").join(keys, on="normalized_smiles", how="left")
    folds_pd = pd.read_parquet(f"{a.folds}/structures.parquet")[["inchikey14", "scorer_key", "identity_group", "fold_identity", "mono_mass"]].drop_duplicates("inchikey14")
    used_keys = set(meta.filter(pl.col("ingest_lib") == "enveda-np-examples")["scorer_ik14"].to_list())
    used_keys |= set(meta.filter(pl.col("ingest_lib") == "enveda-np-examples")["inchikey14"].to_list())
    excl_files = []
    for f in a.exclude:
        df = pd.read_csv(f); n0 = len(used_keys)
        for col in ("molecule", "scorer_key"):
            if col in df.columns: used_keys |= set(df[col].dropna().astype(str))
        excl_files.append(dict(file=f, rows=len(df), new_keys=len(used_keys) - n0))
    used_groups = set(folds_pd[folds_pd.inchikey14.isin(used_keys) | folds_pd.scorer_key.isin(used_keys)].identity_group)
    print(f"exclusions: MSG raw {len(msg_raw)} / scorer {len(msg_keys)}; development keys {len(used_keys)} -> identity groups {len(used_groups)} ({time.time()-t0:.0f}s)", flush=True)

    folds_pl = pl.from_pandas(folds_pd[["inchikey14", "identity_group", "fold_identity"]])
    pos = (meta.filter((pl.col("adduct") == "[M+H]+") & (pl.col("ionization_mode") == "positive"))
           .join(folds_pl, on="inchikey14", how="left")
           .filter(~pl.col("inchikey14").is_in(list(msg_raw)) & ~pl.col("scorer_ik14").is_in(list(msg_keys))
                   & ~pl.col("scorer_ik14").is_in(list(used_keys)) & ~pl.col("inchikey14").is_in(list(used_keys))
                   & ~pl.col("identity_group").is_in(list(used_groups)) & (pl.col("fold_identity") == 0)))

    def pick(lib_filter, name):
        d = pos.filter(lib_filter)
        g = (d.group_by("inchikey14").agg(pl.col("normalized_smiles").first(), pl.col("scorer_ik14").first(), pl.col("molecular_formula").first(),
                                          pl.col("ingest_lib").first(), pl.col("identity_group").first(), pl.len().alias("n_spectra_lib"),
                                          pl.col("precursor_mz").median().alias("prec_median"), pl.col("precursor_error_ppm").median().alias("ppm_err_median_label"),
                                          pl.col("ce_min").is_not_null().mean().alias("ce_known_frac"),
                                          pl.col("instrument_type").fill_null("").unique().sort().str.join("|").alias("instruments"))
             .sort("inchikey14").to_pandas())
        n_groups = g.identity_group.nunique()
        g = g.drop_duplicates("identity_group").sample(frac=1.0, random_state=a.seed).head(a.n).reset_index(drop=True)
        g["group"] = ["fit", "tune", "eval"][0:0] + [("fit", "tune", "eval")[i * 3 // len(g)] for i in range(len(g))]
        g["set"] = name
        print(f"{name}: eligible identity groups (fold 0, unused, not MSG) {n_groups}; sampled {len(g)}; libs {g.ingest_lib.value_counts().to_dict()}; "
              f"CE known frac mean {g.ce_known_frac.mean():.2f}", flush=True)
        return g

    if a.require_other_lib:
        multi = set(meta.group_by("inchikey14").agg(pl.col("ingest_lib").n_unique().alias("nl")).filter(pl.col("nl") >= 2)["inchikey14"].to_list())
        pos = pos.filter(pl.col("inchikey14").is_in(list(multi))); print(f"require_other_lib: {len(multi)} molecules have spectra in >= 2 libraries", flush=True)
    all_sets = {"A_timstof": (pl.col("ingest_lib") == "enveda-180"), "B_nplib": pl.col("ingest_lib").is_in(NP_LIBS)}
    sets = [pick(all_sets[n], n) for n in a.sets]
    mols = pd.concat(sets, ignore_index=True)
    lib_of = dict(zip(mols.inchikey14, mols.ingest_lib))

    # ---------------------------------------------------------------- spectra (selection library only, electron shift for enveda-180)
    sp = (pl.scan_parquet(f"{a.raw}/train.parquet")
          .filter(pl.col("inchikey14").is_in(mols.inchikey14.tolist()) & (pl.col("adduct") == "[M+H]+") & (pl.col("ionization_mode") == "positive"))
          .select("inchikey14", "ms2_mzs", "ms2_normalized_intensities", "precursor_mz", "adduct", "ionization_mode", "instrument_type",
                  "collision_energy_ev", "collision_energy_orig", "collision_energy_orig_units", "ingest_lib").collect().sort("inchikey14", "precursor_mz"))
    spectra_by = {}
    for s in sp.iter_rows(named=True):
        if s["ingest_lib"] != lib_of.get(s["inchikey14"]): continue
        shift = ELECTRON if s["ingest_lib"] == "enveda-180" else 0.0
        spectra_by.setdefault(s["inchikey14"], []).append(dict(
            mz=[float(x) - shift for x in s["ms2_mzs"]], it=[float(x) for x in s["ms2_normalized_intensities"]], prec=float(s["precursor_mz"]) - shift,
            adduct=s["adduct"], mode=s["ionization_mode"], instrument=s["instrument_type"], lib=s["ingest_lib"],
            ce_ev=[float(x) for x in s["collision_energy_ev"]] if s["collision_energy_ev"] is not None else None,
            ce_orig=s["collision_energy_orig"], ce_units=s["collision_energy_orig_units"]))
    print(f"spectra fetched for {len(spectra_by)} molecules ({time.time()-t0:.0f}s)", flush=True)

    # ---------------------------------------------------------------- pool + coco sources
    pool = pl.read_parquet(a.pool).select("key", "smiles", "formula", "mass", "src").sort("mass")
    pmass = pool["mass"].to_numpy(); pkey = pool["key"].to_numpy(); psrc = pool["src"].to_numpy(); pform = pool["formula"].to_numpy()
    pool_keys_ext = set(pool.filter(pl.col("src").is_in([2, 3]))["key"].to_list())
    cmeta = pickle.load(open(f"{a.coco}/coco_meta.pkl", "rb")); cmass = np.load(f"{a.coco}/coco_mass.npy"); ckey = np.asarray(cmeta["keys"]); csmi = np.asarray(cmeta["smiles"])
    rng = np.random.default_rng(0); idx = rng.choice(len(csmi), 300, replace=False)
    coco_key_is_official = float(np.mean([skey(Chem.MolFromSmiles(str(csmi[i]))) == str(ckey[i]) for i in idx if Chem.MolFromSmiles(str(csmi[i])) is not None]))
    coco_key_is_raw = float(np.mean([Chem.MolToInchiKey(Chem.MolFromSmiles(str(csmi[i])))[:14] == str(ckey[i]) for i in idx if Chem.MolFromSmiles(str(csmi[i])) is not None]))
    coco_keys = set(ckey.tolist())
    print(f"coco keys: official-key agreement {coco_key_is_official:.3f}, raw-key agreement {coco_key_is_raw:.3f} on 300 samples", flush=True)

    rows, items, jobs = [], [], []
    for r in mols.itertuples(index=False):
        tm = Chem.MolFromSmiles(r.normalized_smiles)
        spectra = spectra_by.get(r.inchikey14, [])[: a.max_spectra]
        if tm is None or not spectra: print("skip", r.inchikey14, "no mol/spectra"); continue
        truth_key = skey(tm); truth_raw = Chem.MolToInchiKey(tm)[:14]; formula = CalcMolFormula(tm); exact = ExactMolWt(tm)
        neutral = float(np.median([s["prec"] for s in spectra])) - PROTON
        tol = neutral * PPM * 1e-6
        lo = int(np.searchsorted(pmass, neutral - tol, "left")); hi = int(np.searchsorted(pmass, neutral + tol, "right"))
        pk, ps, pf = pkey[lo:hi], psrc[lo:hi], pform[lo:hi]
        ext = np.isin(ps, [2, 3]); trn = np.isin(ps, [1, 3])
        in_pool_ext_win = bool(np.any((pk == truth_key) & ext)); in_pool_trn_win = bool(np.any((pk == truth_key) & trn))
        clo = int(np.searchsorted(cmass, neutral - tol, "left")); chi = int(np.searchsorted(cmass, neutral + tol, "right"))
        in_coco_win = (truth_key in set(ckey[clo:chi].tolist())) if coco_key_is_official > 0.95 else (truth_raw in set(ckey[clo:chi].tolist()))   # coco keys are raw InChIKey14
        rows.append(dict(set=r.set, group=r.group, molecule=r.inchikey14, scorer_key=truth_key, raw_key=truth_raw, lib=r.ingest_lib, identity_group=int(r.identity_group),
                         formula=formula, exact_mass=exact, neutral_mass_measured=neutral, ppm_err_measured=(neutral - exact) / exact * 1e6,
                         ppm_err_median_label=r.ppm_err_median_label, n_spectra_lib=int(r.n_spectra_lib), n_spectra_used=len(spectra),
                         ce_known_frac=float(np.mean([bool(s["ce_ev"]) for s in spectra])), instruments="|".join(sorted({s["instrument"] or "" for s in spectra})),
                         n_pool_window=int(len(set(pk.tolist()))), n_pool_ext_window=int(len(set(pk[ext].tolist()))), n_pool_same_formula=int(len({k for k, f in zip(pk, pf) if f == formula})),
                         n_coco_window=int(len(set(ckey[clo:chi].tolist()))),
                         truth_in_pool_ext=truth_key in pool_keys_ext, truth_in_coco=(truth_key in coco_keys) if coco_key_is_official > 0.95 else (truth_raw in coco_keys),
                         truth_in_pool_ext_window=in_pool_ext_win, truth_in_pool_train_window=in_pool_trn_win, truth_in_coco_window=in_coco_win))
        items.append(dict(mid=r.inchikey14, set=r.set, group=r.group, spectra=spectra, truth_smiles=r.normalized_smiles, truth_key=truth_key, truth_raw=truth_raw,
                          formula=formula, neutral_mass=neutral, lib=r.ingest_lib))
        jobs.append((neutral, exact, truth_raw, r.normalized_smiles, formula))
    print(f"pool/coco recall done for {len(rows)} molecules; PubChem tier checks with {a.workers} workers ... ({time.time()-t0:.0f}s)", flush=True)
    with Pool(a.workers, initializer=_init, initargs=(a.tier,)) as pool_:
        tier = []
        for i, res in enumerate(pool_.imap(_tier_job, jobs, chunksize=4)):
            tier.append(res)
            if (i + 1) % 50 == 0: print(f"  tier {i+1}/{len(jobs)} ({time.time()-t0:.0f}s)", flush=True)
    df = pd.concat([pd.DataFrame(rows), pd.DataFrame(tier)], axis=1)
    df["db_present_external"] = df.truth_in_pool_ext | df.truth_in_coco.astype(bool) | df.truth_in_tier_exact
    df["window_external"] = df.truth_in_pool_ext_window | df.truth_in_coco_window.astype(bool) | df.truth_in_tier_window
    df["window_train"] = df.truth_in_pool_train_window
    df["window_any"] = df.window_external | df.window_train
    df.to_csv(f"{a.out}/p1_molecules.csv", index=False)
    json.dump(items, open(f"{a.out}/p1_items.json", "w"))
    lines = []
    for name, d in df.groupby("set"):
        lines += [f"== {name}: N={len(d)} | libs {d.lib.value_counts().to_dict()} | groups {d.group.value_counts().to_dict()} | CE known frac {d.ce_known_frac.mean():.2f} | instruments {d.instruments.value_counts().head(5).to_dict()}",
                  f"   measured ppm error: median {d.ppm_err_measured.median():+.2f}, |err|>10 ppm: {int((d.ppm_err_measured.abs() > 10).sum())} molecules",
                  f"   window sizes (median): PubChem tier {d.n_tier_window.median():.0f} (same formula {d.n_tier_same_formula.median():.0f}); pool {d.n_pool_window.median():.0f} (external {d.n_pool_ext_window.median():.0f}); coco {d.n_coco_window.median():.0f}",
                  f"   STAGE db_present_external {int(d.db_present_external.sum())}/{len(d)}  [COCONUT(pool) {int(d.truth_in_pool_ext.sum())}, coco dataset {int(d.truth_in_coco.astype(bool).sum())}, PubChem tier @exact {int(d.truth_in_tier_exact.sum())}]",
                  f"   STAGE window_external     {int(d.window_external.sum())}/{len(d)}  [pool-COCONUT {int(d.truth_in_pool_ext_window.sum())}, coco {int(d.truth_in_coco_window.astype(bool).sum())}, tier {int(d.truth_in_tier_window.sum())} (official-key fallback hits {int((d.tier_window_match == 'official').sum())})]",
                  f"   STAGE window_train (class-1 route, masked later) {int(d.window_train.sum())}/{len(d)} | window_any {int(d.window_any.sum())}/{len(d)}"]
    print("\n".join(lines), flush=True); open(f"{a.out}/p1_recall_summary.txt", "w").write("\n".join(lines))
    import rdkit
    man = dict(seed=a.seed, n_per_set=a.n, fold_identity=0, max_spectra=a.max_spectra, ppm_window=PPM, exact_tol_da=EXACT_TOL, electron_shift_libs=["enveda-180"],
               exclusions=dict(msg_raw=len(msg_raw), msg_scorer=len(msg_keys), development_keys=len(used_keys), development_identity_groups=len(used_groups), files=excl_files),
               coco_key_is_official=coco_key_is_official, coco_key_is_raw=coco_key_is_raw, rdkit=rdkit.__version__,
               inputs={p: sha(p) for p in (a.pool, f"{a.coco}/coco_mass.npy", f"{a.folds}/structures.parquet", f"{a.processed}/train_scorer_keys.parquet")},
               tier_rows=int(np.load(f"{a.tier}/pc_mass.npy", mmap_mode="r").shape[0]), seconds=round(time.time() - t0))
    json.dump(man, open(f"{a.out}/p1_select_manifest.json", "w"), indent=1)
    print(f"done {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
