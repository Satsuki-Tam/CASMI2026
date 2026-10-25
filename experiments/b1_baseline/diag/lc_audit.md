# Per-condition library support: pre-training audit (Codex 030)

runs: ['experiments/b1_baseline/run_panel_fe_lc:P_np250', 'experiments/b1_baseline/run_p2dev_fe_lc:C_np_crosslib,D_np_single,E_np_negonly,F_np_uncovered,G_tims_crosslib']

## standard tables (training / evaluation masks)

### view C1: shortlist rows 166,639 | with references 6,048 | lib_sup2 observed 4,170 | molecules with any observed 432 of 747 | truth rows with references 532 (observed 378)

matched comparison (rows with references and >= 2 conditions): lib_sup2 by max-similarity bin x condition count x truth

```
                                 count  median   mean
sim_bin      ncond_bin is_truth                      
[0.0, 0.5)   2         False      1195   0.111  0.130
                       True          5   0.353  0.323
             3+        False      1913   0.172  0.179
                       True          2   0.174  0.174
[0.5, 0.7)   2         False       127   0.341  0.316
                       True         13   0.381  0.368
             3+        False       324   0.491  0.465
                       True         29   0.575  0.543
[0.7, 0.85)  2         False        55   0.566  0.469
                       True         45   0.655  0.556
             3+        False       118   0.693  0.670
                       True        118   0.739  0.701
[0.85, 1.01) 2         False        20   0.847  0.655
                       True         58   0.765  0.650
             3+        False        30   0.861  0.840
                       True        108   0.851  0.829
```

best library match c_L per molecule (687 molecules): P(c_L is the truth) by max similarity x gap to the second condition

```
                            count  P(c_L is truth)
sim_bin      sup_bin                              
[0.0, 0.5)   [-0.01, 0.05)     13            0.000
             [0.05, 0.15)      10            0.100
             [0.15, 1.01)       5            0.000
             unobserved       107            0.131
[0.5, 0.7)   [-0.01, 0.05)     16            0.875
             [0.05, 0.15)      11            0.909
             [0.15, 1.01)      15            0.600
             unobserved        32            0.500
[0.7, 0.85)  [-0.01, 0.05)     57            0.895
             [0.05, 0.15)      65            0.831
             [0.15, 1.01)      43            0.814
             unobserved        56            0.732
[0.85, 1.01) [-0.01, 0.05)     83            0.819
             [0.05, 0.15)      60            0.883
             [0.15, 1.01)      40            0.850
             unobserved        74            0.932
```

### view C2: shortlist rows 166,681 | with references 5,570 | lib_sup2 observed 3,842 | molecules with any observed 401 of 747 | truth rows with references 0 (observed 0)

best library match c_L per molecule (638 molecules): P(c_L is the truth) by max similarity x gap to the second condition

```
                            count  P(c_L is truth)
sim_bin      sup_bin                              
[0.0, 0.5)   [-0.01, 0.05)     89              0.0
             [0.05, 0.15)      59              0.0
             [0.15, 1.01)      41              0.0
             unobserved       176              0.0
[0.5, 0.7)   [-0.01, 0.05)     23              0.0
             [0.05, 0.15)      26              0.0
             [0.15, 1.01)      35              0.0
             unobserved        39              0.0
[0.7, 0.85)  [-0.01, 0.05)     26              0.0
             [0.05, 0.15)      27              0.0
             [0.15, 1.01)      24              0.0
             unobserved        28              0.0
[0.85, 1.01) [-0.01, 0.05)     21              0.0
             [0.05, 0.15)       8              0.0
             [0.15, 1.01)       7              0.0
             unobserved         9              0.0
```

## symmetric-mask diagnostic (query library removed for every candidate in the C1 view)

### view C1: shortlist rows 102,291 | with references 3,586 | lib_sup2 observed 2,807 | molecules with any observed 378 of 448 | truth rows with references 441 (observed 359)

matched comparison (rows with references and >= 2 conditions): lib_sup2 by max-similarity bin x condition count x truth

```
                                 count  median   mean
sim_bin      ncond_bin is_truth                      
[0.0, 0.5)   2         False       690   0.079  0.114
                       True          5   0.353  0.323
             3+        False      1340   0.157  0.167
                       True          1   0.347  0.347
[0.5, 0.7)   2         False        87   0.335  0.319
                       True         11   0.383  0.435
             3+        False       197   0.504  0.495
                       True         28   0.563  0.541
[0.7, 0.85)  2         False        32   0.623  0.540
                       True         43   0.655  0.551
             3+        False        81   0.698  0.680
                       True        117   0.738  0.700
[0.85, 1.01) 2         False         5   0.828  0.607
                       True         52   0.765  0.659
             3+        False        11   0.819  0.761
                       True        102   0.848  0.823
```

best library match c_L per molecule (447 molecules): P(c_L is the truth) by max similarity x gap to the second condition

```
                            count  P(c_L is truth)
sim_bin      sup_bin                              
[0.0, 0.5)   [-0.01, 0.05)      7            0.143
             [0.05, 0.15)       1            1.000
             unobserved        12            0.583
[0.5, 0.7)   [-0.01, 0.05)     16            0.875
             [0.05, 0.15)      13            0.923
             [0.15, 1.01)       9            0.889
             unobserved        13            0.923
[0.7, 0.85)  [-0.01, 0.05)     60            0.917
             [0.05, 0.15)      64            0.875
             [0.15, 1.01)      38            0.921
             unobserved        24            0.875
[0.85, 1.01) [-0.01, 0.05)     67            0.970
             [0.05, 0.15)      54            0.926
             [0.15, 1.01)      38            0.921
             unobserved        31            0.968
```

### view C2: shortlist rows 102,304 | with references 3,163 | lib_sup2 observed 2,463 | molecules with any observed 341 of 448 | truth rows with references 0 (observed 0)

best library match c_L per molecule (409 molecules): P(c_L is the truth) by max similarity x gap to the second condition

```
                            count  P(c_L is truth)
sim_bin      sup_bin                              
[0.0, 0.5)   [-0.01, 0.05)    106              0.0
             [0.05, 0.15)      57              0.0
             [0.15, 1.01)      37              0.0
             unobserved        52              0.0
[0.5, 0.7)   [-0.01, 0.05)     22              0.0
             [0.05, 0.15)      18              0.0
             [0.15, 1.01)      21              0.0
             unobserved        14              0.0
[0.7, 0.85)  [-0.01, 0.05)     22              0.0
             [0.05, 0.15)      18              0.0
             [0.15, 1.01)      13              0.0
             unobserved        12              0.0
[0.85, 1.01) [-0.01, 0.05)      5              0.0
             [0.05, 0.15)       5              0.0
             [0.15, 1.01)       4              0.0
             unobserved         3              0.0
```
