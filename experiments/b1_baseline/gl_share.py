"""Codex 112: candidate-level GLACIER cache shared between the arms of a paired comparison, so a (molecule, SMILES) pair has ONE GLACIER value
in every arm and only candidates that no cache covers are computed.
  prepare: --inp RUN/b1_runner_S_in.json --cache IN:OUT [IN:OUT ...] --todo TODO_in.json --plan PLAN.json
           A cache entry is used for a molecule only if the cache's runner input item of that molecule has IDENTICAL query spectra (every field of
           the item except 'cands'); a candidate is covered only by a FINITE cached value (a cached null is recomputed). The todo input keeps the
           uncovered candidates of each molecule (molecules with none are left out); the plan records the source of every (molecule, SMILES).
  merge:   --inp ... --plan PLAN.json --todo_out TODO_out.json --out RUN/work/gl_S.json
           final value = cached value (covered) or the todo run's value; writes out.json + out.json.meta.json (status from the todo run's meta,
           'ok' when nothing had to be computed) and a counts line. Values are never invented: an uncovered candidate missing from the todo
           output stays null (and is then flagged by gl_audit.py).
Usage: python gl_share.py prepare|merge ..."""
import argparse, json, os, sys
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
    plan, todo, n_cached, n_todo, n_spec_mismatch = {}, [], 0, 0, 0
    for it in items:
        m = it["mid"]; src = {}
        for name, cin, cout in caches:
            if m not in cin or m not in cout: continue
            if key(cin[m]) != key(it): n_spec_mismatch += 1; continue
            for s in it["cands"]:
                v = (cout[m] or {}).get(s)
                if s not in src and v is not None and v == v: src[s] = [name, float(v)]
        rest = [s for s in it["cands"] if s not in src]
        plan[m] = dict(cached=src, todo=rest); n_cached += len(src); n_todo += len(rest)
        if rest: todo.append(dict(it, cands=rest))
    json.dump(plan, open(a.plan, "w")); json.dump(todo, open(a.todo, "w"))
    print(f"prepare: molecules {len(items)}, candidates cached {n_cached}, to compute {n_todo} in {len(todo)} molecules, cache items with different spectra {n_spec_mismatch}")
else:
    plan = json.load(open(a.plan)); tout = json.load(open(a.todo_out)) if a.todo_out and os.path.exists(a.todo_out) else {}
    tmeta = json.load(open(a.todo_out + ".meta.json")) if a.todo_out and os.path.exists(a.todo_out + ".meta.json") else {}
    out, n_c, n_t, n_null = {}, 0, 0, 0
    for it in items:
        m = it["mid"]; p = plan[m]; d = {}
        for s in it["cands"]:
            if s in p["cached"]: d[s] = p["cached"][s][1]; n_c += 1
            else:
                v = (tout.get(m) or {}).get(s); d[s] = v; n_t += 1; n_null += v is None
        out[m] = d
    json.dump(out, open(a.out, "w"))
    status = "ok" if not any(p["todo"] for p in plan.values()) else tmeta.get("status", "missing")
    json.dump(dict(status=status, n_mols=len(items), via="gl_share.py", cached=n_c, computed=n_t, computed_null=n_null, todo_meta=tmeta), open(a.out + ".meta.json", "w"))
    print(f"merge: cached {n_c}, computed {n_t} (null {n_null}), todo status {tmeta.get('status')}")
