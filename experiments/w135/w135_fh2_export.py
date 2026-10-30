"""Export the v2.1 U2 tables (w135_fh2.py) into a casmi-harness v2 workspace (156 / 158 decisions; same rules as w135_fh_export.py).
- Opaque ids with a NEW salt kept outside the workspace (--map_dir): uid = 'q' + sha256(salt | world | molecule)[:16], iid likewise per molecule.
- Allowlisted columns only. U2: uid, key, smiles, rep, membership flags, P / common / product / E2 / F features (+ y for development rows).
  Q2: uid (+ iid for development) and the query features. The F-world reference lists (f_top25, a deterministic function of P and E2, the
  fixed control) are written to a SEPARATE reference file fref_dev.parquet (uid, f_applied, f_top25) for the auxiliary reader; they are not
  model inputs. Development management metadata (batch, pi, class, family, truth) -> units_dev.parquet (never a model input).
- Test = the fold-0 e-worlds at pi3 0.3 only, features only (no y / truth / class / family / world / molecule / iid; no F reference).
Usage: python -X utf8 experiments/w135/w135_fh2_export.py --part dev|hold_ids|hold --src DIR --ws WORKSPACE --map_dir DIR"""
import argparse, glob, hashlib, json, os, secrets, sys
import pandas as pd

PROD = ["apsc", "log_npar", "src_peer", "src_train", "n_steps", "off_mass", "e_sugar", "e_methyl", "e_redox", "e_acyl", "e_other"]
U_COLS = ["uid", "key", "smiles", "rep", "rP", "sP", "sP_miss", "fz", "gl", "gl_miss", "frag", "in_wwin", "in_P", "in_E25", "in_Ewin", "in_B", "gen_only", "in_B_added"] + PROD + \
         ["e2_score", "e2_rank", "e_miss", "in_coconut", "in_pcl", "in_bio", "in_train_w", "lib_sim_w", "ana_ap_w", "f_score", "in_F_pool", "f_applied", "f_rank"]
Q_COLS = ["uid", "gl_ok", "lib_max", "n_cand", "n_b", "n_p", "p_gap12", "log_ncand", "best_analog", "n_peer_struct", "n_train", "n_e", "e_empty", "n_e25", "n_u2", "f_applied"]
DEV_WORLDS = [f"{b}_p{p}" for b in ("dF1", "dF2", "dF3", "dR1", "dR2", "dR3") for p in (0, 30, 60)] + \
             [f"{b}_p{p}" for b in ("cF1", "cF2", "cF3", "cR1", "cR2", "cR3") for p in (0, 30)] + ["cU1_p30"]
HOLD_WORLDS = [f"{b}_p30" for b in ("eF1", "eF2", "eF3", "eR1", "eR2", "eR3")]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
def stop(m): sys.exit(f"STOP (w135_fh2_export): {m}")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--part", required=True, choices=["dev", "hold_ids", "hold"]); ap.add_argument("--src", default="")
    ap.add_argument("--ws", required=True); ap.add_argument("--map_dir", required=True); ap.add_argument("--batches_dir", default="experiments/w135/batches"); a = ap.parse_args()
    ws_r = os.path.normcase(os.path.realpath(a.ws)); mp_r = os.path.normcase(os.path.realpath(a.map_dir))
    if os.path.commonpath([ws_r, mp_r]) == ws_r: stop("the mapping must stay outside the workspace")
    os.makedirs(a.map_dir, exist_ok=True); sp = os.path.join(a.map_dir, "salt.txt")
    if not os.path.exists(sp): open(sp, "w").write(secrets.token_hex(32))
    s = open(sp).read().strip()
    uid_of = lambda w, m: "q" + hashlib.sha256(f"{s}|{w}|{m}".encode()).hexdigest()[:16]
    iid_of = lambda m: "i" + hashlib.sha256(f"{s}|{m}".encode()).hexdigest()[:16]
    if a.part == "hold_ids":
        rows = []
        for w in HOLD_WORLDS:
            d = pd.read_csv(os.path.join(a.batches_dir, f"{w.split('_p')[0]}.csv"), dtype={"molecule": str})
            rows += [dict(uid=uid_of(w, m), world=w, molecule=m) for m in d.molecule.astype(str)]
        M = pd.DataFrame(rows)
        if M.uid.duplicated().any(): stop("uid collision")
        M.to_parquet(os.path.join(a.map_dir, "map_hold_ids.parquet"), index=False); M[["uid"]].to_csv(os.path.join(a.ws, "data/raw/hold_ids.csv"), index=False)
        print(f"hold ids: {len(M)}"); return
    worlds = DEV_WORLDS if a.part == "dev" else HOLD_WORLDS
    sub = "w135_u2_dev_v1" if a.part == "dev" else "w135_u2_hold_e_v1"; out = os.path.join(a.ws, "data/raw", sub)
    if os.path.exists(out): stop(f"{out} exists (no overwrite)")
    os.makedirs(out); maps = []; units = []; frefs = []; man = dict(part=a.part, worlds={}, script_sha256=sha(os.path.abspath(__file__)))
    for i, w in enumerate(worlds):
        mt = json.load(open(os.path.join(a.src, f"U2_{w}.meta.json")))
        pu, pq = os.path.join(a.src, f"U2_{w}.parquet"), os.path.join(a.src, f"Q2_{w}.parquet")
        if sha(pu) != mt["U2_sha256"] or sha(pq) != mt["Q2_sha256"]: stop(f"{w}: U2 / Q2 differ from their meta")
        U = pd.read_parquet(pu); Q = pd.read_parquet(pq); U["molecule"] = U.molecule.astype(str); Q["molecule"] = Q.molecule.astype(str)
        U["uid"] = [uid_of(w, m) for m in U.molecule]; Q["uid"] = [uid_of(w, m) for m in Q.molecule]
        uc = U_COLS + (["y"] if a.part == "dev" else []); qc = Q_COLS + (["iid"] if a.part == "dev" else [])
        if a.part == "dev": Q["iid"] = [iid_of(m) for m in Q.molecule]
        miss = (set(uc) - set(U.columns)) | (set(qc) - set(Q.columns))
        if miss: stop(f"{w}: missing columns {sorted(miss)}")
        tag = w if a.part == "dev" else f"{i:02d}"
        U[uc].to_parquet(os.path.join(out, f"U_{tag}.parquet"), index=False); Q[qc].to_parquet(os.path.join(out, f"Q_{tag}.parquet"), index=False)
        maps.append(Q[["uid", "world", "molecule", "truth", "wclass", "fam", "batch", "pi"]].assign(iid=[iid_of(m) for m in Q.molecule]))
        if a.part == "dev":
            units.append(Q[["uid", "iid", "batch", "pi", "wclass", "fam", "truth"]]); frefs.append(Q[["uid", "f_applied", "f_top25"]])
        man["worlds"][w] = dict(source_U2=mt["U2_sha256"], source_Q2=mt["Q2_sha256"])
    pd.concat(maps, ignore_index=True).to_parquet(os.path.join(a.map_dir, f"map_{a.part}.parquet"), index=False)
    if a.part == "dev":
        pd.concat(units, ignore_index=True).to_parquet(os.path.join(out, "units_dev.parquet"), index=False)
        pd.concat(frefs, ignore_index=True).to_parquet(os.path.join(out, "fref_dev.parquet"), index=False)
    man["files"] = {os.path.basename(p): sha(p) for p in sorted(glob.glob(os.path.join(out, "*.parquet")))}
    json.dump(man, open(os.path.join(a.map_dir, f"export_{a.part}_manifest.json"), "w"), indent=1)
    print(f"{a.part}: {len(worlds)} worlds -> {out}")


if __name__ == "__main__":
    main()
