# Is using PubChem (structures and metadata) allowed as external data?
topic 749209 | by **Masa.Yamashita_00** (https://www.kaggle.com/myamashi) | posted 2026-10-14 | votes 0 | comments 2 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/749209

Hi everyone, and hosts,

I understand that the Rules allow external data in general, but I am not sure whether PubChem qualifies, so I would like to confirm before relying on it.

Specifically:

- Candidate structures: Can I use PubChem compound records (SMILES / InChIKey / exact mass) to extend the candidate pool used for retrieval and ranking?

- Metadata: Can I use PubChem-derived statistics (for example, the number of depositing substances or linked PubMed articles) as a prior or feature in a ranking model?

- Offline use: Internet access is disabled at submission time, so I would need to upload a processed snapshot as a Kaggle Dataset and attach it to my notebook. Is this acceptable, and does the Dataset need to be public?

- License: As far as I understand, NCBI places no restrictions on the use of PubChem itself, but individual data providers may claim rights over their records. Is there anything else participants should consider?

- Test set: PubChem may contain the ground-truth structures of the test molecules. Is there any concern about this from the hosts' side?

Thank you in advance for any clarification.

## Comments (2 top-level)

- **?** (2026-10-14, votes 0)
  
- **Marie Killian** **[Organizer]** (2026-10-14, votes 0)
  Thank you for asking for clarification!
  
  - Yes
  
  - Yes, PubChem-derived statistics are permitted as ranking features. Any additional information gathered by following references in PubChem would depend on the licensing of that particular source.
  
  - Yes, uploading PubChem data as a Kaggle Dataset for offline use is acceptable. The dataset would need to be included with a prize-eligible solution but does not need to be public during the competition.
  
  - See the answer to 2. 
  
  - No. PubChem is an allowed resource.
