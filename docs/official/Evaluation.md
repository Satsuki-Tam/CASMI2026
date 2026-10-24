# Evaluation

(name=Evaluation, mime=None, published=None)

Submissions are evaluated using Mean Reciprocal Rank @ 25 (MRR@25):

$$\text{MRR@25} = \frac{1}{U} \sum_{u=1}^{U} \frac{1}{rank_u}$$

where \\( U \\) is the number of molecules and \\( rank_u \\) is the position of the first correct structure in your ranked list for molecule \\( u \\). A molecule scores 0 if none of your guesses is correct. Each molecule has exactly one correct structure, so only your **first** correct guess counts. A correct guess at position 1 scores 1.0, at position 2 scores 0.5, at position 25 scores 0.04.

## Matching

A prediction is correct when it describes the same **atom connectivity** as the answer. Both your SMILES and the answer are passed through RDKit's tautomer canonicalization (pinned at 2026.03.3) and reduced to the first block of their InChIKey (the InChIKey14), then compared. The prediction is correct when the two first-block keys match.

This means you are not penalized for getting stereocenters or tautomer forms wrong. For example, both of the following score identically against an answer of glucose, because they reduce to the same InChIKey14 (`WQZGKKKJIJFFOK`):

    OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O
    OCC1OC(O)C(O)C(O)C1O

This is the link to the [metric notebook](https://www.kaggle.com/code/metric/casmi-mean-reciprocal-rank).

## Submission File

For each `molecule_id` in the test set, predict up to 25 candidate structures as SMILES, **best guess first**, joined by semicolons in a single field.

Every `molecule_id` must appear exactly once. The file should contain a header and have the following format:

    molecule_id,smiles
    m_0014ef,CC1=CC(=O)C=CC1=O;OC(=O)c1ccccc1O;CN1C=NC2=C1C(=O)N(C)C(=O)N2C
    m_004d06,NCCc1ccc(O)cc1;CC(=O)Nc1ccc(O)cc1;OCC(O)CO
    ... 

Fewer than 25 guesses is allowed but there is no penalty for a wrong guess beyond the rank it occupies. A submission is rejected if it is missing the `molecule_id` or `smiles` column, is empty, contains nulls in either column, repeats a `molecule_id`, or gives more than 25 semicolon-separated guesses for any molecule.