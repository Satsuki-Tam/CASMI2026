"""Codex 112 / 114: candidate-level GLACIER cache shared between the arms of a paired comparison, so a (molecule, SMILES) pair has ONE GLACIER value
in every arm and only candidates that no cache covers are computed. Classification = gl_classify.py (the runner's own rules); run with .venv-ice.
  prepare: --inp RUN/b1_runner_S_in.json --cache IN:OUT [IN:OUT ...] --todo TODO_in.json --plan PLAN.json
           A cache entry is used for a molecule only if the cache's runner input item of that molecule has IDENTICAL query spectra (every field of
           the item except 'cands'); a candidate is covered only by a FINITE cached value (type-checked, math.isfinite). Uncovered candidates that
           the runner would never score (molecule without a covered query spectrum, structure rejected by the runner's rules) are recorded as
           scheduled nulls and NOT sent to the todo run; the todo input keeps only scoreable uncovered candidates.
  merge:   --inp ... --plan PLAN.json --todo_out TODO_out.json --out RUN/work/gl_S.json
           final value = cached value, the todo run's value, or a scheduled null. The merged file's meta status describes the MERGED output (not the
           todo run): 'ok' when every scoreable candidate is finite and at least one value is finite; 'error' with n_mols_scored 0 when every
           candidate is a scheduled null (the evaluator's runner_empty case, as the runner itself reports it); 'partial' when a scoreable candidate
           stayed null (gl_audit.py then fails). The todo run's own meta is kept under 'todo_meta'.
Usage: .venv-ice/bin/python gl_share.py prepare|merge ..."""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gl_classify as GC
ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["prepare", "merge"]); ap.add_argument("--inp", required=True)
ap.add_argument("--cache", nargs="*", default=[]); ap.add_argument("--todo", default=""); ap.add_argument("--plan", required=True)
ap.add_argument("--todo_out", default=""); ap.add_argument("--out", default="")
a = ap.parse_args()
items = json.load(open(a.inp)); by_mid = {it["mid"]: it for it in items}
if len(by_mid) != len(items): sys.exit("duplicate molecules in the runner input")
key = lambda it: json.dumps({k: v for k, v in it.items() if k != "cands"}, sort_keys=True)
if a.mode == "prepare":
    caches = []
    for c in a.cache:
        ci, co = c.split(":")
        cin = {it["mid"]: it for it in json.load(open(ci))}; cout = json.load(open(co)); caches.append((c, cin, cout))
    plan, todo, n_cached, n_todo, n_sched, n_spec_mismatch = {}, [], 0, 0, 0, 0
    for it in items:
        m = it["mid"]; src = {}; cov = GC.molecule_covered(it)
        for name, cin, cout in caches:
            if m not in cin or m not in cout: continue
            if key(cin[m]) != key(it): n_spec_mismatch += 1; continue
            for s in it["cands"]:
                v = (cout[m] or {}).get(s)
                if s not in src and GC.is_finite(v): src[s] = [name, float(v)]
        sched, rest = {}, []
        for s in it["cands"]:
            if s in src: continue
            if not cov: sched[s] = "null_uncovered"
            elif GC.accepted(s) is False: sched[s] = "null_rejected"
            else: rest.append(s)
        plan[m] = dict(cached=src, scheduled=sched, todo=rest); n_cached += len(src); n_todo += len(rest); n_sched += len(sched)
        if rest: todo.append(dict(it, cands=rest))
    json.dump(plan, open(a.plan, "w")); json.dump(todo, open(a.todo, "w"))
    print(f"prepare: molecules {len(items)}, cached {n_cached}, scheduled null {n_sched}, to compute {n_todo} in {len(todo)} molecules, cache items with different spectra {n_spec_mismatch}")
else:
    plan = json.load(open(a.plan)); tout = json.load(open(a.todo_out)) if a.todo_out and os.path.exists(a.todo_out) else {}
    tmeta = json.load(open(a.todo_out + ".meta.json")) if a.todo_out and os.path.exists(a.todo_out + ".meta.json") else {}
    out, n_c, n_t, n_fail, n_sched, scored = {}, 0, 0, 0, 0, 0
    for it in items:
        m = it["mid"]; p = plan[m]; d = {}
        for s in it["cands"]:
            if s in p["cached"]: d[s] = p["cached"][s][1]; n_c += 1
            elif s in p["scheduled"]: d[s] = None; n_sched += 1
            else:
                v = (tout.get(m) or {}).get(s); d[s] = float(v) if GC.is_finite(v) else None; n_t += 1; n_fail += not GC.is_finite(v)
        out[m] = d; scored += any(GC.is_finite(v) for v in d.values())
    json.dump(out, open(a.out, "w"))
    status = "partial" if n_fail else ("ok" if scored else "error")
    json.dump(dict(status=status, n_mols=len(items), n_mols_scored=scored, via="gl_share.py", cached=n_c, computed=n_t, computed_not_finite=n_fail, scheduled_null=n_sched,
                   todo_meta=tmeta), open(a.out + ".meta.json", "w"))
    print(f"merge: status {status}, cached {n_c}, computed {n_t} (not finite {n_fail}), scheduled null {n_sched}, molecules scored {scored}/{len(items)}, todo status {tmeta.get('status')}")
