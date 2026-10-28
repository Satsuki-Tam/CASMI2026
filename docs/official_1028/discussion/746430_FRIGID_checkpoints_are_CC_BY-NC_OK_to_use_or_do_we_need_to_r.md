# FRIGID checkpoints are CC BY-NC: OK to use, or do we need to retrain?
topic 746430 | by **Alpha223** (https://www.kaggle.com/alpha223) | posted 2026-10-07 | votes 3 | comments 8 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/746430

Hi David / Enveda team,

Quick licensing question about one specific model, following up on your answer in 742991 (models trained on MassSpecGym and released under permissive licenses are fair game).

FRIGID from the Coley group (github.com/coleygroup/FRIGID) generates candidate structures from a spectrum: a MIST encoder predicts a fingerprint, and a diffusion decoder writes molecules from that fingerprint plus the formula. The code is Apache-2.0, and as far as we can tell everything was trained on public data only (MassSpecGym and NPLIB1, no NIST or METLIN). The catch is that the pretrained checkpoints on Zenodo (record 19685145, which contains the decoder and the MIST encoders) are released under CC BY-NC 4.0.

So two questions:

- Can a prize-eligible solution use these checkpoints as they are released, even though the weights themselves carry a non-commercial license?

- If not, is it fine to retrain the models ourselves with the Apache-2.0 code on allowed data (MassSpecGym, train.parquet, public structure databases like PubChem / COCONUT) and use our own weights under a permissive license instead?

Asking before we build anything on it, since you mentioned before that the final compliance check can remove teams from the leaderboard.

Thanks!

## Comments (6 top-level)

- **Patrick Chan** (2026-10-07, votes 0)
  The competition's own data is CC BY-NC 4.0, so the whole challenge is a non-commercial context. CC BY-NC 4.0 weights permit non-commercial use — so using them inside this competition is arguably consistent with their licence, not a violation. But the hosts' earlier guidance ("models trained on MassSpecGym and released under permissive licences are fair game") points the other way: they singled out permissive, and CC BY-NC is not permissive. Can the host help confirm above?
- **Patrick Chan** (2026-10-07, votes 0)
  One more check for your question: is NPLIB1 itself NIST-derived? The question asserts "no NIST or METLIN", but NPLIB1 is the CANOPUS natural-product library — worth confirming its provenance, since NIST-derived training data is NOT allowed?
    - **Alpha223** (2026-10-07, votes 0)
      Thanks Patrick, both fair points.
      
      On NPLIB1: I checked the MIST repo (Coley group), which is where the dataset was assembled. It describes NPLIB1 (originally "canopus_train") as public data extracted from GNPS, prepared for the 2021 CANOPUS paper. NIST only shows up there for a separate dataset (CSI2022), which isn't the one in question. So as far as I can tell NPLIB1 is GNPS-only, but happy to be corrected if anyone has seen otherwise.
      
      On the licence, I agree it could be read either way, which is why I'd rather have an explicit answer. @David (/David), since ChEBI/LIPID MAPS were confirmed fine in 745841, could you say whether the same applies to the CC BY-NC FRIGID checkpoints, or whether we should retrain them from the Apache-2.0 code?
- **Odim David Emeka** (2026-10-12, votes 0)
  Following up on this question: we’d also like a host ruling on whether model checkpoints released under CC BY-NC 4.0 (e.g. FRIGID from the Coley group) count as “released with permissive licenses” for prize-eligible submissions. If not, is training from the published code with our own data acceptable? Thank you!
- **Truthseeking** (2026-10-13, votes 0)
  Hello, a question on Rule 2.5.a.3 for the FRIGID checkpoints discussed in this thread.
  Rule 2.5.a.3 says that pretrained models with an incompatible licence need no open-source grant when they are “used to generate your winning solution”. FRIGID’s checkpoints on Zenodo (record 19685145) are CC BY-NC 4.0, and its code is Apache-2.0.
  Does 2.5.a.3 cover those checkpoints if a solution loads them at inference but does not redistribute the weights? And does it still cover them if the submission contains only the model’s outputs?
  We are asking before deciding whether to build on them.
- **Marie Killian** (2026-10-13, votes 1)
  Yes, the official FRIGID checkpoints are allowed for prize-eligible solutions. Teams do not need to retrain the models themselves, but must provide the original training code and access to the permitted training data needed to reproduce the weights.
- **Truthseeking** (2026-10-15, votes 0)
  MS-GPT MIST encoder: do FRIGID checkpoint terms cover third-party mirrors?
  
  Question on the FRIGID checkpoint terms: the MS-GPT project (github.com/VIKI623/MS-GPT) redistributes MIST spectrum encoders that originate from the FRIGID checkpoint release. Do the FRIGID checkpoint terms in your reply extend to redistributed copies of those checkpoints in third-party mirrors, or only to the official release? We are proceeding under the conservative reading (CC BY-NC 4.0 with disclosed provenance) unless you say otherwise.
    - **Marie Killian** (2026-10-16, votes 0)
      The previous statement was only about the official FRIGID release. But if these third-party mirrors comply with the licensing rules and you can provide the original training code and permitted training data to fully reproduce them, they would be permitted to be used.
