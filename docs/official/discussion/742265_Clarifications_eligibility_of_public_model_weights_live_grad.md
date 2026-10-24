# Clarifications: eligibility of public model weights, live grader version, accepted GPUs
topic 742265 | by **Fernando Faria** (https://www.kaggle.com/fernandoadefaria) | posted 2026-09-21 | votes 0 | comments 4 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/742265

Three questions for the hosts/staff, so teams don't find out late.

1. Public artifacts derived from train.parquet. Some public Kaggle datasets contain model weights or ranker-training rows that were produced from train.parquet (CC BY-NC 4.0) and are labelled CC0 by their uploader. Given thread 741844 and the MIT winner license: may a prize-eligible solution use such third-party artifacts as published, or must the weights be trained by the submitting team from train.parquet? Does the answer change for weights a team trained itself on train.parquet?

2. Grader version. Is the live scorer identical to the published metric/casmi-mean-reciprocal-rank (v13)? In v13, an unparseable guess only consumes a rank position, and I checked locally with RDKit 2026.03.3 that filler after the correct answer does not change the score. One forum post (thread 742088) reports a submission padded with filler SMILES scoring 0.000, so I'd like to be sure the live grader treats invalid SMILES the same way.

3. Accelerators. The Overview says "GPU Notebook <= 9 hours" without naming a GPU. Are P100 sessions accepted for submissions, or only T4? (Some earlier Kaggle code competitions refused P100.)

Thanks!

## Comments (3 top-level)

- **David Healey** **[HOST]** (2026-09-25, votes 0)
  I will address #1, and we'll double check with the Kaggle hosts on #2 and #3.
  
  Yes, any open source models trained on train.parquet are fair game.  train.parquet is compiled from open source libraries and we are essentially just redistributing them with some minor touching up and normalization.
- **Marie Killian** **[Organizer]** (2026-09-28, votes 0)
  We've clarified 2 and 3:
  
  2: The live scorer is identical to the published casmi-mean-reciprocal-rank v13. It has not changed. We are investigating the concerns raised in the thread you referenced.
  
  3: The P100s have been sunsetted. Here's a post with the announcement and suggestions of alternative options. (https://www.kaggle.com/discussions/product-announcements/735239)
- **Abhinav Kumar** (2026-10-04, votes 0)
  Thanks, David, that's very helpful on pretrained weights. One follow-up on code, so teams don't find out late:
  some public models are loaded through small Python files (a model definition and a featurization module) that
  carry no licence header, and the dataset licence field says "Other". For a prize-eligible solution, do such
  files need an explicit OSI-approved licence (rule 3.6.c), or is attaching them to a public competition notebook
  enough (3.6.b)? And for winners (2.8), is citing and linking public weights sufficient, or must the winner's
  package include training code that reproduces them?
    - **Marie Killian** **[Organizer]** (2026-10-14, votes 0)
      Hi @abhinavkumar93 (/abhinavkumar93) ! 
      
      Use of public competition datasets and code shared by other competitors (including code files inside public models) is allowed, provided they come from permissible sources and comply with applicable licensing requirements. 
      
      For pretrained model weights, citing or linking the weights alone is not sufficient. The original training code and access to the permitted training data needed to reproduce them must also be available.
