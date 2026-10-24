# What we've learned so far: the answer usually isn't in the library
topic 744417 | by **Truthseeking** (https://www.kaggle.com/truthseeking) | posted 2026-09-29 | votes 0 | comments 0 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/744417

We've written up our progress so far and would really value feedback. In short: library matching scores zero once whole structures are held out; PubChem contains the answer for about 96% of our held-out spectra, but leaves around 10,000 candidates each; and simple single-bond fragmentation gives a real but modest ranking signal (16.7% top-25 against 8.9% for a mismatched-spectrum control).

The notebook has the summary, figures and four open questions: https://www.kaggle.com/code/truthseeking/casmi-2026-progress-report
The full 377-page record is here: https://www.kaggle.com/datasets/truthseeking/casmi-2026-experiment-compendium

We'd especially like to hear how others handle fragment rarity, matching tolerance and isomer separation.

## Comments (0 top-level)

