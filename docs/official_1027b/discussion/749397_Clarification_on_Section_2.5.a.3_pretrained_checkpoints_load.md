# Clarification on Section 2.5.a.3: pretrained checkpoints loaded at inference
topic 749397 | by **Truthseeking** (https://www.kaggle.com/truthseeking) | posted 2026-10-14 | votes 0 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/749397

Section 2.5.a.3 states that pretrained models with an incompatible licence do not need an open-source grant when “used to generate your winning solution.”
A candidate solution loads a pretrained model (CC BY-NC 4.0 weights, Apache-2.0 code) at inference time. The submission ships code and inference outputs (candidate lists), not the model weights. Our own code and models trained on train.parquet are MIT-licensed.
Two questions:
Does 2.5.a.3 cover pretrained weights loaded at inference and not redistributed?
Does the answer change if the submission ships only candidate lists produced by the model, rather than the model or its weights?
Please also link any thread where a commercial-use restriction on external components was clarified, if one exists.

## Comments (1 top-level)

- **Marie Killian** (2026-10-26, votes 0)
  Thank you for your patience. 
  Section 2.5.a.3 does cover permitted pretrained weights used at inference, provided you provide the original training code and permitted training data. The training code and permitted training data need to be provided if the pretrained weights are used anywhere in your solution (including generating the candidate list). Section 2.5.a.3 does not change the reproducibility requirement.
  If you are using candidate lists from another pretrained model, but the model weights themselves were not used to generate those lists, then if the candidate list falls within the regulations for permitted data, that candidate list can be used.
  Clarification on permitted external data sources is given in https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/750330
