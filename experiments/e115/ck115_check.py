"""115 v2 completion check (Codex 119 Q1-7): a finished R / A run is used only if every item passes (exit 1 otherwise).
Checks: no trainer process of the tag remains; <tag>_receipt.json complete with step == the registered S; the receipt args equal the registered
recipe (S, bs 256, K 63, lr 1e-4, wd 0.01, warmup 500, merge_p 0.3, w_bce 1, w_el 0.1, workers 6, seed 0, holdout 'hold,np', device cuda,
sim_frac 0 for R / 0.25 for A, init / bits sha256, max_fail 0.01, no smoke, no dump); the trainer code sha256 equals the registered one; the final
checkpoint (torch.load weights_only=True) has step == S, finite weights and the sha256 the receipt recorded; A only: the ledger's consumed
simulated items == the schedule's planned items (the schedule is deterministic), the consumed-jobs file sha256 matches, a planned wrap (plan reuse from its start
after recorded generation failures) is at most 1% of the plan and recorded.
Writes <run>/<tag>_ck115.json. Usage: python -I ck115_check.py <run> <tag> <S> <R|A> <trainer_sha256>"""
import hashlib, json, math, os, subprocess, sys
RUN, TAG, S, ARM, CODE_SHA = os.path.abspath(sys.argv[1]), sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
INIT_SHA = "1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4"; BITS_SHA = "c3869e86449d6fed6e79e9655f8a7d35bd55c3138ecddfc1dae5072627e78677"
fail, res = [], {}
def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'} {name} {detail}", flush=True); res[name] = dict(ok=bool(ok), detail=str(detail)); (None if ok else fail.append(name))
def fsha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
ps = subprocess.run(["pgrep", "-f", f"train_fpaug2.py.*--tag {TAG}( |$)"], capture_output=True, text=True).stdout.split()
check("no trainer process remains", not ps, str(ps))
rc = json.load(open(os.path.join(RUN, f"{TAG}_receipt.json"))); a = rc["args"]
check("receipt complete, step == S", rc.get("complete") is True and rc.get("step") == S, f"{rc.get('complete')} {rc.get('step')}")
want = dict(steps=S, bs=256, K=63, lr=1e-4, wd=0.01, warmup=500, merge_p=0.3, w_bce=1.0, w_el=0.1, workers=6, seed=0, holdout="hold,np", device="cuda",
            sim_frac=0.0 if ARM == "R" else 0.25, init_sha=INIT_SHA, bits_sha=BITS_SHA, max_fail=0.01, smoke_steps=0, dump_batches=0, tag=TAG)
diff = {k: (a.get(k), v) for k, v in want.items() if a.get(k) != v}
check("registered recipe", not diff, str(diff))
check("trainer code sha256", rc.get("code_sha256") == CODE_SHA, f"{str(rc.get('code_sha256'))[:16]} vs {CODE_SHA[:16]}")
fp = os.path.join(RUN, f"{TAG}_final.pt")
import torch
ck = torch.load(fp, map_location="cpu", weights_only=True)
finite = all(torch.isfinite(v).all().item() for v in ck["model"].values() if torch.is_tensor(v) and v.is_floating_point())
check("final checkpoint step / finite weights", ck.get("step") == S and finite, f"step {ck.get('step')} finite {finite}")
check("final checkpoint sha256 == receipt", fsha(fp) == rc.get("checkpoint_sha256"), rc.get("checkpoint_sha256", "")[:16])
if ARM == "A":
    led, sc = rc.get("ledger", {}), rc["setup"]["schedule"]
    check("consumed == planned simulated items", led.get("consumed_sim_items") == sc.get("planned_sim_items"), f"{led.get('consumed_sim_items')} vs {sc.get('planned_sim_items')}")
    check("consumed-jobs file sha256", fsha(os.path.join(RUN, led["consumed_jobs_file"])) == led.get("consumed_jobs_sha256"))
    pu = rc["setup"]["sim"]["plan_used"]   # the fixed 2-cycle plan is reused from its start when recorded failures shortened it (Codex 119 Q3); bounded
    check("planned wrap within 1% of the plan (recorded)", sc.get("planned_wrap_positions", 0) <= 0.01 * pu, f"{sc.get('planned_wrap_positions')} of {pu}")
res["passed"] = not fail; res["final_sha256"] = fsha(fp)
json.dump(res, open(os.path.join(RUN, f"{TAG}_ck115.json"), "w"), indent=2)
print("CK115", "PASS" if not fail else f"FAIL {fail}"); sys.exit(1 if fail else 0)
