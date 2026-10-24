# Newer public releases of GNPS / MassBank / MoNA: allowed as external data if we keep only CC0 / CC BY records?
topic 745228 | by **Amin** (https://www.kaggle.com/aminvafaei) | posted 2026-10-02 | votes 2 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/745228

Hi David / Enveda team,

train.parquet includes snapshots of the GNPS, MassBank and MoNA libraries. The current public releases of these libraries contain some spectra and structures that are not in train.parquet. Examples are the per-library downloads at external.gnps2.org, MassBank release 2026.03 (GitHub / Zenodo) and the MoNA download exports.

Each record in these libraries carries its own licence:

. most records are CC0 or CC BY;
. some are CC BY-NC, CC BY-NC-SA or CC BY-NC-ND;
. a few libraries are NIST-derived (for example GNPS-NIST14-MATCHES) or HMDB-derived.
For a prize-eligible solution:

- May we use the current public releases as external data, both for training and as a reference library at inference? We would keep only records whose own licence allows commercial use and redistribution (CC0, CC BY), and drop every non-commercial or no-derivatives record and every NIST- or HMDB-derived library.

- Are CC BY-SA records acceptable too, or should we drop them as well?

- If neither is acceptable, should external spectra be limited to what is already in train.parquet?

Thank you.

## Comments (1 top-level)

- **Marie Killian** **[Organizer]** (2026-10-05, votes 0)
  Thanks for clarifying! Newer releases of public datasets are fine to use and CC BY-SA records are acceptable.
