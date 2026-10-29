"""Mechanical reader of the five 10/29 diagnostic submissions (written before any of their scores was seen). It only applies the readings fixed
in 101_decision, 1029_submission_plan (addendum 2) and the reading order of Codex 125; it decides nothing else.
eta = 0.015 is the diagnostic guide (not a significance threshold). B / T scores are compressed-rank scores of fixed candidate-membership
groups; they are not additive parts of the normal score and not hidden class ratios (Codex 124 / 125).
Amended before any score (Codex 126): the G_B-small wording, and the next-slot line is marked provisional until all five are scored.
Usage: python -X utf8 reports/agent_review/1029_read_results.py [saved_submissions.csv]
  without an argument it calls the kaggle CLI once (--csv) and saves the raw table to reports/agent_review/1029_scores.csv."""
import csv, io, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ETA = 0.015
IDS = dict(ENG_B="57753331", PRE_RANK2_B="57753342", V8W7A_T="57753951", V8W7A_B="57754031", E0_T="57754476")
KNOWN = dict(E0_B=0.259, BASE_B=0.213, OLD_B1_B=0.204, OLD_B1_T_M2x=0.160, V8W7A=0.394, E0=0.464)
if len(sys.argv) > 1:
    raw = open(sys.argv[1], encoding="utf-8").read()
else:
    exe = os.path.join(os.path.dirname(HERE), "..", ".venv", "Scripts", "kaggle.exe")
    raw = subprocess.run([os.path.normpath(exe), "competitions", "submissions", "enveda-CASMI26-molecule-id-mass-spectra", "--csv"],
                         capture_output=True, text=True, timeout=180, check=True).stdout
    open(os.path.join(HERE, "1029_scores.csv"), "w", encoding="utf-8").write(raw)
rows = {r["ref"]: r for r in csv.DictReader(io.StringIO(raw[raw.index("ref,"):]))}
S, status = {}, {}
for k, i in IDS.items():
    r = rows.get(i); status[k] = r["status"] if r else "missing"
    S[k] = float(r["publicScore"]) if r and "COMPLETE" in r["status"] and r["publicScore"] else None
def cls(x):
    return None if x is None else ("+eta" if x >= ETA else ("-eta" if x <= -ETA else "small"))
def sub(a, b):
    return None if a is None or b is None else round(a - b, 4)
Q = {}
Q["G_B = E0_B - v8w7a_B"] = sub(KNOWN["E0_B"], S["V8W7A_B"])
Q["G_T = E0_T - v8w7a_T"] = sub(S["E0_T"], S["V8W7A_T"])
Q["ENG_B - BASE_B"] = sub(S["ENG_B"], KNOWN["BASE_B"])
Q["E0_B - max(BASE_B, ENG_B)"] = None if S["ENG_B"] is None else round(KNOWN["E0_B"] - max(KNOWN["BASE_B"], S["ENG_B"]), 4)
Q["D = E0_B - pre-rank2_B"] = sub(KNOWN["E0_B"], S["PRE_RANK2_B"])
Q["pre-rank2_B - BASE_B"] = sub(S["PRE_RANK2_B"], KNOWN["BASE_B"])
Q["v8w7a_B - old B1_B 0.204 (descriptive)"] = sub(S["V8W7A_B"], KNOWN["OLD_B1_B"])
Q["v8w7a_T - old B1_T 0.160 (descriptive)"] = sub(S["V8W7A_T"], KNOWN["OLD_B1_T_M2x"])
READ = {
 "G_B = E0_B - v8w7a_B": {"+eta": "B-path gap remains -> decomposing E0's later stages stays first", "small": "no large net B-policy difference observed on this Public (not equivalence; offsetting gains / losses inside B are not excluded) -> revisit priorities", "-eta": "on B, v8w7a is above E0"},
 "G_T = E0_T - v8w7a_T": {"+eta": "E0 has a T-path (train structure) lead -> study E0's T path (library merge, engine-1 handling of train structures) as a port candidate; first separate reference / seen-ness / prior on the local C1 ledger (Codex 125)", "small": "no large net T gap observed on this Public", "-eta": "on T, B1 is above E0"},
 "ENG_B - BASE_B": {"+eta": "the second list alone is stronger than BASE on B", "small": "second list alone ~ BASE on B (complementarity not refuted)", "-eta": "second list alone weaker than BASE on B (complementarity not refuted)"},
 "E0_B - max(BASE_B, ENG_B)": {"+eta": "final is stronger than both single lists (fusion / forward / adoption worth studying)", "small": "final ~ the better single list", "-eta": "final below the better single list"},
 "D = E0_B - pre-rank2_B": {"+eta": "rank-2 insertion contributes -> local donor reach / complementarity and rank-2 gain-loss analysis (not fwdoff)", "small": "most of the net gain is before the insertion", "-eta": "insertion costs on the B policy -> do not prioritise a rank-2 port; register which earlier stage to study"},
}
L = ["# 10/29 diagnostic submissions: mechanical reading (eta %.3f, fixed before the scores)" % ETA, "",
     "| probe | submission | status | Public |", "|---|---|---|---:|"]
for k, i in IDS.items():
    L.append(f"| {k} | {i} | {status[k]} | {'' if S[k] is None else S[k]:} |")
L += ["", "| order | quantity | value | class | registered reading |", "|---|---|---:|---|---|"]
order = {"G_B = E0_B - v8w7a_B": 1, "G_T = E0_T - v8w7a_T": 1, "ENG_B - BASE_B": 2, "E0_B - max(BASE_B, ENG_B)": 2, "D = E0_B - pre-rank2_B": 3, "pre-rank2_B - BASE_B": 3}
for q, v in Q.items():
    c = cls(v); L.append(f"| {order.get(q, '-')} | {q} | {'' if v is None else f'{v:+.4f}'} | {c or ''} | {READ.get(q, {}).get(c, 'descriptive') if c else 'pending'} |")
# Codex 125 queue for the next slot (one candidate; nothing is pushed by this script)
gB, D, pr = Q["G_B = E0_B - v8w7a_B"], Q["D = E0_B - pre-rank2_B"], S["PRE_RANK2_B"]
POP0 = "fixed pop coefficient 0 on the current P (Codex 116 / 124 definition and parity; built before use)"
if None in (gB, D, pr):
    nxt, loc = "pending: not all of G_B / D / pre-rank2_B are scored", ""
elif gB >= ETA and abs(D) < ETA and pr > KNOWN["BASE_B"]:
    nxt, loc = "fwdoff_B (kernels/e0-probe-fwdoffb, audit-hardened, REBUILD sha 9966254...): read pre-rank2_B - fwdoff_B with eta", ""
elif D >= ETA:
    nxt, loc = POP0 + " (the donor comparison is not ready)", "local donor analysis (reach of ENG's top-1, complementarity, rank-2 gain/loss); a Public donor comparison only after its normal-MRR cost and submission path are checked"
elif D <= -ETA:
    nxt, loc = POP0, "do not prioritise the rank-2 port; register which pre-insertion stage to study (the fwdoff condition is not treated as met)"
else:
    nxt, loc = POP0 + (" (B gap small)" if gB < ETA else " (fwdoff condition not met)"), ""
allc = all(S[k] is not None for k in IDS)
L += ["", f"**Next diagnostic slot (Codex 125 queue){'' if allc else ' - PROVISIONAL: not all five scored'}:** {nxt}", "(Codex 126: this is a proposal only; technical checks of every run come first and nothing is pushed automatically.)"] + ([f"**Local work first:** {loc}"] if loc else [])
if Q["G_T = E0_T - v8w7a_T"] is not None and Q["G_T = E0_T - v8w7a_T"] >= ETA:
    L.append("**T gap >= eta:** first separate reference / seen-ness / prior effects on the local C1 ledger (Codex 125).")
L += ["", "Limits (Codex 125): all five use the same Public (related policy comparisons, not replications); |G| < eta = no large net difference observed on this Public, not equivalence; using these results for the next research choice is itself Public adaptation (ledgered)."]
out = chr(10).join(L) + chr(10)
open(os.path.join(HERE, "1029_results_reading.md"), "w", encoding="utf-8").write(out)
json.dump(dict(scores=S, status=status, known=KNOWN, quantities=Q, next=nxt, local=loc), open(os.path.join(HERE, "1029_results_reading.json"), "w"), indent=2)
print(out)
