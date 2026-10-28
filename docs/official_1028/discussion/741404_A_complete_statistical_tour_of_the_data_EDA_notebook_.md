# A complete statistical tour of the data (EDA notebook)
topic 741404 | by **José Freitas** (https://www.kaggle.com/josefreitasalvesneto) | posted 2026-09-15 | votes 29 | comments 3 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/741404

I went through this dataset column by column and wrote the whole thing up in a public notebook. Sharing it here because three of the findings change how you should set up your validation, and it seems better if we all start from the same picture of the data.

https://www.kaggle.com/code/josefreitasalvesneto/casmi-2026-a-complete-statistical-tour

A few things you may want to know before you write any preprocessing code:

The public leaderboard is measuring the wrong thing. The data page says the test file is "comprised of examples from the training dataset" — it turns out to be enveda-180 rows, and the ones I checked are byte-for-byte identical to training spectra. That library is drug-like screening chemistry, not the natural products the prize is decided on. I would not read anything into a public score.
Test spectra only look 10x richer than training spectra. Median 230 raw peaks vs 27 — but 82% of the test peaks are below 1% relative intensity, and at a 1% floor the two land at 18 and 14. The apparent train/test shift is mostly noise floor.
A plain library search already scores MRR@25 = 0.907 on natural products that have reference spectra. Novelty Class 1 is close to solved without any learning, which means the entire score differential is in Classes 2 and 3.
The notebook also covers the 11 source libraries and how little they overlap, chemical space, adducts, collision energy, neutral losses, and where the labels wobble. Every number is computed in the notebook, so you can check any of it yourself.

Corrections very welcome — if something looks wrong, tell me and I will fix it. Good luck, everyone.

## Comments (3 top-level)

- **David Healey** **[HOST]** (2026-09-15, votes 7)
  Thanks for making this notebook, and welcome to CASMI 2026!
  
  Just to clarify something about the public leaderboard and test.parquet: the public leaderboard score is calculated not on the contents of the test.parquet downloadable dummy file (which as you say just contains a sample of Enveda-180 spectra and is there to demonstrate the size and scope and structure of the test data), but rather on the public split of the Hidden test set provided to your submission notebook.
- **Mahmoud saad Elgharib** (2026-09-15, votes 3)
  Thank you for sharing this detailed analysis. @josefreitasalvesneto (/josefreitasalvesneto) I’m still a beginner and learning step by step, but I’m very interested in the chemistry + data science side of this competition.
  I’m currently trying to organize the main areas that could be useful for this type of problem, including:
  
  - Cheminformatics
  Molecular structures, SMILES, fingerprints, molecular descriptors, similarity search.
  Python: RDKit
  
  - QSAR / QSPR
  Predicting molecular or chemical properties using machine learning.
  Python: RDKit + Scikit-learn
  
  - Molecular Property Prediction
  Predicting properties such as activity, toxicity, solubility, and other molecular characteristics.
  Python: RDKit + Scikit-learn / PyTorch
  
  - Molecular Representation Learning
  Learning useful representations from SMILES, fingerprints, molecular graphs, and molecular features.
  Python: RDKit + PyTorch / TensorFlow
  
  - Graph Neural Networks for Chemistry
  Representing atoms as nodes and chemical bonds as edges.
  Python: PyTorch Geometric / DGL + RDKit
  
  - AI for Drug Discovery
  Virtual screening, molecular activity prediction, hit discovery, and lead optimization.
  Python: RDKit + DeepChem
  
  - Molecular Generation / Generative Chemistry
  Using generative models to create or modify molecules with desired properties.
  Python: RDKit + PyTorch + Transformers / diffusion models
  
  - Chemical Reaction Prediction
  Reaction prediction, reaction classification, retrosynthesis, and reaction-condition prediction.
  Python: RDKit + reaction datasets + Transformer models
  
  - Molecular Optimization
  Optimizing molecules toward specific chemical or biological objectives.
  Python: RDKit + Bayesian Optimization / evolutionary optimization
  
  - Virtual Screening
  Searching large chemical libraries and ranking compounds that may match a target.
  Python: RDKit + similarity search + Mranking
  
  - Computational Chemistry + Machine Learning
  Combining computational chemistry, molecular simulations, and ML.
  Python: RDKit + DeepChem + scientific Python tools
  
  - Chemometrics
  Applying statistics and machine learning to chemical and experimental data.
  Python: NumPy + Pandas + Scikit-learn + SciPy
  
  - Spectroscopy + Machine Learning
  Working with NMR, IR, Raman, and mass-spectrometry data.
  Python: NumPy + SciPy + Scikit-learn + PyTorch
  
  - Materials Informatics
  Using data science and ML to discover and predict properties of materials and compounds.
  Python: pymatgen + Matminer + Scikit-learn / PyTorch
  I’m also trying to collect books, research papers, courses, official documentation, GitHub repositories, Python libraries, datasets, and practical notebooks for each section, so I can understand both the theory and the implementation.
  Your analysis of the validation setup, source-library overlap, noise floor, adducts, collision energy, and especially the Class 1 vs. Classes 2–3 difference is very helpful. I’ll definitely go through the notebook carefully before making assumptions about preprocessing or validation.
  I’m still learning, so I may not understand everything correctly yet, but I’d really appreciate any corrections or recommendations from people with more experience in computational chemistry and mass spectrometry.
  Thank you again for sharing your work and helping everyone start from a better understanding of the data. 🙏
  Good luck with the competition!
- **?** (2026-10-10, votes 0)
  
