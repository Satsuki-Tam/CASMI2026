# Are ion-mobility / CCS fields available for the evaluation spectra?
topic 743368 | by **Vedrin Jeliazkov** (https://www.kaggle.com/vedrinjeliazkov) | posted 2026-09-25 | votes 0 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/743368

@davidhealeyenveda (/davidhealeyenveda) (sorry to ping — question for the organizers)

Hi! Thank you for the quick clarifications this week, they've been very helpful.

A data-schema question: the frames list TimsTOF-style instrument_type values, and Enveda's own public releases (e.g. the enveda-180 dataset) carry a precursor ion-mobility field — but the train.parquet / test.parquet frames we receive contain no IM / 1/K0 / CCS columns. Could you confirm whether the source spectra behind the evaluation (hidden) set carry precursor ion-mobility or CCS values at all, and whether such a field is intended to be exposed (or was deliberately excluded from the task inputs)?

We ask because collision cross-section looks like a natural tie-breaker for isomer pairs in this task, and we'd like to know whether exploring that direction is meaningful for the final scoring set before investing in it. If it's deliberately excluded, that's a perfectly good answer — we just want to build against the right assumptions.

Thanks a lot for your time and for running the competition!

## Comments (1 top-level)

- **David Healey** **[HOST]** (2026-09-27, votes 0)
  Its deliberately excluded; the test set has no CCS values.
