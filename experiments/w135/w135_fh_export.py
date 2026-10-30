"""Export the W135 FH tables into the casmi-harness workspace (Codex 154 Q3; 154_decision.md item 2).
- Query ids become opaque: uid = 'q' + sha256(salt | world | molecule)[:16]; identity ids iid = 'i' + sha256(salt | molecule)[:16]
  (dev only, for the per-identity training weights). The salt and the uid -> (world, molecule, truth, class, family) mapping stay OUTSIDE the
  workspace (--map_dir, CASMI repo side). The W135 molecule id is the query's InChIKey14 (= the truth's key family), so it never enters the workspace.
- Only ALLOWLISTED columns are written. U (candidates): uid, key, smiles, src, is_gen, in_wwin, rP, sP, sP_miss, fz, gl, gl_miss, frag, apsc,
  log_npar, src_peer, src_train, n_steps, off_mass, e_* (+ y for development rows). Q (query features): uid (+ iid for development), gl_ok,
  lib_max, n_cand, n_b, n_p, p_gap12, log_ncand, best_analog, n_peer_struct, n_train. Development management metadata for src/cv.py
  (units_dev.parquet: uid, iid, batch, pi, wclass, fam, truth) is written separately and is never a model input.
- Test (hold) = the fold-0 e-worlds at pi3 0.3 ONLY: a molecule's pi0 and pi0.3 candidate lists could be linked and differenced (a C3 truth
  disappears from the window), so only one world per test molecule is exported.
Usage: python -X utf8 experiments/w135/w135_fh_export.py --part dev --src DIR --ws WORKSPACE --map_dir DIR
       python -X utf8 experiments/w135/w135_fh_export.py --part hold_ids --batches_dir experiments/w135/batches --ws WORKSPACE --map_dir DIR
       python -X utf8 experiments/w135/w135_fh_export.py --part hold --src DIR --ws WORKSPACE --map_dir DIR"""
import argparse, glob, hashlib, json, os, secrets, sys
import pandas as pd

U_COLS = ["uid", "key", "smiles", "src", "is_gen", "in_wwin", "rP", "sP", "sP_miss", "fz", "gl", "gl_miss", "frag", "apsc", "log_npar", "src_peer",
          "src_train", "n_steps", "off_mass", "e_sugar", "e_methyl", "e_redox", "e_acyl", "e_other"]
Q_COLS = ["uid", "gl_ok", "lib_max", "n_cand", "n_b", "n_p", "p_gap12", "log_ncand", "best_analog", "n_peer_struct", "n_train"]
DEV_WORLDS = [f"{b}_p{p}" for b in ("dF1", "dF2", "dF3", "dR1", "dR2", "dR3") for p in (0, 30, 60)] + \
             [f"{b}_p{p}" for b in ("cF1", "cF2", "cF3", "cR1", "cR2", "cR3") for p in (0, 30)] + ["cU1_p30"]
HOLD_WORLDS = [f"{b}_p30" for b in ("eF1", "eF2", "eF3", "eR1", "eR2", "eR3")]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
def stop(m): sys.exit(f"STOP (w135_fh_export): {m}")


def salt(map_dir):
    p = os.path.join(map_dir, "salt.txt")
    if not os.path.exists(p):
        os.makedirs(map_dir, exist_ok=True); open(p, "w").write(secrets.token_hex(32))
    return open(p).read().strip()


def uid_of(s, w, m): return "q" + hashlib.sha256(f"{s}|{w}|{m}".encode()).hexdigest()[:16]
def iid_of(s, m): return "i" + hashlib.sha256(f"{s}|{m}".encode()).hexdigest()[:16]


def load(src, w):
    mt = json.load(open(os.path.join(src, f"U_{w}.meta.json")))
    if sha(os.path.join(src, f"U_{w}.parquet")) != mt["U_sha256"] or sha(os.path.join(src, f"Q_{w}.parquet")) != mt["Q_sha256"]: stop(f"{w}: source tables differ from their meta")
    U = pd.read_parquet(os.path.join(src, f"U_{w}.parquet")); Q = pd.read_parquet(os.path.join(src, f"Q_{w}.parquet"))
    U["molecule"] = U.molecule.astype(str); Q["molecule"] = Q.molecule.astype(str)
    return U, Q, mt


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--part", required=True, choices=["dev", "hold_ids", "hold"]); ap.add_argument("--src", default="")
    ap.add_argument("--ws", required=True); ap.add_argument("--map_dir", required=True); ap.add_argument("--batches_dir", default="experiments/w135/batches")
    a = ap.parse_args(); s = salt(a.map_dir)
    if os.path.abspath(a.map_dir).startswith(os.path.abspath(a.ws)): stop("the mapping must stay outside the workspace")
    if a.part == "hold_ids":
        rows = []
        for w in HOLD_WORLDS:
            b = w.split("_p")[0]; d = pd.read_csv(os.path.join(a.batches_dir, f"{b}.csv"), dtype={"molecule": str})
            rows += [dict(uid=uid_of(s, w, m), world=w, molecule=m) for m in d.molecule.astype(str)]
        M = pd.DataFrame(rows)
        if M.uid.duplicated().any(): stop("uid collision")
        M.to_parquet(os.path.join(a.map_dir, "map_hold_ids.parquet"), index=False)
        out = os.path.join(a.ws, "data/raw/hold_ids.csv"); M[["uid"]].to_csv(out, index=False)
        print(f"hold ids: {len(M)} opaque test uids -> {out}; mapping kept in {a.map_dir}"); return
    worlds = DEV_WORLDS if a.part == "dev" else HOLD_WORLDS
    sub = "w135_u_dev_v2" if a.part == "dev" else "w135_u_hold_e_v2"
    out = os.path.join(a.ws, "data/raw", sub)
    if os.path.exists(out): stop(f"{out} exists (no overwrite)")
    os.makedirs(out); maps = []; units = []; man = dict(part=a.part, worlds={}, script_sha256=sha(os.path.abspath(__file__)))
    for w in worlds:
        U, Q, mt = load(a.src, w)
        U["uid"] = [uid_of(s, w, m) for m in U.molecule]; Q["uid"] = [uid_of(s, w, m) for m in Q.molecule]
        ucols = U_COLS + (["y"] if a.part == "dev" else []); qcols = Q_COLS + (["iid"] if a.part == "dev" else [])
        if a.part == "dev": Q["iid"] = [iid_of(s, m) for m in Q.molecule]
        missing = (set(ucols) - set(U.columns)) | (set(qcols) - {"iid"} - set(Q.columns))
        if missing: stop(f"{w}: missing columns {sorted(missing)}")
        U[ucols].to_parquet(os.path.join(out, f"U_{w}.parquet"), index=False) if a.part == "dev" else U[ucols].to_parquet(os.path.join(out, f"U_{len(maps):02d}.parquet"), index=False)
        qp = os.path.join(out, f"Q_{w}.parquet" if a.part == "dev" else f"Q_{len(maps):02d}.parquet"); Q[qcols].to_parquet(qp, index=False)
        maps.append(Q[["uid", "world", "molecule", "truth", "wclass", "fam", "batch", "pi"]].assign(iid=[iid_of(s, m) for m in Q.molecule]))
        if a.part == "dev": units.append(Q[["uid", "iid", "batch", "pi", "wclass", "fam", "truth"]])
        man["worlds"][w] = dict(source_U=mt["U_sha256"], source_Q=mt["Q_sha256"])
    pd.concat(maps, ignore_index=True).to_parquet(os.path.join(a.map_dir, f"map_{a.part}.parquet"), index=False)
    if a.part == "dev": pd.concat(units, ignore_index=True).to_parquet(os.path.join(out, "units_dev.parquet"), index=False)
    man["files"] = {os.path.basename(p): sha(p) for p in sorted(glob.glob(os.path.join(out, "*.parquet")))}
    json.dump(man, open(os.path.join(a.map_dir, f"export_{a.part}_manifest.json"), "w"), indent=1)
    print(f"{a.part}: {len(worlds)} worlds -> {out} ({len(man['files'])} files); mapping + manifest in {a.map_dir}")


if __name__ == "__main__":
    main()
