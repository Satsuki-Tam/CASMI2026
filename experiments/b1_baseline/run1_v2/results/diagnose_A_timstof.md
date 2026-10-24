# B1 failure diagnostic: experiments/b1_baseline/run1_v2 / A_timstof

## A_timstof (N=300; GL ok; ICE ok)

### Class-2 funnel (strict: unreachable = 0)

| stage | molecules | share of N | MRR mass lost here (of N) |
|---|---:|---:|---:|
| truth in B1 window | 300 | 100% |  |
| reachable via PubChem/COCONUT (strict denominator) | 287 | 96% | 0.043 (unreachable) |
| truth in class-2 shortlist | 275 | 92% | 0.040 (not shortlisted) |
| rank 1 under S(2,1,0.5) | 166 | 55% |  |
| rank 2-5 | 78 | 26% | 0.153 |
| rank 6-25 | 28 | 9% | 0.082 |
| rank > 25 | 3 | 1% | 0.010 |

strict MRR@25 = 0.702 over 287 reachable; all-N MRR (unreachable counted 0) = 0.671; top-1 (reachable) = 0.578

### Where each component ranks the truth (reachable, truth in shortlist)

| component | n | truth top-1 | top-5 | top-25 | median rank |
|---|---:|---:|---:|---:|---:|
| fp | 275 | 37% | 73% | 93% | 2 |
| gl | 275 | 47% | 82% | 98% | 2 |
| ice | 275 | 41% | 72% | 96% | 2 |
| pop | 275 | 0% | 3% | 21% | 49 |
| S | 275 | 60% | 89% | 99% | 1 |

oracle 'pick the right component per molecule' top-1 = 70% vs S top-1 60%; truth in S top-5 = 89% (rerank ceiling), top-25 = 99%; median shortlist size 124, median candidates with the truth's formula 110

### When S is wrong: which term pushes the winner above the truth

| blamed term | errors | share | mean push (score units) | winner is a library structure | winner in COCONUT | truth in COCONUT | winner Tanimoto to truth (median) | winner Tanimoto >= 0.7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fp | 22 | 20% | 1.12 | 45% | 0% | 0% | 0.60 | 18% |
| gl | 45 | 41% | 2.01 | 16% | 0% | 0% | 0.40 | 4% |
| ice | 30 | 28% | 0.93 | 23% | 0% | 0% | 0.48 | 17% |
| pop | 12 | 11% | 1.00 | 25% | 0% | 0% | 0.35 | 0% |

all errors: 109; winner has the truth's formula in 98%; winner pop > truth pop in 49%; max Tanimoto of the S top-5 to the truth: median 0.61

mean push per term over all errors (positive = hurts the truth): fp -0.05, gl +0.98, ice +0.40, pop +0.13

### Strict MRR by stratum

| stratum | value | n (reachable) | strict MRR | top-1 |
|---|---|---:|---:|---:|
| group | eval | 95 | 0.656 | 0.516 |
| group | fit | 96 | 0.725 | 0.615 |
| group | tune | 96 | 0.724 | 0.604 |
| lib | enveda-180 | 287 | 0.702 | 0.578 |
| n_adducts | 1 | 183 | 0.714 | 0.596 |
| n_adducts | 2 | 93 | 0.706 | 0.581 |
| n_adducts | 3 | 11 | 0.458 | 0.273 |
| n_query | 2-3 | 85 | 0.726 | 0.588 |
| n_query | 4-10 | 201 | 0.689 | 0.572 |
| window size (unique structures) | (713.999, 7426.5] | 72 | 0.747 | 0.611 |
| window size (unique structures) | (7426.5, 10405.0] | 72 | 0.736 | 0.611 |
| window size (unique structures) | (10405.0, 14211.0] | 71 | 0.701 | 0.606 |
| window size (unique structures) | (14211.0, 40296.0] | 72 | 0.622 | 0.486 |

### Class-1 view (7 usable molecules; truth in shortlist 7)

best library match is the truth: 71%; S(2,1,0.5) top-1: 43%; libpri(0.8,0.2) fires in 43% and is top-1 in 71%; MRR lib-only 0.821, S 0.590, libpri 0.793

| truth library similarity | n | lib top-1 | S top-1 | libpri top-1 |
|---|---:|---:|---:|---:|
| <0.4 | 1 | 0% | 100% | 100% |
| 0.4-0.6 | 1 | 0% | 0% | 0% |
| 0.6-0.8 | 2 | 100% | 50% | 50% |
| 0.8-0.9 | 3 | 100% | 33% | 100% |

false-confident library hits (lib max >= 0.8 but the best match is not the truth): 0 of 3 confident cases; of these, margin >= 0.2: 0; winner Tanimoto to truth median nan; winner is itself a library structure: -

