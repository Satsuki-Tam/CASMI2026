"""105 GLACIER adaptation: run an ms-pred script (training / preprocessing) inside .venv-glt with the same module setup as the inference runner
(data/external/glacier/gl_runner.py setup_env), except that LinSATNet / pygmtools are the REAL packages (training losses use their values; stage 0a):
  sys.path = [data/glt/shim_train (dgl, torch_scatter pure-torch shims only), ms-pred-train src (commit 708148c2)] + the venv;
  plotting / tuning-only ms_pred modules are empty placeholders (matplotlib / seaborn / ray are never imported).
Usage (Spark): .venv-glt/bin/python experiments/glt/run_mspred.py <script path relative to the ms-pred repo> [script args ...]
       e.g. ... run_mspred.py src/ms_pred/magma/run_magma.py --spectra-dir ... (cwd stays the caller's)"""
import os, runpy, sys, types
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MP = os.path.join(ROOT, "data/external/ms-pred-train/ms-pred")
for p in reversed([os.path.join(ROOT, "data/glt/shim_train"), os.path.join(MP, "src")]):
    while p in sys.path: sys.path.remove(p)
    sys.path.insert(0, p)
import LinSATNet, pygmtools   # noqa: F401  (the real packages must resolve, not a shim)
assert "glacier/shim" not in LinSATNet.__file__, LinSATNet.__file__
import tempfile
for name in ("ms_pred.common.plot_utils", "ms_pred.nn_utils.tune_utils", "ms_pred.nn_utils.base_hyperopt"):
    mod = types.ModuleType(name); mod.__ice_placeholder__ = True; sys.modules[name] = mod
for f in ("plot_mol_as_vector", "plot_compare_ms", "plot_ms"): setattr(sys.modules["ms_pred.common.plot_utils"], f, lambda *x, **k: None)
import ms_pred.common.chem_utils as cu
cache_root = os.path.join(tempfile.gettempdir(), "glt_ms_pred_cache"); cu.user_cache_dir = lambda name, *x, **k: os.path.join(cache_root, name)
script = sys.argv[1]; path = script if os.path.isabs(script) else os.path.join(MP, script)
sys.argv = [path] + sys.argv[2:]
runpy.run_path(path, run_name="__main__")
