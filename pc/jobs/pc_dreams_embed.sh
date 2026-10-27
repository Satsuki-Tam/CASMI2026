#!/bin/bash
# DreaMS embeddings (fp32, exact O(N) graphormer bias, dreams_min.py) of every spectra-store row -> data/processed/dreams_emb. GPU (one CUDA job at a time).
set -u
cd /c/kaggle/CASMI/experiments/b1_baseline || exit 1
export OMP_NUM_THREADS=2 PYTHONUTF8=1
W=C:/kaggle/CASMI/data/external_kaggle/casmi26-attributed-v4g-reproduction-assets/hengck23-dreams-enveda-casmi26/hengck23-dreams-enveda-casmi26
/c/kaggle/CASMI/.venv/Scripts/python.exe -X utf8 dreams_embed.py --weights $W/embedding_model_state_dict.pt --out C:/kaggle/CASMI/data/processed/dreams_emb --bf16 0 --bs 512 > /c/kaggle/CASMI/logs/dreams_embed.log 2>&1
echo "== $(date +%T) dreams embed exit $? $(tail -1 /c/kaggle/CASMI/logs/dreams_embed.log | cut -c1-80)"
echo "DREAMS_EMBED_DONE $(date +%T)"
