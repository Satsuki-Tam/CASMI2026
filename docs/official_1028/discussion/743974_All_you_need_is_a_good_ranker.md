# All you need is a good ranker
topic 743974 | by **Adarsh** (https://www.kaggle.com/madarshbb) | posted 2026-09-28 | votes 24 | comments 3 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/743974

When I started this competition, I thought the hardest issue would be finding the right molecule. Turns out, the bottleneck is the ranker. (of course, excluding Regime C)

For instance, my CV scores MRR @ 25 : 0.584 in Regime B and 0.846 in Regime A

Among them, number of molecules not in my top 25 are very low:- (below are CV MRR scores)

On an unrelated note, it's so sad to see instances where the true structure isnt part of my guesses, but the guesses my pipeline makes is so close

Also, feel free to use my ranker if it helps anyone : https://claude.ai/artifact/VAQDJb8q7hLFyhv66hWMNL
(It is still at Phase-0 and very unstable, so if anyone is using it, please share some feedback)

It is very useful to visualize and see where you went wrong and its very fun to visualize these molecules

## Comments (2 top-level)

- **Zejun_** (2026-09-28, votes 1)
  Your dashboard is amazing! Simple but informative, did you use AI to make it? Could you open source the UI or prompt?
    - **Adarsh** (2026-09-30, votes 0)
      Thank you !
      
      Yes, the app was made by Claude code. I'm still building it, it's not very user-friendly right now ;-;
- **kenneth uchegbu** (2026-10-01, votes 0)
  please what is the path to Concatenate key spectral metadata as tabular features: precursor_mz, ionization_mode, adduct (one-hot encoded), collision_energy_ev, and instrument_type.
