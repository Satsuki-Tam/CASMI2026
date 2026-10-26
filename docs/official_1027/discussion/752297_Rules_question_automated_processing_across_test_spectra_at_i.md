# Rules question: automated processing across test spectra at inference
topic 752297 | by **Odim David Emeka** (https://www.kaggle.com/odimdavidchukwuemeka) | posted 2026-10-24 | votes 1 | comments 3 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/752297

Hi David,

A quick rules clarification. Is it permitted for a submission notebook to apply automated, unsupervised processing that uses relationships across the test spectra at inference time? Examples would be clustering test spectra by similarity, or using a confidently identified test molecule to help rank candidates for similar test molecules.

Everything would be fully automated inside the notebook, with no hand labelling and no human prediction (Rule 2.5.b), and no external information about the test set.

A yes/no would be very helpful. Thank you!

## Comments (3 top-level)

- **Vitalii Neibauer** (2026-10-24, votes 0)
  +1, a short yes/no here would help many teams plan their final selections. Specifically: is it allowed for a notebook to use, fully automatically and label-free, the similarity between test spectra of different molecule_ids at inference (e.g. letting a confidently identified test molecule inform the ranking of candidates for a spectrally related test molecule)? Thank you!
- **PC Jimmmy** (2026-10-24, votes 0)
  Its always been ok to use test data in fashion you describe, see no reason this would be different.
- **Marie Killian** (2026-10-26, votes 0)
  Yes, automated, unsupervised processing across test spectra at inference time is allowed.
