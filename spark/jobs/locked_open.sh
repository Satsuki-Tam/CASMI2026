#!/bin/bash
# Open the locked set ONCE for the two pre-registered candidates (008_decision §5, 009_decision §1-2). Manual launch only; no code sync here:
# the checked-out code and the listed artifacts are frozen into a manifest (git HEAD, sha256 of scripts and models, runner status) before scoring.
#   M1 = B1 v2: run_locked_v2 (shortlist FP100 ∪ FP+prior100 ∪ lib20, GL + ICE), model rank_v2/lambdarank.txt, insurance S(2,1,0.5)+libpri(0.9,0.2)
#   M2 = B1 v3: run_v3_locked (FP100 ∪ FP+prior200 ∪ lib20 ∪ prior50, GL only), model rank_v3/lambdarank.txt, insurance S(2,0,0.5)+libpri(0.9,0.2)
# Adoption rule (frozen): per set paired C2 difference; C1 loss of M2 must be <= 0.02 (lower CI > -0.02 for a "protected" claim); if the C2
# difference is < 0.01 with C1 protected, the candidate with the shorter MEASURED runtime; otherwise "undecided", both kept.
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; OUT=$B/locked_open_v2v3
fail() { echo "LOCKED_OPEN ABORTED: $*"; exit 1; }
[ -e $OUT/manifest.txt ] || [ -e $OUT/locked_results.json ] || [ -e $OUT/manifest.json ] && fail "$OUT already holds an opening record; the locked set is opened once (no re-run)"
mkdir -p $OUT
echo "evaluator sha256: $(sha256sum $B/b1_locked_eval.py | cut -c1-64)"
for f in $B/run_locked_v2/b1_features_A_timstof.parquet $B/run_locked_v2/b1_features_B_nplib.parquet $B/run_v3_locked/b1_features_A_timstof.parquet $B/run_v3_locked/b1_features_B_nplib.parquet \
         $B/rank_v2/lambdarank.txt $B/rank_v3/lambdarank.txt $B/locked_eval/p1_molecules.csv data/processed/train_scorer_keys.parquet; do [ -s $f ] || fail "missing $f"; done
# runner outputs: a crashed runner (GB10 CUDA bug) is repaired with the resumable driver (--reuse keeps the scored molecules); anything else aborts
repair() {  # run_dir model set
  local RUN=$1 R=$2 S=$3 st IN PKG SCR
  st=$($PY -c "import json; print(json.load(open('$RUN/work/${R}_${S}.json.meta.json')).get('status'))" 2>/dev/null)
  case "$st" in ok|partial) return 0;; esac
  echo "repairing $RUN $R $S (status '$st')"; IN=$RUN/b1_runner_${S}_in.filtered.json; [ -f $IN ] || IN=$RUN/b1_runner_${S}_in.json
  if [ "$R" = gl ]; then PKG=data/external/glacier; SCR=gl_runner.py; else PKG=data/external/iceberg; SCR=ice_runner.py; fi
  .venv-ice/bin/python spark/jobs/ice_resume.py --reuse --python .venv-ice/bin/python $PKG/$SCR $PKG $IN $RUN/work/${R}_${S}.json -- --device cuda --site none --budget 7200 > $RUN/work/${R}_${S}_resume.log 2>&1
  st=$($PY -c "import json; print(json.load(open('$RUN/work/${R}_${S}.json.meta.json')).get('status'))" 2>/dev/null); case "$st" in ok|partial) echo "repaired: $st";; *) fail "$RUN $R $S still '$st'";; esac
}
for S in A_timstof B_nplib; do repair $B/run_locked_v2 gl $S; repair $B/run_locked_v2 ice $S; repair $B/run_v3_locked gl $S; done
{
  echo "opened_at: $(date '+%F %T')"; echo "git_head: $(git rev-parse HEAD)"; echo "git_status_dirty_files: $(git status --short | wc -l)"
  for f in $B/b1_locked_eval.py $B/b1_rankfeats.py $B/b1_evaluate.py $B/b1_features.py src/metric.py $B/rank_v2/lambdarank.txt $B/rank_v3/lambdarank.txt; do echo "sha256 $f $(sha256sum $f | cut -c1-64)"; done
  for r in run_locked_v2 run_v3_locked; do for m in $B/$r/work/*.json.meta.json; do echo "$m $(tr -d '\n ' < $m | cut -c1-160)"; done; cat $B/$r/b1_features_manifest.json 2>/dev/null | tr -d '\n ' | cut -c1-300; echo; done
} > $OUT/manifest.txt
echo "manifest written: $OUT/manifest.txt"; head -12 $OUT/manifest.txt | cut -c1-160
$PY -X utf8 $B/b1_locked_eval.py --eval_csv $B/locked_eval/p1_molecules.csv --cands M1:$B/run_locked_v2:$B/rank_v2/lambdarank.txt:1 M2:$B/run_v3_locked:$B/rank_v3/lambdarank.txt:0 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --out $OUT > $OUT/locked_open.log 2>&1
rc=$?; echo "locked eval exit $rc"; grep -v Warning $OUT/locked_open.log | cut -c1-230
if [ $rc = 0 ]; then echo "LOCKED_OPEN_DONE $(date +%T)"; else echo "LOCKED_OPEN FAILED rc=$rc (nothing scored unless validation passed; see $OUT/locked_open.log)"; exit $rc; fi
