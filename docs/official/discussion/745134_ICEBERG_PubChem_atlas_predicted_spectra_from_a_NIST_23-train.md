# ICEBERG PubChem atlas (predicted spectra from a NIST'23-trained model) — usable as a spectral library?
topic 745134 | by **Zihao Ou** (https://www.kaggle.com/nicholasooo) | posted 2026-10-02 | votes 0 | comments 4 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/745134

The MIT Coley group's ICEBERG atlas (iceberg-ms.mit.edu) offers downloadable predicted MS/MS spectra for 91,424,208 PubChem structures. The page states "All NIST'23 structures are excluded to avoid license conflict", and the ms-pred README distributes the NIST'23-trained ICEBERG weights only on proof of a NIST licence, while the MassSpecGym-trained weights are open. The atlas page states no data licence. Two readings: (a) the atlas spectra are model outputs publicly offered by the authors, so a solution may use them as an in-silico library, as with CFM-ID/ISDB (thread 743774); (b) outputs of NIST-trained weights fall under "any solution using or trained on NIST" (thread 744470) and are ineligible. Which reading applies to atlas-predicted spectra used only as library entries?

## Comments (3 top-level)

- **Marie Killian** **[Organizer]** (2026-10-14, votes 0)
  The first reading applies. The atlas spectra are model outputs publicly offered by the authors and can be used.
- **Young Uk Song** (2026-10-15, votes 0)
  Thank you for the clear answer on this topic. One follow-up, so that a prize-eligible solution can comply when it is shipped: the atlas page states no data licence. If a solution uses atlas spectra as library entries, may it include only the subset it uses (the predicted spectra of its candidate structures) as a private Kaggle dataset attached to the submission notebook, as described in topic 749209 for PubChem data? Or should such spectra instead be regenerated within the solution with the public MassSpecGym-trained ICEBERG weights?
    - **Marie Killian** **[Organizer]** (2026-10-16, votes 0)
      It should be fine to provide the notebook with only the predicted spectra as a dataset, but include the code used to generate those spectra. You don't need to regenerate them within the notebook, but we do require that you provide sufficient documentation for reproducibility (training code and access to permitted data) .
- **VUMANIAcom** (2026-10-17, votes 0)
  Hi Marie / David, thank you for the 10-14 and 10-16 answers on the ICEBERG PubChem atlas. One last compliance point for a prize-eligible solution:
  
  The atlas spectra come from NIST'23-trained ICEBERG weights that are not public (the ms-pred README releases them only on proof of a NIST licence). The atlas page states no data licence and excludes NIST'23 structures.
  
  - May a solution ship, as a private Kaggle dataset attached to the notebook, precomputed atlas predictions for the candidate structures it can reach (the pool/candidate universe), together with the script that queries iceberg-ms.mit.edu (WebDAV / query_smiles) to rebuild them? Is that "generation code + access to permitted data" for the reproducibility rule, even though the generating weights are NIST-trained and cannot be retrained by a reviewer?
  
  - Would a much smaller artifact be acceptable: only the atlas MEMBERSHIP list (InChIKey-14 of the structures in the atlas, no spectra), used as a candidate feature?
  
  - Or must atlas-like spectra be regenerated inside the notebook with the public MassSpecGym ICEBERG weights?
  A yes/no for each is enough. Thanks!
