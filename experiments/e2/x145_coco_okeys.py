"""145 (Codex 145 Q2): query-independent official identities of the COCONUT store structures (data/external/coconut/coco_meta.parquet, the
one-time parquet of the opcode-verified pickle) with b1_features._okey (RDKit 2026.03.3) -> experiments/e2/coco_store_okeys.parquet."""
import os, sys, time
from multiprocessing import Pool
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, os.path.join(ROOT, "experiments/b1_baseline"))
import b1_features as BF


def main():
    t0 = time.time(); smi = pd.read_parquet(os.path.join(ROOT, "data/external/coconut/coco_meta.parquet"), columns=["smiles"]).smiles.astype(str).tolist()
    with Pool(16, initializer=BF._init, initargs=(os.path.join(ROOT, "data/external/v3_models/code"), os.path.join(ROOT, "data/external/fold_safe_fpnet"))) as wp:
        ok = [k for r in wp.map(BF._okey, [smi[i:i + 1000] for i in range(0, len(smi), 1000)]) for k in r]
    pd.DataFrame(dict(store_row=range(len(smi)), official_key=ok)).to_parquet(os.path.join(ROOT, "experiments/e2/coco_store_okeys.parquet"), index=False)
    print(f"COCONUT store {len(smi)} structures, official keys {sum(k is not None for k in ok)}, unique {len(set(k for k in ok if k))} ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
