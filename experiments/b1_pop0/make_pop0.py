"""116 / 124 / 125 DIAGNOSTIC pop0 (build only; not a method candidate): the frozen v7f pipeline (experiments/b1_v7f038, sha 6e3b4d04) with ONE
change, the fixed-rule prior coefficient LAM (0.5) of S = z(fp) + LAM * pop as a parameter (--lam_fixed). S feeds both paths: the GL path's blend
2 z(pred) + z(S_plain) and the GL-coverage fallback path (S + library priority, then analog / frag). Unchanged: the shortlist's FP+prior branch
(SHORTLIST_LAM 0.15) and pop branch (K_pop), the ranker and its popularity features, candidates, references, GL, every other score and output step.
Construction: the frozen per-molecule fusion loop is moved VERBATIM into a nested function _fusion_pass(LAM, fused_stats) (the parameter shadows
the module constant, so the loop text is byte-identical apart from indentation; checked below on the AST). With --lam_fixed the run makes two
passes over the same in-memory rows / GL / ICE / ranker predictions: the main pass with LAM = lam_fixed (submission.csv, submission_fixed.csv,
probes) and a reference pass with the frozen LAM (submission_lamref.csv, _fixed, _probe_train, _probe_nontrain) = the v8w7a lists of this very run (in-run parity; GLACIER scores can
differ between runs). Without --lam_fixed: one pass with the frozen LAM, outputs as before (no submission_lamref.csv).
Usage: python -X utf8 experiments/b1_pop0/make_pop0.py   (writes experiments/b1_pop0/*.py and prints the checks)"""
import ast, hashlib, os, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(os.path.dirname(HERE), "b1_v7f038")
for f in ("b1_common.py", "b1_analog.py", "b1_frag.py", "b1_rankfeats.py"):
    shutil.copy(os.path.join(SRC, f), os.path.join(HERE, f))
s = open(os.path.join(SRC, "b1_pipeline.py"), encoding="utf-8").read()
assert hashlib.sha256(s.encode()).hexdigest().startswith("6e3b4d043b20"), "frozen pipeline changed"
L = s.split("\n")
def idx(prefix):
    k = [i for i, x in enumerate(L) if x.startswith(prefix)]; assert len(k) == 1, (prefix, k); return k[0]
i_init = idx("    sub, sub_fixed, fused_stats = [], [], Counter()"); i_probe = idx("    sub_probe = {\"train\": [], \"nontrain\": []}")
i_loop = idx("    for mid in all_ids:"); i_df = idx("    df = pd.DataFrame(sub, columns=[\"molecule_id\", \"smiles\"]); df.to_csv(")
assert i_probe == i_init + 1 and i_init < i_loop < i_df
loop = L[i_loop:i_df]; assert all(x == "" or x.startswith("        ") for x in loop[1:]), "loop body indentation"
new = L[:i_init] + ["    fused_stats = Counter()   # pop0 (116/124): sub / sub_fixed / sub_probe are built per pass by _fusion_pass below"] + L[i_probe + 1:i_loop]
new += ["    def _fusion_pass(LAM, fused_stats):   # pop0 (116/124): the frozen per-molecule fusion loop, verbatim; LAM = the fixed-rule prior coefficient of this pass",
        "        sub, sub_fixed = [], []", "        " + L[i_probe].lstrip()]
new += [("    " + x if x else x) for x in loop]
new += ["        return sub, sub_fixed, sub_probe",
        "    sub, sub_fixed, sub_probe = _fusion_pass(LAM if args.lam_fixed is None else args.lam_fixed, fused_stats)",
        "    fused_stats_ref = Counter()",
        "    if args.lam_fixed is not None:   # reference pass with the frozen LAM on the same in-memory inputs = the unchanged list of this run (in-run parity)",
        "        log(f\"pop0: main pass done (lam_fixed {args.lam_fixed}); reference pass (frozen LAM {LAM}) starts\")",
        "        sub_ref, sub_ref_fixed, sub_ref_probe = _fusion_pass(LAM, fused_stats_ref)",
        "        for _n, _v in ((\"\", sub_ref), (\"_fixed\", sub_ref_fixed), (\"_probe_train\", sub_ref_probe[\"train\"]), (\"_probe_nontrain\", sub_ref_probe[\"nontrain\"])):   # all four lists of the frozen-LAM pass (cross-run content checks)",
        "            pd.DataFrame(_v, columns=[\"molecule_id\", \"smiles\"]).to_csv(f\"{P['work']}/submission_lamref{_n}.csv\", index=False)",
        "        _a, _b = dict(sub), dict(sub_ref); _ch = [m for m in _a if _a[m] != _b[m]]; _t1 = [m for m in _a if _a[m].split(';')[:1] != _b[m].split(';')[:1]]",
        "        log(f\"pop0: lam_fixed {args.lam_fixed} vs LAM {LAM}: lists changed {len(_ch)} / {len(_a)}, rank-1 changed {len(_t1)}\")",
        "        fused_stats[\"lamref_lists_changed\"] = len(_ch); fused_stats[\"lamref_top1_changed\"] = len(_t1)"]
new += L[i_df:]
t = "\n".join(new)
arg_anchor = '    ap.add_argument("--frag_w_fallback", type=float, default=0.0,'
assert t.count(arg_anchor) == 1
t = t.replace(arg_anchor, '    ap.add_argument("--lam_fixed", type=float, default=None, help="116/124 pop0 DIAGNOSTIC: fixed-rule prior coefficient of S (both paths); the run also writes the frozen-LAM list as submission_lamref.csv (default None = frozen LAM, one pass)")\n' + arg_anchor)
man_anchor = "W_GL=W_GL, W_ICE=W_ICE, LAM=LAM, TAU=TAU, MARGIN=MARGIN, folds=folds)),"
assert t.count(man_anchor) == 1
t = t.replace(man_anchor, "W_GL=W_GL, W_ICE=W_ICE, LAM=LAM, TAU=TAU, MARGIN=MARGIN, folds=folds, lam_fixed=args.lam_fixed), fusion_lamref=dict(fused_stats_ref)),")
fw_old = "    GL, ICE = {}, {}\n    if not args.no_forward and items:"
assert t.count(fw_old) == 1
t = t.replace(fw_old, "    GL, ICE = {}, {}\n    if args.gl_json and not KAGGLE:   # pop0 local parity only: reuse the stored GLACIER output of an earlier run on the same items (no forward run)\n"
              "        GL.update(json.load(open(args.gl_json))); log(f\"GL loaded from {args.gl_json}: {len(GL)} molecules (forward models not run)\")\n    elif not args.no_forward and items:")
t = t.replace('    ap.add_argument("--lam_fixed",', '    ap.add_argument("--gl_json", default=None, help="pop0 local parity only (ignored on Kaggle): load GL from this gl_out.json instead of running the forward models")\n    ap.add_argument("--lam_fixed",')
open(os.path.join(HERE, "b1_pipeline.py"), "w", encoding="utf-8", newline="\n").write(t)
# ---- checks on the AST: the loop inside _fusion_pass is the frozen loop node for node; nothing else in main changed except the listed lines
def main_fn(src):
    return next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "main")
mo, mn = main_fn(s), main_fn(t)
fo = next(n for n in mo.body if isinstance(n, ast.For) and getattr(n.target, "id", "") == "mid")
fp_ = next(n for n in mn.body if isinstance(n, ast.FunctionDef) and n.name == "_fusion_pass")
fn = next(n for n in fp_.body if isinstance(n, ast.For) and getattr(n.target, "id", "") == "mid")
assert ast.dump(fo) == ast.dump(fn), "the fusion loop differs from the frozen one"
assert [a.arg for a in fp_.args.args] == ["LAM", "fused_stats"]
names_assigned = {x.id for x in ast.walk(fn) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store)}
print("loop identical on the AST; names assigned inside the loop:", sorted(names_assigned))
after = mo.body[mo.body.index(fo) + 1:]
class _Scope(ast.NodeVisitor):   # names at main scope (nested function / lambda bodies are separate scopes and are skipped), in source order
    def __init__(self): self.ev = []
    def visit_FunctionDef(self, n): pass
    def visit_Lambda(self, n): pass
    def visit_For(self, n):   # the target is bound before the body runs
        self.visit(n.iter); self.visit(n.target); [self.visit(b) for b in n.body + n.orelse]
    def visit_Name(self, n): self.ev.append((n.lineno, n.col_offset, type(n.ctx).__name__, n.id))
sc_ = _Scope(); [sc_.visit(n) for n in after]
first = {}
for ln, col, ctx, nm in sc_.ev: first.setdefault(nm, (ln, ctx))
leak = sorted(nm for nm in names_assigned if nm in first and first[nm][1] == "Load" and nm not in {"sub", "sub_fixed", "sub_probe", "fused_stats"})
print("loop-assigned names whose first main-scope use after the loop is a read:", leak, "| first uses of the rest:", {nm: first[nm] for nm in sorted(names_assigned) if nm in first})
assert not leak, ("a name assigned in the loop is read after it in main (would be lost inside the function)", leak)
before = mo.body[:mo.body.index(fo)]; outer = {x.id for n in before for x in ast.walk(n) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store)}
shadow = sorted((names_assigned & outer) - {"sub", "sub_fixed", "sub_probe", "fused_stats"})
print("names assigned in the loop that also exist before it in main (become local to the function; must not be read before assignment):", shadow)
o_other = [ast.dump(n) for n in mo.body if n is not fo]; n_other = [ast.dump(n) for n in mn.body if n is not fp_]
print("main statements: frozen", len(mo.body), "new", len(mn.body))
print("b1_pipeline.py sha256", hashlib.sha256(t.encode()).hexdigest())
