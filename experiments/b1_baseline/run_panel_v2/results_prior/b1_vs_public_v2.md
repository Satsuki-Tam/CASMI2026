# B1 vs public pipeline on the panel (experiments/b1_baseline/run_panel_v2, P_np250)

## view c2 (public scenario 'structure_in_pool_no_reference'; 250 molecules with a public main list)

| system | MRR@25 | top-1 |
|---|---:|---:|
| public main list | 0.971 | 0.952 |
| B1 fixed S(2,1,0.5) | 0.864 | 0.804 |
| B1 learned (rank_v2) | 0.900 | 0.848 |
| B1 insurance (libpri 0.9) | 0.860 | 0.796 |

### public top-1 but B1 learned not top-1: 36 molecules (reverse: 10)

| B1 stage where the truth is lost | molecules |
|---|---:|
| rank 2-5 | 27 |
| rank 6-25 | 6 |
| rank > 25 | 3 |

public lib_max for these (median): 0.680; B1 learned RR mean 0.345

### public top-1 but B1 fixed not top-1: 45 molecules (reverse: 8)

| B1 stage where the truth is lost | molecules |
|---|---:|
| rank 2-5 | 31 |
| rank 6-25 | 13 |
| rank > 25 | 1 |

public lib_max for these (median): 0.760; B1 fixed RR mean 0.303

paired mean ΔRR (B1 learned − public): -0.0710 | (B1 fixed − public): -0.1067

## view c1 (public scenario 'reference_in_other_libraries'; 250 molecules with a public main list)

| system | MRR@25 | top-1 |
|---|---:|---:|
| public main list | 0.955 | 0.924 |
| B1 fixed S(2,1,0.5) | 0.864 | 0.804 |
| B1 learned (rank_v2) | 0.600 | 0.428 |
| B1 insurance (libpri 0.9) | 0.867 | 0.808 |

### public top-1 but B1 learned not top-1: 132 molecules (reverse: 8)

| B1 stage where the truth is lost | molecules |
|---|---:|
| rank 2-5 | 97 |
| rank 6-25 | 32 |
| rank > 25 | 3 |

public lib_max for these (median): 0.870; B1 learned RR mean 0.311

### public top-1 but B1 fixed not top-1: 42 molecules (reverse: 12)

| B1 stage where the truth is lost | molecules |
|---|---:|
| rank 2-5 | 30 |
| rank 6-25 | 11 |
| rank > 25 | 1 |

public lib_max for these (median): 0.850; B1 fixed RR mean 0.315

paired mean ΔRR (B1 learned − public): -0.3553 | (B1 fixed − public): -0.0909

## prior alignment (public 'popularity' vs B1 'pop_public' on common candidates)

common candidates 9058 of 28616 public-list rows; Spearman(popularity, pop_public) = 0.957; share public popularity > 0 : 0.955; share pop_public > 0 : 0.996

