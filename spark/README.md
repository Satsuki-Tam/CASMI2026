# DGX Spark (GPU box) — how experiments run there

- Host `spark-8fda.local` (DHCP; use the name), user `svlg`, key `~/.ssh/spark_ed25519` (no passphrase).
  `ssh -i ~/.ssh/spark_ed25519 -o IdentitiesOnly=yes -o BatchMode=yes svlg@spark-8fda.local`
- Hardware: NVIDIA GB10 (sm_121, 128 GB unified memory), 20 CPUs (aarch64), 3.1 TB free. CUDA 13 wheels (`torch==2.14.1+cu130`).
- Layout on the Spark: `~/CASMI2026` = clone of this repository; `~/CASMI2026/data/{raw,processed,external}` mirrors the PC
  (streamed with `tar | ssh`, the spectra store is rebuilt with `experiments/b1_baseline/build_spectra_store.py`).
- Environments (`spark/setup_spark.sh`): `.venv` (Python 3.11, rdkit 2026.03.3 = scorer version, torch cu130, polars, lightgbm) and
  `.venv-ice` (Python 3.12, rdkit 2025.3.6 for the ICEBERG/GLACIER runners). No Docker, `sudo` needs the user.
- Rules that avoided failures: scripts in LF (scp them, do not paste); long jobs detached with
  `setsid nohup <cmd> > log 2>&1 < /dev/null &` (never chain with `&&` after `cd`); results come back with `scp`/`git`.
- GPU experiments after 2026-10-24 run here (user request); the PC's RTX 5070 Ti only finishes jobs that were already running.
