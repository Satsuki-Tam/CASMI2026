# Do MassSpecGym-trained open weights satisfy the training-data licence rule?
topic 742991 | by **Marc Silveira** (https://www.kaggle.com/marcsilveira) | posted 2026-09-24 | votes 2 | comments 2 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/742991

Hi David / Enveda team,

A clarification request on the open-weights rule from discussion 742193 ("open-weight models are acceptable only if distributed in compliance with the licence for the data they were trained on"), because it decides whether several publicly available models can be used in a prize-eligible solution.

The case: MassSpecGym (Bushuiev et al., NeurIPS 2024) is released by its authors under MIT on Hugging Face and GitHub, and its datasheet states no third-party restrictions. Several open models are trained on it and released with permissive code licences — e.g. ICEBERG 2.1's MassSpecGym checkpoints (coleygroup/ms-pred, MIT; the README labels them "open-source" and separately gates the NIST-trained weights behind proof of a NIST licence), and the MIST encoders released with FRIGID.

The ambiguity: MassSpecGym was assembled from MoNA, MassBank and GNPS. MassBank licenses per record and includes CC BY-NC / SA entries; the GNPS library exports it draws on include third-party imports such as HMDB (non-commercial terms). The aggregate dataset's declared licence is MIT; some of its constituent records carry stricter terms.

The question: for rule 742193, is compliance judged against the declared licence of the training dataset as released by its authors (MIT here), or against the record-level licences of the dataset's upstream sources? Concretely: are ICEBERG 2.1 / MIST weights trained on MassSpecGym acceptable in a solution released under MIT?

A general principle would help everyone plan, since this affects any model trained on the public spectral libraries, including ones several teams are already using. Thanks — and thanks for the fast answers so far.

## Comments (2 top-level)

- **David Healey** **[HOST]** (2026-09-25, votes 1)
  Thank you for asking.  For the purposes of solution eligibility, we consider MassSpecGym and models trained on it and released with permissive licenses as fair game.
  
  For the aforementioned rule, what we had in mind to avoid are datasets like NIST, whose licenses aggressively restrict distribution of model weights  (or proprietary commercial datasets like  METLIN, or those distributed by the mass spectrometer companies). I am not aware of prominent open-sourced pretrained models that are trained on those datasets; most of them are not even downloadable.  But if they do exist they would not be eligible.  I hope this helps with calibrating the level of data restrictiveness we are thinking of.  I will add this distinction to the other thread.  Happy to continue answering for specific cases like these.
- **علي الخليفاوي** (2026-09-25, votes 0)
  وضعت قانون في صفحتي يبين نوع العنصر او الجسيم من خلال اطياف المادة وكان التطابق 99بالمئة
