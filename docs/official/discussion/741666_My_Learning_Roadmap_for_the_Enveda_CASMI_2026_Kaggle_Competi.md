# My Learning Roadmap for the Enveda CASMI 2026 Kaggle Competition
topic 741666 | by **Mahmoud saad Elgharib** (https://www.kaggle.com/mah20050) | posted 2026-09-16 | votes 25 | comments 0 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/741666

I’m still a beginner and learning step by step, and I’m not participating in this competition at the moment. However, I found the chemistry + data science side of this problem very interesting, so I decided to organize the topics and resources that I think could be useful for understanding this type of challenge.

I may misunderstand some parts, so corrections and recommendations from people working in computational chemistry, metabolomics, mass spectrometry, and machine learning are very welcome.

My goal here is not to present a solution, but to build a learning roadmap.

1️⃣ Cheminformatics

Understanding molecules computationally:

- SMILES

- Molecular structures

- Molecular fingerprints

- Molecular descriptors

- Molecular similarity

🐍 Main tool: RDKit

📚 Resources:

- RDKit Documentation: https://www.rdkit.org/docs/

- RDKit Book: https://www.rdkit.org/docs/RDKit_Book.html

- RDKit Python Getting Started: https://www.rdkit.org/docs/GettingStartedInPython.html

RDKit provides functionality for fingerprints, molecular similarity, descriptors, chemical features, and many other cheminformatics tasks.

2️⃣ QSAR / QSPR & Molecular Property Prediction

Using molecular representations and machine learning to predict chemical properties.

Useful topics:

- Molecular descriptors

- Fingerprints

- Regression / classification

- Molecular property prediction

- Dataset splitting

- Cross-validation

🐍 Tools:
RDKit + Scikit-learn + DeepChem

📚 Resource:

- DeepChem Tutorials: https://deepchem.io/tutorials/

- DeepChem Book: https://deepchem.io/

DeepChem includes tutorials covering molecular fingerprints, molecular featurization, graph convolutions, dataset splitting, and molecular machine learning.

📄 Research:

- Analyzing Learned Molecular Representations for Property Prediction: https://arxiv.org/abs/1904.01561

3️⃣ Molecular Representation Learning

A molecule can be represented in many ways:

SMILES → sequence
Fingerprint → vector
Molecule → graph
Chemical descriptors → numerical features

The interesting question is: which representation captures the information needed by the model?

📚 Useful resources:

- DeepChem Molecular ML tutorials: https://deepchem.io/tutorials/

- RDKit Book: https://www.rdkit.org/docs/RDKit_Book.html

📄 Research:

- Analyzing Learned Molecular Representations for Property Prediction: https://arxiv.org/abs/1904.01561

4️⃣ Graph Neural Networks for Chemistry

Representing:

Atoms → Nodes
Bonds → Edges

Then using message passing to learn molecular representations.

🐍 Tools:

- PyTorch Geometric: https://pytorch-geometric.readthedocs.io/

- DGL: https://www.dgl.ai/

- RDKit: https://www.rdkit.org/

📄 Research:

- Graph Neural Networks for Molecules: https://arxiv.org/abs/2209.05582

- Geometric Deep Learning: https://arxiv.org/abs/2104.13478

PyTorch Geometric provides a framework for GNNs and geometric deep learning, while research on molecular GNNs covers property prediction, molecular optimization, generation, and related tasks.

5️⃣ Mass Spectrometry / MS/MS ⭐

For this competition, this is one of the areas I would study most carefully.

Important concepts include:

- MS1 / MS2

- Precursor ions

- Fragment ions

- m/z

- Peak intensity

- Adducts

- Ionization modes

- Collision energy

- Mass tolerance

- Spectral similarity

- Spectral libraries

🐍 Python tools:

matchms
https://matchms.readthedocs.io/

GitHub:
https://github.com/matchms/matchms

matchms is designed for importing, processing, cleaning, and comparing tandem mass spectra.

6️⃣ Spectral Similarity & Spectral Embeddings

Instead of treating a spectrum as just a list of peaks, machine learning can learn relationships between fragments.

One interesting approach is Spec2Vec, inspired by Word2Vec.

GitHub:
https://github.com/iomega/spec2vec

Tutorial / practical notebooks:
https://github.com/iomega/spec2vec_gnps_data_analysis

The repository includes practical notebooks for processing MS/MS data, calculating spectral similarities, and building molecular networks.

📄 Research:
Spec2Vec: Improved mass spectral similarity scoring through learning of structural relationships

https://doi.org/10.1371/journal.pcbi.1008724

7️⃣ Molecular Identification From MS/MS

This is especially relevant to the competition.

The general problem can be viewed as:

Mass spectrum → possible molecular candidates → rank candidates

Important concepts:

- Molecular formula prediction

- Structure identification

- Candidate generation

- Candidate ranking

- Spectral matching

- Fragmentation patterns

One important ecosystem to study is SIRIUS + CSI:FingerID.

GitHub:
https://github.com/sirius-ms/sirius

SIRIUS documentation:
https://v6.docs.sirius-ms.io/

SIRIUS can use isotope and fragmentation information for molecular-formula identification and integrate tools such as CSI:FingerID for structure identification.

8️⃣ Spectral Libraries & External Chemical Data

Potentially useful sources for understanding and experimenting with MS/MS data include:

🧪 GNPS
https://gnpsdocs.readthedocs.io/

GNPS provides spectral-library search, molecular networking, public MS/MS datasets, and tools for MS/MS identification and analysis.

🧪 MassBank of North America (MoNA)
https://mona.fiehnlab.ucdavis.edu/

MoNA provides downloadable mass-spectral collections, including experimental and LC-MS/MS spectra.

🧪 NIST Chemistry WebBook
https://webbook.nist.gov/chemistry/

NIST provides mass spectra for more than 33,000 compounds along with other chemical and physical data.

9️⃣ Machine Learning for MS/MS

This is where chemistry and ML become particularly interesting.

Possible approaches include:

- Classical spectral similarity

- Fingerprint-based retrieval

- Neural networks

- Contrastive learning

- Spectral embeddings

- Transformer-based models

- Candidate retrieval + reranking

One interesting open-source example is MIST, which works with MS/MS spectra and molecular candidates.

GitHub:
https://github.com/samgoldman97/mist

The repository includes examples for candidate ranking and embedding mass spectra into a continuous representation space.

🔟 Molecular Networking

Another useful concept is molecular networking.

Instead of analyzing every spectrum independently:

Spectrum → Spectrum similarity → Network → Molecular families

GNPS documentation:
https://gnpsdocs.readthedocs.io/en/latest/networking/

This represents spectra as nodes and spectral similarities as connections, allowing related molecules to form molecular families.

1️⃣1️⃣ Computational Chemistry + Machine Learning

For deeper study:

- Molecular simulation

- Quantum chemistry

- Molecular descriptors

- 3D molecular representations

- ML approximation of expensive calculations

📄 Useful research:

- Molecular Property Prediction: A Multilevel Quantum Interactions Modeling Perspective
https://arxiv.org/abs/1906.11081

This is probably a deeper direction rather than the first thing I would study for understanding the competition.

1️⃣2️⃣ Chemometrics

The statistical side of chemical data:

- PCA

- PLS

- Feature selection

- Dimensionality reduction

- Regression

- Classification

- Experimental variation

🐍 Tools:

NumPy + Pandas + SciPy + Scikit-learn

This area is useful because chemical datasets are not only an ML problem; understanding measurement variability and experimental structure is also important.

1️⃣3️⃣ Spectroscopy + Machine Learning

A broader area worth exploring:

- Mass spectrometry

- NMR

- IR

- Raman

- UV/Vis

The ML pipeline can often look like:

Raw/processed spectrum → preprocessing → representation → model → identification/prediction

For this competition, however, I would focus primarily on MS/MS rather than trying to study every spectroscopy field at once.

📚 A few resources I would prioritize

If I had to organize the learning path, I would start with:

- RDKit
https://www.rdkit.org/docs/

- DeepChem
https://deepchem.io/

- matchms
https://matchms.readthedocs.io/

- GNPS
https://gnpsdocs.readthedocs.io/

- Spec2Vec
https://github.com/iomega/spec2vec

- SIRIUS
https://github.com/sirius-ms/sirius

- MoNA
https://mona.fiehnlab.ucdavis.edu/

- NIST Chemistry WebBook
https://webbook.nist.gov/chemistry/

- MIST
https://github.com/samgoldman97/mist

- DeepChem Book
https://deepchem.io/

🧠 What I am trying to understand

After reading more about this competition, I think the interesting part is not simply:

«"Train a neural network on spectra."»

There are several layers:

Chemical structure
↓
Ionization / adduct
↓
Precursor ion
↓
Fragmentation
↓
MS/MS spectrum
↓
Spectral representation
↓
Candidate retrieval
↓
Candidate ranking
↓
Molecular identification

And this makes the problem interesting from both the chemistry and machine learning perspectives.

I also want to understand the validation strategy carefully before making assumptions about preprocessing or modeling. Things such as source-library overlap, adducts, collision energy, noise, and differences between chemical classes can potentially affect how well a model generalizes.

I’m still learning, so I may have some things wrong. If you have experience with mass spectrometry, metabolomics, cheminformatics, computational chemistry, or ML for chemistry, I would really appreciate corrections, resources, or recommendations.

I’m sharing this mainly as a learning roadmap, not as a competition solution.

Thank you for reading, and good luck to everyone participating in the competition!

## Comments (0 top-level)

