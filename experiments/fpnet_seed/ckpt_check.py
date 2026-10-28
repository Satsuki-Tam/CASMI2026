"""110 amendment (Codex 110 (3)): completion check of the seed-1 run before any use. Not used as evidence: the job's 'F1S1_DONE' line, file
existence alone, and the job log's 'segment N exit S' field (always 0: `echo "$(date +%T) ... $?"` expands $? after the date substitution).
Checks (any failure -> exit 1): no trainer process of the run remains; <tag>_progress.json has step == optimizer_updates == max_steps and complete
true; <tag>_final.pt (torch.load weights_only=True) has step == max_steps, nbits 10226 and the registered args (seed, max_steps, holdout 'hold,np',
tag, run dir) and the public recipe values (bs 256, lr 3e-4, wd 0.01, warmup 2000, merge_p 0.3, w_bce 1, w_el 0.1, layers 8, d 512, bias_init 0); <tag>_history.json's last entry is final with step == max_steps (its metrics are not read); train.log has no Traceback /
non-finite / Error line. Only the final checkpoint is used (never <tag>_last.pt or an intermediate one; the trainer's EVAL lines are not read).
Writes <run>/ckpt_check.json (incl. the final checkpoint's sha256). Usage: python -I ckpt_check.py <run> <tag> <max_steps> <seed>"""
import hashlib, json, os, subprocess, sys
RUN, TAG, MAX, SEED = os.path.abspath(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
fail = []
def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'} {name} {detail}"); (None if ok else fail.append(name))
ps = subprocess.run(["pgrep", "-f", f"train_fivefold.py.*--tag {TAG}"], capture_output=True, text=True).stdout.split()
check("no trainer process remains", not [p for p in ps if p != str(os.getpid())], str(ps))
pg = json.load(open(os.path.join(RUN, f"{TAG}_progress.json")))
check("progress step / updates / complete", pg.get("step") == MAX and pg.get("optimizer_updates") == MAX and pg.get("complete") is True, str({k: pg.get(k) for k in ("step", "optimizer_updates", "complete", "skipped_scaled_steps")}))
fp = os.path.join(RUN, f"{TAG}_final.pt")
import torch
ck = torch.load(fp, map_location="cpu", weights_only=True); ar = ck.get("args", {})
check("final checkpoint step / nbits", ck.get("step") == MAX and ck.get("nbits") == 10226, f"step {ck.get('step')} nbits {ck.get('nbits')}")
want = dict(seed=SEED, max_steps=MAX, holdout="hold,np", tag=TAG,   # + the public recipe values (Codex 112: assert, not only display)
            bs=256, lr=3e-4, wd=0.01, warmup=2000, merge_p=0.3, w_bce=1.0, w_el=0.1, layers=8, d=512, bias_init=0)
check("final checkpoint args", all(ar.get(k) == v for k, v in want.items()) and os.path.abspath(str(ar.get("run"))) == RUN, str({k: ar.get(k) for k in list(want) + ["run", "bs", "lr", "warmup", "merge_p", "w_bce", "w_el", "layers", "d"]}))
hist = json.load(open(os.path.join(RUN, f"{TAG}_history.json")))
check("history ends with the final entry", bool(hist) and hist[-1].get("final") is True and hist[-1].get("step") == MAX, f"entries {len(hist)}")
log = open(os.path.join(RUN, "train.log"), encoding="utf-8", errors="replace").read().splitlines()
bad = [l for l in log if "Traceback" in l or "non-finite" in l or "Error" in l]
check("train.log has no error line", not bad, str(bad[:3]))
h = hashlib.sha256()
with open(fp, "rb") as f:
    for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
out = dict(passed=not fail, failed=fail, run=RUN, tag=TAG, final=fp, final_sha256=h.hexdigest(), step=ck.get("step"), segments=sum(1 for l in log if l.startswith("[Data]")),
           elapsed_seconds=pg.get("elapsed_seconds"), args={k: ar.get(k) for k in sorted(ar)})
json.dump(out, open(os.path.join(RUN, "ckpt_check.json"), "w"), indent=2); print(json.dumps(out)[:600]); sys.exit(1 if fail else 0)
