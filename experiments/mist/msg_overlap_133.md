# MSG exposure of the ranker-training and development identities (Codex 131 Q2, counts only)

```
{
 "msg_spectra": 231104,
 "msg_smiles": 31602,
 "msg_smiles_unparsed": 0,
 "msg_official_keys": 28895,
 "msg_keys_by_fold": {
  "train": 22724,
  "val": 3179,
  "test": 2992
 }
}
```

## training runs: unique identities (official key) by group and exposure

| group | identities | msg_train_or_val | msg_test_only | not_in_msg | kept (not train/val) share |
|---|---:|---:|---:|---:|---:|
| eval | 300 | 0 | 0 | 300 | 1.000 |
| fit | 2900 | 0 | 0 | 2900 | 1.000 |
| tune | 300 | 0 | 0 | 300 | 1.000 |

## fit identities by polarity / reference condition / library and exposure

| stratum | value | identities | msg_train_or_val | kept |
|---|---|---:|---:|---:|
| polarity | both | 624 | 0 | 624 |
| polarity | negative | 438 | 0 | 438 |
| polarity | positive | 1818 | 0 | 1818 |
| polarity | unknown | 20 | 0 | 20 |
| c1_usable | False | 1499 | 0 | 1499 |
| c1_usable | True | 1401 | 0 | 1401 |
| lib | enveda-180 | 800 | 0 | 800 |
| lib | gnps | 1576 | 0 | 1576 |
| lib | massbank | 116 | 0 | 116 |
| lib | mona | 143 | 0 | 143 |
| lib | msdial | 126 | 0 | 126 |
| lib | riken | 139 | 0 | 139 |

## development tables: identities by exposure

| table | set | identities | msg_train_or_val | msg_test_only | not_in_msg | unresolved key | positive-capable (pos/both) |
|---|---|---:|---:|---:|---:|---:|---:|
| c1bankdev | C1_neg_few | 52 | 0 | 0 | 52 | 0 | 0 |
| c1bankdev | C1_neg_many | 13 | 0 | 0 | 13 | 0 | 0 |
| c1bankdev | C1_pos_few | 366 | 0 | 0 | 366 | 0 | 358 |
| c1bankdev | C1_pos_many | 1 | 0 | 0 | 1 | 0 | 1 |
| c1conf | C1_neg_few | 51 | 0 | 0 | 51 | 0 | 0 |
| c1conf | C1_neg_many | 12 | 0 | 0 | 12 | 0 | 0 |
| c1conf | C1_pos_few | 365 | 0 | 0 | 365 | 0 | 364 |
| c1conf | C1_pos_many | 1 | 0 | 0 | 1 | 0 | 1 |
| f1dev | C_np_crosslib | 100 | 0 | 0 | 100 | 0 | 98 |
| f1dev | D_np_single | 100 | 0 | 0 | 100 | 0 | 100 |
| f1dev | E_np_negonly | 100 | 0 | 0 | 100 | 0 | 1 |
| f1dev | F_np_uncovered | 100 | 0 | 0 | 100 | 0 | 98 |
| f1dev | G_tims_crosslib | 100 | 0 | 0 | 100 | 0 | 92 |
| f2dev | C_np_crosslib | 100 | 0 | 0 | 100 | 0 | 99 |
| f2dev | D_np_single | 100 | 0 | 0 | 100 | 0 | 99 |
| f2dev | E_np_negonly | 100 | 0 | 0 | 100 | 0 | 3 |
| f2dev | F_np_uncovered | 100 | 0 | 0 | 100 | 0 | 94 |
| f2dev | G_tims_crosslib | 100 | 0 | 0 | 100 | 0 | 96 |
| np053f1dev | NP_H | 200 | 0 | 0 | 200 | 0 | 199 |
| np053f1dev | NP_N | 60 | 0 | 0 | 60 | 0 | 1 |
| np053f1dev | NP_X | 60 | 0 | 0 | 60 | 0 | 60 |
| np053f2dev | NP_H | 200 | 0 | 0 | 200 | 0 | 197 |
| np053f2dev | NP_N | 60 | 0 | 0 | 60 | 0 | 0 |
| np053f2dev | NP_X | 60 | 0 | 0 | 60 | 0 | 58 |
| np096_conf093 | NP_H | 200 | 0 | 0 | 200 | 0 | 199 |
| np096_conf093 | NP_N | 200 | 0 | 0 | 200 | 0 | 0 |
| np102_d0conf | D_np_single | 286 | 0 | 0 | 286 | 0 | 284 |
| panel | P_np250 | 250 | 226 | 10 | 14 | 0 | 232 |

raw IK14 vs official-key agreement on the MSG membership (train runs): 1.0000
