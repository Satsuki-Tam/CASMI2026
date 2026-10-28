"""111 (Codex 114): before scoring, check that a trained checkpoint is the registered run: receipt complete, step == budget, the recipe arguments
(steps, K 63, K_F 48, workers 6, seed 0, lr_fp 1e-4, lr_head 5e-4, warmup 500, merge_p 0.3, loss weights 1 / 1 / 1 / 0.1, d_out 256, hid 1024,
holdout hold,np), the checkpoint's own step / cfg / args equal to the receipt's, init = the fold-1 slot (sha 1739d568...), split.parquet sha equal
to the training manifest, and the checkpoint's sha recorded in the training manifest equal to the current file. Exit 1 on any mismatch.
Usage: python ck111_check.py <run_dir> <tag> <steps> <init.pt> <split.parquet> <train_manifest.txt>"""
import hashlib, json, os, sys
import torch
R, TAG, S, INIT, SPLIT, MAN = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6]
SLOT = "1739d5683fa94fd73fe3b37db98ac364cb5dfdc22ad5bea9789be9c48d7cadc4"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()


fail = []
def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'} {TAG} {name} {detail}"); (None if ok else fail.append(name))


rc = json.load(open(os.path.join(R, f"{TAG}_receipt.json"))); ra = rc.get("args", {})
want = dict(steps=S, K=63, K_F=48, workers=6, seed=0, lr_fp=1e-4, lr_head=5e-4, warmup=500, merge_p=0.3, w_cos=1.0, w_rank=1.0, w_bce=1.0, w_el=0.1, d_out=256, hid=1024,
            holdout="hold,np", tag=TAG, smoke_steps=0)
check("receipt complete / step", rc.get("complete") is True and rc.get("step") == S, f"{rc.get('complete')} {rc.get('step')}")
check("receipt recipe", all(ra.get(k) == v for k, v in want.items()), str({k: ra.get(k) for k in want}))
fp = os.path.join(R, f"{TAG}_s{S}.pt")
ck = torch.load(fp, map_location="cpu", weights_only=True); ca = ck.get("args", {})
check("checkpoint step / cfg", ck.get("step") == S and ck.get("cfg", {}).get("nbits") == 10226 and ck.get("cfg", {}).get("d_out") == 256, f"{ck.get('step')} {ck.get('cfg')}")
check("checkpoint args == receipt args", all(ca.get(k) == ra.get(k) for k in set(ca) | set(ra)), "")
check("init = fold-1 slot", os.path.realpath(str(ca.get("init", ck.get("init")))) == os.path.realpath(INIT) and sha(INIT) == SLOT, str(ca.get("init", ck.get("init"))))
man = {}
for line in open(MAN):
    p = line.strip().split(" ", 1)
    if len(p) == 2 and len(p[0]) == 64: man[os.path.abspath(p[1]) if os.path.isabs(p[1]) else p[1]] = p[0]
split_sha = sha(SPLIT); check("split sha == training manifest", split_sha in man.values(), split_sha[:16])
ck_sha = sha(fp); check("checkpoint sha recorded in the training manifest", ck_sha in man.values(), ck_sha[:16])
sys.exit(1 if fail else 0)
