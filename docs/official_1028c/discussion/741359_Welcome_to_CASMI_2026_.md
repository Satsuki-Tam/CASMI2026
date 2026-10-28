# Welcome to CASMI 2026!
topic 741359 | by **David Healey** **[HOST]** (https://www.kaggle.com/davidhealeyenveda) | posted 2026-09-14 | votes 27 | comments 11 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/741359

Welcome to CASMI 2026! Identifying molecules from their mass spectra is one of the most important challenges in life sciences, but the number of machine learning scientists who have worked on mass spectra is very small relative to the size and importance of the scientific problem. This creates a great opportunity to have a large impact in a short amount of time. Hence this competition!  

The kinds of methods that have been developed in recent years against standing benchmarks like MassSpecGym span a wide variety of approaches that resemble those used across technology and life sciences. We are very excited to see the approaches this community comes up with to tackle this problem. We are especially excited to be providing spectra for many molecules whose structures have not been previously described. 

A note on external data and licensing

We want everyone to have a fair and enjoyable competition, so a quick reminder on the use of external data and models.

Per the competition rules, the winning solution cannot include any licenses that would otherwise prohibit (EDIT)   redistribution. When you submit a winning solution, you grant us, the Competition Sponsor, a license to that solution and represent that you have the unrestricted right to grant it. Any external data, models, or tools you rely on must be compatible with that license.

We're aware that datasets exist which carry licenses that fall into this category, i.e. terms that (EDIT) restrict  redistribution. These should be avoided. Solutions built on data or tools that (EDIT) are not open source  will not be eligible to win, and we reserve the right to disqualify any submission that does not comply or can’t be reproduced with allowed data and tools.

As always, any external data used must be free to use, publicly available and equally accessible to all participants.

Special thanks to the Kaggle team Ashley, Walter, and Addison for all their support!

Happy modeling! 

EDIT 17 Oct 2026 please see the discussion topic here.  Open source external data with noncommercial provisions are acceptable
https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/750330

## Comments (5 top-level)

- **?** (2026-09-17, votes 0)
  
- **kenneth uchegbu** (2026-10-01, votes 0)
  please what technique do i use to Concatenate key spectral metadata as tabular features: precursor_mz, ionization_mode, adduct (one-hot encoded), collision_energy_ev, and instrument_type.
- **Naseem Akhtar** (2026-10-02, votes 0)
  What if I learn every concept from Gemini?? Means of python , data science and every skill needed?? Is it that reliable or I should use some different app?? Please guide me.
    - **kenneth uchegbu** (2026-10-02, votes 0)
      Using gemini is very reliable. Also, you will need to watch youtube tutorials or register for a course that will be guiding you on how to go about learning. Lastly, practice with previous competitions from kaggle
- **Amirah Alimi** (2026-10-03, votes 0)
  Looking to form or join a team for CASMI 2026 - need two more people.
  
  Where I'm at: I've completed a thorough EDA pass on the training data molecule-level train/validation splitting (to avoid spectra from the same structure leaking across both sets), rebalancing the heavy spectra-per-molecule skew, checking precursor mass and adduct coverage against the test set's documented ranges, and isolating a systematic adduct-mislabeling bug that was corrupting ~40k rows (traced to an adduct-standardization error, fixed rather than discarded). Background: final-year Biochemistry student, currently a Machine Learning Engineering intern, comfortable in Python and ML fundamentals, with real domain chemistry knowledge to bring to structure elucidation. Worth noting this is my first Kaggle competition specifically, though not my first serious ML project.
  
  What I need: two teammates who'll engage seriously and contribute real work I'm not filtering by experience level, just looking for genuine commitment. Complementary skills that would help a lot: cheminformatics/RDKit experience, deep learning or generative modeling (spectrum-to-structure especially), or bandwidth to help split up retrieval-baseline and modeling work.
  
  Comment or DM if you're interested, or if you've got a team with a spot open.
  
  — Dara
    - **kenneth uchegbu** (2026-10-03, votes 0)
      i already responded to your message. can you hmu on Linkedin for further discussion. Username: Kenneth Uchegbu
    - **Luis Angel Urdez Rojas** (2026-10-04, votes 0)
      Please contact me Angel Urdez (https://www.linkedin.com/in/luis-%C3%A1ngel-urdez-rojas-203253301)
    - **TICY** (2026-10-06, votes 0)
      Hi Amin,
      
      I saw your team-up post. I work on text-based person search (TBPS) — cross-modal retrieval, embedding learning, and re-ranking, so analysing retrieval baselines is squarely in my area, and it's what you said you're looking for help with.
      
      The part of your post that stuck with me most was the ~40k-row systematic adduct mislabeling you traced back to the adduct-standardization step. Bugs like that quietly destroy a retrieval pipeline, and I've spent a lot of my own time guarding against the equivalent failure on the retrieval side.
      
      On time — I want to be concrete rather than vague about this:​
      
      I can commit weekday evenings plus most weekends from now until the Dec 7 merge deadline, and through the Dec 14 final submission.
      I'd rather show up steadily than in occasional heroics. In a competition like this, consistency compounds more than intensity.
      I don't expect to be the strongest person on the team. I just want to actually deliver my part and not leave anyone waiting on me.
      What I'd bring:​
      
      Retrieval-side modelling — candidate scoring, cross-modal embedding alignment, re-ranking, and ensemble selection under a submission runtime budget.
      Validation infrastructure — this is my strongest area. Leakage in a validation split is the most common way retrieval pipelines lose quietly, so I've put a lot of work into split design and leakage self-checks. I'd like to build a harness that can actually tell configurations apart, rather than just report one number.
      Pipeline and kernel iteration offline, so experiments don't eat into submit-time budget.
      On division of labour:​ the chemistry side — molecular formula inference, isomer disambiguation, adduct standardisation — is where I'm weakest and where you're strongest. I'd want you leading that, and me handling retrieval and validation.
      
      One more thing: there's a thread on hard-coded molecule_id → SMILES mappings (discussion 745715) that a couple dozen teams appear to be using. I don't want any ambiguity around our submission, so I'd exclude that line entirely. Happy to compare notes on how to handle it if you've seen that discussion too.
      
      You mentioned you're looking for two more people. If you have someone in mind, I'd be glad to talk with them too.
        - **Amirah Alimi** (2026-10-06, votes 0)
          Amirah Alimi (www.linkedin.com/in/amirah-alimi-11947b288) contact
- **kenneth uchegbu** (2026-10-09, votes 0)
  please who can help me with the reson why code has been saying submission error for like 4 submissions now?
    - **Oktavianus Misro Adrianto** (2026-10-17, votes 0)
      Maybe check your internet connection.
