# 230 peaks, 18 that matter: a guide to reading CASMI spectra
topic 741641 | by **starkhushi** (https://www.kaggle.com/starkhushi) | posted 2026-09-16 | votes 9 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/741641

A lot of us joined this competition as ML people, not chemists. The data looks like two arrays of numbers per row, and it's hard to know which of those numbers matter. Here's the short version I wish I'd had on day one, with real numbers from this competition's files.

1. What the instrument actually does

Think of it as weighing the pieces of a smashed object to work out what the object was.

- Ionise. The molecule picks up (or loses) a small charged group so the instrument can steer it.

- Select. The instrument isolates ions of one mass. This is the precursor.

- Smash. The precursor is collided with gas and breaks into fragments.

- Weigh. It records the mass-to-charge ratio (m/z) and abundance (intensity) of every fragment.

A row in train.parquet / test.parquet is one run of that experiment: precursor_mz from step 2, and the aligned arrays ms2_mzs + ms2_normalized_intensities from step 4.

2. The precursor is not the molecule's mass — undo the adduct first

The instrument weighs the ion, not the molecule. The adduct column tells you what was attached. Subtract it to get the neutral mass, the number you can compare against a candidate structure.

Adduct
Meaning
Neutral mass M =

[M+H]+
gained a proton
precursor − 1.00728

[M+Na]+
gained sodium
precursor − 22.98922

[M-H]-
lost a proton
precursor + 1.00728

[M+CH2O2-H]-
gained formic acid, lost a proton
precursor − 44.99820

Worked example from test.parquet: a spectrum with precursor 375.0709 and adduct [M+H]+ gives M = 375.0709 − 1.00728 = 374.0636 Da.

Why it matters: a molecule measured as [M+Na]+ in one library and [M+H]+ in another has different precursor m/z values but the same neutral mass. Compare on neutral mass and the two meet; compare on precursor m/z and they never will.

How precise is this? Very. In the visible test file, molecules measured with more than one adduct agree on the neutral mass to a median of 1.3 ppm, which is about 0.0005 Da at 350 Da. So a ±10 ppm window around the neutral mass is plenty.

3. Peaks: most of what you see is noise

Intensities are normalised so the tallest peak (the base peak) equals 1.0. The test spectra look rich: a median of 230 peaks. But 93% of those peaks are below 1% of the base peak. After dropping everything under 1%, the median spectrum has just 18 peaks.

So the first preprocessing step, a relative-intensity floor, changes your input more than any model choice will.

4. Fragments and neutral losses: two views of the same break

When a molecule breaks, one piece keeps the charge (you see it as a fragment peak) and the other flies off uncharged (invisible, but you can infer its mass):

$$\text{neutral loss} = \text{precursor m/z} - \text{fragment m/z}$$

Losses are often more informative than fragments, because they name the chemical group that fell off:

Loss (Da)
What fell off
Tells you

18.0106
H₂O
a hydroxyl group

17.0265
NH₃
an amine

43.9898
CO₂
a carboxylic acid

46.0055
HCOOH
formic acid / carboxyl

162.0528
C₆H₁₀O₅ (hexose)
a sugar attached: very common in natural products

A neat consequence: a molecule and the same molecule with an extra –OH have different fragment m/z values but many identical losses. That's why feature sets that include a neutral-loss channel find structural relatives much better.

5. Collision energy: how hard you hit it

Higher energy means more breakage and smaller fragments. You can see it directly in the test file. The intensity-weighted average fragment m/z, as a fraction of the precursor (positive mode, median):

Energy
Avg fragment / precursor

20 eV
0.64

40 eV
0.44

60 eV
0.36

So low-energy spectra show big pieces (close to the whole molecule) and high-energy spectra show small building blocks. They're complementary, not redundant.

6. One molecule, many spectra

Scoring is per molecule_id, and a molecule usually has several rows: different energies (20, 40, 60 eV and a merged spectrum), different adducts, sometimes both polarities. In the visible test, 97 of 400 molecules have positive and negative spectra. Treat each row as another camera angle on the same object and combine the evidence, rather than predicting from one row.

7. Three gotchas that catch ML people

- The collision-energy sign flips in negative mode. collision_energy_orig stores negative-mode energies as negative numbers (-40), while collision_energy_ev is positive ([40.0]). Use collision_energy_ev.

- The precursor peak is often missing. Only 56% of test spectra contain a peak at the precursor m/z. Treat precursor_mz as metadata, not as a peak you can count on.

- Stereochemistry is free. The metric compares the first block of the InChIKey (connectivity only) after tautomer canonicalisation. Two SMILES differing only in @/@@ count as the same answer, and as the same wasted slot if you submit both.

Where to go from here

- EDA notebook (https://www.kaggle.com/code/starkhushi/casmi-2026-eda-library-search): charts for all of the above across the 11 source libraries (noise floors, adducts, energies, neutral losses).

- Modeling notebook (https://www.kaggle.com/code/starkhushi/casmi-2026-modeling-retrieval): turns these ideas into a working pipeline: neutral-mass candidate retrieval, spectral library search, and ranking structures that have never been measured.

What confused you most when you first opened the data? I'm happy to add a section for it.

## Comments (1 top-level)

- **nafspf** (2026-09-30, votes 0)
  Thanks for sharing the info, I don't have a good chemistry background and have a few questions for the training.parquet
  
  - I checked unique adduct, and found one being [Cat]2+, how does it relate to M if I would like to compute neutral mass?
  
  2.
  If I look at 57th row, adduct is [M+Na]+, precursor is 303.2319. When I use normalized_smiles to calculate mass with codes below,
  
  smiles = casmi_all_df['normalized_smiles'].iloc[57]
  mol = Chem.MolFromSmiles(smiles)
  Descriptors.ExactMolWt(mol)
  
  the returned mass is 302.2245802, from what you wrote, the neutral mass should be 303.2319 − 22.98922 > 302.2245802. It seems the adduct is maybe [M+H]+ or do I just misunderstand your guide?
  
  In fact, it seems that the training.parquet has many errors like this if I check in this way. There are some cases the precusor_mz is about twice than the normalized smiles while adduct and adduct_orig indicates M instead of 2M. Is it normal for this to happen in chemistry data collection; I guess adduct is manually given during the collection process?
  
  3.
  Probably 2 has resulted from your statement that 
  
    The precursor peak is often missing. Only 56% of test spectra contain a peak at the precursor m/z. Treat precursor_mz as metadata, not as a peak you can count on
  
  In that sense, does it mean the Mass Spectra data in general (or the hidden test data) do not have reliable precursor_mz and adduct as a mean to compute neutral mass? I suppose checking mass is an important way to see if a guessed SMILES is valid/reasonable.
