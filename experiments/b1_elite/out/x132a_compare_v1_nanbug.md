# 132 parity (A): shared E-lite function inside the 102 evaluator vs the stored 102 results

**PARITY_A FAIL: np053f1dev: unique True, key sets equal True, differing columns {'e_reach': 1}, assertion counts {'c1': 52, 'c2': 319} vs rows with candidates {'c1': 52, 'c2': 319}; np053f2dev: unique True, key sets equal True, differing columns {'e_reach': 6}, assertion counts {'c1': 69, 'c2': 314} vs rows with candidates {'c1': 69, 'c2': 314}; f1dev: unique True, key sets equal True, differing columns {'e_reach': 6}, assertion counts {'c1': 294, 'c2': 494} vs rows with candidates {'c1': 294, 'c2': 494}; f2dev: unique True, key sets equal True, differing columns {'e_reach': 7}, assertion counts {'c1': 295, 'c2': 493} vs rows with candidates {'c1': 295, 'c2': 493}; p2dev: unique True, key sets equal True, differing columns {'e_reach': 3}, assertion counts {'c1': 292, 'c2': 497} vs rows with candidates {'c1': 292, 'c2': 497}**


| table | rows | key sets equal | columns equal | assertion count c1 / c2 (= rows with candidates) | E empty | truth outside E | negative only | strong C1 ref (c1) | GL fallback (c1 / c2) |
|---|---:|---|---|---|---:|---:|---:|---:|---|
| np053f1dev | 372 | True | {'e_reach': 1} | 52 / 319 (= 52 / 319) | 3 | 0 | 74 | 24 | 16 / 120 |
| np053f2dev | 389 | True | {'e_reach': 6} | 69 / 314 (= 69 / 314) | 2 | 0 | 81 | 31 | 29 / 119 |
| panel | 500 | True | all | 250 / 250 (= 250 / 250) | 0 | 0 | 36 | 30 | 34 / 34 |
| f1dev | 794 | True | {'e_reach': 6} | 294 / 494 (= 294 / 494) | 6 | 191 | 178 | 101 | 115 / 210 |
| f2dev | 795 | True | {'e_reach': 7} | 295 / 493 (= 295 / 493) | 5 | 210 | 169 | 103 | 107 / 204 |
| p2dev | 792 | True | {'e_reach': 3} | 292 / 497 (= 292 / 497) | 8 | 194 | 176 | 111 | 105 / 208 |
