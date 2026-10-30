#!/bin/bash
# v2.1 prep (158 decision): per W135 world -> world E window under spark/gpu.lock (b1_ewin_world.py v2.1, zlog provenance vs the B1 gen dump)
# -> invariants (w135_ewin_check.py) -> world E2 features (e2_feats_world.py v2.1) -> invariants incl. analog lists == W135 P (--feats)
# -> frozen E2 scores (e2_score_world.py v2.1) -> a completion RECEIPT (input / code / model / output hashes, check lines, wall time and max RSS
# per stage). A world is skipped only when its receipt verifies against the files; a world with outputs but no valid receipt is a failure
# (no overwrite). Any failed world makes the list end with V2_LIST_PARTIAL and exit 1. Data only: no reach / truth number is printed.
# Usage: bash spark/jobs/spark_v2_1_world_e2.sh "dF1_p30 dR1_p30 ..."   (status lines in experiments/w135/v2_1/status.txt)
cd ~/CASMI2026 || exit 1
PY=$HOME/CASMI2026/.venv/bin/python; export PYTHONUTF8=1; R=experiments/w135/v2_1; L=$R/status.txt; mkdir -p $R; FAILED=0
receipt_ok() { $PY -X utf8 - "$1" <<'PYEOF'
import hashlib, json, os, sys
r = sys.argv[1]
try:
    rc = json.load(open(r)); d = os.path.dirname(r)
    ok = all(hashlib.sha256(open(os.path.join(d, f), "rb").read()).hexdigest() == h for f, h in rc["outputs"].items())
except Exception:
    ok = False
sys.exit(0 if ok else 1)
PYEOF
}
stage() { local name=$1; shift; /usr/bin/time -v -o $O/time_$name.txt "$@" > $O/$name.log 2>&1; }
for w in $1; do
  b=${w%_p*}; O=$R/$w; M=experiments/w135/worlds/$w/world_masks.json; GD=experiments/w135/worlds/$w/gen/gen_$b.npz
  case $b in d*) FS=data/external/fpnet_fold1_as_fold0;; c*) FS=data/external/fpnet_fold2_as_fold0;; e*) FS=data/external/fold_safe_fpnet;; *) echo "V2_FAIL unknown $w" >> $L; FAILED=1; continue;; esac
  if [ -e $O/receipt.json ] && receipt_ok $O/receipt.json; then echo "skip $w (receipt verified)" >> $L; continue; fi
  if [ -e $O ] && [ -n "$(ls -A $O 2>/dev/null)" ]; then echo "V2_FAIL outputs-without-receipt $w $(date '+%F %T')" >> $L; FAILED=1; continue; fi
  mkdir -p $O
  stage ewin flock spark/gpu.lock env OMP_NUM_THREADS=1 nice -n 5 $PY -X utf8 experiments/e2/b1_ewin_world.py --eval_csv experiments/w135/batches/$b.csv --sets $b --fold_safe $FS --masks $M --gen_dump $GD --out $O --workers 8 || { echo "V2_FAIL ewin $w $(date '+%F %T')" >> $L; FAILED=1; continue; }
  stage check $PY -X utf8 experiments/e2/w135_ewin_check.py --ewin $O --masks $M --set $b || { echo "V2_FAIL check $w $(date '+%F %T') $(head -1 $O/check.log | cut -c1-120)" >> $L; FAILED=1; continue; }
  stage feats nice -n 5 $PY -X utf8 experiments/e2/e2_feats_world.py --ewin $O --eval_csv experiments/w135/batches/$b.csv --masks $M --sets $b --workers 8 || { echo "V2_FAIL feats $w $(date '+%F %T')" >> $L; FAILED=1; continue; }
  stage checkf $PY -X utf8 experiments/e2/w135_ewin_check.py --ewin $O --masks $M --set $b --feats --world_p experiments/w135/worlds/$w/P.parquet || { echo "V2_FAIL checkf $w $(date '+%F %T') $(head -1 $O/checkf.log | cut -c1-120)" >> $L; FAILED=1; continue; }
  stage score $PY -X utf8 experiments/e2/e2_score_world.py --ewin $O --sets $b || { echo "V2_FAIL score $w $(date '+%F %T')" >> $L; FAILED=1; continue; }
  $PY -X utf8 - "$O" "$w" "$b" "$M" "$GD" <<'PYEOF' || { echo "V2_FAIL receipt $w" >> $L; FAILED=1; continue; }
import hashlib, json, os, re, sys
O, w, b, M, GD = sys.argv[1:6]; sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
outs = [f"ewin_{b}.parquet", f"ewin_molecules_{b}.csv", f"ewin_refs_{b}.json", f"ewin_zlog_{b}.npz", f"e2f_{b}.parquet", f"e2f_analogs_{b}.json", f"e2s_{b}.parquet",
        "ewin_manifest.json", "e2f_world_manifest.json", "e2s_manifest.json"]
code = {f: sha(f) for f in ("experiments/e2/b1_ewin_world.py", "experiments/e2/w135_ewin_check.py", "experiments/e2/e2_feats_world.py", "experiments/e2/e2_score_world.py", "experiments/e2/e2_common.py")}
timing = {}
for st in ("ewin", "check", "feats", "checkf", "score"):
    t = open(os.path.join(O, f"time_{st}.txt")).read()
    timing[st] = dict(wall=re.search(r"Elapsed \(wall clock\) time.*?: (\S+)", t).group(1), max_rss_kb=int(re.search(r"Maximum resident set size \(kbytes\): (\d+)", t).group(1)))
rc = dict(world=w, version="2.1", inputs=dict(masks=sha(M), gen_dump=sha(GD), batch_csv=sha(f"experiments/w135/batches/{b}.csv")), code=code,
          model=json.load(open(os.path.join(O, "e2s_manifest.json")))["model_sha256"], outputs={f: sha(os.path.join(O, f)) for f in outs},
          checks=[open(os.path.join(O, f)).readline().strip() for f in ("check.log", "checkf.log")], timing=timing)
tmp = os.path.join(O, ".receipt.tmp"); json.dump(rc, open(tmp, "w"), indent=1); os.replace(tmp, os.path.join(O, "receipt.json"))
PYEOF
  echo "V2_WORLD_DONE $w $(date '+%F %T') $(head -1 $O/checkf.log | cut -c1-80)" >> $L
done
if [ $FAILED = 0 ]; then echo "V2_LIST_DONE $(date '+%F %T')" >> $L; exit 0; fi
echo "V2_LIST_PARTIAL $(date '+%F %T')" >> $L; exit 1
