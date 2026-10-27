# 067 reading (locked2 opened once)

- C - A: NP C2 (C/D/E/F equal) -0.0039 [-0.0159, +0.0076] | n per set {'C_np_crosslib': 100, 'D_np_single': 100, 'E_np_negonly': 100, 'F_np_uncovered': 100}
    C_np_crosslib c2: n 100 0.5686 -> 0.5454 (-0.0231; up 8 / down 16)
    C_np_crosslib c1: n 95 0.9375 -> 0.9370 (-0.0005; up 2 / down 2)
    D_np_single c2: n 100 0.3244 -> 0.3197 (-0.0048; up 3 / down 9)
    E_np_negonly c2: n 100 0.4347 -> 0.4347 (+0.0000; up 8 / down 13)
    E_np_negonly c1: n 51 0.8667 -> 0.8863 (+0.0196; up 3 / down 2)
    F_np_uncovered c2: n 100 0.2378 -> 0.2499 (+0.0121; up 10 / down 6)
    F_np_uncovered c1: n 27 0.7930 -> 0.7733 (-0.0197; up 1 / down 2)
    G_tims_crosslib c2: n 100 0.7218 -> 0.7392 (+0.0174; up 7 / down 7)
    G_tims_crosslib c1: n 100 0.7309 -> 0.7303 (-0.0006; up 9 / down 12)
- B - A: NP C2 (C/D/E/F equal) -0.0130 [-0.0280, +0.0011] | n per set {'C_np_crosslib': 100, 'D_np_single': 100, 'E_np_negonly': 100, 'F_np_uncovered': 100}
    C_np_crosslib c2: n 100 0.5686 -> 0.5453 (-0.0233; up 12 / down 17)
    C_np_crosslib c1: n 95 0.9375 -> 0.9368 (-0.0008; up 1 / down 3)
    D_np_single c2: n 100 0.3244 -> 0.3185 (-0.0059; up 5 / down 10)
    E_np_negonly c2: n 100 0.4347 -> 0.4107 (-0.0240; up 10 / down 22)
    E_np_negonly c1: n 51 0.8667 -> 0.8667 (+0.0000; up 5 / down 5)
    F_np_uncovered c2: n 100 0.2378 -> 0.2388 (+0.0009; up 10 / down 11)
    F_np_uncovered c1: n 27 0.7930 -> 0.7922 (-0.0007; up 2 / down 1)
    G_tims_crosslib c2: n 100 0.7218 -> 0.7431 (+0.0213; up 11 / down 7)
    G_tims_crosslib c1: n 100 0.7309 -> 0.7084 (-0.0225; up 8 / down 15)
- panel C1 clean (n 202): C - A -0.0134 [-0.0317, +0.0034] | panel C2 (identity seen by F) -0.0185 | panel C1 all -0.0108
- REGISTERED VERDICT (C only): FAIL (point > 0: False; lower > -0.01: False; panel C1 clean lower > -0.01: False)
