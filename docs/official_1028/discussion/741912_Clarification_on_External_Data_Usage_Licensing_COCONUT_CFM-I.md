# Clarification on External Data Usage & Licensing (COCONUT / CFM-ID) for CASMI 2026
topic 741912 | by **Endark Wang** (https://www.kaggle.com/endarkwang) | posted 2026-09-18 | votes 1 | comments 2 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/741912

Hi everyone,

I’m preparing to participate in Enveda CASMI 2026 – Molecule ID From Mass Spectra and I’d appreciate clarification on two compliance-related points regarding external resources:
﻿
1) External data generated with COCONUT / CFM-ID

The competition rules allow “External Data” if it is publicly available and equally accessible (or meets the “Reasonableness” standard). If a participant generates in-silico spectra features/representations locally using COCONUT and CFM-ID (both publicly obtainable), would that be considered compliant under the External Data policy—especially if the participant does not redistribute the generated spectra files, but instead runs the pipeline locally?
﻿
2) Licensing implications for a winning submission (MIT requirement)

If someone’s winning solution must be released under MIT, how should we handle dependencies with licenses such as LGPL (if applicable to the specific CFM-ID/COCONUT implementation/version)? Concretely:

- Is it acceptable to rely on an LGPL-licensed tool/model only at runtime (end-users can install it themselves), without including that tool’s code in the submission repository?

- Are there any specific obligations we should expect if we publish a repository that calls external tools/models?
﻿
Thanks in advance for any guidance—happy to provide more details about the exact pipeline and versions I plan to use.

## Comments (2 top-level)

- **David Healey** **[HOST]** (2026-09-19, votes 0)
  1.) Spectra generated from COCONUT structures with CFM-ID is fine; compliant with the external data policy.
  
  2.) LGPL-licensed runtime dependency is fine also. 
  
  Specific obligations: none that I can think of other than what is in the rules, particularly to make sure all versions are documented to be reproducible. But if you have any specific other possibilities you're wondering about, we're happy to address them. 
  
  (guidance for solution eligibility not legal advice)
- **?** (2026-09-26, votes 0)
  
