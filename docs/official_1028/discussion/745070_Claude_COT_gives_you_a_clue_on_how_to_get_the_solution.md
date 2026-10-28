# Claude COT gives you a clue on how to get the solution
topic 745070 | by **hengck23** (https://www.kaggle.com/hengck23) | posted 2026-10-02 | votes 15 | comments 7 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/745070

I am impressed (even chatgpt says it is impressive)

## Comments (3 top-level)

- **hengck23** (2026-10-02, votes 1)
  answer is correct!
- **hengck23** (2026-10-02, votes 2)
  i hope to do something like peak --> fragment loss, then fragment --> assemble to molecule; instead of just directly ms/ms --> molecule
    - **耶✌** (2026-10-02, votes 0)
      Yes, I'm thinking along the same lines. The end-to-end task of predicting SMILES is just too difficult. Instead, based on the fragment losses and the observed m/z values, we can predict the combinations of lost molecular formulas. Moreover, for classic substructures like benzene rings, the abundance at m/z 91 almost always indicates the presence of a benzene ring in the molecule. We can compile these kinds of prior knowledge into statistics and let the model learn from them.
- **hengck23** (2026-10-04, votes 2)
  in summary:
  [(mz,intensity) … ] --> [(mz,intensity, fragment formula) …] --> smiles 
  
  hints:
   fragment formula must obey mz is mass/charge value
    - **hengck23** (2026-10-04, votes 0)
      - iterative refinement (precursor --> fragment --> precursor --> fragment … ), high resolution, make use of different energy
      
      - another advantage is that this method can use sythetic data (chemically generated fragementation)
        - **hengck23** (2026-10-04, votes 0)
          my idea is hard SIRUS to netural SIRUS:
        - **hengck23** (2026-10-04, votes 0)
          anology:
          
          - MSA = retrieved spectrum from precursor weight   
          
          - coevolution = chemical fragmentation
