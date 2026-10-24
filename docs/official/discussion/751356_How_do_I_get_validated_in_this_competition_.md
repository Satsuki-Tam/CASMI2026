# How do I get validated in this competition?
topic 751356 | by **Mark** (https://www.kaggle.com/markdjadchenko) | posted 2026-10-21 | votes 1 | comments 3 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/751356

I have been trying to create something that correlates reasonably well with the LB (leaderboard), but so far, I am only getting a low correlation. My current approach is to train the model on all the data, excluding the "envenda np examples."

## Comments (3 top-level)

- **Md Mobashir Rahman** (2026-10-22, votes 0)
  Thats a huge problem for me as well.
- **Jake** (2026-10-22, votes 0)
  I created a set aside validation subset of the training data and simulated type 1/2/3 molecules from it by masking features from inference.  For example, simulated type2 molecules have their spectra masked from the reference catalog that my inference pipeline uses but the molecule itself is still allowed to be in the catalog.  Simulated type3 molecules get completely masked.
- **Tra Crew** (2026-10-23, votes 0)
  I have built a fairly accurate mock scorer by making a hidden test set, holding out from the training data.
  Its fairly accurate now after some calibration and tuning, ive been able to prevalidate my submissions score and predict exactly the last 15 or so submission scores.
   Its saved me a few wasted runs and helped me catch countless bugs in my notebook prevalidation gates, try holding out a few hundred molecules from your training data and tune the scoring against your submissions until you are consistently getting really close with your predictions.
