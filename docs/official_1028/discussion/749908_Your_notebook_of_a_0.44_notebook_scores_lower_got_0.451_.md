# Your notebook of a 0.44+ notebook scores lower? got (0.451+)  
topic 749908 | by **Aryan Awasthi** (https://www.kaggle.com/aryanawasthiteykik) | posted 2026-10-16 | votes 2 | comments 9 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/749908

Copies of top notebooks scoring lower? Check your environment

Pin the Docker image. Several top notebooks assert Python 3.12 and RDKit versions. A copy that runs on the latest image (Python 3.13) can silently score lower. One of our unpinned copies of a 0.441 notebook scored 0.427; the pinned copy scored 0.441. In the notebook’s settings choose Pin to original environment, or copy docker_image from kaggle kernels pull -m.

What separates the 0.446+ notebooks from the 0.443 ones, as far as we can tell from the public code: a lower PubChem promotion threshold (rel > 150), a metric-identity-exact engine-2 rank-2 insert, and the CC-BY ChEBI/LMSD candidate set.

Quick tip after burning a few submissions: when we copied some of the top public notebooks, a few scored noticeably lower than their source, one by over 0.01.

The cause wasn’t the code; it was the runtime environment. Some of these pipelines are sensitive to the Python/library versions they were built on. Matching the original environment fixed it, and our copies reproduced the original scores exactly.

Two other small lessons:

- A title’s score isn’t always the notebook’s real score. Check the score on the notebook page.

- Most of our “small improvements” on top of strong pipelines ended up slightly worse than the untouched version.

## Comments (1 top-level)

- **Kino Lutor** (2026-10-16, votes 1)
  we are looking for equally skilled Team member's here!if you want to join,leave your contact information or just come to contact us!!!🥳
    - **AlexMoura2023** (2026-10-16, votes 1)
      Hi! I'm interested in exploring a potential collaboration with your team.
      
      I'm Alex Moura, an Associate Professor at the Federal University of Juiz de Fora (UFJF), Brazil.
      
      A brief overview of my academic background:
      
      ****- Ph.D. in Electrical Engineering — Federal University of Minas Gerais (UFMG).
      
      - M.Sc. in Mathematics — University of Brasília (UnB), specializing in Mathematical Analysis.
      
      - B.Sc. in Mathematics — Federal University of Espírito Santo (UFES).****
      
      My research experience includes applied mathematics, numerical methods, computational modeling, discrete exterior calculus, electromagnetics, and large-scale numerical problems.
      
      I'm currently working extensively on AI-driven molecular identification from MS/MS spectra, developing candidate retrieval strategies, fragmentation analysis, ensemble ranking, and machine-learning approaches for CASMI 2026.
      
      My team has achieved a public leaderboard score of 0.446, and we are actively researching approaches to push beyond 0.500.
      
      I believe my mathematical and computational background could complement your team's expertise. I'd be happy to discuss a potential collaboration and exchange ideas.
      
      Kaggle: AlexMoura2023
      
      Best regards,
      Alex Moura
        - **Kino Lutor** (2026-10-16, votes 0)
          ok,of course,professor,how can we get contact?
        - **Kino Lutor** (2026-10-16, votes 0)
          If available,you can add me on discord:Kino
        - **AlexMoura2023** (2026-10-16, votes 0)
          alexmoura1714
        - **AlexMoura2023** (2026-10-16, votes 0)
          in discord
          alexmoura1714
        - **Kino Lutor** (2026-10-16, votes 0)
          OK,i sent asking  permission to you
        - **Aryan Awasthi** (2026-10-16, votes 0)
          well ofcourse, will add you in discord and connect with you there
        - **Aryan Awasthi** (2026-10-16, votes 0)
          alright check my username would be teykik there
