"""Codex 112 / 114: GLACIER output audit, a STOP gate before any comparison is read. For every expected (molecule, candidate) of the runner input,
gl_classify.classify (the runner's own rules; run with .venv-ice so RDKit matches the runner): finite / null_uncovered / null_rejected / failure
(missing key, non-finite number, unscheduled null, or an exception in the structure check). Also checks that the evaluator's loader
(b1_locked_eval.runner rule: meta status ok / partial -> the JSON; error with n_mols_scored 0 and all-null -> empty; otherwise None) would accept
the file with exactly the audited finite values (status 'error' with finite values or a missing meta = failure).
Writes <out>.audit.json with sha256 of the input, the output, its meta, gl_classify.py and the runner, RDKit version; exit 1 on any failure.
Usage: .venv-ice/bin/python gl_audit.py RUN/b1_runner_S_in.json RUN/work/gl_S.json [more pairs ...]"""
import hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gl_classify as GC
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RUNNER = os.path.join(ROOT, "data", "external", "glacier", "gl_runner.py")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()


args = sys.argv[1:]
if not args or len(args) % 2: sys.exit("usage: gl_audit.py IN OUT [IN OUT ...]")
try:
    import rdkit; rdv = rdkit.__version__
except Exception as e: rdv = f"unavailable {e!r}"
bad_total = 0
for inp, outp in zip(args[0::2], args[1::2]):
    items = json.load(open(inp)); out = json.load(open(outp))
    meta = json.load(open(outp + ".meta.json")) if os.path.exists(outp + ".meta.json") else None
    c = dict(molecules=len(items), candidates=0, finite=0, null_uncovered=0, null_rejected=0, failure=0); fails = []
    for it in items:
        m = it["mid"]; d = out.get(m)
        for s in it["cands"]:
            c["candidates"] += 1; present = isinstance(d, dict) and s in d
            k = GC.classify(it, s, present, d.get(s) if present else None); c[k] += 1
            if k == "failure": fails.append((m, s, "missing" if not present else repr(d.get(s))))
    st = (meta or {}).get("status")
    if meta is None: loader = "rejected (no meta)"
    elif st in ("ok", "partial"): loader = "accepted"
    elif st == "error" and int(meta.get("n_mols_scored") or 0) == 0 and c["finite"] == 0: loader = "accepted-empty"
    else: loader = f"rejected (status {st})"
    if not loader.startswith("accepted"): c["failure"] += 1; fails.append(("-", "-", f"loader {loader}"))
    c.update(examples=fails[:5], loader=loader, meta_status=st, rdkit=rdv,
             sha256=dict(input=sha(inp), output=sha(outp), meta=sha(outp + ".meta.json") if meta is not None else None,
                         gl_classify=sha(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gl_classify.py")), runner=sha(RUNNER) if os.path.exists(RUNNER) else None))
    json.dump(c, open(outp + ".audit.json", "w"), indent=1)
    print(("PASS" if c["failure"] == 0 else "FAIL"), outp, json.dumps({k: v for k, v in c.items() if k not in ("examples", "sha256")}), flush=True)
    bad_total += c["failure"]
sys.exit(1 if bad_total else 0)
