"""Inputs for the offline E0 port on the Spark (run with .venv/bin/python -I: it only READS the downloaded, untrusted asset trees).

shared  <shared>/kaggle_input/datasets/dmitriigluzdov/<slug>/...  per-file symlink mirrors in the Kaggle layout. The per-file download of the
        v4g assets nested every file under its own directory twice (casmi26-iceberg/casmi26-iceberg/ice_runner.py, casmi26-v4b-models/code/casmi/
        casmi26-v4b-models/code/casmi/engine.py) and stored some top-level files under their transport name (pubchem_tier__pc_mass.npy); the
        mirror undoes both so the notebook's globs (`/kaggle/input/**/<slug>/<marker>`, `**/pc_smiles.npy`, ...) resolve as on Kaggle.
        <shared>/train_c2_<tag>.parquet  class-2 proxy: data/raw/train.parquet minus every row whose official identity (train_scorer_keys.parquet)
        is in <eval_dir>/exclude_identities_c2.json, minus the query rows of <eval_dir>/exclude_rows_c1.json.
run     <run_dir>/kaggle_input/competitions/enveda-CASMI26-molecule-id-mass-spectra/{train.parquet,test.parquet,sample_submission.csv} (+ datasets ->
        shared). test.parquet is our evaluation test file re-written in the real test schema (spectrum_id / base_peak_intensity added, spectrum_row
        kept aside in <run_dir>/test_rows.csv); --limit N keeps the first N molecules (smoke).
Usage:
  python -I e0_prepare.py shared --root ~/CASMI2026 --shared experiments/e0_offline/runs/_shared [--eval_dir experiments/b1_baseline/eval_test_full3 --tag full3 --view c2|c1]
  python -I e0_prepare.py run --root ~/CASMI2026 --shared ... --run_dir experiments/e0_offline/runs/<name> --test <test.parquet> --train <train.parquet> [--limit 5]
"""
import argparse, glob, hashlib, json, os, sys, time
import numpy as np, pyarrow as pa, pyarrow.compute as pc, pyarrow.parquet as pq

SLUG, OWNER = "enveda-CASMI26-molecule-id-mass-spectra", "dmitriigluzdov"
# slug -> local copies (later entries override earlier ones file by file)
DATASETS = {   # slug -> local copies, in override order; a (dir, prefix) entry is mounted under <slug>/<prefix>/
    "casmi26-attributed-v4g-reproduction-assets": ["data/external_kaggle/casmi26-attributed-v4g-reproduction-assets",
                                                   # the GB10 copies B1 runs (src/ms_pred/nn_utils/{nn_utils,dgl_graph_ops}.py patched; everything else identical)
                                                   ("data/external/iceberg", "casmi26-iceberg"), ("data/external/glacier", "casmi26-glacier")],
    "casmi26-natural-product-knowledge-table": ["data/external_kaggle/casmi26-natural-product-knowledge-table"],
    "casmi26-pubchem-popularity-prior": ["data/external/pubchem_popularity", "data/external_kaggle/casmi26-pubchem-popularity-prior",
                                         ("data/external/pubchem_tier", "casmi26-pubchem-tier")],   # on Kaggle the tier arrays live inside this dataset
    "casmi26-natural-product-panel-benchmark": ["data/external/panel_benchmark"],
    "casmi26-fold-safe-fpnet": ["data/external/fold_safe_fpnet", "data/external_kaggle/casmi26-fold-safe-fpnet"],   # + the fivefold manifest / check files the PubChem channel asserts
}
# notebook globs (cells 03, 04, 11, 12, 13, 17) that must resolve inside <datasets root>
REQUIRED = ["casmi26-attributed-v4g-reproduction-assets/ATTRIBUTION.md", "casmi26-pubchem-popularity-prior/pc_lsid.npy",
            "casmi26-natural-product-panel-benchmark/panel.parquet", "casmi26-natural-product-knowledge-table/natural_products.parquet",
            "casmi26-fold-safe-fpnet/MODEL_INPUTS.json", "casmi26-fold-safe-fpnet/fpnet_fold4.pt", "casmi26-fold-safe-fpnet/MANIFEST_FIVEFOLD.json",
            "casmi26-fold-safe-fpnet/FIVEFOLD_VALIDATION.json", "casmi26-fold-safe-fpnet/check_inputs_fold0.json", "casmi26-fold-safe-fpnet/check_inputs_fold4.json",
            "casmi26-natural-product-knowledge-table/external_reference_spectra/external_delta.parquet",
            "casmi26-natural-product-knowledge-table/external_reference_spectra/external_record_quality.parquet",
            "casmi26-natural-product-knowledge-table/external_reference_spectra/external_scorer_sid_links.parquet",
            "**/casmi26-v4b-models/**/casmi/engine.py", "**/casmi26-v4b-models/**/MANIFEST.json", "**/casmi26-v3-models/**/casmi/engine.py",
            "**/casmi26-v3-models/**/ranker_0.pkl", "**/pool_meta.parquet", "**/pc_smiles.npy", "**/casmi26-iceberg/**/ice_runner.py",
            "**/casmi26-glacier/**/gl_runner.py", "**/casmi26-fpnet-full1/**/fpnet_full1.pt", "**/pool_lsid.npy", "**/pool_lpmid.npy"] + [f"casmi26-pubchem-popularity-prior/{n}" for n in
            ("pc_src_mask.npy", "pc_np.npy", "aligned_public_priors.py", "pc_lotus_refs.npy", "pc_lsynonyms.npy", "delta_pc_mass.npy",
             "growth_pc_mass.npy", "delta_pc_lsynonyms.npy", "growth_pc_lsynonyms.npy", "pc_formula_isomers.npy", "pc_different_parent_rows.npy")]


def sha256(path, n=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(n), b""): h.update(b)
    return h.hexdigest()


def kaggle_rel(rel, transport):
    """on-disk relative path -> Kaggle path: transport-named top-level file, or the doubled directory prefix collapsed."""
    parts = rel.split("/")
    if len(parts) == 1 and parts[0] in transport: return transport[parts[0]]
    for k in range(len(parts) // 2, 0, -1):
        if len(parts) >= 2 * k + 1 and parts[:k] == parts[k:2 * k]: return "/".join(parts[k:])
    return rel


def mirror(src_roots, dst_root):
    made, n = {}, 0
    for entry in src_roots:
        src_root, prefix = (entry if isinstance(entry, tuple) else (entry, ""))
        if not os.path.isdir(src_root): print("  (absent source)", src_root); continue
        transport = {}
        man = os.path.join(src_root, "MANIFEST.json")
        if os.path.exists(man):
            try:
                for v in json.load(open(man)).get("files", {}).values():
                    if isinstance(v, dict) and "transport_name" in v and "path" in v: transport[str(v["transport_name"])] = str(v["path"])
            except Exception as e: print("  manifest unreadable", man, repr(e))
        for root, _, fs in os.walk(src_root):
            for f in fs:
                src = os.path.abspath(os.path.join(root, f)); rel = os.path.relpath(src, os.path.abspath(src_root)).replace(os.sep, "/")
                if rel.startswith(".download") or "/__pycache__/" in "/" + rel or rel.endswith(".zip"): continue
                made[(prefix + "/" if prefix else "") + kaggle_rel(rel, transport)] = src     # later source roots override
    for tgt, src in made.items():
        dst = os.path.join(dst_root, tgt); os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.islink(dst):
            if os.readlink(dst) == src: continue
            os.remove(dst)
        elif os.path.exists(dst): raise RuntimeError(f"mirror target exists and is not a symlink: {dst}")
        os.symlink(src, dst); n += 1
    return n, made


def cmd_shared(a):
    root = os.path.abspath(a.root); shared = os.path.abspath(a.shared); dsroot = os.path.join(shared, "kaggle_input", "datasets", OWNER)
    os.makedirs(dsroot, exist_ok=True); report = {"datasets": {}, "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
    for slug, srcs in DATASETS.items():
        n, made = mirror([(os.path.join(root, s[0]), s[1]) if isinstance(s, tuple) else os.path.join(root, s) for s in srcs], os.path.join(dsroot, slug))
        report["datasets"][slug] = dict(files=len(made), new_links=n, sources=srcs); print(f"mirror {slug}: {len(made)} files ({n} new links)")
    missing = [p for p in REQUIRED if not glob.glob(os.path.join(dsroot, p), recursive=True)]
    report["missing_required"] = missing
    report["missing_optional"] = [p for p in ("**/dreams_np_mass.npy", "**/dreams_np_smiles.npy") if not glob.glob(os.path.join(dsroot, p), recursive=True)]
    print("optional (cell-17 tail filler) missing:", report["missing_optional"])
    print("required globs missing:", missing if missing else "none")
    # v4g manifest coverage (every manifest path should exist in the mirror)
    man = os.path.join(root, DATASETS["casmi26-attributed-v4g-reproduction-assets"][0], "MANIFEST.json")
    try:
        paths = [v["path"] for v in json.load(open(man))["files"].values()]
        absent = [p for p in paths if not os.path.exists(os.path.join(dsroot, "casmi26-attributed-v4g-reproduction-assets", p))]
        report["v4g_manifest"] = dict(paths=len(paths), absent=absent); print(f"v4g manifest: {len(paths)} paths, absent {len(absent)} {absent[:5]}")
    except Exception as e: print("v4g manifest check failed", repr(e))
    # the simulator packages E0 will use vs the copies B1 uses (same lineage?)
    for slug_dir, ours in (("casmi26-iceberg", "data/external/iceberg"), ("casmi26-glacier", "data/external/glacier")):
        mdir = os.path.join(dsroot, "casmi26-attributed-v4g-reproduction-assets", slug_dir); odir = os.path.join(root, ours); diff = []
        for r_, _, fs in os.walk(odir):
            for f in fs:
                if "__pycache__" in r_: continue
                rel = os.path.relpath(os.path.join(r_, f), odir).replace(os.sep, "/"); m = os.path.join(mdir, rel); o = os.path.join(r_, f)
                if not os.path.exists(m): diff.append(("only_ours", rel))
                elif os.path.getsize(m) != os.path.getsize(o) or (os.path.getsize(m) < 50 << 20 and sha256(m) != sha256(o)): diff.append(("differs", rel))
        for r_, _, fs in os.walk(mdir):
            for f in fs:
                rel = os.path.relpath(os.path.join(r_, f), mdir).replace(os.sep, "/")
                if not os.path.exists(os.path.join(odir, rel)): diff.append(("only_assets", rel))
        report[f"{slug_dir}_vs_{ours}"] = diff; print(f"{slug_dir} vs {ours}: {'identical' if not diff else diff[:12]}")
    if a.eval_dir:
        out = os.path.join(shared, f"train_{a.view}_{a.tag}.parquet")
        if os.path.exists(out) and not a.force: print(f"train_{a.view} exists", out)
        else: report[f"train_{a.view}"] = build_train(root, os.path.abspath(a.eval_dir), out, a.view)
    json.dump(report, open(os.path.join(shared, "prepare_report.json"), "w"), indent=1, default=str)
    return 1 if missing else 0


def build_train(root, eval_dir, out, view):
    """class-2 proxy (view c2): drop every train row whose official identity is an evaluation truth (+ the query rows);
    class-1 proxy (view c1): drop the query rows and the truth's references from the query's own library (mask_c1.json same_lib) only --
    references of the identity from other libraries stay, as in B1's C1 view (cross-library matching)."""
    t0 = time.time()
    keys = pq.read_table(os.path.join(root, "data/processed/train_scorer_keys.parquet"), columns=["inchikey14", "scorer_ik14"])
    ids = set(json.load(open(os.path.join(eval_dir, "exclude_identities_c2.json"))))
    k2off = {a_: b_ for a_, b_ in zip(keys.column("inchikey14").to_pylist(), keys.column("scorer_ik14").to_pylist()) if b_ in ids}
    rows_c1 = np.asarray(sorted(json.load(open(os.path.join(eval_dir, "exclude_rows_c1.json")))), np.int64)
    pairs = None
    if view == "c1":
        m1 = json.load(open(os.path.join(eval_dir, "mask_c1.json")))
        pairs = {(v["same_lib"]["identity"], v["same_lib"]["lib"]) for v in m1.values()}
    src = os.path.join(root, "data/raw/train.parquet"); pf = pq.ParquetFile(src)
    ik_type = pf.schema_arrow.field("inchikey14").type; vals = pa.array(sorted(k2off), type=ik_type)
    w = pq.ParquetWriter(out + ".tmp", pf.schema_arrow); off = 0; n_id = n_row = n_both = 0; per_off = {}
    for b in pf.iter_batches(batch_size=1 << 16):
        ik = b.column("inchikey14"); m_id = pc.fill_null(pc.is_in(ik, value_set=vals), False).to_numpy(zero_copy_only=False).astype(bool)
        if pairs is not None and m_id.any():          # c1: only the same-library references of the identity
            iks = np.asarray(ik.to_pylist(), dtype=object); libs = np.asarray(b.column("ingest_lib").to_pylist(), dtype=object)
            m_id = np.array([bool(m) and (k2off.get(k_), l_) in pairs for m, k_, l_ in zip(m_id, iks, libs)], dtype=bool)
        idx = np.arange(off, off + b.num_rows); m_row = np.isin(idx, rows_c1)
        n_id += int(m_id.sum()); n_row += int((m_row & ~m_id).sum()); n_both += int((m_row & m_id).sum())
        if m_id.any():
            for k_ in np.asarray(ik.to_pylist(), dtype=object)[m_id]: per_off[k2off[k_]] = per_off.get(k2off[k_], 0) + 1
        keep = ~(m_id | m_row)
        if keep.any(): w.write_table(pa.Table.from_batches([b]).filter(pa.array(keep)))
        off += b.num_rows
    w.close(); os.replace(out + ".tmp", out)
    zero = sorted(i for i in ids if i not in per_off)
    rep = dict(view=view, source=src, rows_in=off, rows_out=off - n_id - n_row, dropped_by_identity=n_id, dropped_query_rows_not_in_identity=n_row,
               query_rows_in_identity=n_both, identities=len(ids), identities_without_dropped_rows=len(zero), identities_without_dropped_rows_list=zero[:50],
               inchikey14_mapped=len(k2off), seconds=round(time.time() - t0), out=out)
    json.dump(rep, open(out + ".report.json", "w"), indent=1); print(f"train_{view}:", json.dumps(rep)[:800]); return rep


def cmd_run(a):
    root = os.path.abspath(a.root); run_dir = os.path.abspath(a.run_dir); shared = os.path.abspath(a.shared)
    comp = os.path.join(run_dir, "kaggle_input", "competitions", SLUG); os.makedirs(comp, exist_ok=True)
    ds = os.path.join(run_dir, "kaggle_input", "datasets")
    if os.path.islink(ds): os.remove(ds)
    os.symlink(os.path.join(shared, "kaggle_input", "datasets"), ds)
    te = pq.read_table(os.path.abspath(a.test))
    mids = list(dict.fromkeys(te.column("molecule_id").to_pylist()))
    if a.limit: mids = mids[:a.limit]; te = te.filter(pc.is_in(te.column("molecule_id"), value_set=pa.array(mids, type=te.schema.field("molecule_id").type)))
    rows = te.column("spectrum_row").to_pylist(); mol = te.column("molecule_id").to_pylist()
    bpi = pq.read_table(os.path.join(root, "data/raw/train.parquet"), columns=["base_peak_intensity"]).column(0).to_numpy(zero_copy_only=False)
    ref = pq.ParquetFile(os.path.join(root, "data/raw/test.parquet")).schema_arrow
    cols = {"molecule_id": pa.array(mol, pa.large_string()), "spectrum_id": pa.array([f"{m}_{r}" for m, r in zip(mol, rows)], pa.large_string()),
            "ms2_mzs": te.column("ms2_mzs").cast(pa.list_(pa.float64())), "ms2_normalized_intensities": te.column("ms2_normalized_intensities").cast(pa.list_(pa.float64())),
            "base_peak_intensity": pa.array([float(bpi[r]) for r in rows], pa.float64()), "adduct": te.column("adduct").cast(pa.large_string()),
            "ionization_mode": te.column("ionization_mode").cast(pa.large_string()), "instrument_type": te.column("instrument_type").cast(pa.large_string()),
            "precursor_mz": te.column("precursor_mz").cast(pa.float64()), "collision_energy_orig": te.column("collision_energy_orig").cast(pa.large_string()),
            "collision_energy_ev": te.column("collision_energy_ev").cast(pa.list_(pa.float64())), "collision_energy_orig_units": te.column("collision_energy_orig_units").cast(pa.large_string())}
    assert [f.name for f in ref] == list(cols), ([f.name for f in ref], list(cols))
    out = pa.table(cols); pq.write_table(out, os.path.join(comp, "test.parquet"))
    with open(os.path.join(run_dir, "test_rows.csv"), "w") as f:
        f.write("spectrum_id,molecule_id,spectrum_row\n"); f.writelines(f"{m}_{r},{m},{r}\n" for m, r in zip(mol, rows))
    with open(os.path.join(comp, "sample_submission.csv"), "w") as f:
        f.write("molecule_id,smiles\n"); f.writelines(f"{m},CCO\n" for m in mids)
    tr = os.path.join(comp, "train.parquet")
    if os.path.islink(tr) or os.path.exists(tr): os.remove(tr)
    os.symlink(os.path.abspath(a.train), tr)
    info = dict(run_dir=run_dir, test_source=os.path.abspath(a.test), test_sha256=sha256(os.path.abspath(a.test)), train=os.path.abspath(a.train),
                train_bytes=os.path.getsize(os.path.abspath(a.train)), limit=a.limit, molecules=len(mids), spectra=out.num_rows, time=time.strftime("%Y-%m-%dT%H:%M:%S"))
    json.dump(info, open(os.path.join(run_dir, "run_inputs.json"), "w"), indent=1); print("run inputs:", json.dumps(info)); return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("shared"); s.add_argument("--root", required=True); s.add_argument("--shared", required=True); s.add_argument("--eval_dir", default=None); s.add_argument("--tag", default="full3"); s.add_argument("--view", default="c2", choices=["c2", "c1"]); s.add_argument("--force", action="store_true")
    r = sp.add_parser("run"); r.add_argument("--root", required=True); r.add_argument("--shared", required=True); r.add_argument("--run_dir", required=True); r.add_argument("--test", required=True); r.add_argument("--train", required=True); r.add_argument("--limit", type=int, default=0)
    a = ap.parse_args(); sys.exit(cmd_shared(a) if a.cmd == "shared" else cmd_run(a))
