"""158 v2 table builder (158_prereg_v2_diag.md section 1; data preparation, no metric is printed).
U2(q) = P's top 25  U  E2's top 25 (by the full-window E2 rank)  U  the generated products B (at most 50), one row per official key
(at most 100 slots). Slot order: P by rank, then the E-only candidates by E2 rank, then the B-only products by key.
Membership flags: in_P, in_E25, in_Ewin (in the masked world E window), in_B (generated), gen_only (in_B and not in_P and not in_Ewin).
Representative SMILES (registered rule): P's if in P, else E's if in the E window, else B's. Common features (fz, gl, frag) are the
representative's: P rows as w135_fh.py; E-represented rows take the E window's f.z and MetFrag-lite, GL = not computed (gl_miss = 1, never 0);
B-only rows as w135_fh.py. Product features (apsc, n_steps, edit groups, ...) come from the generation whenever in_B.
E2 features: e2_score, e2_rank (full window), n_e, E source flags (in_coconut / in_pcl / in_bio / in_train_w), world library similarity and
analog ap (0 with e_miss = 1 when not in the E window).
F features: in_F_pool = in_P or in_E25; f_score = 1[in_P]/(10 + rP) + 0.5 x 1[in_Ewin]/(10 + rE); f_rank = position in the F-world list.
F-world reference: e2_engine.fuse_rrf(P top 25, full-window E2 ranks, E2 top 25, 0.5) -- the submitted rule; the builder checks that ordering
the F-pool rows by (-f_score, rP, rE, key) reproduces it exactly (STOP otherwise). E empty -> F = P (as the pipeline).
Labels: y = 1[key == truth] on every development row (the world's batch scorer key). No metric is computed or printed.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_fh2.py --worlds dF1_p30 [...]"""
import argparse, hashlib, json, os, sys, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE); sys.path.insert(1, os.path.join(ROOT, "experiments/e2")); sys.path.insert(2, os.path.join(ROOT, "experiments/b1_baseline"))
import w135_fh as FH
import e2_engine as E2M

OUTD = os.path.join(ROOT, "experiments/w135/fh2")
EDITS = ["e_sugar", "e_methyl", "e_redox", "e_acyl", "e_other"]
PROD = ["apsc", "log_npar", "src_peer", "src_train", "n_steps", "off_mass"] + EDITS
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
def stop(m): sys.exit(f"STOP (w135_fh2): {m}")


def build2(w):
    R, Q = FH.build(w); b = w.split("_p")[0]
    V2 = os.path.join(ROOT, "experiments/w135/v2", w)
    man = json.load(open(os.path.join(V2, "e2s_manifest.json")))
    if sha(os.path.join(V2, f"e2s_{b}.parquet")) != man["sets"][b]["sha"]: stop(f"{w}: e2s table differs from its manifest")
    E = pd.read_parquet(os.path.join(V2, f"e2s_{b}.parquet")); E["molecule"] = E.molecule.astype(str)
    Wk = pd.read_parquet(os.path.join(ROOT, "experiments/w135/worlds", w, "gen", f"gen_{b}_window_okeys.parquet"), columns=["molecule", "official_key"])
    Wk["molecule"] = Wk.molecule.astype(str); wkeys = Wk.groupby("molecule").official_key.apply(set).to_dict()
    truth = Q.set_index("molecule").truth.to_dict(); rows = []; qx = []
    for m in Q.molecule:
        r = R[R.molecule == m]; e = E[E.molecule == m].sort_values("e2_rank")
        P = r[r.src == "P"].sort_values("rP"); Bp = r[r.src == "B"]
        if e.official_key.duplicated().any(): stop(f"{w} {m}: duplicated E key")
        e_rank = dict(zip(e.official_key, e.e2_rank.astype(int))); ei = e.set_index("official_key")
        p25 = P.key.astype(str).tolist(); e25 = e.official_key.astype(str).tolist()[:25]
        F_list = E2M.fuse_rrf(p25, e_rank, e25, 0.5)
        Pk = set(p25); E25k = set(e25); Bk = set(Bp.key.astype(str))
        keys = p25 + [k for k in e25 if k not in Pk] + sorted(k for k in Bk if k not in Pk and k not in E25k)
        if len(keys) != len(set(keys)) or len(keys) > 100: stop(f"{w} {m}: slot invariant")
        Pi = P.set_index("key"); Bi = Bp.set_index("key")
        for k in keys:
            inP, inE, inB = k in Pk, k in e_rank, k in Bk
            if inP:
                base = Pi.loc[k].to_dict(); rep = "P"
            elif inE:
                er = ei.loc[k]; rep = "E"
                base = dict(smiles=str(er.smiles), rP=26, sP=0.0, sP_miss=1, fz=float(er.fp), gl=0.0, gl_miss=1, frag=float(er.frag), in_wwin=int(k in wkeys.get(m, set())))
            else:
                base = Bi.loc[k].to_dict(); rep = "B"
            row = dict(world=w, molecule=m, key=k, smiles=base["smiles"], rep=rep, rP=int(base["rP"]) if inP else 26, sP=float(base["sP"]) if inP else 0.0, sP_miss=0 if inP else 1,
                       fz=float(base["fz"]), gl=float(base["gl"]), gl_miss=int(base["gl_miss"]), frag=float(base["frag"]),
                       in_wwin=int(base.get("in_wwin", 1 if inP else 0)), in_P=int(inP), in_E25=int(k in E25k), in_Ewin=int(inE), in_B=int(inB),
                       gen_only=int(inB and not inP and not inE))
            if inB:
                bb = Bi.loc[k]; row.update({c: float(bb[c]) for c in PROD})
            else:
                row.update({c: 0.0 for c in PROD})
            if inE:
                er = ei.loc[k]
                row.update(e2_score=float(er.e2_score), e2_rank=int(er.e2_rank), e_miss=0, in_coconut=int(er.in_coconut), in_pcl=int(er.in_pcl), in_bio=int(er.in_bio),
                           in_train_w=int(er.in_train), lib_sim_w=float(er.lib_sim), ana_ap_w=float(er.ana_ap))
            else:
                row.update(e2_score=0.0, e2_rank=0, e_miss=1, in_coconut=0, in_pcl=0, in_bio=0, in_train_w=0, lib_sim_w=0.0, ana_ap_w=0.0)
            rP_, rE_ = (row["rP"] if inP else None), (row["e2_rank"] if inE else None)
            row["f_score"] = (1.0 / (E2M.FUSE_K + rP_) if inP else 0.0) + (0.5 / (E2M.FUSE_K + rE_) if inE else 0.0)
            row["in_F_pool"] = int(inP or k in E25k); row["f_rank"] = (F_list.index(k) + 1) if k in F_list else 26
            row["y"] = int(k == truth[m])
            rows.append(row)
        pool = [x for x in rows if x["molecule"] == m and x["in_F_pool"]]
        mine = [x["key"] for x in sorted(pool, key=lambda x: (-x["f_score"], x["rP"] if x["in_P"] else 99, x["e2_rank"] if x["in_Ewin"] else 1e9, x["key"]))][:25]
        if mine != F_list: stop(f"{w} {m}: F-world reference does not reproduce fuse_rrf")
        qx.append(dict(molecule=m, n_e=int(len(e)), e_empty=int(len(e) == 0), n_e25=len(e25), n_u2=len(keys), f_top25=json.dumps(F_list)))
    U2 = pd.DataFrame(rows); Q2 = Q.merge(pd.DataFrame(qx), on="molecule", how="left", validate="one_to_one")
    if U2.groupby("molecule").y.sum().max() > 1: stop(f"{w}: more than one positive row in a query")
    num = ["rP", "sP", "fz", "gl", "frag", "e2_score", "f_score", "lib_sim_w", "ana_ap_w"] + PROD
    if not np.isfinite(U2[num].values.astype(float)).all(): stop(f"{w}: non-finite feature")
    return U2, Q2


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--worlds", nargs="+", required=True); a = ap.parse_args(); t0 = time.time(); os.makedirs(OUTD, exist_ok=True)
    for w in a.worlds:
        out = os.path.join(OUTD, f"U2_{w}.parquet")
        if os.path.exists(out): stop(f"{out} exists (no overwrite)")
        U2, Q2 = build2(w)
        U2.to_parquet(out, index=False); Q2.to_parquet(os.path.join(OUTD, f"Q2_{w}.parquet"), index=False)
        meta = dict(world=w, script_sha256=sha(os.path.abspath(__file__)), fh_sha256=sha(os.path.join(HERE, "w135_fh.py")), e2_engine_sha256=sha(os.path.join(ROOT, "experiments/e2/e2_engine.py")),
                    U2_sha256=sha(out), Q2_sha256=sha(os.path.join(OUTD, f"Q2_{w}.parquet")), n_rows=int(len(U2)), n_queries=int(len(Q2)),
                    n_P=int(U2.in_P.sum()), n_E_only=int(((U2.rep == "E")).sum()), n_B_only=int((U2.rep == "B").sum()), n_EB=int(((U2.in_B == 1) & (U2.in_Ewin == 1)).sum()))
        json.dump(meta, open(os.path.join(OUTD, f"U2_{w}.meta.json"), "w"), indent=1)
        print(f"[{time.time()-t0:5.0f}s] {w}: {len(Q2)} queries, {len(U2)} rows (P {meta['n_P']}, E-only {meta['n_E_only']}, B-only {meta['n_B_only']}, E&B {meta['n_EB']}); F-world reproduced -- no metric", flush=True)
