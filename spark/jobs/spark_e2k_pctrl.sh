#!/bin/bash
# 145 P-invariance control on the same platform (Codex 145 Q3): the generated pipeline WITHOUT --e2_model (E2 off; hook None) with exactly the
# arguments of the v2 parity run; its submission.csv must equal the v2 run's submission_pref.csv (ordered lists) if E2 leaves P untouched.
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4
E=experiments/b1_baseline/eval_test_panel250_pc; W=experiments/e2/k_pctrl_c1
[ -e $W ] && { echo "refused: $W exists"; exit 1; }
echo "== $(date +%T) pipeline $(tr -d '\r' < experiments/b1_e2k/b1_pipeline.py | sha256sum | cut -c1-12) (E2 off)"
$PY -X utf8 experiments/b1_e2k/b1_pipeline.py --test $E/test.parquet --out $W --workers 8 --mask_json $E/mask_c1.json --rank_model experiments/b1_baseline/rank_v8w7a/lambdarank.txt \
  --tau 0.9 --main blend21 --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt --analog_w 0 --analog_w_fallback 1 --analog_feat ap \
  --frag_w_fallback 1 --gl_json $E/run_v8w7a_c1/gl_out.json --solution $E/solution.csv > $W.log 2>&1
rc=$?; echo "== $(date +%T) pipeline exit $rc"; [ $rc = 0 ] || { echo "E2K_PCTRL_DONE FAIL pipeline"; exit 1; }
$PY -X utf8 -c "
import pandas as pd, sys
a = pd.read_csv('$W/submission.csv', dtype=str, keep_default_na=False).set_index('molecule_id').smiles
b = pd.read_csv('experiments/e2/k_parity_c1_v2/submission_pref.csv', dtype=str, keep_default_na=False).set_index('molecule_id').smiles
d = [m for m in b.index if a.get(m) != b[m]]; print('E2-off P vs E2-on P: molecules', len(b), 'differing lists', len(d), 'ids equal', set(a.index) == set(b.index))
sys.exit(0 if not d and set(a.index) == set(b.index) else 1)" && echo "E2K_PCTRL_DONE PASS $(date '+%F %T')" || { echo "E2K_PCTRL_DONE FAIL $(date '+%F %T')"; exit 1; }
