# B1 failure diagnostic: experiments/b1_baseline/run1_v2 / B_nplib

## B_nplib (N=300; GL ok; ICE missing)

### Class-2 funnel (strict: unreachable = 0)

| stage | molecules | share of N | MRR mass lost here (of N) |
|---|---:|---:|---:|
| truth in B1 window | 277 | 92% |  |
| reachable via PubChem/COCONUT (strict denominator) | 177 | 59% | 0.410 (unreachable) |
| truth in class-2 shortlist | 159 | 53% | 0.060 (not shortlisted) |
| rank 1 under S(2,1,0.5) | 100 | 33% |  |
| rank 2-5 | 32 | 11% | 0.069 |
| rank 6-25 | 21 | 7% | 0.064 |
| rank > 25 | 6 | 2% | 0.020 |

strict MRR@25 = 0.639 over 177 reachable; all-N MRR (unreachable counted 0) = 0.377; top-1 (reachable) = 0.565

### Where each component ranks the truth (reachable, truth in shortlist)

| component | n | truth top-1 | top-5 | top-25 | median rank |
|---|---:|---:|---:|---:|---:|
| fp | 159 | 15% | 38% | 67% | 9 |
| gl | 159 | 39% | 69% | 82% | 2 |
| pop | 159 | 21% | 45% | 72% | 8 |
| S | 159 | 63% | 83% | 96% | 1 |

oracle 'pick the right component per molecule' top-1 = 58% vs S top-1 63%; truth in S top-5 = 83% (rerank ceiling), top-25 = 96%; median shortlist size 117, median candidates with the truth's formula 93

### When S is wrong: which term pushes the winner above the truth

| blamed term | errors | share | mean push (score units) | winner is a library structure | winner in COCONUT | truth in COCONUT | winner Tanimoto to truth (median) | winner Tanimoto >= 0.7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fp | 17 | 29% | 1.36 | 24% | 12% | 12% | 0.39 | 12% |
| gl | 22 | 37% | 4.77 | 27% | 23% | 45% | 0.23 | 0% |
| pop | 20 | 34% | 4.23 | 80% | 70% | 50% | 0.31 | 5% |

all errors: 59; winner has the truth's formula in 85%; winner pop > truth pop in 61%; max Tanimoto of the S top-5 to the truth: median 0.48

mean push per term over all errors (positive = hurts the truth): fp +0.58, gl +1.52, pop +1.15

### Strict MRR by stratum

| stratum | value | n (reachable) | strict MRR | top-1 |
|---|---|---:|---:|---:|
| group | eval | 54 | 0.654 | 0.593 |
| group | fit | 65 | 0.580 | 0.508 |
| group | tune | 58 | 0.692 | 0.603 |
| lib | gnps | 156 | 0.651 | 0.583 |
| lib | massbank | 9 | 0.713 | 0.556 |
| lib | msdial | 8 | 0.355 | 0.250 |
| n_adducts | 1.0 | 111 | 0.615 | 0.532 |
| n_adducts | 2.0 | 47 | 0.706 | 0.638 |
| n_adducts | 3.0 | 8 | 0.633 | 0.625 |
| n_adducts | 4.0 | 5 | 0.809 | 0.800 |
| n_query | 1 | 64 | 0.559 | 0.469 |
| n_query | 2-3 | 65 | 0.669 | 0.600 |
| n_query | 4-10 | 48 | 0.705 | 0.646 |
| window size (unique structures) | (1.999, 2658.0] | 45 | 0.718 | 0.644 |
| window size (unique structures) | (2658.0, 5638.0] | 44 | 0.606 | 0.545 |
| window size (unique structures) | (5638.0, 10895.0] | 44 | 0.627 | 0.545 |
| window size (unique structures) | (10895.0, 30452.0] | 44 | 0.602 | 0.523 |

### Class-1 view (72 usable molecules; truth in shortlist 71)

best library match is the truth: 89%; S(2,1,0.5) top-1: 48%; libpri(0.8,0.2) fires in 61% and is top-1 in 77%; MRR lib-only 0.913, S 0.581, libpri 0.800

| truth library similarity | n | lib top-1 | S top-1 | libpri top-1 |
|---|---:|---:|---:|---:|
| <0.4 | 7 | 43% | 57% | 57% |
| 0.4-0.6 | 5 | 60% | 40% | 40% |
| 0.6-0.8 | 6 | 100% | 50% | 50% |
| 0.8-0.9 | 20 | 95% | 55% | 90% |
| >=0.9 | 33 | 97% | 42% | 85% |

false-confident library hits (lib max >= 0.8 but the best match is not the truth): 2 of 53 confident cases; of these, margin >= 0.2: 0; winner Tanimoto to truth median 0.36; winner is itself a library structure: 100%

