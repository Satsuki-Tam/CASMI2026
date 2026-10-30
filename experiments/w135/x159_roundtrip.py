"""159 decision D (round trip, step 2 locally): the v2 workspace's P and F references (src/aux_reader.py p_reference / f_reference over
data/folds/validation.npz with 100 slots) must reproduce EXACTLY the expected lists built on Spark from the frozen v1 P and the v2.1 E2 scores
(x159_expected_pf.json), after mapping the opaque uids back with the v2 export map (outside the workspace). Prints only match counts.
Usage: python -X utf8 experiments/w135/x159_roundtrip.py --ws C:/kaggle/competitions/casmi-harness-v2 --map experiments/w135/fh2_export_map/map_dev.parquet --expected experiments/w135/x159_expected_pf.json"""
import argparse, importlib.util, json, os, sys
import numpy as np, pandas as pd


def decode(scores, keys, valid):
    v = np.flatnonzero(valid & (scores > -1e8))
    order = v[np.lexsort((v, -scores[v]))]
    return [str(k) for k in keys[order][:25]]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ws", required=True); ap.add_argument("--map", required=True); ap.add_argument("--expected", required=True); a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("aux_rt", os.path.join(a.ws, "src", "aux_reader.py")); R = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.join(a.ws, "src")); spec.loader.exec_module(R)
    with np.load(os.path.join(a.ws, "data/folds/validation.npz"), allow_pickle=False) as Z: V = {k: Z[k] for k in Z.files}
    Pm, Fm = R.p_reference(V), R.f_reference(V)
    M = pd.read_parquet(a.map).set_index("uid"); X = json.load(open(a.expected))
    keys, valid = V["meta__cand_keys"], V["meta__cand_valid"]; okP = okF = 0; bad = []
    for i, u in enumerate(V["ids"]):
        w, m = M.loc[u, "world"], str(M.loc[u, "molecule"]); exp = X[w][m]
        p, f = decode(Pm[i], keys[i], valid[i]), decode(Fm[i], keys[i], valid[i])
        okP += p == exp["P"][:25]; okF += f == exp["F"][:25]
        if p != exp["P"][:25] or f != exp["F"][:25]: bad.append((w, m))
    n = len(V["ids"])
    print(f"ROUNDTRIP {'PASS' if not bad else 'FAIL'}: P {okP} / {n}, F {okF} / {n} queries reproduce the independent lists exactly")
    if bad: print("  first mismatches:", bad[:5])
    sys.exit(0 if not bad else 1)


if __name__ == "__main__":
    main()
