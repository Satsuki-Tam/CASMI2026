# Adding valid guesses at ranks 2–25 lowers the public score?
topic 748029 | by **Antriksh Arya** (https://www.kaggle.com/antriksharya) | posted 2026-10-10 | votes 3 | comments 5 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/748029

Hi, I am seeing something I can’t explain with the published metric (v14, first-match MRR).

With the same notebook and the identical rank-1 guess for every molecule (we assert this in the notebook):

rank 1 only (1 guess per molecule): 0.426
rank 1 + our original ranks 2–25: 0.426
rank 1 + different valid ranks 2–25 (RDKit-parseable, neutral, single-fragment, ≤25 guesses): 0.388–0.397 (three separate variants)

Since only the first correct guess should count, extra guesses after rank 1 shouldn’t be able to lower the score. Is there anything in the live scorer (timeouts, per-row limits, guess validation) that could make a row score 0 when more or different guesses are present? This looks related to the “filler guesses poison a row” report in discussion 742265.

Thanks!

## Comments (1 top-level)

- **Aryan Awasthi** (2026-10-14, votes 0)
  From the metric source (the scoring function in the competition’s metric notebook): each row’s guesses are canonicalised (stereo removed, tautomer-canonical InChIKey first block) and the loop stops at the first match, scoring 1/rank. So appending guesses after your existing ones can never lower that row’s score. Inserting them before the answer can.
  
  If your score dropped, two common causes:
  
  1) The new guesses moved the answer down. Check whether you appended or merged/re-sorted.
  2) Run-to-run noise. The GPU stages in the public pipelines aren’t bit-reproducible. I’ve seen identical code score 0.437 and 0.440. With ~130 public molecules, one molecule changing rank moves the score by ~0.008.
  
  A quick check: diff the two submission.csv files and compare, for each molecule, the position of its old top-1 in the new list.
    - **Antriksh Arya** (2026-10-14, votes 1)
      yeah, thanks I figured it out later, this public test set is a bit weird with only about 132 public molecules and almost half of it are novel architectures
        - **Aryan Awasthi** (2026-10-14, votes 0)
          That matches what others are estimating. Bull’s CV-fitted class shares in the “Validation strategy” thread put class 3 at ~52%, so “almost half novel” is consistent. It also explains why re-ranking gains look big offline and tiny on the LB.
          
          Out of curiosity, are you attacking the novel ones with candidate generation (beyond PubChem/COCONUT), or still within the existing pools? On my side, an independent fingerprint+ranker engine merged by RRF only moved things +0.001, so I suspect the remaining headroom is mostly in class 3.
        - **Antriksh Arya** (2026-10-14, votes 1)
          yeah its is in class 3, reranking can get you gains but only through rule based reranking and even then the ceiling is low.
          for class 3 you will have to generate candidate and that's the toughest part because you get so less hits on the LB
        - **Aryan Awasthi** (2026-10-14, votes 0)
          yeah makes sense, that’s exactly what I’m seeing too. big gains offline, almost nothing on the LB 
          
          I’m thinking of trying generation from analogs instead of de novo. Take the closest library hits (usually same scaffold, different side chain), tweak them a bit (add/remove CH2, OH, sugar etc.) and only keep the ones that match the formula. Then rank them normally.
          
          did you try any de novo generators? or is the hit rate too low to be worth the runtime?
