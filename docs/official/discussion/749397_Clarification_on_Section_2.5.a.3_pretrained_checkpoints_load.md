# Clarification on Section 2.5.a.3: pretrained checkpoints loaded at inference
topic 749397 | by **Truthseeking** (https://www.kaggle.com/truthseeking) | posted 2026-10-14 | votes 0 | comments 0 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/749397

Section 2.5.a.3 states that pretrained models with an incompatible licence do not need an open-source grant when “used to generate your winning solution.”
A candidate solution loads a pretrained model (CC BY-NC 4.0 weights, Apache-2.0 code) at inference time. The submission ships code and inference outputs (candidate lists), not the model weights. Our own code and models trained on train.parquet are MIT-licensed.
Two questions:
Does 2.5.a.3 cover pretrained weights loaded at inference and not redistributed?
Does the answer change if the submission ships only candidate lists produced by the model, rather than the model or its weights?
Please also link any thread where a commercial-use restriction on external components was clarified, if one exists.

## Comments (0 top-level)

