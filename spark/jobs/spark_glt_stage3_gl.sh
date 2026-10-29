#!/bin/bash
# 105 stage 3 preparation (not evaluated here): GLACIER scores of C0' and A1 on the SAME runner inputs for every fold-1 development table the
# main-output comparison would use (f1dev C / D / E / F / G, np053f1dev NP_H / NP_X / NP_N, c1bankdev 4 sets); cells already scored by the
# stage-2 job (f1G, f1D, npH) are reused by copy. Waits for the stage-2 job (GLT2_SCORED), takes the GPU lock. Output: data/glt/stage3_gl/
# gl_<tag>_<set>_{c0prime,A1}.json + manifest. No main-output evaluation, no reading.
set -u
cd ~/CASMI2026 || exit 1
until grep -q "GLT2_SCORED\|GLT2_FAIL" data/glt/stage2_status.txt 2>/dev/null; do sleep 60; done
grep -q GLT2_SCORED data/glt/stage2_status.txt || { echo "stage 2 failed; nothing to do"; exit 1; }
exec 9>$HOME/CASMI2026/spark/gpu.lock
flock 9
G=data/glt; O=$G/stage3_gl; B=experiments/b1_baseline; PYI=.venv-ice/bin/python; mkdir -p $O
fail() { echo "GLT3GL_FAIL $* $(date '+%F %T')" | tee $O/status.txt; exit 1; }
cp $G/stage2_gl/gl_f1G_c0prime.json $O/gl_f1dev_G_tims_crosslib_c0prime.json; cp $G/stage2_gl/gl_f1G_A1.json $O/gl_f1dev_G_tims_crosslib_A1.json
cp $G/stage2_gl/gl_f1D_c0prime.json $O/gl_f1dev_D_np_single_c0prime.json; cp $G/stage2_gl/gl_f1D_A1.json $O/gl_f1dev_D_np_single_A1.json
cp $G/stage2_gl/gl_npH_c0prime.json $O/gl_np053f1dev_NP_H_c0prime.json; cp $G/stage2_gl/gl_npH_A1.json $O/gl_np053f1dev_NP_H_A1.json
for spec in "f1dev|run_f1dev|C_np_crosslib E_np_negonly F_np_uncovered" "np053f1dev|run_np053_f1dev|NP_X NP_N" "c1bankdev|run_c1bankdev_f1|C1_neg_few C1_neg_many C1_pos_few C1_pos_many"; do
  IFS='|' read -r T RUN SETS <<< "$spec"
  for S in $SETS; do for K in c0prime A1; do
    $PYI spark/jobs/ice_resume.py --python $PYI data/external/glacier/gl_runner.py data/external/glacier $B/$RUN/b1_runner_${S}_in.json $O/gl_${T}_${S}_$K.json -- --device cuda --site none --budget 7200 --ckpt $G/ckpt/$K.pt > $O/gl_${T}_${S}_$K.log 2>&1 || fail "gl $T $S $K"
    echo "== $(date +%T) gl $T $S $K $(grep -a '\[resume\] done' $O/gl_${T}_${S}_$K.log | cut -c1-90)"
  done; done
done
{ for f in $O/gl_*.json $G/ckpt/c0prime.pt $G/ckpt/A1.pt; do case "$f" in *.part*) continue;; esac; echo "$(sha256sum $f | cut -c1-64) $f"; done; } > $O/manifest.txt
echo "GLT3GL_DONE $(date '+%F %T')" | tee $O/status.txt
