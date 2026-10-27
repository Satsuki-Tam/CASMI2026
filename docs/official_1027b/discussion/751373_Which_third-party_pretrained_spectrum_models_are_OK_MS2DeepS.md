# Which third-party pretrained spectrum models are OK? (MS2DeepScore, FIORA, SIRIUS/CSI:FingerID)
topic 751373 | by **GEN.CHOVY** (https://www.kaggle.com/oxazolidinone) | posted 2026-10-21 | votes 1 | comments 6 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/751373

Following up on the earlier clarification that any weights need the original training code plus permitted training data, could you confirm how this applies to a few commonly used open models and artifacts?

- Models trained only on public libraries (GNPS / MassBank / MoNA) with public training code, e.g. MS2DeepScore 2.0 or FIORA-OS: allowed?

- SIRIUS / CSI:FingerID: the training set isn't fully public and may include NIST, so I assume not allowed?

- Chemical language / graph models pretrained on PubChem structures only (no spectra), used just as a prior over candidates: allowed?

- For weights whose training code is public, is it enough to have the code and the permitted data, or does every intermediate file (e.g. a ranker's training table shipped in a public notebook) need to be reproducible bit-for-bit?

- PubChemLite (a CC BY 4.0 subset of PubChem) as a candidate source, with attribution: fine?

Thanks, just want to make sure we don't build on something that gets disqualified later.

## Comments (3 top-level)

- **GEN.CHOVY** (2026-10-21, votes 0)
  Follow-up question on one specific case: coleygroup released MIST checkpoints on Zenodo (record 23303289) on Oct 20 under MIT, with the training code public. They are trained on MassSpecGym; the "aug" variant additionally uses simulated spectra from GLACIER-MSG. I assume these are allowed on the same basis as the GLACIER/ICEBERG MassSpecGym weights, but wanted to confirm since the augmented one is partly distilled from another model. Thanks!
    - **David Healey** **[HOST]** (2026-10-26, votes 0)
      yes allowed
- **Satwik** (2026-10-22, votes 0)
  I think a general rule to follow based on the hosts' previous comments is that both training data and training code need to be publicly available under a valid license for it to be eligible.
- **David Healey** **[HOST]** (2026-10-22, votes 0)
  - Models trained only on public libraries: correct, allowed
  
  - SIRIUS / CSI:FingerID: correct, not allowed
  
  - Chemical language / graph models correct, allowed
  
  - We need the code that generates the intermediates as well
  
  - Yes PubChem Lite is fine
    - **XZXZZX** (2026-10-25, votes 0)
      Thank you for the answer. Two short follow-ups; a yes/no per item is enough.
      
      - Intermediates (your point 4). Is it sufficient that the code that generates the intermediates (candidate tables, ranker training rows, etc.) and the permitted input data are available so they can be regenerated, or must the shipped intermediate files be reproducible bit-for-bit (for example, when an upstream public source such as COCONUT or PubChem has since released a newer version)?
      
      - Using relationships across test spectra (thread 752297, which so far has only a participant reply). Is fully automated, label-free use of similarity between test spectra of different molecule_ids at inference time allowed, e.g. letting a confidently identified test molecule inform the ranking of candidates for a spectrally similar one?
      
      Thank you!
        - **David Healey** **[HOST]** (2026-10-26, votes 0)
          - yes its sufficient to just make sure the code and permitted data are there; bit for bit reproducibility isn't required where versions are changing. However, we would ask that you provide a version number or download date so that it could be reproducible. 
          
          - yes its allowed
