# 099 transductive generation on the fold-safe panel (exploratory)

- parent quality: c2-view rank-1 correct for 0.852 of 250 molecules

| run | c3 n | c3 gt3 MRR | c3 truth generated (novel) | c2 main | c2 gt3 - main | c1 gt3 - main |
|---|---:|---:|---:|---:|---:|---:|
| A | 250 | 0.0253 | 0.156 | 0.9037 | -0.0001 | -0.0005 |
| B | 250 | 0.0413 | 0.288 | 0.9037 | -0.0014 | -0.0018 |
| C | 250 | 0.0600 | 0.444 | 0.9037 | -0.0005 | -0.0022 |
| D | 250 | 0.0680 | 0.544 | 0.9037 | -0.0015 | -0.0024 |

| run | c3 truth generated (novel) | of which a parent (another molecule's top-1) has the truth key | c2 insertions (gt3 != main) | c1 insertions |
|---|---:|---:|---:|---:|
| A | 39 | 0 | 3 | 7 |
| B | 72 | 2 | 5 | 9 |
| C | 111 | 0 | 6 | 14 |
| D | 136 | 2 | 9 | 16 |
