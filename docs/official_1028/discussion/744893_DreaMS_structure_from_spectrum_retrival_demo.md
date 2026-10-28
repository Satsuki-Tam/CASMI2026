# DreaMS : structure from spectrum retrival demo
topic 744893 | by **hengck23** (https://www.kaggle.com/hengck23) | posted 2026-10-01 | votes 14 | comments 3 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/744893

Three test datasets =  three different problems, three different solutions:

1 — known structure, known public spectra libraries : retrival

2 — known structure, no public spectra : prediction  (think of it as "interpolating train data" in closeset)

3 — novel structure : de novo generation  

"DreaMS : structure from spectrum retrival demo" is for problem one .

demo notebook: https://www.kaggle.com/code/hengck23/dreams-structure-from-spectrum-retrival-demo

1) input precursor_mz + spectra

2) use NN to make embeddings

3) search KNN matches in a database using cosine distance ( in the demo, we use "MassSpecGym_DreaMS_embeddings")     

original repo and credits:  https://github.com/pluskal-lab/DreaMS 

in the results above:

- input : Precursor mz, spectrum (blue)  

- output (top1 match) : Ref molecule,name,ID, spectrum (red)

## Comments (2 top-level)

- **?** (2026-10-01, votes 0)
  
- **hengck23** (2026-10-02, votes 1)
  i can use dreams basically as a fast probe without training: how much coverage is the hidden PUBLIC test set with the reference dataset?
  
  version 1: reference = MassSpecGym
  
  version2: reference = kaggle enveda-180
  
  version3: reference = kaggle non enveda-180
    - **?** (2026-10-05, votes 0)
      
