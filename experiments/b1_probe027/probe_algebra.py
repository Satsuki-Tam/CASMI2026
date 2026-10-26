"""Readings of the 10/26 Public probes (Codex 027 / 030 / 032 / 033 corrections), from the observed scores.
Usage: python probe_algebra.py PT PB P26 DUP"""
import sys
PT, PB, P26, DUP = (float(x) for x in sys.argv[1:5])
M, PK, PP, FE = 0.354, 0.336, 0.046, 0.370
L = [f"observed: T {PT:.3f} | COCONUT-only (B) {PB:.3f} | band26 {P26:.3f} | DUP off {DUP:.3f} (vs working baseline {FE:.3f}: {DUP - FE:+.3f})", ""]
L.append(f"P_T + P_B - P_K = {PT + PB - PK:+.3f}  (extra recovery from choosing T vs B membership inside the pool; >= 0.03 / <= 0.01 guides)")
L.append(f"P_T + P_B + P_P = {PT + PB + PP:.3f}  (membership oracle with the three groups' internal orders fixed; vs M {M:.3f}: {PT + PB + PP - M:+.3f})")
lo_T, hi_T = max(0.0, M - PB - PP), min(PT, PK, M); lo_B, hi_B = max(0.0, M - PT - PP), min(PB, PK, M)
L.append(f"M_T (class-1 contribution of the M2x main) in [{lo_T:.3f}, {hi_T:.3f}]; M_B (COCONUT-only truths) in [{lo_B:.3f}, {hi_B:.3f}]; M_P (PubChem-only) in [0.018, 0.046] (10/25)")
L.append(f"band: P_26 = {P26:.3f} -> share q of molecules with the truth at ranks 26-50 satisfies {P26:.3f} <= q <= {min(25 * P26, 1):.3f}; main + band oracle = {M + P26:.3f}")
L.append("")
L.append("pre-registered calibration predictions (033_prereg): model A P_T 0.209 [0.096, 0.296], P_B 0.149 [0.048, 0.272]; model B P_T 0.275 [0.26, 0.29], P_B 0.078 [0.04, 0.11]; band w*s_band 0.0016 [0.0006, 0.0026]")
inA = 0.096 <= PT <= 0.296 and 0.048 <= PB <= 0.272; inB = 0.26 <= PT <= 0.29 and 0.04 <= PB <= 0.11
L.append(f"inside A's marginal intervals: {inA}; inside B's: {inB} (marginals only; A and B overlap, Codex 033)")
print("\n".join(L))
