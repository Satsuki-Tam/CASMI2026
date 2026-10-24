#!/bin/bash
# DGX Spark (aarch64, GB10) environment for CASMI2026. Run detached: setsid nohup bash ~/setup_spark.sh > ~/setup_spark.log 2>&1 &
set -u
export PATH="$HOME/.local/bin:$PATH"
R="$HOME/CASMI2026"
echo "== $(date) start setup on $(hostname) $(uname -m)"
if [ ! -d "$R/.git" ]; then git clone https://github.com/Satsuki-Tam/CASMI2026.git "$R"; else (cd "$R" && git pull --ff-only); fi
mkdir -p "$R/data/raw" "$R/data/processed" "$R/data/external" "$R/logs"
TORCH_INDEX="https://download.pytorch.org/whl/cu130"

echo "== main env (.venv, Python 3.11: rdkit 2026.03.3 = scorer version, torch cu130, polars, lightgbm)"
uv venv "$R/.venv" --python 3.11 --clear
uv pip install --python "$R/.venv/bin/python" --index-url "$TORCH_INDEX" --extra-index-url https://pypi.org/simple --index-strategy unsafe-best-match \
   "torch==2.14.1" numpy scipy pandas polars pyarrow scikit-learn lightgbm "rdkit==2026.3.3" kaggle tqdm markdown 2>&1 | tail -5
"$R/.venv/bin/python" - <<'PY'
import torch, rdkit, polars, lightgbm, numpy, sys
print("main env:", sys.version.split()[0], "torch", torch.__version__, "cuda", torch.cuda.is_available(), "rdkit", rdkit.__version__, "polars", polars.__version__, "lightgbm", lightgbm.__version__, "numpy", numpy.__version__)
PY

echo "== forward-model env (.venv-ice, Python 3.12: rdkit 2025.3.6 for ICEBERG/GLACIER runners)"
uv venv "$R/.venv-ice" --python 3.12 --clear
uv pip install --python "$R/.venv-ice/bin/python" --index-url "$TORCH_INDEX" --extra-index-url https://pypi.org/simple --index-strategy unsafe-best-match \
   "torch==2.14.1" numpy scipy pandas "rdkit==2025.3.6" einops pytorch_lightning torchmetrics lightning_utilities numba 2>&1 | tail -5
"$R/.venv-ice/bin/python" - <<'PY'
import torch, rdkit, numba, sys
print("ice env:", sys.version.split()[0], "torch", torch.__version__, "cuda", torch.cuda.is_available(), "rdkit", rdkit.__version__, "numba", numba.__version__)
PY
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo "== $(date) setup done"
