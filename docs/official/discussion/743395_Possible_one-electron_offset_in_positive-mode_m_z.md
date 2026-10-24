# Possible one-electron offset in positive-mode m/z
topic 743395 | by **Bryce Hedelius** (https://www.kaggle.com/bhedelius) | posted 2026-09-25 | votes 3 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/743395

In the Enveda-180 processing code, the positive-mode m/z calibrants are sodium formate clusters built as SOME_POLYMER_UNIT_MZ * num + SODIUM_MAYBE_MZ (calibration.py, line 45 (https://github.com/enveda/enveda-180/blob/2fb7a301470d3ead68769e07bdf736749f67182f/data_processing/ms_prepper/calibration.py#L45)), with SODIUM_MAYBE_MZ = 22.989769 (line 14 (https://github.com/enveda/enveda-180/blob/2fb7a301470d3ead68769e07bdf736749f67182f/data_processing/ms_prepper/calibration.py#L14)).

That is the mass of the neutral Na atom (NIST (https://physics.nist.gov/cgi-bin/Compositions/stand_alone.pl?ele=Na)). Subtracting one electron (0.55 mDa, CODATA (https://physics.nist.gov/cgi-bin/cuu/Value?meu)) gives Na⁺ = 22.989221 Da, so every positive cluster reference is 0.55 mDa too heavy. The negative-mode clusters use HCOO⁻ = 44.998203 Da, which correctly includes the electron.

The released data is consistent with this. Fragment masses read 0.49 mDa higher in [M+H]⁺ spectra than in [M−H]⁻ spectra, and the gap is roughly the same at every m/z.

If your peak matching tolerance is 0.01 Da or more, this won't affect you. It matters more for tight fragment-formula matching. Subtracting ~0.5 mDa from positive-mode MS2 m/z values corrects it.

Could the organizers confirm whether the hidden test spectra went through the same calibration?

## Comments (1 top-level)

- **David Healey** **[HOST]** (2026-09-29, votes 2)
  Thank you for your patience on this.  Tracking down which test spectra were processed with this version.
