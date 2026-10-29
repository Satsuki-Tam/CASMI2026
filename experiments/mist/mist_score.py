"""MIST per-candidate scores for the B1 development tables (label-free; stage 2 input, written before any MIST result on CASMI data).
Queries = the b1_features policy (n111_score.py): selection library, test adducts, select_queries round-robin, max 8, electron correction for
enveda-180 positive spectra; then only queries whose adduct is [M+H]+ or [M+Na]+ (MIST's trained adducts) are used.
Candidate formula = experiments/b1_baseline/wf_common.neutral_formula (128 v2: the SAME definition as the evaluator; unparsable, net charge != 0
or isotope -> no_formula) and then MIST's 18-element vocabulary / counts <= 254 (else no_formula). A (query, formula) pair is used only if
|theoretical m/z - measured precursor| <= max(20 ppm x measured, 5 mDa), theoretical m/z = monoisotopic mass of the formula (MIST masses) +
chem_utils.ion_to_mass[adduct], measured = precursor_mz - the enveda-180 positive electron correction (as b1_features).
For each used pair: p = MIST(query features from mist_adapter.featurize, formula, adduct) (EMA weights, weights_only loading, FP32, eval);
candidate bits = RDKit MorganGenerator(radius 2, fpSize 4096) on the representative SMILES (MIST's contract, chirality ignored).
  mist_cos = mean over the candidate's usable queries of cos(p, bits);  mist_ll = mean over them of the per-bit Bernoulli log-likelihood / 4096
  (diagnostic); n_q = number of usable queries; status in {ok, no_qrows (no spectrum of the selection library with a test adduct),
  no_mist_adduct (selected queries, none [M+H]+ / [M+Na]+), no_formula, mass_mismatch, no_fp}.  The table is restricted to the selected molecules
  of the eval CSV (with or without --limit) and checked complete; the manifest binds code / checkpoint / MIST commit / inputs / outputs by sha256.
Predictions are cached per (query row, formula, adduct) and shared by all candidates (and both views) of a molecule.
v3 (Codex 129): the adapter rounds intensities as the official path (float32 then float16); --threads; an empty window is accepted only when
the molecule ledger's n_shortlist is 0. Writes <out>/mist_<tag>_<set>.parquet and <out>/mist_<tag>_manifest.json (checkpoint sha256, counts).
Usage (Spark, .venv-mist): python -X utf8 experiments/mist/mist_score.py --ckpt C --store data/processed/spectra_store --run <table dir>
       --eval_csv CSV --tag T --sets S1 ... --out DIR [--device cpu] [--limit N]"""
import argparse, hashlib, json, os, sys, time
import numpy as np, pandas as pd, polars as pl, torch
HERE = os.path.dirname(os.path.abspath(__file__)); B1 = os.path.abspath(os.path.join(HERE, "..", "b1_baseline")); sys.path.insert(0, HERE); sys.path.insert(0, B1)
import mist_adapter as A
from wf_common import neutral_formula
from b1_common import select_queries, ADDUCT_SHIFT, ELECTRON
from mist.models.scaled_mist import ScaledMIST
from mist.utils import chem_utils as C
from rdkit import Chem, RDLogger
from rdkit.Chem import rdFingerprintGenerator
RDLogger.DisableLog("rdApp.*")
ap = argparse.ArgumentParser()
for k in ("ckpt", "store", "run", "eval_csv", "tag", "out"): ap.add_argument(f"--{k}", required=True)
ap.add_argument("--sets", nargs="+", required=True); ap.add_argument("--device", default="cpu"); ap.add_argument("--limit", type=int, default=0); ap.add_argument("--max_spectra", type=int, default=8)
ap.add_argument("--batch", type=int, default=256); ap.add_argument("--threads", type=int, default=4)
a = ap.parse_args()
MG = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=4096); MIST_ADD = ("[M+H]+", "[M+Na]+")
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
def cand_info(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None: return None, None, "no_fp"
    bits = np.zeros(4096, np.float32); bits[list(MG.GetFingerprint(m).GetOnBits())] = 1.0
    f = neutral_formula(smi)
    if f is None: return None, bits, "no_formula"
    try: v = C.formula_to_dense(f)
    except Exception: return None, bits, "no_formula"
    if (v > 254).any(): return None, bits, "no_formula"
    return f, bits, "ok"
def fmass(f):
    v = C.formula_to_dense(f); return float(v @ C.VALID_MONO_MASSES)
def main():
    t0 = time.time(); os.makedirs(a.out, exist_ok=True); torch.set_num_threads(a.threads)
    ck = torch.load(a.ckpt, map_location="cpu", weights_only=True); model = ScaledMIST(**ck["config"]["model"]); model.load_state_dict(ck["ema_model"], strict=True)
    dev = torch.device(a.device); model = model.to(dev).eval()
    S_MZ = np.load(f"{a.store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{a.store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{a.store}/spec_off.npy")
    meta = pl.read_parquet(f"{a.store}/spec_meta.parquet")
    lib_of_row = meta["ingest_lib"].to_numpy(); add_of_row = meta["adduct"].to_numpy(); mode_of_row = meta["ionization_mode"].to_numpy()
    prec_of_row = meta["precursor_mz"].to_numpy(); ce_of_row = meta["ce_mean"].to_numpy(); ins_of_row = meta["instrument_type"].to_numpy() if "instrument_type" in meta.columns else None
    ik_rows = {k: np.asarray(r, np.int64) for k, r in meta.group_by("inchikey14").agg(pl.col("row")).iter_rows()}
    mols = pd.read_csv(a.eval_csv); mols["molecule"] = mols.molecule.astype(str)
    import subprocess, rdkit
    mist_dir = os.path.dirname(os.path.dirname(os.path.abspath(C.__file__)))
    try: mist_commit = subprocess.run(["git", "-C", mist_dir, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    except Exception: mist_commit = "unknown"
    man = dict(ckpt=a.ckpt, ckpt_sha256=sha(a.ckpt), step=int(ck["step"]), run=a.run, eval_csv=a.eval_csv, eval_csv_sha256=sha(a.eval_csv), sets={}, max_spectra=a.max_spectra,
               device=a.device, adducts=MIST_ADD, mass_rule="|M(F) + ion_to_mass[adduct] - (precursor_mz - enveda-180 positive electron)| <= max(20e-6 * measured, 0.005)",
               code={f: sha(os.path.join(HERE, f)) for f in ("mist_score.py", "mist_adapter.py")} | {"wf_common.py": sha(os.path.join(B1, "wf_common.py"))},
               mist_commit=mist_commit, rdkit=rdkit.__version__, torch=torch.__version__, numpy=np.__version__)
    for s in a.sets:
        T = pd.read_parquet(os.path.join(a.run, f"b1_features_{s}.parquet"), columns=["molecule", "smiles", "official_key"]); T["molecule"] = T.molecule.astype(str)
        ms = mols[mols.set == s]
        if a.limit: ms = ms.head(a.limit)
        T = T[T.molecule.isin(set(ms.molecule))]   # 128 v2 (Codex 128): always restricted to the selected molecules
        LED = pd.read_csv(os.path.join(a.run, f"b1_molecules_{s}.csv")); LED["molecule"] = LED.molecule.astype(str); LED = LED.set_index("molecule")   # Codex 129: an empty window must be in the ledger
        man["sets"][s] = dict(table_sha256=sha(os.path.join(a.run, f"b1_features_{s}.parquet")))
        INFO = {smi: cand_info(smi) for smi in T.smiles.astype(str).unique()}
        rows, cnt, npred = [], dict(no_qrows=0, no_mist_adduct=0, empty_window=0), 0
        for r in ms.itertuples(index=False):
            mid = str(r.molecule); lib = r.lib; shift = ELECTRON if lib == "enveda-180" else 0.0
            qrows = sorted(int(x) for x in ik_rows.get(mid, []) if lib_of_row[x] == lib and add_of_row[x] in ADDUCT_SHIFT)
            q0 = select_queries(qrows, a.max_spectra, lambda x: add_of_row[x], lambda x: float(ce_of_row[x]))
            q = [x for x in q0 if add_of_row[x] in MIST_ADD]; qreason = "no_qrows" if not q0 else ("no_mist_adduct" if not q else "")
            cand = T[T.molecule == mid]
            if not len(cand):
                if mid not in LED.index or float(LED.loc[mid, "n_shortlist"]) != 0: raise RuntimeError(f"{s} {mid}: no candidate rows but the ledger shortlist is not empty")
                cnt["empty_window"] += 1
            forms = sorted({INFO[str(c)][0] for c in cand.smiles if INFO[str(c)][0] is not None})
            pairs, feats = [], []
            for x in q:
                sh = shift if mode_of_row[x] == "positive" else 0.0
                so, eo = int(S_OFF[x]), int(S_OFF[x + 1]); mz = np.asarray(S_MZ[so:eo], np.float64) - sh; it = np.asarray(S_IT[so:eo], np.float64); prec = float(prec_of_row[x]) - sh
                for f in forms:
                    dm = abs(fmass(f) + float(C.ion_to_mass[add_of_row[x]]) - prec)
                    if dm > max(20e-6 * prec, 0.005): continue
                    pairs.append((x, f)); feats.append(A.featurize(mz, it, prec, f, add_of_row[x], str(ins_of_row[x]) if ins_of_row is not None else "unknown"))
            P = {}
            with torch.inference_mode():
                for b in range(0, len(feats), a.batch):
                    out, _ = model({k: v.to(dev) for k, v in A.collate(feats[b:b + a.batch]).items()})
                    for j, p in enumerate(out.float().cpu().numpy()): P[pairs[b + j]] = p
            npred += len(feats)
            if qreason: cnt[qreason] += 1
            for c in cand.itertuples(index=False):
                f, bits, st = INFO[str(c.smiles)]
                cs, ll = [], []
                if st == "ok":
                    for x in q:
                        p = P.get((x, f))
                        if p is None: continue
                        cs.append(float(p @ bits / (np.linalg.norm(p) * np.linalg.norm(bits) + 1e-12)))
                        pc = np.clip(p, 1e-6, 1 - 1e-6); ll.append(float((bits * np.log(pc) + (1 - bits) * np.log(1 - pc)).mean()))
                    if qreason: st = qreason
                    elif not cs: st = "mass_mismatch"
                rows.append(dict(set=s, molecule=mid, smiles=c.smiles, official_key=c.official_key, mist_cos=float(np.mean(cs)) if cs else np.nan,
                                 mist_ll=float(np.mean(ll)) if ll else np.nan, n_q=len(cs), status=st))
        O = pd.DataFrame(rows, columns=["set", "molecule", "smiles", "official_key", "mist_cos", "mist_ll", "n_q", "status"])
        if len(O) != len(T) or O.duplicated(["molecule", "official_key"]).any(): raise RuntimeError(f"{s}: scored rows {len(O)} != table rows {len(T)} or duplicates")
        if len(T) and set(T.molecule) - set(O.molecule): raise RuntimeError(f"{s}: molecules of the table without scored rows")
        O.to_parquet(os.path.join(a.out, f"mist_{a.tag}_{s}.parquet"), index=False)
        outp = os.path.join(a.out, f"mist_{a.tag}_{s}.parquet")
        man["sets"][s].update(rows=len(O), molecules=int(ms.molecule.nunique()), molecules_without_query=dict(cnt), predictions=npred, status=O.status.value_counts().to_dict(), output_sha256=sha(outp))
        print(f"{s}: {len(O)} rows, {ms.molecule.nunique()} molecules, predictions {npred}, status {O.status.value_counts().to_dict()} ({time.time() - t0:.0f}s)", flush=True)
    json.dump(man, open(os.path.join(a.out, f"mist_{a.tag}_manifest.json"), "w"), indent=2); print("DONE", json.dumps(man)[:600])
if __name__ == "__main__":
    main()
