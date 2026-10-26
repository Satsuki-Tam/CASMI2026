# 050 confirmation (arm a, 053 conf NP_X, read once)

| fold | view | n | base | arm a | delta [95%] | up / down |
|---|---|---:|---:|---:|---|---|
| 1 | c1 | 3 | 0.8333 | 0.6667 | -0.1667 [-0.5000, +0.0000] | 0 / 1 |
| 1 | c2 | 60 | 0.5622 | 0.5850 | +0.0228 [-0.0619, +0.1069] | 21 / 18 |
| 2 | c1 | 14 | 0.6798 | 0.7908 | +0.1110 [-0.0577, +0.2896] | 4 / 1 |
| 2 | c2 | 60 | 0.4745 | 0.5411 | +0.0666 [-0.0041, +0.1397] | 26 / 11 |

- primary (C2, blocks equal): +0.0447 [-0.0091, +0.1003]
- C1 per fold: f1 n 3 -0.1667, f2 n 14 +0.1110
- registered verdict: FAIL (primary > 0: True; C1 >= -0.01 per fold: False)
- 049b reading of the primary aggregate (eps 0.01): non-inferior; C1 n is tiny -> protection evidence comes from the dev F C1 and the panel diagnostic
