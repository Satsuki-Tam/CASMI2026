# 095 reading: B-group specialist, B-position-preserving reorder (v7f base)

missing (stress/report only): ['panel', 'p2dev']
- **Primary 053 NP C2 (H,N) bpp - main: +0.0082 [+0.0019, +0.0149]**
- f1/f2 NP C2 (C-F): +0.0010 [-0.0018, +0.0039]
- checks: max |d| on rows whose truth is not B = 0.000000; on C1 rows = 0.000000
- **GATE to a new confirmation set: GO**

| table | view | truth-B rows | main | bpp | d (truth-B rows) | B-in-rank MRR main -> spec |
|---|---|---:|---:|---:|---:|---|
| np053f1dev | c2 | 271 | 0.5562 | 0.5671 | +0.0129 | 0.8013 -> 0.8237 |
| np053f1dev | c1 | 0 | 0.8358 | 0.8358 | +0.0000 | 0.0000 -> 0.0000 |
| np053f2dev | c2 | 280 | 0.5922 | 0.6018 | +0.0110 | 0.8373 -> 0.8449 |
| np053f2dev | c1 | 0 | 0.8761 | 0.8761 | +0.0000 | 0.0000 -> 0.0000 |
| f1dev | c2 | 132 | 0.4752 | 0.4762 | +0.0037 | 0.7427 -> 0.7421 |
| f1dev | c1 | 0 | 0.8168 | 0.8168 | +0.0000 | 0.0000 -> 0.0000 |
| f2dev | c2 | 111 | 0.4892 | 0.4898 | +0.0027 | 0.7535 -> 0.7721 |
| f2dev | c1 | 0 | 0.8239 | 0.8239 | +0.0000 | 0.0000 -> 0.0000 |
