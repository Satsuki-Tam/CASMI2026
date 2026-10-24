# Clarification on private external compute
topic 741876 | by **Alaa Mostafa** (https://www.kaggle.com/onlineopp) | posted 2026-09-17 | votes 3 | comments 6 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/741876

Hello,

Could the organisers please clarify whether an individual participant may process the competition data in a secure private third-party cloud-computing environment solely for model training or inference?

The environment would be accessible only to the participant. The competition data would not be published or shared with anyone outside the participant’s official Kaggle team.

Would this comply with the competition’s Data Access and Data Security rules?

Thank you.
Alaa

## Comments (3 top-level)

- **Jessie Grubaugh** (2026-09-18, votes -2)
  3n+1=1+3*n
  *N=10
  P√np=npp=0
  A+b=c=a=-(-c+b
- **David Healey** **[HOST]** (2026-09-18, votes 1)
  You are referring to the competition training data?  Yes, my understanding is that can be processed and trained on on a cloud environment.
    - **Alaa Mostafa** (2026-09-18, votes 0)
      Hi David. Yes, I am referring to the competition training data.
      
      Could you please confirm specifically whether I am allowed to upload the competition training data to my private Hugging Face storage, process it and train models in the Hugging Face cloud environment, then use the resulting model weights or training outputs in my Kaggle submission notebook?
        - **David Healey** **[HOST]** (2026-09-19, votes 0)
          Yes, you can do that.
- **Navneet** (2026-09-18, votes 1)
  Thank you for the Clarification on private external compute @onlineopp (/onlineopp)
    - **Alaa Mostafa** (2026-09-18, votes 1)
      Thank you. To avoid any misunderstanding, could one of the competition hosts please provide a direct yes-or-no confirmation:
      
      Am I permitted to upload the competition training files to a private Hugging Face repository, train the model using Hugging Face cloud compute, and bring the resulting model weights back into Kaggle for submission inference?
