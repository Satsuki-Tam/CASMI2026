"""159 decision A: audit of the v2.1 world E2 assets (no performance number). For each of the 37 expected worlds:
  receipt  : world, version 2.1, the exact set of outputs and their hashes, inputs (world_masks / gen dump / batch CSV) equal to the files,
             code hashes equal to the committed v2.1 versions, the frozen E2 model's full SHA-256 and 800 trees, both check lines PASS;
  manifests: ewin (masks, eval_csv, gen_dump, fold-safe FPNet, version 2.1), e2f (masks, eval_csv, input ewin, output, analogs), e2s (input ewin /
             e2f, output, model) all agree with each other and with the receipt;
  analogs  : every scored query's analog list equals the W135 world P's list: keys exactly, values within rtol 0 / atol 1e-12 (max diff kept);
  zlog     : every query's |zlog - B1 gen dump| <= 1e-5 (from the E ledger).
Writes experiments/w135/v2_1/audit.json; exit 1 when any world fails.
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_v21_audit.py --expect experiments/w135/v21_expected.json"""
import argparse, hashlib, json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
R = os.path.join(ROOT, "experiments/w135/v2_1")
WORLDS = [f"{b}_p{p}" for b in ("dF1", "dF2", "dF3", "dR1", "dR2", "dR3") for p in (0, 30, 60)] + [f"{b}_p{p}" for b in ("cF1", "cF2", "cF3", "cR1", "cR2", "cR3") for p in (0, 30)] + \
         ["cU1_p30"] + [f"{b}_p30" for b in ("eF1", "eF2", "eF3", "eR1", "eR2", "eR3")]
FS = {"d": "data/external/fpnet_fold1_as_fold0", "c": "data/external/fpnet_fold2_as_fold0", "e": "data/external/fold_safe_fpnet"}
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()


def audit(w, X):
    b = w.split("_p")[0]; O = os.path.join(R, w); fails = []
    def need(c, msg):
        if not c: fails.append(msg)
    rc = json.load(open(os.path.join(O, "receipt.json")))
    outs = [f"ewin_{b}.parquet", f"ewin_molecules_{b}.csv", f"ewin_refs_{b}.json", f"ewin_zlog_{b}.npz", f"e2f_{b}.parquet", f"e2f_analogs_{b}.json", f"e2s_{b}.parquet",
            "ewin_manifest.json", "e2f_world_manifest.json", "e2s_manifest.json"]
    need(rc.get("world") == w and rc.get("version") == "2.1", "receipt world / version")
    need(set(rc.get("outputs", {})) == set(outs), "receipt output set")
    for f in outs:
        need(os.path.exists(os.path.join(O, f)) and sha(os.path.join(O, f)) == rc["outputs"].get(f), f"output hash {f}")
    M = os.path.join(ROOT, "experiments/w135/worlds", w, "world_masks.json"); GD = os.path.join(ROOT, "experiments/w135/worlds", w, "gen", f"gen_{b}.npz"); BC = os.path.join(ROOT, "experiments/w135/batches", f"{b}.csv")
    need(rc["inputs"] == dict(masks=sha(M), gen_dump=sha(GD), batch_csv=sha(BC)), "receipt inputs differ from the files")
    need(rc["code"] == X["code"], "receipt code hashes differ from the committed v2.1 versions")
    need(rc["model"] == X["model_sha256"], "receipt model hash")
    need(all(str(c).startswith("EWIN_CHECK PASS") for c in rc.get("checks", [])) and len(rc.get("checks", [])) == 2, "check lines")
    me = json.load(open(os.path.join(O, "ewin_manifest.json"))); mf = json.load(open(os.path.join(O, "e2f_world_manifest.json"))); ms = json.load(open(os.path.join(O, "e2s_manifest.json")))
    need(me.get("version") == "2.1" and me["masks"] == rc["inputs"]["masks"] and me["eval_csv"] == rc["inputs"]["batch_csv"] and me["gen_dump"] == rc["inputs"]["gen_dump"], "ewin manifest inputs")
    need(me["fpnet"] == sha(os.path.join(ROOT, FS[b[0]], "fpnet_fold0.pt")), "ewin fold-safe FPNet")
    need(me["sets"][b]["outputs"][f"ewin_{b}.parquet"] == rc["outputs"][f"ewin_{b}.parquet"], "ewin manifest output")
    need(mf.get("version") == "2.1" and mf["masks"] == rc["inputs"]["masks"] and mf["eval_csv"] == rc["inputs"]["batch_csv"], "e2f manifest inputs (masks / eval_csv)")
    need(mf["sets"][b]["input_ewin"] == rc["outputs"][f"ewin_{b}.parquet"] and mf["sets"][b]["output"] == rc["outputs"][f"e2f_{b}.parquet"] and mf["sets"][b]["analogs"] == rc["outputs"][f"e2f_analogs_{b}.json"], "e2f manifest chain")
    need(ms.get("version") == "2.1" and ms["model_sha256"] == X["model_sha256"] and ms.get("model_rounds") == X["model_rounds"], "e2s manifest model")
    need(ms["sets"][b]["input_ewin"] == rc["outputs"][f"ewin_{b}.parquet"] and ms["sets"][b]["input_e2f"] == rc["outputs"][f"e2f_{b}.parquet"] and ms["sets"][b]["sha"] == rc["outputs"][f"e2s_{b}.parquet"], "e2s manifest chain")
    an = json.load(open(os.path.join(O, f"e2f_analogs_{b}.json")))
    Pw = pd.read_parquet(os.path.join(ROOT, "experiments/w135/worlds", w, "P.parquet")); Pw["molecule"] = Pw.molecule.astype(str); pan = dict(zip(Pw.molecule, Pw.analogs))
    max_d = 0.0
    for m, lst in an.items():
        ref = json.loads(pan.get(m, "[]"))
        if [k for k, _ in lst] != [k for k, _ in ref]: fails.append(f"analog keys differ for {m}"); break
        if lst: max_d = max(max_d, float(np.max(np.abs(np.array([v for _, v in lst]) - np.array([v for _, v in ref])))))
    need(max_d <= 1e-12, f"analog values differ (max {max_d:.2e})")
    L = pd.read_csv(os.path.join(O, f"ewin_molecules_{b}.csv"), dtype={"molecule": str})
    need((L.zlog_maxdiff.astype(float) <= 1e-5).all(), "zlog provenance")
    return dict(world=w, ok=not fails, fails=fails, analog_max_diff=max_d, zlog_max=float(L.zlog_maxdiff.max()), queries=int(len(L)), analog_lists=len(an))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--expect", required=True); a = ap.parse_args()
    X = json.load(open(os.path.join(ROOT, a.expect))); res = []
    for w in WORLDS:
        if not os.path.exists(os.path.join(R, w, "receipt.json")): res.append(dict(world=w, ok=False, fails=["no receipt"])); continue
        try:
            res.append(audit(w, X))
        except Exception as e:
            res.append(dict(world=w, ok=False, fails=[f"{type(e).__name__}: {e}"]))
    bad = [r for r in res if not r["ok"]]
    json.dump(dict(expected=X, worlds=res, n_ok=len(res) - len(bad), n_fail=len(bad)), open(os.path.join(R, "audit.json"), "w"), indent=1)
    print(f"V21_AUDIT {'PASS' if not bad else 'FAIL'}: {len(res) - len(bad)} / {len(res)} worlds; max analog diff {max([r.get('analog_max_diff', 0) for r in res] or [0]):.2e}; "
          f"max zlog diff {max([r.get('zlog_max', 0) for r in res] or [0]):.2e}")
    for r in bad: print("  -", r["world"], r["fails"][:3])
    sys.exit(0 if not bad else 1)


if __name__ == "__main__":
    main()
