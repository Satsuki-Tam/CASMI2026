# Understanding the actual task 
topic 745029 | by **hengck23** (https://www.kaggle.com/hengck23) | posted 2026-10-01 | votes 22 | comments 3 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/745029

In the commercial world, this is called “understanding your customer.” ChatGPT is quite good at doing market research.  

I looked more closely at the competition description and focused on the phrase “natural product structures” from mass spectra. I then asked ChatGPT to investigate what Enveda is really interested in.  

does this look familiar to our 3 class of test set??  

Here are some Enveda papers/resources you should not miss:  

- Butler et al., “MS2Mol: A transformer model for illuminating dark chemical space from mass spectra.”
Their goal is de novo prediction of natural metabolites that are not present in existing databases.

They also introduced EnvedaDark, a benchmark of 226 natural products that were absent from major databases.  

- MS2Prop: A machine learning model that directly predicts chemical properties from mass spectrometry data for novel compounds.  

- PRISM, Enveda’s current foundation model: 
https://enveda.com/news/pr-enveda-biosciences-announces-microsoft-collaboration-and-reveals-foundation-model-to-read-and-translate-chemistry/  

- https://www.bruker.com/en/landingpages/bdal/customer-insight-enveda.html  

- https://pubs.acs.org/jnprdf/article/89/9/2436/5428694/Chemotaxonomic-Map-of-Labdane-Diterpenoids-in

example of dark chemical prior

"timsTOF is the combination of high-resolution MS + fast MS/MS + ion mobility, which fits complex natural-product profiling very well."

There is much more information available. It may be worth asking your AI agent to research Enveda’s papers, platform, and view of natural-product chemical space.  

Some useful natural-product structure databases to investigate are COCONUT, LOTUS, and NPAtlas.
The key point is that “natural product structures” may be a very important clue about the target distribution of this competition.  

just my guess. take with a pinch of large grains of salt …

## Comments (3 top-level)

- **Patrick Chan** (2026-10-01, votes 1)
  Hi hengck23, Thanks for the interesting share! As usual, very good insights. Usually in specialized domains, customized transformers perform way better than large generalized model.
- **Naseem Akhtar** (2026-10-02, votes 0)
  Should we team up here . I am a data scientist and ML Engineer.
- **Raagav Anand** (2026-10-02, votes 0)
  some of this i had but the articles were really interesting and helpful! thanks a lot
