# new molecules (not in any database)'s prediction:how can we improve that?
topic 750241 | by **Kino Lutor** (https://www.kaggle.com/kinolutor) | posted 2026-10-17 | votes 2 | comments 2 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/750241

Hi everyone!
V22 performs almost perfectly on known molecules, but on 130 molecules absent from the candidate databases, it places the correct structure first only 7 times.
The encouraging finding: Engine 1’s generator could produce the correct structure for 100 of those 130 molecules when given suitable starting analogs. However, the default pipeline starts generation from only the 6 closest known molecules. We’re now testing 12, 20 and 30 parents on CPU, without using GPU resources.
Has anyone investigated this bottleneck?

- Does expanding the parent set improve final identification, or mostly add distracting candidates?

- Would selecting structurally diverse parents work better than simply taking more nearest analogs?

- How would you distinguish generation failures from cases where the correct generated candidate is lost during filtering or ranking?
The 100/130 figure is generation potential, not end-to-end identification accuracy. Any suggestions for controlled experiments would be appreciated!

## Comments (1 top-level)

- **ZavodRobotov** (2026-10-17, votes 0)
  Same problem has been observed in AlphaStar training to play StarCraft. Learning from human games in initial stage was crutical, because model cannot learn new tactics by itself. First attempts for new tactics give bad results for model, so model drop these new tactics. You can read paper about training AlphaFold and AlphaStar to find some interesting.
    - **Kino Lutor** (2026-10-17, votes 0)
      ok,thank you so much
