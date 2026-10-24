# Is a model pretrained only on public MassIVE/GNPS data allowed if its authors monitored a NIST20 probe during pretraining?
topic 748799 | by **HIDEYO CHIBA** (https://www.kaggle.com/hideyochiba) | posted 2026-10-13 | votes 0 | comments 2 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/748799

Hi organizers, a quick eligibility question about Discussion 744470 (NIST-trained solutions are disqualified).

We are considering the self-supervised DreaMS backbone (Bushuiev et al., Nat. Biotechnol. 2025; weights on Zenodo 10997887, CC BY 4.0). Its pretraining data is GeMS only (public MassIVE/GNPS LC-MS/MS files). We would not use any of the released fine-tuned heads, since some of those were fine-tuned on NIST20/MoNA, and we would fine-tune only on train.parquet / MassSpecGym.

One detail: during pretraining, the authors' code logged a validation metric computed by a separate linear probe trained on a NIST20+MoNA subset. The backbone itself received no gradients from NIST data (the probe ran under torch.no_grad), but the released checkpoint might have been chosen partly by looking at that metric.

Would using this self-supervised backbone be considered "using NIST" under the rule? Thank you!

## Comments (1 top-level)

- **David Healey** **[HOST]** (2026-10-13, votes 0)
  If the model weights aren't a derivative of NIST then they are not in violation of the nist license so should be fine.
    - **HIDEYO CHIBA** (2026-10-13, votes 0)
      Thank you very much, David, for the quick and clear answer!
      
      Just to confirm our understanding: we will use only the self-supervised DreaMS backbone (ssl_model.ckpt, pretrained on GeMS / public MassIVE data), which is not derived from NIST. We will not use any of the released fine-tuned heads, since some of those may have been trained on NIST20. Any further training on our side will use only the competition data and other permitted sources.
      
      Thanks again for clarifying, and for hosting this competition!
