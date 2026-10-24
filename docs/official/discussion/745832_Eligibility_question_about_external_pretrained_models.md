# Eligibility question about external pretrained models
topic 745832 | by **Joakim Eklund** (https://www.kaggle.com/joakimeklund) | posted 2026-10-04 | votes 0 | comments 6 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/745832

Hi David,

I have a narrow eligibility question about external pretrained models.

Suppose a publicly released model was trained on a public dataset that includes community spectra whose annotations were derived from matching against NIST, but does not redistribute the proprietary NIST library itself.

Would such pretrained weights be eligible for CASMI26, or would any NIST-derived subset need to be excluded and the model retrained?

Thanks!

## Comments (3 top-level)

- **David Healey** **[HOST]** (2026-10-07, votes 0)
  @joakim (/joakim) thank you, interesting question.  I'm inclined to say yes, this would be a derivative of NIST and NIST does not allow derivatives.  And it would give you annotated data that is only available because of access to NIST.  But if you point me to the dataset in question I will take a look in more depth, there may be a well established exception.
- **David Healey** **[HOST]** (2026-10-07, votes 0)
  Actually I will make an exception here after looking into it more.  There is at least one dataset in GNPS that has this form, with fairly old and small NIST data.  We'll say if it was on GNPS well before the competition started (say, 6 months), and hasn't been taken down, its fair game.
    - **Amin** (2026-10-09, votes 1)
      Thank you, David, that is very helpful. To make sure we apply it correctly, could you confirm whether it covers the GNPS spectral library GNPS-NIST14-MATCHES (https://external.gnps2.org/gnpslibrary)? As far as we understand, it holds spectra from public GNPS/MassIVE datasets whose structure annotations came from matches against NIST14, and it has been publicly downloadable from GNPS for several years.
      
      If it is covered, may we use it (a) as reference spectra for library matching at inference time and (b) as training data for our own models? We would not use any NIST library itself or any model trained on NIST data.
      
      Thanks again!
        - **David Healey** **[HOST]** (2026-10-09, votes 0)
          Yes, specifically GNPS-NIST14-MATCHES is allowed, because it has been in the GNPS open repository for many years and we won't require everyone to remove it from their GNPS library dumps.  Allowed for library matching and training.
          
          However, I believe NIST would consider any newly created such datasets to be derivatives and in violation of their license.
- **Joakim Eklund** (2026-10-07, votes 0)
  Thank you, David. One narrow follow-up on inference inputs: we generate our own candidate structures for each unknown spectrum, and each candidate has a molecular formula derived from that candidate structure. Would it be permitted to use that candidate-derived formula as an input when scoring that same candidate with an eligible pretrained model, provided that no ground-truth formula or structure is used? The scores would only be used to rerank candidates sharing the same molecular formula, not to compare scores across different formulas.
    - **Marie Killian** **[Organizer]** (2026-10-14, votes 0)
      Yes, using molecular formulas for candidate structures as inputs to an eligible pretrained model is permitted.
