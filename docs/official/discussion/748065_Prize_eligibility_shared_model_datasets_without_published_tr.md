# Prize eligibility: shared model datasets without published training code (yes/no needed)
topic 748065 | by **Fasil** (https://www.kaggle.com/fasiltheengineer) | posted 2026-10-10 | votes 4 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/748065

Hello hosts,

Many public notebooks, including most of those above about 0.40 on the public leaderboard, load pretrained artifacts from participant-shared Kaggle datasets. Examples: ahmedberatozer/casmi26-v4b-models, casmi26-v3-models, casmi26-fpnet-full1 and casmi26-v2-pool, and prvsiyan/casmi26-fp-models-v2. These datasets are labelled "Other" (described as non-commercial) or CC BY-NC-SA, and for some of the weights the training code has not been published.

The rules ask winners to deliver training code and to license their solution under an OSI-approved licence. The welcome post says that solutions built on data or tools that cannot be commercially licensed will not be eligible to win. On 5 October you confirmed that models trained on train.parquet, and redistributed artifacts of them, are fine.

Could you please confirm three points, so that teams can plan their final selections?

(1) Is a solution that loads such third-party weights as-is prize-eligible if the team cannot deliver the code that trained them? Or must every model used at inference be retrained with code the winner can deliver?

(2) Does a "non-commercial" or CC BY-NC-SA label on a participant-shared dataset, derived only from train.parquet and public databases, make a solution that uses it ineligible?

(3) Does the final compliance check apply only to a team's two selected submissions, or to all of its submissions?

A short yes or no on each would settle a question raised in several threads (745072, 745841). Thank you.

## Comments (1 top-level)

- **David Healey** **[HOST]** (2026-10-13, votes 0)
  - No, for now any winning solution needs to be able to be reproducible. If there's no way to retrain the weights can be retrained on allowed datasets, or to that would be a problem. 
  
  - No, solutions derived from open source datasets even with NC, are fine to use. 
  
  - I believe the compliance check only applies to the selected submissions, but will clarify if otherwise
