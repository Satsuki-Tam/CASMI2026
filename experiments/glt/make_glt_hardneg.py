"""141 A3 hard negatives (141_decision.md; fixed before training): (1) --mode input: a GLACIER runner input with ONE entry per TRAIN spectrum of
data/glt/tims_s1 (mid = the labels.tsv spec name; spectra = that spectrum rebuilt from the spectra store row with the runner format of
b1_world (enveda-180 positive electron shift; CE / adduct / instrument of the row); cands = the same-formula candidates of its identity
(make_glt_decoys.py, <= 200, heavy-atom filter of b1_features)); (2) --mode select: after the released (C0') GL run on that input, the top-K
candidates per spectrum by the C0' GL score (ties: candidate key), only scored candidates, K = 7 -> fixed_k7.json {spec: [SMILES, ...]} +
select_manifest.json (counts: spectra with K, with fewer, with none; hashes). --mode tech: the technical-check decoys = the first K by the
Tanimoto pre-selection rank (no GL), for finetune_glt_v3 --precheck only.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/glt/make_glt_hardneg.py --mode input|select|tech"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd, polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, os.path.join(ROOT, "experiments/b1_baseline"))
from b1_common import ELECTRON
from b1_features import heavy_ok
ap = argparse.ArgumentParser(); ap.add_argument("--mode", required=True, choices=["input", "select", "tech"]); ap.add_argument("--k", type=int, default=7); a = ap.parse_args()
DD = os.path.join(ROOT, "data/glt/decoys"); D = os.path.join(ROOT, "data/glt/tims_s1"); sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
lab = pd.read_csv(os.path.join(D, "labels.tsv"), sep="\t"); spl = pd.read_csv(os.path.join(D, "splits/split.tsv"), sep="\t"); lab = lab.merge(spl, left_on="spec", right_on="name"); tr = lab[lab.split == "train"]
C = pd.read_parquet(os.path.join(DD, "cands.parquet")); C["identity"] = C.identity.astype(str)
byid = {k: g.sort_values("rank") for k, g in C.groupby("identity")}
if a.mode == "tech":
    out = {r.spec: [s for s in byid[str(r.inchikey)].smiles.tolist() if heavy_ok(s)][:a.k] for r in tr.itertuples(index=False) if str(r.inchikey) in byid}
    json.dump(out, open(os.path.join(DD, "tech_k7.json"), "w")); print(f"tech decoys: {len(out)} spectra"); sys.exit(0)
if a.mode == "input":
    st = os.path.join(ROOT, "data/processed/spectra_store")
    S_MZ = np.load(f"{st}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{st}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{st}/spec_off.npy")
    meta = pl.read_parquet(f"{st}/spec_meta.parquet", columns=["row", "ingest_lib", "adduct", "ionization_mode", "precursor_mz", "ce_mean", "instrument_type"])
    lib = meta["ingest_lib"].to_numpy(); add = meta["adduct"].to_numpy(); mode = meta["ionization_mode"].to_numpy(); prec = meta["precursor_mz"].to_numpy(); ce = meta["ce_mean"].to_numpy(); inst = meta["instrument_type"].to_numpy()
    out, n = [], 0
    for r in tr.itertuples(index=False):
        if str(r.inchikey) not in byid: continue
        x = int(r.store_row); sh = ELECTRON if (lib[x] == "enveda-180" and mode[x] == "positive") else 0.0; s, e = int(S_OFF[x]), int(S_OFF[x + 1])
        c_ = float(ce[x]) if np.isfinite(ce[x]) else None
        spec = dict(mz=(np.asarray(S_MZ[s:e], np.float64) - sh).tolist(), it=np.asarray(S_IT[s:e], np.float64).tolist(), prec=float(prec[x]) - sh, adduct=add[x], mode=mode[x], instrument=inst[x] or "",
                    ce_ev=[c_] if c_ is not None else None, ce_orig=None, ce_units="eV" if c_ is not None else None)
        cands = [s_ for s_ in byid[str(r.inchikey)].smiles.tolist() if heavy_ok(s_)]; n += len(cands)
        out.append(dict(mid=str(r.spec), spectra=[spec], cands=cands))
    json.dump(out, open(os.path.join(DD, "hardneg_runner_in.json"), "w")); print(f"runner input: {len(out)} train spectra, {n} candidate jobs"); sys.exit(0)
gl = json.load(open(os.path.join(DD, "hardneg_gl_c0prime.json"))); gm = json.load(open(os.path.join(DD, "hardneg_gl_c0prime.json.meta.json")))
if gm.get("status") not in ("ok", "partial"): sys.exit(f"STOP: C0' GL status {gm.get('status')}")
KEY = dict(zip(C.smiles, C.cand_key)); out, cnt = {}, dict(k=0, fewer=0, none=0)
for r in tr.itertuples(index=False):
    sc = [(float(v), KEY.get(s_, s_), s_) for s_, v in (gl.get(str(r.spec)) or {}).items() if v is not None]
    top = [s_ for _, _, s_ in sorted(sc, key=lambda t: (-t[0], t[1]))[:a.k]]
    if top: out[str(r.spec)] = top
    cnt["k" if len(top) == a.k else ("fewer" if top else "none")] += 1
json.dump(out, open(os.path.join(DD, "fixed_k7.json"), "w"))
man = dict(rule="per train spectrum: top-7 same-formula candidates by the released (C0') GL score (ties: candidate key), scored candidates only", counts=cnt,
           fixed_sha256=sha(os.path.join(DD, "fixed_k7.json")), gl_sha256=sha(os.path.join(DD, "hardneg_gl_c0prime.json")), cands_sha256=sha(os.path.join(DD, "cands.parquet")), script_sha256=sha(os.path.abspath(__file__)))
json.dump(man, open(os.path.join(DD, "select_manifest.json"), "w"), indent=1); print(json.dumps(man, indent=1))
