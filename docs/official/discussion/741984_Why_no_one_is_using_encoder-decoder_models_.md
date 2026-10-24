# Why no one is using encoder-decoder models ?
topic 741984 | by **RISHAV KUMAR** (https://www.kaggle.com/atomstack001) | posted 2026-09-18 | votes 1 | comments 7 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/741984

Hi was going through the code and all the shared code is around some ranker model. 
Why no one is training a encoder decoder based model?

## Comments (2 top-level)

- **Kamran Heydarov** (2026-09-18, votes 0)
  it takes long time
    - **RISHAV KUMAR** (2026-09-20, votes 0)
      long time to compte or like long time to build it ?
- **Whisper Last** (2026-09-20, votes 0)
  Do you you mean a spectrum2SMILES model? Generated SMILES might not be valid, while ranker models always choose valid ones.
    - **kiro** (2026-09-20, votes 0)
      how can ranker models rank novel structures tho? if the inchikey14 is not present in available datasets?
        - **RISHAV KUMAR** (2026-09-20, votes 0)
          yes same doubt
           @whisperlast (/whisperlast)
    - **RISHAV KUMAR** (2026-09-20, votes 0)
      yes, spectrum 2 smiles. the shared code by the organizers have an encoder decoder architecture
    - **RISHAV KUMAR** (2026-09-20, votes 0)
      also can we generate the output through the model and then validate that compound is valid and then only give our top candidates something like this.
