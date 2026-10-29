# 10/29 diagnostic submissions: mechanical reading (eta 0.015, fixed before the scores)

| probe | submission | status | Public |
|---|---|---|---:|
| ENG_B | 57753331 | SubmissionStatus.COMPLETE | 0.223 |
| PRE_RANK2_B | 57753342 | SubmissionStatus.COMPLETE | 0.249 |
| V8W7A_T | 57753951 | SubmissionStatus.COMPLETE | 0.148 |
| V8W7A_B | 57754031 | SubmissionStatus.COMPLETE | 0.22 |
| E0_T | 57754476 | SubmissionStatus.COMPLETE | 0.16 |

| order | quantity | value | class | registered reading |
|---|---|---:|---|---|
| 1 | G_B = E0_B - v8w7a_B | +0.0390 | +eta | B-path gap remains -> decomposing E0's later stages stays first |
| 1 | G_T = E0_T - v8w7a_T | +0.0120 | small | no large net T gap observed on this Public |
| 2 | ENG_B - BASE_B | +0.0100 | small | second list alone ~ BASE on B (complementarity not refuted) |
| 2 | E0_B - max(BASE_B, ENG_B) | +0.0360 | +eta | final is stronger than both single lists (fusion / forward / adoption worth studying) |
| 3 | D = E0_B - pre-rank2_B | +0.0100 | small | most of the net gain is before the insertion |
| 3 | pre-rank2_B - BASE_B | +0.0360 | +eta | descriptive |
| - | v8w7a_B - old B1_B 0.204 (descriptive) | +0.0160 | +eta | descriptive |
| - | v8w7a_T - old B1_T 0.160 (descriptive) | -0.0120 | small | descriptive |

**Next diagnostic slot (Codex 125 queue):** fwdoff_B (kernels/e0-probe-fwdoffb, audit-hardened, REBUILD sha 9966254...): read pre-rank2_B - fwdoff_B with eta
(Codex 126: this is a proposal only; technical checks of every run come first and nothing is pushed automatically.)

Limits (Codex 125): all five use the same Public (related policy comparisons, not replications); |G| < eta = no large net difference observed on this Public, not equivalence; using these results for the next research choice is itself Public adaptation (ledgered).
