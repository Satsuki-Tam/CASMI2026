"""Class-3 feasibility probe for analog-derivative generation (b1_gen), 2026-10-26.

Simulates "the truth is in no structure database": for each evaluation molecule the parents are the top train analogs found by
spectral similarity under the C2 mask (truth key, raw keys and identity group removed, query rows never), the target is the truth's
neutral mass (the pipeline would use precursor m/z - adduct), and b1_gen.derive() enumerates one/two-step derivatives of the top-P
parents. Measures (labels used only for these measurements):
  * gen_hit       : the truth (raw InChIKey first block or scorer key) is among the generated products
  * n_products    : unique generated structures (the decoys the ranker would have to beat)
  * hit_rank_ap   : the truth's rank among the products by a label-free score = max over parents of sim^3 * Tanimoto(product, parent),
                    ties by the number of parents producing the structure
Usage: python -X utf8 gen_probe.py --sets EVAL_CSV:SET1,SET2 ... --out diag/genprobe_<name> [--parents 10] [--workers 16]
"""
import argparse, os, sys, time
import numpy as np, pandas as pd, polars as pl
from multiprocessing import Pool
from numba import set_num_threads
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from b1_common import ADDUCT_SHIFT, ELECTRON, select_queries  # noqa: E402
import b1_analog as BA  # noqa: E402

ap_ = argparse.ArgumentParser()
ap_.add_argument("--store", default="data/processed/spectra_store")
ap_.add_argument("--structs", default="data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/casmi26-v2-pool/casmi26-v2-pool/train_structs.parquet")
ap_.add_argument("--folds", default="data/external/identity_folds/structures.parquet")
ap_.add_argument("--sets", nargs="+", required=True)
ap_.add_argument("--parents", type=int, default=10); ap_.add_argument("--workers", type=int, default=16); ap_.add_argument("--limit", type=int, default=0)
ap_.add_argument("--out", required=True); ap_.add_argument("--max_spectra", type=int, default=8); ap_.add_argument("--threads", type=int, default=16)
a = ap_.parse_args()
ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); T0 = time.time()
def log(*x): print(f"[gen {time.time() - T0:6.0f}s]", *x, flush=True)


def gen_job(t):
    """t = (set, molecule, truth_keys, truth_smiles, [(parent_smiles, sim)]) -> result row."""
    import b1_gen as BG
    from rdkit import Chem, RDLogger, DataStructs
    from rdkit.Chem import rdFingerprintGenerator, Descriptors
    RDLogger.DisableLog("rdApp.*"); gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    s, mid, tkeys, tsmi, parents = t
    tm = Chem.MolFromSmiles(tsmi) if tsmi else None
    if tm is None: return dict(set=s, molecule=mid, ok=False)
    M = Descriptors.ExactMolWt(tm); prods = {}
    for pi, (psmi, sim) in enumerate(parents):
        pm = Chem.MolFromSmiles(psmi)
        if pm is None: continue
        pfp = gen.GetFingerprint(pm)
        for smi, combo in BG.derive(psmi, M - Descriptors.ExactMolWt(pm)).items():
            m = Chem.MolFromSmiles(smi)
            if m is None: continue
            try: k = Chem.MolToInchiKey(m)[:14]
            except Exception: continue
            if not k: continue
            sc = sim ** 3 * DataStructs.TanimotoSimilarity(gen.GetFingerprint(m), pfp)
            d = prods.setdefault(k, dict(score=0.0, n=0, first_parent=pi, combo="+".join(combo)))
            d["n"] += 1
            if sc > d["score"]: d["score"] = sc
    row = dict(set=s, molecule=mid, ok=True, n_parents=len(parents), n_products=len(prods), top_parent_sim=(parents[0][1] if parents else 0.0))
    hit = [k for k in prods if k in tkeys]
    row["gen_hit"] = bool(hit)
    if hit:
        order = sorted(prods, key=lambda k: (-prods[k]["score"], -prods[k]["n"], k)); r = min(order.index(k) + 1 for k in hit); h = prods[hit[0]]
        row.update(hit_rank_ap=r, hit_parent=h["first_parent"], hit_combo=h["combo"], hit_n=h["n"])
    return row


if __name__ == "__main__":
    set_num_threads(a.threads)
    S_MZ = np.load(f"{ROOT}/{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{ROOT}/{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{ROOT}/{a.store}/spec_off.npy")
    meta = pl.read_parquet(f"{ROOT}/{a.store}/spec_meta.parquet", columns=["row", "inchikey14", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean", "scorer_ik14"])
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
    prec_of_row = meta["precursor_mz"].to_numpy().astype(np.float64); ce_of_row = meta["ce_mean"].to_numpy().astype(np.float64); key_of_row = meta["scorer_ik14"].to_numpy()
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    def spectrum(x): return np.asarray(S_MZ[S_OFF[x]:S_OFF[x + 1]], np.float64), np.asarray(S_IT[S_OFF[x]:S_OFF[x + 1]], np.float64)
    store = BA.Store(np.arange(meta.height), lib_of_row, add_of_row, mode_of_row, ce_of_row, key_of_row, prec_of_row, spectrum, log=log)
    ts = pd.read_parquet(f"{ROOT}/{a.structs}", columns=["key", "smiles"]).drop_duplicates("key"); KEY_SMI = dict(zip(ts.key.astype(str), ts.smiles.astype(str)))
    _idf = pd.read_parquet(f"{ROOT}/{a.folds}", columns=["scorer_key", "identity_group"]).dropna().drop_duplicates()
    GROUP_KEYS = _idf.groupby("identity_group").scorer_key.apply(lambda x: set(x.astype(str))).to_dict(); KEY_GROUP = dict(zip(_idf.scorer_key.astype(str), _idf.identity_group))
    tasks = []
    for spec in a.sets:
        eval_csv, sets = spec.split(":")
        ev = pd.read_csv(os.path.join(HERE, eval_csv)); ev["molecule"] = ev["molecule"].astype(str)
        for s in sets.split(","):
            mols = ev[ev.set == s]
            if a.limit: mols = mols.head(a.limit)
            for r in mols.itertuples(index=False):
                mid, lib, tk = str(r.molecule), r.lib, str(r.scorer_key)
                qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
                q = select_queries(qrows, a.max_spectra, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
                qspec = []
                for x in q:
                    sh = ELECTRON if (lib_of_row[x] == "enveda-180" and mode_of_row[x] == "positive") else 0.0
                    mz, it = spectrum(x); qspec.append(dict(mz=mz - sh, it=it, prec=float(prec_of_row[x]) - sh, adduct=add_of_row[x], mode=mode_of_row[x]))
                raw = {key_of_row[x] for x in ik_rows.get(mid, []) if key_of_row[x] is not None}
                drop = raw | {tk} | set(GROUP_KEYS.get(KEY_GROUP.get(tk), set()))
                an = store.analogs(qspec, query_rows=q, drop_keys=drop)
                parents = [(KEY_SMI[k], float(v)) for k, v in an if k in KEY_SMI][:a.parents]
                tasks.append((s, mid, raw | {tk, mid}, KEY_SMI.get(tk), parents))
            log(f"{s}: analogs for {len(mols)} molecules")
    rows = []
    with Pool(a.workers) as p:
        for i, r in enumerate(p.imap_unordered(gen_job, tasks, chunksize=1)):
            rows.append(r)
            if i % 100 == 0: log(f"generated {i + 1}/{len(tasks)}")
    R = pd.DataFrame(rows); R.to_csv(os.path.join(HERE, a.out + ".csv"), index=False)
    L = [f"# Analog-derivative generation, class-3 simulation (parents = top {a.parents} C2 train analogs; {time.strftime('%Y-%m-%d %H:%M')})", "",
         "| set | n | truth generated | median products | hit rank 1 | hit rank <=5 | hit rank <=25 | oracle MRR@25 (generated list only) |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for s, g in R[R.ok].groupby("set", sort=False):
        hr = g.hit_rank_ap if "hit_rank_ap" in g else pd.Series(np.nan, index=g.index)
        rr = np.where(hr.notna() & (hr <= 25), 1.0 / hr.fillna(1e9), 0.0)
        L.append(f"| {s} | {len(g)} | {g.gen_hit.mean():.3f} | {g.n_products.median():.0f} | {(hr == 1).mean():.3f} | {(hr <= 5).mean():.3f} | {(hr <= 25).mean():.3f} | {rr.mean():.3f} |")
    open(os.path.join(HERE, a.out + ".md"), "w", encoding="utf-8").write("\n".join(L) + "\n"); print("\n".join(L))
