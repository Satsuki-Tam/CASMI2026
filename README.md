# CASMI 2026 (Enveda) — Molecule ID from Mass Spectra

Kaggle: https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra
Goal: gold zone (Public LB >= 0.480, ideally >= 0.500). Metric: MRR@25 on the official identity (RemoveStereo -> tautomer-canonical InChIKey14).

**Live dashboard**: open `site/index.html` (auto-refreshes). Research, experiments, Codex reviews and submissions have their own pages under `site/`.

## Layout

| path | content |
|---|---|
| `src/` | shared tools: official scorer replica (`metric.py`), metadata builders, Kaggle API fetchers, notebook patcher |
| `experiments/<id>/` | one directory per experiment: scripts, results (md/json/csv). Large intermediates are not committed (see `.gitignore`) |
| `kernels/<name>/` | Kaggle notebooks that were pushed/submitted, with their generator scripts and patch notes |
| `docs/` | competition overview, progress reports, design documents, official pages and all discussion threads |
| `reports/`, `research_notes/` | research on similar competitions / benchmarks / papers; `reports/agent_review/` = Codex review loop (request / answer / decision) |
| `site/` | static HTML dashboard (`build_site.py` renders it from the docs and the event log) |

## Experiment index (code -> result)

| id | question | code | results | status |
|---|---|---|---|---|
| E0 | reproduce the public lineage faithfully (measurement baseline) | `kernels/baseline-v18/` | Public LB **0.464** (submission 57567821) | done |
| E1 | does the public class-2 performance depend on the documentation prior? (panel replay) | `experiments/e1_panel/e1_panel_replay.py` | `experiments/e1_panel/e1_results.json` | done |
| E2 / E2b | forward models (ICEBERG/GLACIER) vs fingerprint model on unseen molecules (formula known) | `experiments/e2_forward/e2b_prepare_v2.py`, `e2b_fpnet_score.py`, `e2b_evaluate_v2.py` | `experiments/e2_forward/v2/results_*.json` | done |
| E2c | label-free funnel (window -> FP -> forward models) | `experiments/e2_forward/e2c_funnel.py`, `e2c_evaluate.py` | `experiments/e2_forward/funnel/` | done (superseded by P1) |
| P1 | frozen unused molecules; label-free retrieval -> official scoring; stage recall; public rule vs global fusion | `experiments/p1_baseline/` | `experiments/p1_baseline/run1/results_final/`, `docs/p1_baseline_2026-10-24.md` | done |
| E4 | one-off measurement: does the P1 finding transfer to the LB? (public notebook + 4 replacements) | `kernels/e4-pclist/make_e4.py` | `kernels/e4-pclist/PATCH_NOTES.md`; LB pending (v5) | submitted |
| B1 | own baseline: unified candidate table, library similarity, FPNet, GL/ICE, fixed fusion -> LambdaRank | `experiments/b1_baseline/`, `kernels/b1-baseline/` | `docs/b1_baseline_design.md`; results pending | running |

Codex review loop: `reports/agent_review/00N_{request,codex,decision}.md`.
