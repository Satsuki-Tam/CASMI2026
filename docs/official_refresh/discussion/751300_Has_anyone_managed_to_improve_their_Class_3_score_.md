# Has anyone managed to improve their Class 3 score?
topic 751300 | by **Bull** (https://www.kaggle.com/welshonionman) | posted 2026-10-21 | votes 6 | comments 6 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/751300

I've been working on improving my Class 3 score for the past two weeks, but I still haven't managed to get any improvement on the leaderboard.

My methods show improvements on local validation problems I've created from the training data, but those improvements don't translate to the LB at all.

How is everyone else doing with Class 3?

## Comments (3 top-level)

- **Mansur Nurmukhambetov** (2026-10-21, votes 1)
  Same here, I have my local / proxy class-3 metrics move, but the LB basically flat for me too. I don’t really trust validation carved from training anymore; feels optimistic vs true novelty (analogs, wrong difficulty). Still chasing recall not rerank tweaks, no clean LB win to report yet.
- **Tra Crew** (2026-10-23, votes 1)
  I managed a class 3 lever with consistent tiny leaderboard gains but I am having a little trouble getting any more than +.003-.004 for weeks now..
   I think I may be close to another lever worth a +.007-.010 LB gain , but ive run out of GPU a few days ago -- just when I was really making some progress it seems…if I win, I am totally investing in a Spark or something.
    - **Bull** (2026-10-23, votes 0)
      Are you doing local validation for Class 3? If so, is there a correlation between your local validation scores and the leaderboard scores?
- **ZavodRobotov** (2026-10-23, votes 0)
  Is there main problem is overfitting or underfitting? Train, validation, and LB datasets are small or big? Is the class balance shifted between CV and LB?
    - **Bull** (2026-10-23, votes 0)
      I think my local validation problems are not accurately representative of the Class 3 problems on LB.
        - **ZavodRobotov** (2026-10-23, votes 0)
          data balance (or class balance) shift is a very common reason of inconsistency of CV and LB
