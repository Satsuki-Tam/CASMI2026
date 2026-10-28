# 106 GL-summary pilot (exploratory; fixed before the run)

| layer | rows (GL covered) | GL-alone gl_mean | GL-alone GL2 | GL2 - gl_mean | rescued / lost | main | main+0.5 z(net) - main | rescued / lost |
|---|---|---:|---:|---|---|---:|---|---|
| C2 NP_H/NP_N (053) | 120 (79) | 0.3872 | 0.3726 | -0.0146 [-0.0375, +0.0019] | 5 / 8 | 0.5693 | -0.0231 [-0.0464, -0.0049] | 3 / 13 |
| C2 C/D (f1/f2) | 120 (118) | 0.2927 | 0.2824 | -0.0102 [-0.0362, +0.0142] | 11 / 12 | 0.4424 | -0.0244 [-0.0467, -0.0034] | 3 / 14 |
| C1 G (f1/f2) | 60 (54) | 0.6771 | 0.7004 | +0.0233 [+0.0014, +0.0507] | 8 / 3 | 0.8482 | -0.0181 [-0.0486, +0.0028] | 1 / 2 |
| C1 panel | 40 (35) | 0.5504 | 0.5363 | -0.0141 [-0.0775, +0.0501] | 6 / 9 | 0.9388 | -0.0374 [-0.0873, +0.0001] | 1 / 3 |

GLACIER rerun vs the stored GL JSON (batch-composition noise; the detail reproduces the rerun exactly):

| input | candidates | share diff > 1e-6 | p99 | max |
|---|---:|---:|---:|---:|
| f1dev C_np_crosslib | 6220 | 0.029 | 0.00066 | 0.00794 |
| f1dev D_np_single | 6656 | 0.025 | 0.00034 | 0.01716 |
| f1dev G_tims_crosslib | 6342 | 0.026 | 0.00055 | 0.01186 |
| f2dev C_np_crosslib | 6658 | 0.036 | 0.00033 | 0.01331 |
| f2dev D_np_single | 6857 | 0.025 | 0.00029 | 0.02128 |
| f2dev G_tims_crosslib | 7344 | 0.029 | 0.00039 | 0.00549 |
| np053f1dev NP_H | 8952 | 0.033 | 0.00060 | 0.01224 |
| np053f1dev NP_N | 0 (no covered spectrum) | - | - | - |
| np053f2dev NP_H | 8046 | 0.031 | 0.00045 | 0.00657 |
| np053f2dev NP_N | 0 (no covered spectrum) | - | - | - |
| panel P_np250 | 7953 | 0.040 | 0.00064 | 0.02791 |
