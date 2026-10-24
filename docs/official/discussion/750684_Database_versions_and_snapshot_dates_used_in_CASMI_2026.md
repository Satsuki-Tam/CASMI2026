# Database versions and snapshot dates used in CASMI 2026
topic 750684 | by **Chybgyz** (https://www.kaggle.com/chybgyz) | posted 2026-10-19 | votes 0 | comments 0 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/750684

Hi CASMI 2026 organizers,

Could you please clarify the database versions and reference dates used for this competition?

Training spectral libraries: Which release/version and download date were used for each of the 11 sources listed under ingest_lib in train.parquet? Is there a source manifest with this information?

The three molecule groups: Which database snapshots or cutoff dates were used to distinguish:

structures with publicly available reference MS/MS spectra;

known structures in PubChem or COCONUT without public reference spectra;

novel structures absent from PubChem?

Subsequent updates: Are these categories fixed according to those snapshots, even if a structure or its reference spectra become publicly available later?

I found publication dates for some public releases, but could not identify the exact versions used to prepare the competition data or the reference date for defining these groups.

A table with source name, version, and snapshot/download date would help us make database comparisons reproducible and design appropriate validation sets.

Thank you!

## Comments (0 top-level)

