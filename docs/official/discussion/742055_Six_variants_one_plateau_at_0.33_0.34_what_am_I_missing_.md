# Six variants, one plateau at 0.33–0.34: what am I missing? 
topic 742055 | by **starkhushi** (https://www.kaggle.com/starkhushi) | posted 2026-09-19 | votes 2 | comments 8 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/742055

Hi everyone. I've been working my way up the retrieval ladder and have now hit a wall I can't reason my way past. I'm hoping the more experienced people here (Grandmasters, Masters, and anyone with a real mass-spec background) can tell me which of my assumptions is wrong.
My modeling notebook, which covers the retrieval pipeline up to the gated library term, is here: CASMI 2026 Modeling Retrieval (https://www.kaggle.com/code/starkhushi/casmi-2026-modeling-retrieval).

How I got here

With my own pipeline (candidate pool = train ∪ COCONUT, entropy library search, analog propagation, in-silico fragmentation):

Step
Public LB

Spectral library search
0.158

+ COCONUT candidates ranked by analog propagation
0.223

+ newer COCONUT release
0.243

+ gated library term
0.250

+ in-silico fragmentation channel
0.283

I then moved to the stronger public pipeline by @prvsiyan (/prvsiyan) (four channels + fingerprint model + calibrated ranker). Huge credit to him: it's the best-documented work in this competition.

Where I'm stuck

Every change I've tried since then lands inside a band the size of the noise:

Variant
Public LB

A. Public pipeline as published
0.335

B. + the popular fork's settings (8.5 ppm, sim⁴, 100 analogs, W1 0.45, ChEBI/LIPID MAPS)
0.335

C. + two extra fingerprint models I trained (new seeds), 4-model ensemble
0.337

D. My two models instead of the originals
0.330

E. C + derivative candidates (±O, ±CH₂, ±hexose, +acetyl, ±2H applied to strong analogs)
0.335

F. Two-ranker engine (prvsiyan ranker 0.65 + @megayak (/megayak)'s 7-library ranker 0.35), as published by @haideptry (/haideptry)
0.323

For scale: prvsiyan measured that resubmitting the same notebook moves the score by ~0.006 because of the ranker's random seed. So everything from 0.330 to 0.337 is effectively one number, while the top of the LB is at 0.36.

The three things I don't understand

1. My fingerprint models looked much better offline, then did nothing on the LB.
I rebuilt the training data and trained two more spectrum→fingerprint models. On my held-out split (a random 2% of structures) they reached hard-negative top-1 of 0.694 and 0.640. Swapping them in alone scored lower (0.330) than the originals. My guess is that a random structure split is far too easy: near-identical molecules leak across it. How are you splitting validation for the fingerprint model — by scaffold, by source library, or by something else?
2. The domain gap.
The test set is 100% timsTOF, and the public fingerprint models reportedly score ~0.80 on the public libraries they were trained on but ~0.49 on held-out timsTOF natural products. I'm now fine-tuning the existing models with half of every batch drawn from timsTOF spectra, validating on enveda-np-examples. But the only large timsTOF source is enveda-180, which is drug-like chemistry. Is instrument matching worth more than chemistry matching here? Has anyone seen fine-tuning on enveda-180 help or hurt?
3. Is ~0.34 a ceiling for retrieval?
Derivative candidates fired on the hidden test and still didn't help (0.337 → 0.335). A bigger pool keeps hurting (PubChem is catastrophic, as prvsiyan measured). That makes me suspect a large share of the hidden test is Class 3, which retrieval can never reach. For those above 0.35: is the gain coming from better ranking of the same pool, from a different pool, or from generating structures?

What I'd most like to hear

- A validation setup that actually orders configurations the way the LB does. The enveda-np-examples split doesn't, for me.

- Whether anyone has made a de novo / generative component add anything, given the "generation can hurt before it helps" argument in another thread.

- From anyone with MS/MS experience: is there a physics-based signal (isotope patterns, charge-carrier rules, collision-energy behaviour) that the four current channels ignore?
Thanks in advance.

## Comments (3 top-level)

- **Evsprakash** (2026-09-19, votes -3)
  Area
  Criticality
  Why
  
  MS/MS interpretation
  🔴 Very high
  You must infer molecular structure from fragment ions rather than simply identify a known compound.
  
  Machine learning
  🔴 Very high
  The problem naturally supports supervised, unsupervised/self-supervised, and potentially reinforcement-learning approaches.
  
  Chemical knowledge
  🔴 Very high
  Fragmentation rules, neutral losses, adducts, formula constraints and substructures strongly affect predictions.
  
  Large-scale data processing
  🔴 Very high
  ~2.5 million spectra and ~275k structures require efficient preprocessing and indexing.
  
  Spectral similarity/search
  🔴 Very high
  Class-1 compounds can potentially be recovered through reference-spectrum matching.
  
  Structure retrieval
  🔴 Very high
  Class-2 molecules require connecting spectra to external chemical databases.
  
  De novo prediction
  🔴🔴 Extreme
  Class-3 compounds aren't in PubChem, so database lookup alone cannot solve them.
  
  Multi-spectrum aggregation
  🔴 Very high
  One molecule can have 1–16 spectra; you need one final ranked list per molecule.
  
  Model validation
  🔴 Very high
  Random spectrum-level splitting can produce misleadingly good results because the same molecule may occur in multiple spectra/libraries.
  
  Computational resources
  🟠 High
  3 GB input is manageable, but training large neural models from scratch can become computationally expensive.
- **DancingLumberjack** (2026-09-19, votes 3)
  Your third question — "is ~0.34 a retrieval ceiling, and are the top teams gaining from better ranking, a different pool, or generation?" — is answerable from CV, and our answer is ranking, not the pool. Numbers, then the method, because the method is the part that took us longest to get right.
  
  We ran a per-query failure taxonomy on 250 held-out natural-product structures under the class-2 condition (every spectrum of the held-out structure removed from every library — see below). Of the queries not ranked first:
  
  bucket
  queries
  MRR headroom
  
  truth absent from the candidate set (recall)
  4 (1.6 %)
  +0.016
  
  truth present, ranked 2–25
  100 (40 %)
  +0.274
  
  truth present, ranked > 25
  6 (2.4 %)
  +0.024
  
  Ranking beats recall about 17:1 in available MRR. Expanding the pool cannot buy what is not missing: of the 4 recall failures, 2 were formula mismatches, 1 fell outside a ±10 ppm window, 1 is absent from COCONUT.
  
  Two details inside the ranking bucket that surprised us:
  
  - The truth is usually not short of analog evidence — its mass-shifted analog score is already ~90 % of the best candidate's (median), and only 2 % of ranking failures are analog-poor. Stronger analog propagation is not what separates the truth from the isomer that beat it.
  
  - The winner is usually not a close analogue of the truth — median Tanimoto between them is 0.48, only 20 % above 0.7. These are structurally different molecules of the same formula.
  
  So the plateau looks like isomer discrimination after analogs have spoken, and the failures are concentrated: 36 of our 250 sit at rank 2 and 23 at rank 3.
  
  On fingerprint models that look better offline and do nothing on the leaderboard. Two measurement traps cost us real submissions:
  
  - A random 2 % split of structures is contaminated. The 250 enveda-np-examples structures also have 55,599 spectra in riken / gnps / mona / massbank / pluskal_ms2 / msdial / drug_plus / masaryk. Holding out by ingest_lib, or by a random split that only removes some rows, leaves the structure in the library and a plain spectral search finds it. Hold out by InChIKey14 across every library, and check it: run your library search on the holdout and require zero exact InChIKey14 self-matches (we get best cosine 0.000). If it returns any, every number downstream is inflated.
  
  - Your CV probably has more spectra per molecule than the test — and the fix has a trap in it. The public test copy averages 3.03 spectra per molecule; our held-out sets average 4.34 and 4.99. Resampling CV molecules to the test's count distribution — rebuilding the fingerprint scores and any cross-spectrum aggregates from the same sample — gives the honest effect size at test-like counts, and that is the right instrument for ranking candidate features against each other. For one aggregation feature we measured +0.019 at our own counts and +0.0065 ± 0.0033 count-matched (5 draws).
  The trap: those two numbers are on different scales, so whatever you use to translate a CV delta into an expected leaderboard delta must be built from CV numbers measured the same way. We mixed them once — applied a translation fitted on full-count CV to a count-matched CV number — and under-predicted a submission by 4×. Measured consistently it was fine: full-count CV predicted +0.006 for that feature and the leaderboard moved +0.008, inside the resubmission noise you and prvsiyan measured.
  Two practical notes: a single resampled draw is worth ±0.011 on this metric, so one draw is not evidence — average five or more; and capping k at the spectra a molecule actually has drags the realised mean below your target (we landed at 2.5 aiming for 3.03 before compensating), so report the sampler's realised mean next to the test's.
  
  On the domain gap. Worth checking what the instrument label selects in your pool before fine-tuning on it. In train.parquet there are 1,154,969 timsTOF rows and 1,153,785 of them are enveda-180; only 1,184 lie outside it, and those belong to the 250 np-examples structures. So "fine-tune on timsTOF" is in practice "fine-tune on enveda-180 chemistry" — it can teach the instrument's fragmentation style but not natural-product chemistry, and the 0.80-vs-0.49 gap you are seeing is at least partly a chemistry gap wearing an instrument label.
  
  On the noise floor: your reading matches ours. Our last several submissions span 0.318–0.327 and only the ends of that range are distinguishable; we treat anything under ~0.006 as unmeasurable from one submission.
    - **starkhushi** (2026-09-20, votes 2)
      This is extremely helpful, especially the 17:1 ranking-vs-recall result. That changes how I’m thinking about the plateau — I was leaning toward missing candidates/Class 3, but your failure taxonomy suggests there’s much more to gain from isomer discrimination and ranking.
      
      The InChIKey14 holdout point is also exactly the validation issue I suspected. I’ll rebuild my fingerprint validation around that and match the spectra-per-molecule distribution to the test before judging new features.
      
      Really appreciate you sharing the actual numbers and methodology — this gives me a much more concrete direction to test.
    - **alex chilton** (2026-09-21, votes 2)
      Our numbers match DancingLumberjack's almost exactly, from a separate pipeline, so the
      diagnosis looks solid rather than like anyone's holdout artifact:
      
                                           DancingLumberjack        us
      np-examples spectra in 8 other libs          55,599          55,599
      spectra/molecule, holdout                 4.34 / 4.99          4.74
      truth ranked >25                            6 (2.4%)        6 (2.4%)
      truth at rank 2                                   36              42
      median Tanimoto(truth, winner)                  0.48          0.4919
       fraction above 0.7                             20%             26%
      
      The oracle version of their 17:1, on 249 held-out natural products under the same class-2
      condition (every spectrum of the truth removed from every library, library route asserted
      at exactly 0.0000):
      
      shipped                                          MRR@25 0.7315
      same-formula blockers removed                           0.9869
      truth at rank 1 everywhere                              1.0000
      
      So perfect same-formula separation is 95.1% of the total gap. Everything else combined,
      including recall, is worth 0.013. Of about 83 candidates in a window, roughly 66 share the
      truth's formula. In the rank-2 cases specifically, 40 of 42 blockers carry the truth's exact
      formula and 69% have a different Murcko scaffold. Mass and composition cannot separate them
      by construction.
      Answering your question 3 directly: for us the gain is not in the pool. NPAtlas adds 1,113
      structures our pool lacks (0.16% growth), 45 of them inside the test's 279-374 Da band, and
      zero holdout truths. LOTUS: 97.5% already contained, zero truths added. That is consistent
      with DancingLumberjack's recall bucket.
      What I can contribute is negative results, since they are what cost us the most time. Seven
      things aimed at same-formula separation, each measured marginally against the shipped ranker
      with an out-of-fold control that must read exactly +0.0000:
      
      fragment channel (MetFrag-lite)   +0.00367, and leave-one-out says the whole channel
                                       is +0.0025, i.e. free to delete
      connectivity scoring              +0.0000 check-half, 0 of 10 splits positive
      formula/sub-formula gate          +0.0000, the fit half chose weight 0.0 in all 10 splits
      collision-energy depth            80.3% separation on isomers -> 4 molecules of 249 move
      S-CNLF (base neutral loss)        truth reaches its own base loss 45.4% vs decoys 18.6%,
                                       but fails its own test 54.6% of the time
      ICEBERG as a learned feature      +0.0015 in the >100-candidate stratum
      ring-cut infeasibility            passes a paired test on the blocked pairs (18 of 24
                                       unrelated ones, 75.0%, p=0.023) and delivers
                                       -0.00178 marginally, 3 molecules of 247
      
      The pattern is the same every time. A real separation on a selected cohort, then nothing
      once it competes with the ranker's own probability. The coverage column explains it: these
      features discriminate on a third to a half of pairs, and the ranker is already right on most
      of those.
      DreaMS was the strongest instrument we tried and it does not clear the bar either. It
      separates same-molecule from same-formula spectrum pairs at AUC 0.88 in general, but on our
      actual blocked pairs, using measured spectra on both sides, the truth is closer than the
      blocker in only 20 of 42. Below chance. Split out, it is 51.9% on different-scaffold pairs
      (n=27) and 40.0% on near-twins. A structure encoder trained against a frozen DreaMS teacher
      can at best place a candidate where its own spectrum sits, so that number caps the whole
      approach.
      Two method notes that cost us submissions, in case they are useful:
      An AUC against a selected subpopulation is not an MRR. We had a feature at 80.3%
      truth-above-isomer that moved 4 molecules of 249. The selection is what makes it look large.
      A decoy control has to differ in the one property under test and match everything else. We
      tested a halogen isotope signal by scanning for peak pairs at the 37Cl spacing, controlled
      it with half-integer mass offsets, and got a 100x separation. Then we validated against known
      structures: 8.5% precision. Half-integer offsets fall in the gaps between peak clusters and
      cannot fire whether the signal is real or not. The control could not fail.
      So the question I would most like answered, same as yours but narrower: has anyone got
      anything to work on two same-formula molecules with different scaffolds, measured marginally
      against a ranker rather than as a standalone AUC? Seven attempts here say the shipped
      channels have already extracted whatever those signals contain, and I would like to be wrong
      about that.
        - **starkhushi** (2026-09-22, votes 0)
          No, nothing worked here either. Two data points in the same direction:
          
          Fragmentation, as a choice rather than an AUC. On a leak-checked class-2 split, only the cases where the truth is in the top 3 but not first (n=72, SE 0.056), asking each variant to pick one of three. Random = 0.333:
          
          explain - chance coverage   0.292
          +-1 H / 0 H (strict)        0.250
          +-2 H, 0.01 Da (as used)    0.222
          fewer fragment masses       0.181
          
          Nothing above chance — your "+0.0025, free to delete" from another angle. Notebook (https://www.kaggle.com/code/starkhushi/casmi-2026-fragmentation-check)
          
          On your intrinsic-metric point. Fine-tuned the public FPNet checkpoints on timsTOF: held-out np-examples hard-negative top-1 0.459 → 0.491 (merged), 0.433 → 0.464 (single); board 0.337 → 0.328. Same shape as your 26.5% for −0.135 MRR.
        - **alex chilton** (2026-09-22, votes 0)
          I am getting a little traction with Mist - its a component in the iceberg frigid_pretrained_checkpoints - not a lot but i have been playing around with it…have a play - would be interested if you find anything concrete - I am off hiking for 3 weeks so i guess all will be revealed and different when i return!
    - **Nebou Rocket** (2026-10-11, votes 0)
      Thank you for the detailed explanation. I have a question: why did you reduce the number of spectra per molecule to 3?
- **?** (2026-10-11, votes 0)
  
