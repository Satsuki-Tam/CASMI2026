# B1 vs public pipeline on the panel (experiments/b1_baseline/run_panel_v2, P_np250)

## view c2 (public scenario 'structure_in_pool_no_reference'; 234 molecules with a public main list)

| system | MRR@25 | top-1 |
|---|---:|---:|
| public main list | 0.976 | 0.962 |
| B1 fixed S(2,1,0.5) | 0.881 | 0.825 |
| B1 learned (rank_v2) | 0.914 | 0.863 |
| B1 insurance (libpri 0.9) | 0.877 | 0.816 |

### public top-1 but B1 learned not top-1: 31 molecules (reverse: 8)

| B1 stage where the truth is lost | molecules |
|---|---:|
| rank 2-5 | 26 |
| rank 6-25 | 4 |
| rank > 25 | 1 |

public lib_max for these (median): 0.760; B1 learned RR mean 0.378

### public top-1 but B1 fixed not top-1: 38 molecules (reverse: 6)

| B1 stage where the truth is lost | molecules |
|---|---:|
| rank 2-5 | 27 |
| rank 6-25 | 11 |

public lib_max for these (median): 0.778; B1 fixed RR mean 0.321

paired mean ΔRR (B1 learned − public): -0.0623 | (B1 fixed − public): -0.0951

## view c1 (public scenario 'reference_in_other_libraries'; 234 molecules with a public main list)

| system | MRR@25 | top-1 |
|---|---:|---:|
| public main list | 0.964 | 0.940 |
| B1 fixed S(2,1,0.5) | 0.881 | 0.825 |
| B1 learned (rank_v2) | 0.605 | 0.432 |
| B1 insurance (libpri 0.9) | 0.881 | 0.825 |

### public top-1 but B1 learned not top-1: 126 molecules (reverse: 7)

| B1 stage where the truth is lost | molecules |
|---|---:|
| rank 2-5 | 94 |
| rank 6-25 | 29 |
| rank > 25 | 3 |

public lib_max for these (median): 0.870; B1 learned RR mean 0.314

### public top-1 but B1 fixed not top-1: 37 molecules (reverse: 10)

| B1 stage where the truth is lost | molecules |
|---|---:|
| rank 2-5 | 27 |
| rank 6-25 | 9 |
| rank > 25 | 1 |

public lib_max for these (median): 0.843; B1 fixed RR mean 0.332

paired mean ΔRR (B1 learned − public): -0.3593 | (B1 fixed − public): -0.0832

## prior alignment (public 'popularity' vs B1 'pop_public' on common candidates)

common candidates 8525 of 28616 public-list rows; Spearman(popularity, pop_public) = 0.960; share public popularity > 0 : 0.955; share pop_public > 0 : 0.996

