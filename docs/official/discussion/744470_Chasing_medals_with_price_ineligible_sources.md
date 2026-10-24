# Chasing medals with price ineligible sources
topic 744470 | by **greySnow** (https://www.kaggle.com/shlomoron) | posted 2026-09-29 | votes 18 | comments 16 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/744470

Well, pretty much this. Is using NIST dataset, gated weights etc. is going to be enforced somehow on gold medals? My Claude agent insist we need the NIST based model for better score 🤣 Since I don't care about the money, I might as well go and do it if I can (?) Who knows maybe this is what top teams do already 😁😅

## Comments (6 top-level)

- **David Healey** **[HOST]** (2026-09-29, votes 6)
  I’m sorry, the NIST dataset is not permitted for solutions, any solution using or trained on NIST will be disqualified.  It is not freely available and its  license has restrictions on redistribution of itself or derivatives, including model weights.
    - **M Sato** (2026-09-30, votes 3)
      I understand that prize-eligible teams are required to disclose their methods, which should make it possible to review their data sources. However, is there any way to verify compliance for participants who are not eligible for prizes and are therefore not required to disclose their methods?
    - **greySnow** (2026-09-30, votes 9)
      How do you exactly plan to enforce this rule? We as participants don't have to disclose our solutions. In this sense, un-enforceable limitation actually put all the undisclosed results in qurstion (=every solution except those that disclose for price- and even 1st place don't have to disclose afaik he can just forgo the price, keeping his place and medal)
      
      In LEAP there was a similar situation with a limitation that was enforceable only for disclosed solution, and after the competition ended the host said he want to enforce it for all gold range at the very least but turn out that by kaggle rule he cannot force non-price participanta to disclose their solutions and so it was enforced only for price-receiving participants, putting the legitimacy of all non-price medals in question.
      
      This is not a theoretical question, when this competition finish every rule-abiding participant may very well ask himself if all the people above him did not use some NIST or similar source.
      
      Well this is not the first time a competition is in such a situation….IDK I just don't like this uncertainty when its so easy to 'cheat'. All the people chasing medals should be aware to the situation (unless they are here mainly for price, then it's not a problem)
        - **nofreewill42** (2026-10-01, votes 0)
          So if I understand it correctly (I'm new here), there is a possibility to cheat from inside kaggle's submission framework? How severe is it? If someone is just here for a medal, and they cheat, and they dont want to get caught and earn a medal, they wanna aim for landing outside the prize pool so their cheating wont be detected and keep the medal?
        - **nofreewill42** (2026-10-01, votes 0)
          Is this "cheat" that severe?
        - **nofreewill42** (2026-10-01, votes 0)
          if yes its that severe then how'bout hyperparam tuning and covering it up? lol, dont do that. if your medals are mainly from "cheatable" competitions, thats suss af
    - **yuanzhe zhou** (2026-10-01, votes 5)
      How would the host review solutions? Restricting data usage is very hard.
- **Yan Zhou** (2026-09-30, votes 2)
  This brings back some bad memories from the NeurIPS - Open Polymer Prediction 2025 competition.
    - **greySnow** (2026-09-30, votes 0)
      It was the same there too? How the situation enfolded?
        - **Yan Zhou** (2026-09-30, votes 0)
          Yeah, it was pretty similar. There were the same concerns about external data and whether non-prize medalists would actually be checked.
          
          In the end, I don’t remember anyone being disqualified over external data. Though honestly, that became a pretty minor issue compared to everything else that went wrong in that competition 😅
        - **greySnow** (2026-09-30, votes 0)
          This is what I don't like with bio competitions..sigh
- **PC Jimmmy** (2026-09-30, votes 0)
  When I was looking for additional data it seemed like the NIST price was outrageous.  Am I thinking of the wrong data set?
    - **greySnow** (2026-09-30, votes 0)
      Well a lot of people already would have access to it through lab/work/friends in a lab/work
- **hengck23** (2026-10-02, votes 1)
  Another Kaggle competition called "Detect illegal use of forbidden training data (e.g., inducing poison data in hidden test data)". I think some papers claim to "detect" training data, maybe it is possible
- **MarvinTMB** (2026-10-09, votes 4)
  You do not need NIST or any additional data for a better score.
- **Chen Ken** (2026-10-16, votes 1)
  Could you clarify two source-provenance cases for prize eligibility?
  
  - MassSpecGym's supplement describes NIST20/23-assisted filtering of public-library spectra and states that NIST spectra were not disclosed or used in subsequent analyses. Does using NIST only to remove suspect public spectra make downstream weights trained on the retained public data ineligible? This is distinct from training on NIST spectra or NIST-derived pseudoannotations. The question concerns the filtering step; it does not assert that any particular checkpoint's entire lineage has been verified.
  
  - The Rules, section 2.5.a, provide an exception from relicensing incompatible input data and pretrained models, while the welcome announcement says external resources must allow commercial use and redistribution. For features derived solely from the provided competition training data, does a public contributor's noncommercial/share-alike label prevent use or reproduction of a winning model, or does the competition-data exception apply?
  
  Sources: MassSpecGym supplement (https://papers.nips.cc/paper_files/paper/2024/file/c6c31413d5c53b7d1c343c1498734b0f-Supplemental-Datasets_and_Benchmarks_Track.pdf), Rules (https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/rules), welcome announcement (https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/741359).
