"""145 (Codex 145 Q4): the library index of the Kaggle branch vs the development index.
Development: key_rows[scorer_ik14] = store rows (spec_meta scorer_ik14). Kaggle (b1_pipeline when the store has no scorer_ik14): raw InChIKey14
of every v2-pool train SMILES (src 1/3) -> its pool key (official); key_rows[key] = all store rows whose shipped inchikey14 maps to that key.
Reports per official key: identical row sets / missing rows / extra rows, rows with no key in either index, raw keys mapped to several
official keys (overwritten in the Kaggle dict), and the share of spectra whose analog-store key differs. No model, no performance number.
Usage (Spark): .venv/bin/python -X utf8 experiments/e2/x145_index_diff.py"""
import json, os, sys
from multiprocessing import Pool
import numpy as np, polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def _raw(smiles):
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*"); out = []
    for s in smiles:
        try:
            m = Chem.MolFromSmiles(s); out.append(Chem.MolToInchiKey(m)[:14] if m is not None else None)
        except Exception:
            out.append(None)
    return out


def main():
    meta = pl.read_parquet(os.path.join(ROOT, "data/processed/spectra_store/spec_meta.parquet"), columns=["row", "inchikey14", "scorer_ik14"])
    dev = {k: set(map(int, r)) for k, r in meta.filter(pl.col("scorer_ik14").is_not_null()).group_by("scorer_ik14").agg(pl.col("row")).iter_rows()}
    ik_rows = {k: set(map(int, r)) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    pool = pl.read_parquet(os.path.join(ROOT, "data/external/v2_pool/pool_meta.parquet"), columns=["key", "smiles", "src"]).filter(pl.col("src").is_in([1, 3]))
    tsmi = pool["smiles"].to_list(); tkey = pool["key"].to_list()
    with Pool(16) as wp: rk = [k for r_ in wp.map(_raw, [tsmi[i:i + 2000] for i in range(0, len(tsmi), 2000)]) for k in r_]
    ik_to_key, multi = {}, {}
    for ik, key in zip(rk, tkey):   # the pipeline's dict comprehension: the LAST pool row of a raw key wins
        if ik:
            if ik in ik_to_key and ik_to_key[ik] != key: multi.setdefault(ik, {ik_to_key[ik]}).add(key)
            ik_to_key[ik] = key
    kag = {}
    for ik, rows in ik_rows.items():
        k = ik_to_key.get(ik)
        if k: kag.setdefault(k, set()).update(rows)
    keys = set(dev) | set(kag); same = miss = extra = only_dev = only_kag = 0; rows_missing = rows_extra = 0
    for k in keys:
        a, b = dev.get(k, set()), kag.get(k, set())
        if a == b: same += 1; continue
        if not b: only_dev += 1
        elif not a: only_kag += 1
        if a - b: miss += 1; rows_missing += len(a - b)
        if b - a: extra += 1; rows_extra += len(b - a)
    key_dev = {r: k for k, rs in dev.items() for r in rs}; key_kag = {r: k for k, rs in kag.items() for r in rs}
    n = meta.height; diff_rows = sum(1 for r in range(n) if key_dev.get(r) != key_kag.get(r))
    rep = dict(store_rows=n, keys_dev=len(dev), keys_kaggle=len(kag), keys_union=len(keys), keys_identical=same, keys_only_dev=only_dev, keys_only_kaggle=only_kag,
               keys_with_missing_rows=miss, rows_missing=rows_missing, keys_with_extra_rows=extra, rows_extra=rows_extra, raw_keys_to_several_official=len(multi),
               rows_key_differs=diff_rows, rows_key_differs_share=round(diff_rows / n, 5), rows_without_key_dev=n - len(key_dev), rows_without_key_kaggle=n - len(key_kag))
    print(json.dumps(rep, indent=1))
    out = os.path.join(ROOT, "experiments/e2/x145_index_diff.json"); json.dump(rep, open(out, "w"), indent=1)
    # the differing keys themselves, for the parity examples
    dk = sorted(k for k in keys if dev.get(k, set()) != kag.get(k, set()))
    json.dump(dict(differing_keys=dk[:5000], n=len(dk)), open(os.path.join(ROOT, "experiments/e2/x145_index_diff_keys.json"), "w"))


if __name__ == "__main__":
    main()
