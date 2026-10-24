# Request for hidden rerun traceback (Version 12)
topic 745866 | by **Lake Tafere** (https://www.kaggle.com/laketafere) | posted 2026-10-05 | votes 0 | comments 1 | https://www.kaggle.com/competitions/enveda-CASMI26-molecule-id-mass-spectra/discussion/745866

Hello CASMI organizers,

Could you share the traceback or failing stage for my notebook submission, CASMI 2026 v6_light submission, Version 12? Kaggle marks its private hidden-data rerun as “Notebook Threw Exception,” but provides no traceback or score.

The corresponding committed notebook run succeeds in 317.3 seconds. It reads the competition Parquets, writes /kaggle/working/submission.csv, and validates 400 unique molecule IDs, 25 nonempty candidates per molecule, and sample_submission order. Its JSONL debug log reports 809 events, 400 molecule starts and completions, and no fallback, exception, or error events.

Version 12 also uses sample_submission order only when its IDs match the runtime test IDs; otherwise it keeps test.parquet order. The visible run reports matching IDs, so the hidden-rerun failure remains unexplained.

Could you provide the private rerun traceback or identify the failing stage? Also, does the hidden evaluation replace test.parquet while leaving sample_submission.csv unchanged, or are both files replaced?

Thank you.

## Comments (1 top-level)

- **PC Jimmmy** (2026-10-05, votes 0)
  Close to 0.000 percent chance that a private rerun trace back will ever be provided - nicely word try though.  Other than a couple of different error messages - there is never log or trace data on submission runs.
  
  test and sample submission are both replaced. 
  
  Exception errors often shape/memory related.  The fake test is big enough that those errors should have occurred when you saved/run the notebook.  so …..
  
  If you can't work it out - make the notebook public and share a link here - likely someone can help spot the issue.
