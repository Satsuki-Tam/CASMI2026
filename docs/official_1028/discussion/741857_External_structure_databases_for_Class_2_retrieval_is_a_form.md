# External structure databases for Class 2 retrieval: is a formula-filtered PubChem subset prize-eligible?
topic 741857 | by **dead_signals_lab** (https://www.kaggle.com/deadsignalslab) | posted 2026-09-17 | votes 2 | comments 4 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/741857

Question on external structure databases for candidate retrieval.

The data description defines Class 2 as structures "in PubChem or the natural-products database COCONUT, so it is reachable by database retrieval." COCONUT is CC0, so that side is clear.

For PubChem, NCBI's policy page notes that some records carry depositor copyright and that NCBI cannot grant third-party redistribution rights. Since inference runs with internet disabled, any use of PubChem in a submission requires packaging a subset (e.g. formula-filtered structures / InChIKeys) as a Kaggle Dataset, i.e. redistributing it.

Two questions for the hosts:

- Is a formula-filtered PubChem subset, packaged as a public Kaggle Dataset for offline retrieval, acceptable for a prize-eligible solution under the winner-license requirements?

- If not, should participants restrict candidate databases to CC0 / CC-BY sources such as COCONUT, ChEBI and LIPID MAPS?

A clear answer either way would help everyone build compliant pipelines early rather than discovering an issue in December. Thanks!

## Comments (3 top-level)

- **ممدوح** (2026-09-17, votes 0)
  i think it is not just a complexity, learning from top can make better world progress
- **David Healey** **[HOST]** (2026-09-18, votes 1)
  Yes, thank you for asking. PubChem structures for retrieval are acceptable for prize-eligible solutions.
    - **Mazzutti** (2026-10-10, votes 0)
      Follow-up on PubChem use, for a yes/no from the hosts.
      
      You confirmed above that PubChem structures are acceptable for retrieval. Does the same hold for PubChem's literature links, used as a ranking feature?
      
      Concretely: for each candidate structure we count the distinct PubMed IDs that PubChem links to it (the public CID-PMID file on the PubChem FTP site), and use that count as one term when ranking candidates. No text from the papers is used, only the count. The file is free, public, and equally available to all participants.
      
      Is a solution that uses these counts prize-eligible? Several public notebooks use a similar popularity prior, so a clear answer would help many teams before final selection.
- **David Healey** **[HOST]** (2026-10-11, votes 1)
  Yes, submitting subsets of PubChem is fine for prize-eligible solutions.
