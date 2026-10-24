# Is Enveda's public Enveda-180 Zenodo release allowed as external data?
topic 743569 | by **michael duong** (https://www.kaggle.com/sellside) | posted 2026-09-26 | votes 0 | comments 4 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/743569

Hi David / Enveda team,

A short question on external data. Enveda's Enveda-180 spectral library is public on Zenodo (record 21346580, CC BY 4.0). Is it allowed as external data in a prize-eligible solution, both for training models and as a reference library at inference?

Related to 743368: will the hidden evaluation spectra include precursor ion mobility (1/K0 or CCS), or keep the same columns as the provided test.parquet?

Thank you.

## Comments (2 top-level)

- **PC Jimmmy** (2026-09-27, votes 0)
  I was under the impression that the enveda-180 library is part of the train data now.  Have you found differences?  
  
  From the data page
  
  enveda-180    1,153,785   182,941 Enveda's published dataset, acquired on the same Bruker timsTOF as the test set. Consistent and instrument-matched, but the chemistry is synthetic drug-like screening compounds, a different region of chemical space from the test molecules.
- **David Healey** **[HOST]** (2026-09-27, votes 0)
  Yes you can use the Zenodo release
    - **michael duong** (2026-09-28, votes 0)
      Thanks David, that answers the first part. Could you also confirm the second question: will the hidden evaluation spectra include precursor ion mobility (1/K0 or CCS), or keep exactly the same columns as the provided test.parquet? Thank you.
        - **Marie Killian** **[Organizer]** (2026-09-28, votes 0)
          No, the test set does not include 1/K0 or CCS. It has the same columns as provided in test.parquet.
