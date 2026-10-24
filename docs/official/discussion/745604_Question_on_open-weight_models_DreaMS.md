# Question on open-weight models: DreaMS
topic 745604 | by **Truthseeking** (https://www.kaggle.com/truthseeking) | posted 2026-10-03 | votes 0 | comments 2 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/745604

Question on open-weight models: DreaMS

Hi David, a quick licence check on the DreaMS model (Bushuiev et al., Nat. Biotechnol. 2025). Its weights are published under CC BY 4.0 (Zenodo 10997887). It was pretrained on public GNPS spectra (GeMS) and fine-tuned on about 25k MoNA spectra. The paper states that no NIST20 spectra were used for training, but NIST20 was used to evaluate the fine-tuned embedding model.

Is a model whose weights never trained on NIST, but whose checkpoint was evaluated on NIST20, acceptable under the NIST rule?
Is DreaMS acceptable for final submissions given its MoNA fine-tuning data?
Thanks!

## Comments (2 top-level)

- **Marie Killian** **[Organizer]** (2026-10-05, votes 0)
  Thanks for clarifying! Yes, DreaMS weights are allowed.
- **?** (2026-10-05, votes 0)
  
