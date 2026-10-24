# Exact duplicate MS/MS spectra with conflicting structure labels in train.parquet
topic 744446 | by **Benedek Brandschott** (https://www.kaggle.com/benedekbrandschott) | posted 2026-09-29 | votes 0 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/744446

I found 22 pairs of rows in train.parquet where the complete ms2_mzs and ms2_normalized_intensities arrays are exactly identical, but the inchikey14 labels differ. The 44 rows involve six pairs of distinct constitutional isomers. Within each pair, the precursor, adduct, instrument and collision-energy fields also match; one row comes from msdial and the other from riken.
For example, zero-based row positions 1573990 (msdial, Bergapten, BGEBZHIAGXMEMV) and 2371049 (riken, Xanthotoxin, QXKHYNVANLEOEG) share the same 13-peak spectrum at 19.5 eV. Rows 1573996 and 2371042 show the same label conflict at 6.5 eV. Another pair, 1607879 and 2194008, shares a 21-peak spectrum at 40.0 eV despite different structure labels.
The data description mentions removal of exact duplicate spectra. Were duplicates with different structure labels intentionally retained? Could you check the original library accessions or provenance for these records and advise whether either label should be corrected, or whether these rows should be excluded from training?
These are zero-based row positions in my train.parquet file (SHA-256: 9423f90ec08b941a9646b535bf0606183e86ff0c5a297978f5a70693d41bcd98).

## Comments (1 top-level)

- **Yanamii** (2026-10-07, votes 0)
  @davidhealeyenveda (/davidhealeyenveda) A related validation question: could a mapping from spectrum_id to the original library accession or acquisition group be made available? For a Class-1 validation set, the same structure needs to remain in the reference library, but copies of one measurement distributed through different libraries should stay in the same split. An acquisition-level identifier would help distinguish those cases, including spectra with slightly different rounding or filtering. If that provenance is unavailable, is there a recommended way to form an independently acquired query/reference split from the released data?
