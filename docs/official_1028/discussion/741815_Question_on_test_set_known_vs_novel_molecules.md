# Question on test set: known vs novel molecules
topic 741815 | by **Tyree Jones393** (https://www.kaggle.com/tyreejones393) | posted 2026-09-17 | votes 1 | comments 2 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/741815

Hi — competing as tyreejones393. Quick question on the brief: "both known and novel molecules" — am I reading right that part of the test set is structures absent from public libraries? If so, that sets the ceiling for pure retrieval approaches, which is useful to know going in. Appreciate you all putting this one on. Natural products is the right fight.

Best,
Tyree

## Comments (1 top-level)

- **Rishav Yadav** (2026-09-17, votes 2)
  Yeah exactly, you got it right! Some of the test molecules are completely novel and not in any public database (not even in PubChem). So pure library search will definitely hit a ceiling at some point, and we'll need some de novo / generative approach to catch the rest. Best of luck!
    - **Tyree Jones393** (2026-09-17, votes 1)
      Appreciate the straight answer — that's exactly what I needed going in. Confirms the build: retrieval where the library reaches, chemistry-first ranking where it doesn't. Good luck to you too.
