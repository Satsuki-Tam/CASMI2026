# Are the four approved sources meant to extend coverage beyond PubChem?
topic 748552 | by **Marco Pereira** (https://www.kaggle.com/marcofpereira) | posted 2026-10-12 | votes -2 | comments 2 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/748552

THE QUESTION, IN ONE LINE
Do the four sources that were approved by name — COCONUT, PubChemLite, ChEBI and LIPID MAPS — contain any molecule that is NOT already in PubChem? If the intent was to extend coverage beyond PubChem, the released data does not allow it.

WHAT WE MEASURED (and how)
We measured, against our local instrument (a sample of 2,000 identity+scaffold-disjoint queries), how many ground truths each source contains that are NOT already in PubChem:

source    % unique truths vs PubChem  note
COCONUT 10-2024 (already in our pool)    0.1000% (2 of 2,000)    already integrated · +0 truths
PubChemLite    0   already integrated · +0
ChEBI    0 (0.0004% on the scorer_key ruler) not separable on disk
LIPID MAPS    0 (0.0022% in train + visible test) +33 candidates, +0.004%
UNION of the four (dedup by InChIKey)    0.1000% — TWO molecules marginal = 0.001 of MRR
⇒ The union reaches 90.55% coverage; PubChem ALONE already gives 90.45%. On the scorer_key, both give exactly 89.48% — the union adds nothing.

And no single source pays for itself: running the pipeline with one source only — COCONUT 0.1065 · PubChemLite 0.1040 · LIPID MAPS 0.0140 · ChEBI 0.0000 — all of them below our own pool (0.1480). So not even substitution is justified.

Our reading: the approved sources are, in practice, PubChem re-indexed (95.19–99.99%). They cannot contain what PubChem does not have — and that is precisely what we would need.

WHY THIS MATTERS FOR THE COMPETITION
We measured where the answers are and where we reach:

the ground truth sits in the PubChem formula bucket 89.85% of the time;
our pool reaches 13.90% of queries;
and 75.35% of the truths that sit inside the bucket fall outside what we deliver.
⇒ Roughly 11% of the answers are NOT in PubChem. That fraction is what none of the four sources can reach — the most the union adds is 2 molecules out of 2,000.

THE REQUEST, AND IT IS NARROW
A structure collection that is largely ABSENT from PubChem — or, if that is not possible, confirmation that the competition dataset was designed so that the answer IS in PubChem, so that we stop looking for coverage outside it and focus on what exists.

Two natural candidates, if it helps: LOTUS (v11) and NP Atlas — we measured them without using them in any kernel, and they add 0.0435% and 0.0007% respectively on the train+visible-test ruler (+940 and +65 candidates). Small, but it is the only direction with a measured marginal gain.

And the compliance question, which matters most: is using a collection not approved by name subject to the same compliance rules already answered in 741359, 744338 and 744556? If it is, we would rather have the answer than the assumption.

WHAT WE ARE NOT ASKING
we are not asking for hidden-test data, nor for anything that reveals the private split;
we are not asking for a rule exception — if the answer is "there is no complementary collection", that is a useful answer and we will stop this line of investigation;
we are not asking for a deadline — the competition is long and we know there are other questions in the queue.
WHAT WE WILL DO WITH THE ANSWER
"There is no complementary collection" ⇒ we close the coverage line and turn our attention to what exists (an answer that saves weeks);
"Here is collection X" ⇒ we audit provenance from inside the artifact (our usual practice: manifest/hashes against names already approved), measure the marginal coverage before integrating, and only then build;
"The answer is in PubChem by design" ⇒ we change direction and treat the bottleneck as ordering/ambiguity, with a corrected ruler.
Thank you for your time — and for the work on "Rerun test dataset updated" and on RemoveStereochemistry, which we verified and which did not cost us any score.

## Comments (2 top-level)

- **Marie Killian** **[Organizer]** (2026-10-13, votes 1)
  Competitors are not limited to the external datasets that have been explicitly approved by name. Other publicly available datasets may be used, provided they comply with the competition’s external-data rules and applicable licensing requirements.
  
  By definition, class 3 structures are not in PubChem at all and must be predicted de novo.
- **Marco Pereira** (2026-10-14, votes 0)
  Thank you — that answers our question, and it closes a line we had been pursuing for three weeks.
  
  We had asked whether the four sources named in the approved list were meant to extend coverage beyond PubChem. Your answer is that the list is not a ceiling: "Competitors are not limited to the external datasets that have been explicitly approved by name."
  
  We then did the measurement your answer made possible, and it is worth reporting back, because the result is about the DATA and not about the rules.
  
  We measured eight publicly available structure collections (LOTUS v11, NP Atlas, COCONUT, PubChemLite, ChEBI, LIPID MAPS, HMDB, MassSpecGym) for how much of each is genuinely absent from PubChem, and how many evaluation answers each contributes that PubChem alone does not:
