# trick: train a smiles to MS/MS predictor too!
topic 744343 | by **hengck23** (https://www.kaggle.com/hengck23) | posted 2026-09-29 | votes 18 | comments 3 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/744343

Old experienced kaggler will know what this is for! Maybe ChatGPT and Claude know too.  

required for competition:

backward : generator(MS/MS, adduct) = smiles (de novo)

useful:

forward:  predictor(smiles, adduct)= MS/MS

(especially open-source predictor)

## Comments (2 top-level)

- **Barno Barno** (2026-09-29, votes 2)
  i remember a comment from a past competition that their winners generated 1TB or more training data
- **hengck23** (2026-10-01, votes 0)
  Enveda’s GrAFF-MS model
  Efficiently predicting high resolution mass spectra with graph neural networks
  https://proceedings.mlr.press/v202/murphy23a/murphy23a.pdf
  
  note: "We train our model on the NIST-20 tandem MS library"
  https://github.com/murphy17/graff-ms
    - **hengck23** (2026-10-01, votes 0)
      my orginal idea is some RSI harness  + forward/backward spectrum to molecule modelling.
      But it seems this idea has been partially explored
      
      https://github.com/ChrisTho23/dMSdMol   
      
      QOUTE: "Since models for both the forward (e.g., CFM-ID and GrAFF-MS) and backward problem (e.g., MS2Mol) have already been developed, we found this two-way approach to be very promising. We pursued a cycle contrastive GAN architecture, which allows us to create mappings between mass spectra and molecular structures, learning directly from the data in both directions."
