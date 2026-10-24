# Problem is in Isomer identification + Off-the-shelf LLM's are really bad at this task
topic 745468 | by **Adarsh** (https://www.kaggle.com/madarshbb) | posted 2026-10-03 | votes 6 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/745468

In more than 95% of my validation examples, my model is able to predict the correct molecular formula, but fails to differentiate between the isomers.

When I asked Claude Opus 5.5 High, these were its guesses:-

Funnily, the correct answer was ranked last among the di-hydroxy anthraquinones :)

Goes to show off-shelf LLM's aren't very good at this

But once you can determine the molecular formulas for majority of the cases, you can try measuring the molecular formulas of the fragments itself and judge the plausibility of producing those fragments given the original formula of the whole molecule, collision energy, population prior of the fragments over libraries, etc…

Trying this next.

## Comments (1 top-level)

- **Pratham** (2026-10-03, votes 0)
  Thank you!
