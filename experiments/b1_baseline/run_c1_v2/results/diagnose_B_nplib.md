# B1 failure diagnostic: experiments/b1_baseline/run_c1_v2 / B_nplib

## B_nplib (N=300; GL ok; ICE missing)

### Class-2 funnel (strict: unreachable = 0)

| stage | molecules | share of N | MRR mass lost here (of N) |
|---|---:|---:|---:|
| truth in B1 window | 270 | 90% |  |
| reachable via PubChem/COCONUT (strict denominator) | 249 | 83% | 0.170 (unreachable) |
| truth in class-2 shortlist | 216 | 72% | 0.110 (not shortlisted) |
| rank 1 under S(2,1,0.5) | 96 | 32% |  |
| rank 2-5 | 73 | 24% | 0.150 |
| rank 6-25 | 41 | 14% | 0.123 |
| rank > 25 | 6 | 2% | 0.020 |

strict MRR@25 = 0.515 over 249 reachable; all-N MRR (unreachable counted 0) = 0.427; top-1 (reachable) = 0.386

### Where each component ranks the truth (reachable, truth in shortlist)

| component | n | truth top-1 | top-5 | top-25 | median rank |
|---|---:|---:|---:|---:|---:|
| fp | 216 | 14% | 33% | 67% | 10 |
| gl | 215 | 33% | 64% | 87% | 3 |
| pop | 216 | 15% | 34% | 55% | 17 |
| S | 216 | 44% | 78% | 97% | 2 |

oracle 'pick the right component per molecule' top-1 = 50% vs S top-1 44%; truth in S top-5 = 78% (rerank ceiling), top-25 = 97%; median shortlist size 117, median candidates with the truth's formula 96

### When S is wrong: which term pushes the winner above the truth

| blamed term | errors | share | mean push (score units) | winner is a library structure | winner in COCONUT | truth in COCONUT | winner Tanimoto to truth (median) | winner Tanimoto >= 0.7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fp | 38 | 32% | 1.75 | 26% | 13% | 21% | 0.37 | 13% |
| gl | 47 | 39% | 4.28 | 19% | 28% | 47% | 0.24 | 4% |
| pop | 35 | 29% | 2.59 | 69% | 60% | 51% | 0.41 | 11% |

all errors: 120; winner has the truth's formula in 89%; winner pop > truth pop in 62%; max Tanimoto of the S top-5 to the truth: median 0.48

mean push per term over all errors (positive = hurts the truth): fp +0.68, gl +1.56, pop +0.53

### Strict MRR by stratum

| stratum | value | n (reachable) | strict MRR | top-1 |
|---|---|---:|---:|---:|
| group | eval | 81 | 0.465 | 0.346 |
| group | fit | 86 | 0.559 | 0.419 |
| group | tune | 82 | 0.518 | 0.390 |
| lib | gnps | 207 | 0.536 | 0.401 |
| lib | massbank | 9 | 0.552 | 0.444 |
| lib | mona | 20 | 0.520 | 0.400 |
| lib | msdial | 10 | 0.182 | 0.100 |
| n_adducts | 1.0 | 186 | 0.516 | 0.387 |
| n_adducts | 2.0 | 31 | 0.444 | 0.323 |
| n_adducts | 3.0 | 15 | 0.553 | 0.467 |
| n_adducts | 5.0 | 9 | 0.593 | 0.444 |
| n_query | 1 | 113 | 0.512 | 0.372 |
| n_query | 2-3 | 71 | 0.497 | 0.394 |
| n_query | 4-10 | 65 | 0.540 | 0.400 |
| window size (unique structures) | (1.999, 3163.0] | 63 | 0.554 | 0.444 |
| window size (unique structures) | (3163.0, 7199.0] | 62 | 0.524 | 0.387 |
| window size (unique structures) | (7199.0, 12256.0] | 62 | 0.510 | 0.403 |
| window size (unique structures) | (12256.0, 34481.0] | 62 | 0.472 | 0.306 |

### Class-1 view (257 usable molecules; truth in shortlist 257)

best library match is the truth: 86%; S(2,1,0.5) top-1: 40%; libpri(0.8,0.2) fires in 46% and is top-1 in 64%; MRR lib-only 0.888, S 0.545, libpri 0.729

| truth library similarity | n | lib top-1 | S top-1 | libpri top-1 |
|---|---:|---:|---:|---:|
| <0.4 | 33 | 33% | 45% | 45% |
| 0.4-0.6 | 35 | 80% | 40% | 40% |
| 0.6-0.8 | 49 | 92% | 37% | 37% |
| 0.8-0.9 | 55 | 96% | 35% | 87% |
| >=0.9 | 85 | 98% | 45% | 82% |

false-confident library hits (lib max >= 0.8 but the best match is not the truth): 11 of 147 confident cases; of these, margin >= 0.2: 1; winner Tanimoto to truth median 0.40; winner is itself a library structure: 100%

