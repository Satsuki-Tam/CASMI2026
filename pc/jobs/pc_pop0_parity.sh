#!/bin/bash
# pop0 (116/124/125/126) local self-consistency check, CPU only, first N panel molecules, c2 view, GL scores of the 10/27 v8w7a panel run (--gl_json):
#   A = experiments/b1_pop0 pipeline --lam_fixed 0 (main pass LAM 0 -> submission*.csv, reference pass frozen LAM -> submission_lamref*.csv)
#   B = the same pipeline WITHOUT --lam_fixed (one pass, frozen LAM)
# PASS = A's four lamref lists equal B's four lists for every molecule (pass order / shared state cannot change the frozen-LAM output).
# CPU only: CUDA_VISIBLE_DEVICES=-1 (an EMPTY value is dropped from the Windows process environment, so the CUDA runtime still saw the GPU in the
# first attempts at 12:14-12:17) and the harness asserts that torch sees no GPU. The 10/27 GPU (bf16) outputs are compared only descriptively.
# Codex 126: fresh output dirs, every run's rc checked (stop on failure), the comparison's exit code decides PASS / FAIL, DONE only after a PASS.
set -u
cd /c/kaggle/CASMI || exit 1
export CUDA_VISIBLE_DEVICES=-1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONUTF8=1 PYTHONHASHSEED=0
B=experiments/b1_baseline; S=experiments/b1_pop0; PY=/c/kaggle/CASMI/.venv/Scripts/python.exe; E=$B/eval_test_panel250_pc; MODEL=$B/rank_v8w7a/lambdarank.txt
CK=data/external/fpnet_fulleval_as_fold0/fpnet_fold0.pt; N=${1:-60}
echo "== $(date +%T) pipeline $(sha256sum $S/b1_pipeline.py | cut -c1-12) model $(sha256sum $MODEL | cut -c1-12) N=$N"
run() { local W=$1; shift; rm -rf $W $W.log
  $PY -X utf8 -c "import sys, runpy, torch; assert not torch.cuda.is_available(), 'GPU visible'; sys.argv = sys.argv[1:]; runpy.run_path(sys.argv[0], run_name='__main__')" \
    $S/b1_pipeline.py --test $E/test.parquet --out $W --limit $N --workers 6 --mask_json $E/mask_c2.json --rank_model $MODEL --tau 0.9 --main blend21 \
    --k_fpp 200 --k_pop 50 --w_ice 0 --fpnet_ckpt $CK --analog_w 0 --analog_w_fallback 1 --analog_feat ap --frag_w_fallback 1 --gl_json $E/run_v8w7a_c2/gl_out.json "$@" > $W.log 2>&1
  local rc=$?; echo "== $(date +%T) $W rc=$rc $(grep -a -E 'pop0:|submission written' $W.log | tail -3 | cut -c1-200 | tr '\n' ' ')"; return $rc; }
run $E/run_pop0chk_A_c2 --lam_fixed 0 || { echo "POP0_SELFCHECK FAIL run A"; exit 1; }
run $E/run_pop0chk_B_c2 || { echo "POP0_SELFCHECK FAIL run B"; exit 1; }
$PY -X utf8 - <<'PY'
import pandas as pd, sys
E = "experiments/b1_baseline/eval_test_panel250_pc"; A, B, G = f"{E}/run_pop0chk_A_c2", f"{E}/run_pop0chk_B_c2", f"{E}/run_v8w7a_c2"
ok = True
for a_, b_ in (("submission_lamref.csv", "submission.csv"), ("submission_lamref_fixed.csv", "submission_fixed.csv"),
               ("submission_lamref_probe_train.csv", "submission_probe_train.csv"), ("submission_lamref_probe_nontrain.csv", "submission_probe_nontrain.csv")):
    x = pd.read_csv(f"{A}/{a_}", dtype=str, keep_default_na=False).set_index("molecule_id").smiles.sort_index(); y = pd.read_csv(f"{B}/{b_}", dtype=str, keep_default_na=False).set_index("molecule_id").smiles.sort_index()
    same = x.index.is_unique and y.index.is_unique and x.index.equals(y.index) and (x == y).all(); ok &= bool(same)
    print("A", a_, "vs B", b_, "rows", len(x), "identical" if same else f"DIFFER {int((x != y).sum()) if x.index.equals(y.index) else 'ids'}")
proc = set(pd.read_csv(f"{A}/b1_stage_stats.csv").molecule.astype(str)); ok &= proc == set(pd.read_csv(f"{B}/b1_stage_stats.csv").molecule.astype(str))
m = pd.read_csv(f"{A}/submission.csv", dtype=str).set_index("molecule_id").smiles; r = pd.read_csv(f"{A}/submission_lamref.csv", dtype=str).set_index("molecule_id").smiles.loc[m.index]
print("descriptive: processed", len(proc), "| pop0 vs frozen LAM: lists changed", sum(m[k] != r[k] for k in proc), "rank-1 changed", sum(m[k].split(";")[0] != r[k].split(";")[0] for k in proc))
g = pd.read_csv(f"{G}/submission.csv", dtype=str).set_index("molecule_id").smiles
print("descriptive: CPU fp32 frozen-LAM list vs the 10/27 GPU run: identical", sum(r[k] == g[k] for k in proc), "of", len(proc), "| same rank-1", sum(r[k].split(";")[0] == g[k].split(";")[0] for k in proc))
print("POP0_SELFCHECK", "PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
PY
rc=$?; [ $rc -eq 0 ] || { echo "POP0_SELFCHECK comparison rc=$rc"; exit 1; }
echo "POP0_PARITY_RUN_DONE $(date +%T)"
