# W135 stage 1 (reader v2): pi3 = 0.3, design batches dF1, dR1, dF2, dR2, dF3, dR3, arm both = train + peer parents, B = 50

## U (primary interval: the three (dF, dR) pairs, exploratory; auxiliary: families within batches)
- U_both: +0.0683 [+0.0600, +0.0800] | family-bootstrap [+0.0456, +0.0928]
- U_train: +0.0567 [+0.0450, +0.0700] | family-bootstrap [+0.0373, +0.0769]
- U_both_c3: +0.0633 [+0.0600, +0.0700] | family-bootstrap [+0.0417, +0.0867]
- U_both_dbmiss: +0.0050 [+0.0000, +0.0100]
- U_both_B10: +0.0500 [+0.0400, +0.0600]
- U_both_B25: +0.0600 [+0.0500, +0.0700]
- U_both_B100: +0.0733 [+0.0650, +0.0800]
- U_both_Ball: +0.0767 [+0.0650, +0.0850]

- by type: {"family": {"U_both": 0.0833, "U_train": 0.0633, "U_both_c3": 0.0733, "U_both_dbmiss": 0.01, "U_both_B10": 0.0633, "U_both_B25": 0.0767, "U_both_B100": 0.0867, "U_both_Ball": 0.0933}, "random": {"U_both": 0.0533, "U_train": 0.05, "U_both_c3": 0.0533, "U_both_dbmiss": 0.0, "U_both_B10": 0.0367, "U_both_B25": 0.0433, "U_both_B100": 0.06, "U_both_Ball": 0.06}}
- by batch: {"dF1": {"U_both": 0.05, "U_train": 0.04, "U_both_c3": 0.05, "U_both_dbmiss": 0.0}, "dR1": {"U_both": 0.07, "U_train": 0.07, "U_both_c3": 0.07, "U_both_dbmiss": 0.0}, "dF2": {"U_both": 0.11, "U_train": 0.07, "U_both_c3": 0.1, "U_both_dbmiss": 0.01}, "dR2": {"U_both": 0.02, "U_train": 0.02, "U_both_c3": 0.02, "U_both_dbmiss": 0.0}, "dF3": {"U_both": 0.09, "U_train": 0.08, "U_both_c3": 0.07, "U_both_dbmiss": 0.02}, "dR3": {"U_both": 0.07, "U_train": 0.06, "U_both_c3": 0.07, "U_both_dbmiss": 0.0}}
- by class: {"C1": {"n": 160, "truth_generated_both": 0.41875, "reach_both": 0.00625, "reach_train": 0.00625}, "C2": {"n": 260, "truth_generated_both": 0.23846153846153847, "reach_both": 0.007692307692307693, "reach_train": 0.0}, "C3": {"n": 180, "truth_generated_both": 0.23333333333333334, "reach_both": 0.2111111111111111, "reach_train": 0.18333333333333332}}
- truth f.z rank (arm both, pre-selectable products): {'le1': 9, 'le3': 23, 'le10': 30, 'le25': 36, 'le50': 41, 'le100': 44, 'any': 46}
- reached truths by parent source: {'train': 32, 'peer': 7, 'peer|train': 1, 'peer|train|train': 1}
- parents: {'train_median': 10.0, 'both_median': 11.0, 'peer_struct_median': 1.0}

**Decision (registered): INVEST**
