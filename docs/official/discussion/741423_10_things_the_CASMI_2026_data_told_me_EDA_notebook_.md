# 10 things the CASMI 2026 data told me (EDA notebook)
topic 741423 | by **starkhushi** (https://www.kaggle.com/starkhushi) | posted 2026-09-15 | votes 2 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/741423

I went through the training library and the visible test file in detail and wrote it up as a notebook with charts for everything below: CASMI 2026 EDA + Library Search (https://www.kaggle.com/code/starkhushi/casmi-2026-eda-library-search). Here are the findings I found most useful. Train numbers come from the notebook run and the data page; test numbers come from the visible test.parquet.

The training library

1. It is eleven datasets, not one. 2,539,575 spectra of 275,810 structures, but each ingest_lib has its own instruments, collision-energy convention, m/z precision and noise floor. Spectra per structure vary widely between libraries, so a row-level split puts the same compound on both sides. Split on inchikey14.

2. enveda-180 dominates, and it is a chemical island. It holds about 45% of spectra and 66% of structures, and it is the only large library on the test instrument (timsTOF). But the data page describes it as drug-like screening chemistry, a different region of chemical space from the natural-product test molecules, and the notebook's Jaccard heatmap shows how little it shares with the other libraries. You can have instrument match or chemistry match, but not both. enveda-np-examples (1,151 spectra, 250 structures) is the one small bridge.

3. A formula is not an answer. The training set has 51,291 unique molecular formulas for 275,810 structures, about 5.4 structures per formula on average, and the distribution is long-tailed (see the notebook). Exact mass narrows the search, but ranking within the mass window is where the work is.

The test spectra

4. Test spectra look rich, but it is mostly noise floor. The median test spectrum has 230 peaks, yet 93% of all test peaks are below 1% of the base peak (77% below 0.1%). After a 1% floor the median is 18 peaks, and after a 0.1% floor it is 52. Your intensity threshold changes the input far more than anything else in preprocessing.

5. The precursor peak is often missing. A peak within 0.01 Da of precursor_mz appears in only 56% of test spectra. Treat precursor_mz as metadata, not as a peak you can rely on. About 3% of peaks sit slightly above the precursor, within the documented +2 Da isotope allowance.

6. Different adducts of one molecule agree on the neutral mass extremely well. 108 of the 400 visible molecules were measured with more than one adduct. Their neutral masses (precursor − adduct offset) agree to a median of 1.3 ppm (90th percentile 3.1 ppm). That makes the multi-adduct consensus mass a very reliable anchor, and it also sanity-checks your adduct table.

7. Many molecules are measured in both polarities. Of the 400 visible molecules, 276 have only positive-mode spectra, 27 only negative, and 97 both. Positive and negative spectra of the same molecule carry complementary fragments, and the metric scores per molecule, so this evidence can be combined.

Collision energy

8. Collision energy behaves exactly like physics says. Intensity-weighted mean fragment m/z divided by precursor m/z (visible test, positive mode, median): 0.64 at 20 eV, 0.44 at 40 eV, 0.36 at 60 eV. The merged 20,40,60 spectrum sits at 0.57, much closer to the low-energy end than to an average of the three.

9. Watch the sign in negative mode. In negative mode, collision_energy_orig is stored as negative values (-20, -60,-40,-20), while collision_energy_ev is positive ([20.0], [20.0, 40.0, 60.0]). If you parse the original column you will feed negative energies to your model. Use collision_energy_ev.

10. The full energy ladder is not guaranteed. Visible test spectra use 20/40/60 eV plus a merged spectrum, but only 24% of molecules have the complete positive-mode set (20, 40 and 60 eV plus the merged spectrum). Most have a subset, so pooling logic should not assume a fixed ladder. Per the data page, the hidden test can have 1–16 spectra per molecule.

One caution about the visible test file

The visible test.parquet is made of training examples (per the data page), and it doesn't look like the hidden test. Its neutral masses span 246–439 Da (median 327), while the hidden test is described as 157–1,159 Da (median 348). Its adducts are mostly [M+H]+ (959) and [M-H]- (193), and it contains only 7 of the 10 documented adducts. Anything mass- or adduct-dependent that you calibrate on the visible file may not hold for the hidden set.

The notebook also covers adduct coverage in train versus test, the collision-energy unit mix per library, peak-count and precursor-error distributions per library, the most frequent neutral losses in natural-product spectra (water, CO₂, formic acid, hexose …), and how many structures fall inside a 10 ppm window. Corrections welcome if anything looks off.

## Comments (1 top-level)

- **?** (2026-09-19, votes 0)
  
