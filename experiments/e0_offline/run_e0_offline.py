"""Execute the public E0 notebook (0.464 lineage; cells extracted to experiments/e0_offline/cells/NN.py) OFFLINE on the Spark against our own
test file, so that its per-stage lists can be compared with B1 molecule by molecule. Only paths and environment are patched (textually; every
patch is recorded in <work>/e0_port_manifest.json): model code, weights, candidate generation, fusion rules and thresholds are the notebook's own.
Differences to the Kaggle run: main interpreter = .venv (Python 3.11, RDKit 2026.03.3 = official metric; the notebook asserts 3.12 only as an
observer), ICEBERG / GLACIER / N1 runners in .venv-ice (GB10-patched, --site none) through spark/jobs/ice_resume.py, budgets from the CLI.
Usage (repo root):
  python -X utf8 run_e0_offline.py --cells experiments/e0_offline/cells --input <run>/kaggle_input --work <run>/work --runner_python .venv-ice/bin/python
                                   --resume spark/jobs/ice_resume.py --ice_budget 21600 --gl_budget 10800 --n1_budget 3600 [--receipt]
"""
import argparse, glob, hashlib, json, os, subprocess, sys, time, traceback

ap = argparse.ArgumentParser()
ap.add_argument("--cells", required=True); ap.add_argument("--input", required=True); ap.add_argument("--work", required=True)
ap.add_argument("--runner_python", required=True)
ap.add_argument("--resume", default=None, help="spark/jobs/ice_resume.py: restart the ICEBERG/GLACIER runner after a GB10 CUDA crash and merge; omit = plain runner")
ap.add_argument("--ice_budget", type=float, default=21600); ap.add_argument("--gl_budget", type=float, default=10800); ap.add_argument("--n1_budget", type=float, default=3600)
ap.add_argument("--receipt", action="store_true", help="also run cell 23 (mounted-input inventory hashes; optional)")
A = ap.parse_args()
INPUT, WORK = os.path.realpath(A.input), os.path.realpath(A.work); os.makedirs(WORK, exist_ok=True)
RUNNER_PY = os.path.abspath(A.runner_python); RESUME = os.path.realpath(A.resume) if A.resume else None
CELLS = sorted(glob.glob(os.path.join(os.path.realpath(A.cells), "[0-9][0-9].py"))); assert len(CELLS) == 24, CELLS
os.chdir(WORK); os.environ["PYTHONHASHSEED"] = "0"
MANIFEST = dict(input=INPUT, work=WORK, runner_python=RUNNER_PY, resume=RESUME, budgets=dict(ice=A.ice_budget, gl=A.gl_budget, n1=A.n1_budget),
                python=sys.version, started=time.strftime("%Y-%m-%dT%H:%M:%S"), cells={}, patches=[], status="running",
                threads={k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "NUMBA_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")})


def save_manifest(): json.dump(MANIFEST, open(os.path.join(WORK, "e0_port_manifest.json"), "w"), indent=1, default=str)


def E0_RUN_FORWARD(kind, pkg, items, workdir, budget):
    """Stands in for fuse.run_ice / gl_fuse.run_gl: the same runner script, input and output files, but in the Spark's .venv-ice (--site none;
    the bundled x86_64 wheel site cannot be built on the GB10) and, with --resume, through ice_resume.py (runner restarted after a CUDA crash,
    outputs merged). The notebook reads <workdir>/<kind>_out.json(.meta.json) afterwards exactly as on Kaggle."""
    os.makedirs(workdir, exist_ok=True)
    fin, fout = os.path.join(workdir, f"{kind}_in.json"), os.path.join(workdir, f"{kind}_out.json")
    for f in (fout, fout + ".meta.json"):
        if os.path.exists(f): os.remove(f)
    json.dump(items, open(fin, "w"))
    runner = os.path.join(pkg, "ice_runner.py" if kind == "ice" else "gl_runner.py")
    rargs = ["--device", "cuda", "--site", "none", "--budget", str(float(budget)), "--any-rdkit"]
    cmd = ([RUNNER_PY, RESUME, "--python", RUNNER_PY, runner, pkg, fin, fout, "--"] + rargs) if RESUME else ([RUNNER_PY, runner, pkg, fin, fout] + rargs)
    t0 = time.time(); logp = os.path.join(workdir, f"{kind}_runner.log")
    print(f"[port] {kind} runner: {len(items)} molecules, {sum(len(it['cands']) for it in items)} candidates, budget {budget:.0f}s -> {logp}", flush=True)
    with open(logp, "w") as lf: rc = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT).returncode
    out = json.load(open(fout)) if os.path.exists(fout) else {}
    meta = json.load(open(fout + ".meta.json")) if os.path.exists(fout + ".meta.json") else {}
    print(f"[port] {kind} runner rc {rc} {time.time() - t0:.0f}s meta", {k: meta.get(k) for k in ("status", "n_mols", "n_mols_scored", "restarts", "skipped", "seconds")}, flush=True)
    MANIFEST.setdefault("forward", {})[kind] = dict(rc=rc, seconds=round(time.time() - t0), meta=meta, molecules=len(items)); save_manifest()
    return out


CAND_COLS = ["lib_max", "lib_nspec", "lib_hit", "lib_same_adduct", "ap", "best_tan", "fz", "fz_z", "fz_rank", "fz_top", "fp_cos", "mass_ppm", "is_gen", "gen_parent_sim", "n_cand", "xs_max"]
E0_CANDS, E0_INFO = [], {}


def E0_RECORD_CANDS(mid, C, X, score, info):
    """Audit hook (cell 12): every engine-1 window candidate with provenance (pool id / train structure id / generated) and the component
    features the ranker saw (library similarity, analog propagation, FPNet f.z, fingerprint cosine, mass error, generation) + the ranker score."""
    try:
        import numpy as _np
        F_ = list(ns["FEATURES"]); idx = {c: F_.index(c) for c in CAND_COLS if c in F_}
        sc = _np.asarray(score, float); order = _np.argsort(-sc, kind="stable"); rank = _np.empty(len(sc), _np.int64); rank[order] = _np.arange(1, len(sc) + 1)
        X = _np.asarray(X); n = len(sc)
        cols = {c: X[:, j].astype(float).tolist() for c, j in idx.items()}
        tsid = getattr(C, "train_sid", None); form = getattr(C, "formula", None)
        for i in range(n):
            E0_CANDS.append(dict(molecule=str(mid), key=str(C.key[i]), smiles=str(C.smiles[i]), pid=int(C.pid[i]), train_sid=int(tsid[i]) if tsid is not None else -2,
                                 formula=str(form[i]) if form is not None else None, ranker_score=float(sc[i]), ranker_rank=int(rank[i]), **{c: cols[c][i] for c in cols}))
        E0_INFO[str(mid)] = {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in dict(info).items()} if isinstance(info, dict) else str(info)
    except Exception as e:   # the audit must never change or stop the notebook's own flow
        if not E0_INFO.get("_hook_error"): print("[port] candidate audit hook failed (recorded, run continues):", repr(e)[:300], flush=True)
        E0_INFO["_hook_error"] = repr(e)[:300]


def dump_cands():
    import pyarrow as _pa, pyarrow.parquet as _pq
    if E0_CANDS: _pq.write_table(_pa.Table.from_pylist(E0_CANDS), os.path.join(WORK, "e0_engine1_candidates.parquet"))
    dump("e0_engine1_info.json", E0_INFO); print(f"[port] engine-1 candidate audit: {len(E0_CANDS)} rows, {len(E0_INFO)} molecules", flush=True)


def patch(nn, src, old, new, count=1):
    c = src.count(old); assert c == count, (nn, c, old[:90])
    MANIFEST["patches"].append(dict(cell=nn, old=old.strip()[:140], new=new.strip()[:140])); return src.replace(old, new)


CELL01 = '''from pathlib import Path
import os, hashlib, platform, warnings
import numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq
from rdkit import Chem, rdBase, DataStructs
from rdkit.Chem import Descriptors, rdMolDescriptors, rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold
try:
    from rdkit.Chem import Draw
except Exception as _e:
    print('[port] rdkit Draw unavailable:', repr(_e))
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
SEED = 20260915
rng = np.random.default_rng(SEED)
pd.set_option("display.max_colwidth", 100)
pd.set_option("display.max_rows", 100)
display, Markdown = print, str   # [port] matplotlib / seaborn / IPython are not installed on the Spark; the notebook only displays with them
'''
RDKIT_PIP_BLOCK = """tag = f'cp{sys.version_info.major}{sys.version_info.minor}'
whl = [w for w in glob.glob('/kaggle/input/**/rdkit-*.whl', recursive=True) if tag in w and Path(w).name.startswith('rdkit-2026.3.3-')]
assert whl, 'Official RDKit 2026.3.3 wheel is missing'
print('rdkit wheel:', whl)
r = subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--no-index', '--no-deps', whl[0]], capture_output=True, text=True)
print(r.stdout[-500:], r.stderr[-500:])
r.check_returncode()
"""


def prepare(nn, src):
    if nn == 1:
        MANIFEST["patches"].append(dict(cell=1, old="whole cell", new="imports without matplotlib/seaborn/IPython; display=print")); return CELL01
    if nn == 4:
        src = patch(nn, src, RDKIT_PIP_BLOCK, "print('[port] RDKit wheel install skipped: the main venv already provides 2026.03.3', flush=True)\n")
        src = patch(nn, src, "TOPN, ICE_LAM, ICE_BUDGET, ICE_PC = 60, 1.0, 5400, True", f"TOPN, ICE_LAM, ICE_BUDGET, ICE_PC = 60, 1.0, {A.ice_budget:.0f}, True")
        src = patch(nn, src, "print('Simulator RDKit wheel:', simulator_rdkit_wheel(_simulator_pkg))", "print('[port] simulator RDKit comes from the runner venv', E0_RUNNER_PY)")
    if nn == 6:
        src = patch(nn, src, "    assert platform.python_version_tuple()[:2] == ('3', '12')", "    assert platform.python_version_tuple()[:2] in (('3', '11'), ('3', '12'))  # [port] .venv is 3.11")
        src = patch(nn, src, "    assert 'T4' in gpu, gpu", "    assert gpu, gpu  # [port] GB10 instead of T4")
    if nn == 12:
        src = patch(nn, src, "                score = rank_score(np.concatenate([X, F], 1), list(FEATURES) + list(names))",
                    "                score = rank_score(np.concatenate([X, F], 1), list(FEATURES) + list(names)); E0_RECORD_CANDS(mid, C, X, score, info)")
    if nn == 13:
        src = patch(nn, src, "    _claw_preseed_site(ICE_PKG, '/kaggle/working/ice_site')\n", "    print('[port] wheel-site preseed skipped (runner venv)', flush=True)\n")
        src = patch(nn, src, "    ICE_SCORES = ice_fuse.run_ice(ICE_PKG, items, workdir='/kaggle/working/ice_work', device='cuda', budget_s=ICE_BUDGET,\n"
                             "                                  site='/kaggle/working/ice_site', extra_args=['--any-rdkit'])",
                    "    ICE_SCORES = E0_RUN_FORWARD('ice', ICE_PKG, items, '/kaggle/working/ice_work', ICE_BUDGET)")
        src = patch(nn, src, "    GL_SCORES = gl_fuse.run_gl(GL_PKG, gl_items, workdir='/kaggle/working/gl_work', device='cuda', budget_s=GL_BUDGET,\n"
                             "                               site='/kaggle/working/ice_site', wheels=os.path.join(ICE_PKG, 'wheels'), extra_args=['--any-rdkit'])",
                    "    GL_SCORES = E0_RUN_FORWARD('gl', GL_PKG, gl_items, '/kaggle/working/gl_work', GL_BUDGET)")
        src = patch(nn, src, "GL_SCORES, gl_stats, GL_LAM, GL_BUDGET = {}, dict(molecules=0, changed_vs_ice_top25=0, changed_vs_ice_top1=0), 1.0, 4000",
                    f"GL_SCORES, gl_stats, GL_LAM, GL_BUDGET = {{}}, dict(molecules=0, changed_vs_ice_top25=0, changed_vs_ice_top1=0), 1.0, {A.gl_budget:.0f}")
        src = patch(nn, src, "N1_BUDGET = 1200.0 if IS_RERUN else 600.0", f"N1_BUDGET = {A.n1_budget:.1f}")
        src = patch(nn, src, "N1_WORK, N1_SITE, N1_DEVICE, N1_DRIVER_EXTRA = '/kaggle/working/n1_work', '/kaggle/working/ice_site', 'cuda', []",
                    "N1_WORK, N1_SITE, N1_DEVICE, N1_DRIVER_EXTRA = '/kaggle/working/n1_work', 'none', 'cuda', []")
        src = patch(nn, src, "    cmd = [sys.executable, os.path.join(N1_WORK, 'glb_driver.py'), GL_PKG, fin, fout, '--device', N1_DEVICE,",
                    "    cmd = [E0_RUNNER_PY, os.path.join(N1_WORK, 'glb_driver.py'), GL_PKG, fin, fout, '--device', N1_DEVICE,")
    if nn == 14:
        src = patch(nn, src, "rows, stats = [], dict(untouched=0, gentle=0, aggressive=0, no_pc=0, promoted=0)",
                    "rows, stats, E0_MERGE = [], dict(untouched=0, gentle=0, aggressive=0, no_pc=0, promoted=0), {}")
        src = patch(nn, src, "        stats['no_pc'] += 1; final = smis", "        stats['no_pc'] += 1; final = smis; E0_MERGE[mid] = dict(branch='no_pc', lib_max=lib_max)")
        src = patch(nn, src, "        stats['untouched'] += 1; final = smis", "        stats['untouched'] += 1; final = smis; E0_MERGE[mid] = dict(branch='untouched', lib_max=lib_max)")
        src = patch(nn, src, "        stats['aggressive' if rel > REL_TH else 'gentle'] += 1",
                    "        stats['aggressive' if rel > REL_TH else 'gentle'] += 1; E0_MERGE[mid] = dict(branch='aggressive' if rel > REL_TH else 'gentle', lib_max=lib_max, rel=float(rel))")
        src = patch(nn, src, "        if (S is not None and float(S) > S_TAU and pop_top >= POP_TAU) or (rel > 150.0):",
                    "        E0_MERGE[mid].update(S=(float(S) if S is not None else None), top_pop=pop_top, promoted=False)\n"
                    "        if (S is not None and float(S) > S_TAU and pop_top >= POP_TAU) or (rel > 150.0):")
        src = patch(nn, src, "            stats['promoted'] += 1", "            stats['promoted'] += 1; E0_MERGE[mid]['promoted'] = True")
    if nn == 17:
        src = patch(nn, src, "assert _stage_meta['ice'].get('status') == 'ok', _stage_meta['ice']",
                    "print('[port] ICE stage meta status:', _stage_meta['ice'].get('status'), '(hard assert relaxed; recorded)', flush=True)")
        src = patch(nn, src, "if (te.adduct == '[M+H]+').any():\n    assert _stage_meta['glacier'].get('status') == 'ok', _stage_meta['glacier']",
                    "print('[port] GLACIER stage meta status:', _stage_meta['glacier'].get('status'), '(hard assert relaxed; recorded)', flush=True)")
    n_in, n_wk = src.count("/kaggle/input"), src.count("/kaggle/working")
    src = src.replace("/kaggle/input", INPUT).replace("/kaggle/working", WORK)
    if n_in or n_wk: MANIFEST["patches"].append(dict(cell=nn, old=f"/kaggle/input x{n_in}, /kaggle/working x{n_wk}", new="run input tree / work dir"))
    return src


def dump(name, obj):
    with open(os.path.join(WORK, name), "w") as f: json.dump(obj, f, default=str)


HOOKS = {
    12: lambda ns: (dump("e0_base_lists.json", {str(m): dict(smiles=v[0], keys=v[1], lib_max=v[2], scores=v[3], forms=v[4]) for m, v in ns["BASE"].items()}), dump_cands()),
    13: lambda ns: (dump("e0_ice_scores.json", ns["ICE_SCORES"]), dump("e0_gl_scores.json", ns["GL_SCORES"]),
                    dump("e0_base_after_rerank.json", {str(m): dict(smiles=v[0], keys=v[1], lib_max=v[2]) for m, v in ns["BASE"].items()}),
                    dump("e0_pc_after_rerank.json", ns["PC"]),
                    dump("e0_n1.json", dict(n1_mids=sorted(ns["N1_MIDS"]), n1_gl_mids=sorted(ns["N1_GL_MIDS"]), health=ns["N1_HEALTH"], stats=ns["N1_STATS"],
                                            ice_health=ns["CLAW_ICE_HEALTH"], gl_health=ns["CLAW_GL_HEALTH"], ice_stats=ns["ice_stats"], gl_stats=ns["gl_stats"]))),
    14: lambda ns: dump("e0_merge_decisions.json", dict(per_molecule=ns["E0_MERGE"], stats=ns["stats"], LIB_TAU=ns["LIB_TAU"], REL_TH=ns["REL_TH"], S_TAU=ns["S_TAU"], POP_TAU=ns["POP_TAU"])),
    20: lambda ns: dump("e0_frag_gap.json", ns["FRAG_GAP"]),
}

import pandas as pd
try: pd.options.future.infer_string = False; MANIFEST["pandas"] = dict(version=pd.__version__, infer_string=False)   # Kaggle ran pandas 2.x (object strings)
except Exception as e: MANIFEST["pandas"] = dict(version=pd.__version__, infer_string=repr(e))

ns = {"__name__": "__main__", "E0_RUNNER_PY": RUNNER_PY, "E0_RUN_FORWARD": E0_RUN_FORWARD, "E0_RECORD_CANDS": E0_RECORD_CANDS}
last = 23 if A.receipt else 22
print(f"[port] {time.strftime('%H:%M:%S')} input {INPUT} work {WORK} runner {RUNNER_PY} resume {RESUME} budgets ice {A.ice_budget:.0f} gl {A.gl_budget:.0f} n1 {A.n1_budget:.0f}", flush=True)
save_manifest()
for path in CELLS:
    nn = int(os.path.basename(path)[:2])
    if nn > last: break
    raw = open(path, encoding="utf-8").read(); src = prepare(nn, raw)
    MANIFEST["cells"][nn] = dict(sha256_original=hashlib.sha256(raw.encode()).hexdigest()[:16], status="running", started=time.strftime("%H:%M:%S")); save_manifest()
    t0 = time.time(); print(f"[port] ===== cell {nn:02d} start {time.strftime('%H:%M:%S')}", flush=True)
    try:
        exec(compile(src, f"<cell{nn:02d}>", "exec"), ns)
        if nn in HOOKS: HOOKS[nn](ns)
    except Exception as e:
        traceback.print_exc(); print(f"[port] cell {nn:02d} FAILED after {time.time() - t0:.0f}s: {e!r}", flush=True)
        MANIFEST["cells"][nn].update(status="failed", seconds=round(time.time() - t0), error=repr(e)[:500]); MANIFEST["status"] = f"failed at cell {nn}"; save_manifest()
        if nn == 23: break
        sys.exit(2)
    MANIFEST["cells"][nn].update(status="ok", seconds=round(time.time() - t0)); save_manifest()
    print(f"[port] ===== cell {nn:02d} done {time.time() - t0:.0f}s", flush=True)
MANIFEST["status"] = "ok"; MANIFEST["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
try:   # run audit (Codex 016): budgets vs usage, runner coverage, part metas, code / input hashes
    aud = dict(run=WORK, finished=MANIFEST["finished"], budgets=MANIFEST["budgets"], forward=MANIFEST.get("forward"), cells={k: v.get("seconds") for k, v in MANIFEST["cells"].items()},
               code=dict(launcher=hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()[:16], cells={k: v["sha256_original"] for k, v in MANIFEST["cells"].items()}),
               inputs=json.load(open(os.path.join(os.path.dirname(WORK), "run_inputs.json"))) if os.path.exists(os.path.join(os.path.dirname(WORK), "run_inputs.json")) else None,
               parts={}, coverage={})
    for kind in ("ice", "gl", "n1"):
        wd = os.path.join(WORK, f"{kind}_work")
        if os.path.isdir(wd):
            aud["parts"][kind] = {f: json.load(open(os.path.join(wd, f))) for f in sorted(os.listdir(wd)) if f.endswith(".meta.json")}
            for f, m in aud["parts"][kind].items():
                for k in ("log_tail",): m.pop(k, None)
    for kind, fn in (("gl", "e0_gl_scores.json"), ("ice", "e0_ice_scores.json")):
        d = json.load(open(os.path.join(WORK, fn))) if os.path.exists(os.path.join(WORK, fn)) else {}
        aud["coverage"][kind] = dict(molecules_in=len(d), molecules_with_finite=sum(1 for v in d.values() if isinstance(v, dict) and any(isinstance(x, (int, float)) and x == x for x in v.values())),
                                     candidates_finite=sum(1 for v in d.values() if isinstance(v, dict) for x in v.values() if isinstance(x, (int, float)) and x == x))
    aud["budget_cutoff"] = {k: (v.get("meta", {}).get("status") not in ("ok",)) for k, v in (MANIFEST.get("forward") or {}).items()}
    json.dump(aud, open(os.path.join(WORK, "e0_run_audit.json"), "w"), indent=1, default=str)
except Exception as e: print("[port] run audit failed:", repr(e), flush=True)
MANIFEST["outputs"] = {f: os.path.getsize(os.path.join(WORK, f)) for f in sorted(os.listdir(WORK)) if os.path.isfile(os.path.join(WORK, f))}
save_manifest(); print("[port] E0 OFFLINE DONE", MANIFEST["finished"], flush=True)
