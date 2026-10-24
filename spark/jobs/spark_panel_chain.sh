#!/bin/bash
# Panel diagnostic (Codex 007 W1 scope: FP / library / prior; GL+ICE reported but MSG-contaminated): the 250 enveda-np-examples molecules
# (timsTOF, natural products, all with other-library references) through B1 v2 features (K=100), fixed rules with several prior weights,
# library priority, and the frozen learned model rank_v2 (learned / insurance / fixed with the official scorer).
set -u
cd ~/CASMI2026 || exit 1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
B=experiments/b1_baseline; PY=.venv/bin/python; RUN=$B/run_panel_v2
git fetch -q origin && git checkout -q origin/main -- $B/b1_evaluate.py $B/b1_locked_eval.py $B/b1_features.py spark/jobs/b1_features_job_v3.sh && echo "synced $(git rev-parse --short origin/main) $(date +%T)"
mkdir -p $B/panel_np250
$PY - <<'EOF'
import polars as pl
m = pl.read_parquet("data/processed/spectra_store/spec_meta.parquet")
p = m.filter(pl.col("ingest_lib") == "enveda-np-examples").group_by("inchikey14").agg(pl.col("scorer_ik14").first(), pl.len().alias("n_spectra_lib")).sort("inchikey14")
df = p.with_columns(pl.lit("P_np250").alias("set"), pl.lit("diag").alias("group"), pl.col("inchikey14").alias("molecule"), pl.col("scorer_ik14").alias("scorer_key"), pl.col("inchikey14").alias("raw_key"),
                    pl.lit("enveda-np-examples").alias("lib"), pl.int_range(pl.len()).alias("identity_group"), pl.lit(True).alias("window_external"), pl.lit(True).alias("db_present_external"))
df.select("set", "group", "molecule", "scorer_key", "raw_key", "lib", "identity_group", "n_spectra_lib", "window_external", "db_present_external").write_csv("experiments/b1_baseline/panel_np250/p1_molecules.csv")
print("panel csv:", df.height, "molecules")
EOF
FEAT_ARGS="" RUNNERS="gl ice" bash spark/jobs/b1_features_job_v3.sh $B/panel_np250/p1_molecules.csv $RUN P_np250 2>&1 | tail -3 | cut -c1-200
$PY -X utf8 $B/b1_evaluate.py --run $RUN --eval_csv $B/panel_np250/p1_molecules.csv --sets P_np250 > $RUN/evaluate.log 2>&1; echo "evaluate exit $?"
grep -a "^## \|^| prior |\|^| fp |\|^| lib |\|^| S(2,1,0.5) |\|^| S(2,1,1) |\|^| S(2,1,2) |\|^| S(2,1,4) |\|^| S(2,0,0.5) |\|^| S(2,0,1) |\|^| S(2,0,2) |\|libpri(tau=0.9,m=0.2)\|libpri(tau=0.8,m=0.2)\|^C1 diagnostics" $RUN/results/b1_results.md | cut -c1-200
echo "== $(date +%T) learned model rank_v2 on the panel (official scorer; C2 = identity hidden, C1 = cross-library references)"
$PY -X utf8 $B/b1_locked_eval.py --eval_csv $B/panel_np250/p1_molecules.csv --sets P_np250 --cands M1:$RUN:$B/rank_v2/lambdarank.txt:1 --tau 0.9 --margin 0.2 --min_gl_cover 0.5 --out $RUN/learned_eval 2>&1 | grep -v Warning | grep -a "^| P_np250\|VALIDATION\|REFUSED\|saved" | cut -c1-200
echo "PANEL_DONE $(date +%T)"
