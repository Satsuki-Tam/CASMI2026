"""149 prep (Codex 147 S2 (i)): expose an E-window table directory in the layout that experiments/mist/mist_score_v4.py reads, so that the
already-audited MIST scoring code runs unchanged on the E windows:
  <out>/b1_features_<set>.parquet = (molecule, smiles, official_key) of every E-window row (the representative SMILES, as E2 uses it);
  <out>/b1_molecules_<set>.csv    = ledger with n_unique / truth_in_window / n_shortlist for EVERY molecule of the eval CSV of that set
                                    (the E-window ledger n_e and truth_in_ewin; molecules without a query -> n_unique 0, not in window, NaN).
No score, no label is used beyond copying the E-window ledger flags.
Usage: python -X utf8 experiments/e2/e2_mist_inputs.py --ewin experiments/e2/ewin/<dir> --eval_csv <csv> --sets S1 ... --out experiments/e2/mist_in/<dir>"""
import argparse, hashlib, json, os
import numpy as np, pandas as pd


def main():
    ap = argparse.ArgumentParser()
    for k in ("ewin", "eval_csv", "out"): ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--sets", nargs="+", required=True); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    ev = pd.read_csv(a.eval_csv); ev["molecule"] = ev.molecule.astype(str); man = dict(ewin=a.ewin, eval_csv=a.eval_csv, sets={})
    for s in a.sets:
        E = pd.read_parquet(os.path.join(a.ewin, f"ewin_{s}.parquet"), columns=["molecule", "smiles", "official_key"]); E["molecule"] = E.molecule.astype(str)
        if E.duplicated(["molecule", "official_key"]).any(): raise SystemExit(f"STOP: {s} duplicate (molecule, official key)")
        E.to_parquet(os.path.join(a.out, f"b1_features_{s}.parquet"), index=False)
        em = pd.read_csv(os.path.join(a.ewin, f"ewin_molecules_{s}.csv")); em["molecule"] = em.molecule.astype(str); em = em.set_index("molecule")
        L = []
        for m in ev[ev.set == s].molecule:
            if m in em.index:
                n_e = int(em.loc[m, "n_e"]); L.append(dict(molecule=m, n_unique=n_e, truth_in_window=bool(em.loc[m, "truth_in_ewin"]), n_shortlist=float(n_e) if n_e else np.nan))
            else:
                L.append(dict(molecule=m, n_unique=0, truth_in_window=False, n_shortlist=np.nan))
        L = pd.DataFrame(L); L.to_csv(os.path.join(a.out, f"b1_molecules_{s}.csv"), index=False)
        bad = set(E.molecule) - set(L[L.n_unique > 0].molecule)
        if bad: raise SystemExit(f"STOP: {s} {len(bad)} molecules with E rows but n_e 0 in the ledger")
        man["sets"][s] = dict(rows=len(E), molecules=len(L), empty=int((L.n_unique == 0).sum()))
    json.dump(man, open(os.path.join(a.out, "mist_inputs_manifest.json"), "w"), indent=1); print(json.dumps(man))


if __name__ == "__main__":
    main()
