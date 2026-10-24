#!/bin/bash
cd /c/kaggle/CASMI
for f in pc_lsid.npy pc_lpmid.npy pc_lsynonyms.npy pc_np.npy pc_src_mask.npy pc_lotus_refs.npy pool_lsid.npy pool_lpmid.npy pool_lsynonyms.npy pool_np.npy pool_src_mask.npy pool_lotus_refs.npy pool_match.json tier_match.json README.md TECHNICAL_NOTES.md MANIFEST_20261020.json; do
  echo "== $f $(date +%T)"
  ./.venv/Scripts/kaggle.exe datasets download -d dmitriigluzdov/casmi26-pubchem-popularity-prior -f "$f" -p data/external/pubchem_popularity --unzip -q 2>&1 | tail -2
done
echo ALLDONE $(date +%T)
