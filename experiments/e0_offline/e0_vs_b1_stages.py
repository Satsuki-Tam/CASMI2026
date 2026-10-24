"""E0 (public 0.464 lineage, run OFFLINE on our molecules by run_e0_offline.py) vs B1, molecule by molecule and stage by stage, on OFFICIAL
identities (src/metric.py canonicalisation, RDKit 2026.03.3). Both sides saw the same query spectra (make_eval_test.py file) in the same proxy view.
Ledger layout = Codex review 016:
  (1) ledger.csv            one row per molecule x view: same-input audit, implementation / training-overlap audit, C2 leak audit, reference & forward
                            availability, final results of both systems and the loss stage classification
  (2) stages.csv            one row per molecule x system x stage: candidate counts in/out, identities out, truth_present / truth_rank, top-1, ordered
                            top-25 identities, rr25 (ranked outputs only; unranked sets record membership only), failure reason
  (3) candidates.parquet    per-stage output candidates with provenance, component scores (finite flags), membership and rank at every later stage
      gates.csv             gate / merge operations: gate, candidate judged, values at decision time, fired, selected channel, action, rank before/after,
                            hash + count of the normalisation set
  summary.json / report.md paired statistics (official scorer replica; unreached truth = 0) with bootstrap CIs, by stratum, cross-stage table.
Truth labels are attached on the audit side only (never passed into preprocessing or models). No dedup is added that an implementation does not have:
E0's own cell-17 metric-identity dedup is recorded as a stage (before / after); B1 has none.
Usage (Spark .venv):
  python -X utf8 e0_vs_b1_stages.py --e0 experiments/e0_offline/runs/c2_full3/work --b1 experiments/b1_baseline/eval_test_full3/run_c2
      --eval_dir experiments/b1_baseline/eval_test_full3 --mols experiments/b1_baseline/eval_set/p1_molecules.csv --out experiments/e0_offline/runs/c2_full3/compare --view c2
"""
import argparse, hashlib, json, os, sys, time
from functools import lru_cache
import numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq

ap = argparse.ArgumentParser()
ap.add_argument("--e0", required=True); ap.add_argument("--b1", required=True); ap.add_argument("--eval_dir", required=True); ap.add_argument("--mols", required=True)
ap.add_argument("--out", required=True); ap.add_argument("--view", default="c2", choices=["c2", "c1"])
ap.add_argument("--knowledge", default="data/external_kaggle/casmi26-natural-product-knowledge-table"); ap.add_argument("--boot", type=int, default=10000)
ap.add_argument("--skip_train_scan", action="store_true", help="skip the C2 leak audit scan of the run's train.parquet")
A = ap.parse_args(); os.makedirs(A.out, exist_ok=True); t0 = time.time()
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, os.path.join(ROOT, "src"))
from metric import canonicalize_smiles_to_ik14   # official identity
E0, B1, EV = os.path.abspath(A.e0), os.path.abspath(A.b1), os.path.abspath(A.eval_dir); RUN_DIR = os.path.dirname(E0)
RUN_ID = f"{os.path.basename(RUN_DIR)}|{A.view}"


@lru_cache(maxsize=None)
def key(smi): return canonicalize_smiles_to_ik14(smi) if isinstance(smi, str) and smi else None


def idents(smiles):
    """ordered official identities of a ranked list (first occurrence of each identity keeps its position; unparsable -> skipped)"""
    out, seen = [], set()
    for s in smiles:
        k = key(s)
        if k is None or k in seen: continue
        seen.add(k); out.append(k)
    return out


def rank_in(ids, truth): return ids.index(truth) + 1 if truth in ids else None
def rr(rank): return 0.0 if rank is None or rank > 25 else 1.0 / rank
def sha(x): return hashlib.sha256(x.encode() if isinstance(x, str) else x).hexdigest()[:16]
def fsha(p): return sha(open(p, "rb").read()) if os.path.exists(p) else None
def jload(p, default=None): return json.load(open(p)) if os.path.exists(p) else default


def read_sub(path):
    if not os.path.exists(path): return {}
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return {str(m): [x for x in s.split(";") if x] for m, s in zip(df.molecule_id, df.smiles)}


def boot_ci(d, n=A.boot, seed=0):
    d = np.asarray(d, float)
    if len(d) == 0: return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed); m = d[rng.integers(0, len(d), size=(n, len(d)))].mean(1); return (float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)))


def finite(v): return isinstance(v, (int, float)) and not isinstance(v, bool) and np.isfinite(v)
def n_finite(d): return sum(1 for v in (d or {}).values() if finite(v))


# ------------------------------------------------------------------------------------------------------------------ shared inputs
sol = pd.read_csv(os.path.join(EV, "solution.csv"), dtype=str); sol["molecule_id"] = sol.molecule_id.astype(str)
mols = pd.read_csv(A.mols, dtype={"molecule": str}).drop_duplicates("molecule").set_index("molecule")
te = pq.read_table(os.path.join(EV, "test.parquet")).to_pandas()
te["molecule_id"] = te.molecule_id.astype(str)
q_rows = te.groupby("molecule_id").spectrum_row.apply(lambda s: list(map(int, s))).to_dict()                    # ordered query acquisitions (store rows)
add_of = te.groupby("molecule_id").adduct.apply(lambda s: sorted(set(s))).to_dict()
mode_of = te.groupby("molecule_id").ionization_mode.apply(lambda s: "|".join(sorted(set(s)))).to_dict()
inst_of = te.groupby("molecule_id").instrument_type.apply(lambda s: "|".join(sorted(set(map(str, s))))).to_dict()
ce_of = te.groupby("molecule_id").apply(lambda g: (float(np.mean([len(x) > 0 if x is not None else False for x in g.collision_energy_ev])), "|".join(sorted(set(map(str, g.collision_energy_orig_units)))))).to_dict()
masks = {f: fsha(os.path.join(EV, f)) for f in ("exclude_identities_c2.json", "exclude_rows_c1.json", "mask_c1.json", "mask_c2.json", "test.parquet")}


def coverage(adds):
    pos = [a for a in adds if a.endswith("+")]; neg = [a for a in adds if a.endswith("-")]
    if any(a in ("[M+H]+", "[M+Na]+") for a in pos): return "covered"
    return "pos_other_only" if pos else ("negative_only" if neg else "none")


# ------------------------------------------------------------------------------------------------------------------ E0 inputs
base = jload(os.path.join(E0, "e0_base_lists.json"), {}); eng = jload(os.path.join(E0, "eng_lists.json"), {}); pcl = jload(os.path.join(E0, "pc_lists.json"), {})
pc_after = jload(os.path.join(E0, "e0_pc_after_rerank.json"), {}); merge = jload(os.path.join(E0, "e0_merge_decisions.json"), {}); merge_pm = merge.get("per_molecule", {})
gl = jload(os.path.join(E0, "e0_gl_scores.json"), {}); ice = jload(os.path.join(E0, "e0_ice_scores.json"), {}); n1 = jload(os.path.join(E0, "e0_n1.json"), {})
frag = jload(os.path.join(E0, "e0_frag_gap.json"), {}); cand_in = jload(os.path.join(E0, "e004_candidate_inputs.json"), {})
port = jload(os.path.join(E0, "e0_port_manifest.json"), {}); audit = jload(os.path.join(E0, "e0_run_audit.json"), {}); run_inputs = jload(os.path.join(RUN_DIR, "run_inputs.json"), {})
e1_info = jload(os.path.join(E0, "e0_engine1_info.json"), {})
e1c = pq.read_table(os.path.join(E0, "e0_engine1_candidates.parquet")).to_pandas() if os.path.exists(os.path.join(E0, "e0_engine1_candidates.parquet")) else None
if e1c is not None: e1c["molecule"] = e1c.molecule.astype(str); e1c_by = {m: g for m, g in e1c.groupby("molecule")}
else: e1c_by = {}
fact = pd.read_csv(os.path.join(E0, "experiment_audit_factorial.csv"), dtype={"molecule_id": str}).set_index("molecule_id") if os.path.exists(os.path.join(E0, "experiment_audit_factorial.csv")) else None
mfus = pd.read_csv(os.path.join(E0, "experiment_audit.csv"), dtype={"molecule_id": str}).set_index("molecule_id") if os.path.exists(os.path.join(E0, "experiment_audit.csv")) else None
SUB_C15, SUB_C17, SUB_C18, SUB_C21 = (read_sub(os.path.join(E0, f)) for f in ("baseline_submission.csv", "submission_reference.csv", "submission_e004_control.csv", "submission_e006_control.csv"))
E0_FINAL = read_sub(os.path.join(E0, "submission.csv"))
E0_LISTS = [("e1_base60", lambda m: (base.get(m) or {}).get("smiles", [])), ("e2_list40", lambda m: (eng.get(m) or {}).get("smiles", [])),
            ("pc_list25", lambda m: (pcl.get(m) or {}).get("pc", [])), ("pc_after_forward", lambda m: (pc_after.get(m) or {}).get("pc", [])),
            ("merge_prefusion_c14", lambda m: cand_in.get("prefusion", {}).get(m, [])), ("fuse2_gl_c15", lambda m: SUB_C15.get(m, [])),
            ("tail_dedup_c17", lambda m: SUB_C17.get(m, [])), ("metric_fusion_c18", lambda m: SUB_C18.get(m, [])),
            ("e006_overlay_c21", lambda m: SUB_C21.get(m, [])), ("final_rank2_c22", lambda m: E0_FINAL.get(m, []))]
UNRANKED_E0 = ("e2_list40", "pc_list25", "pc_after_forward")      # channel lists: membership (not a submission) -> no RR
e0_cells = port.get("cells", {}); cell_s = lambda n: (e0_cells.get(str(n)) or {}).get("seconds")
E0_STAGE_CELL = {"e1_window": 12, "e1_base60": 12, "e2_list40": 8, "pc_list25": 9, "pc_after_forward": 13, "merge_prefusion_c14": 14, "fuse2_gl_c15": 15, "tail_dedup_c17": 17,
                 "metric_fusion_c18": 18, "e006_overlay_c21": 21, "final_rank2_c22": 22}

# ------------------------------------------------------------------------------------------------------------------ B1 inputs
b1_main, b1_ins = read_sub(os.path.join(B1, "submission.csv")), read_sub(os.path.join(B1, "submission_fixed.csv"))
cand = pq.read_table(os.path.join(B1, "b1_candidates.parquet")).to_pandas(); cand["molecule"] = cand.molecule.astype(str); cand_by = {m: g for m, g in cand.groupby("molecule")}
stage = pd.read_csv(os.path.join(B1, "b1_stage_stats.csv"), dtype={"molecule": str}).drop_duplicates("molecule").set_index("molecule")
evalpm = pd.read_csv(os.path.join(B1, "eval_per_molecule.csv"), dtype={"molecule_id": str}).set_index("molecule_id") if os.path.exists(os.path.join(B1, "eval_per_molecule.csv")) else None
b1_man = jload(os.path.join(B1, "b1_run_manifest.json"), {}); b1_gl = jload(os.path.join(B1, "gl_out.json"), {}); b1_ice = jload(os.path.join(B1, "ice_out.json"), {})
b1_params = b1_man.get("params", {}); TAU, MARGIN, MIN_COVER = float(b1_params.get("tau", 0.9)), float(b1_params.get("margin", 0.2)), float(b1_params.get("min_gl_cover", 0.5))

# ------------------------------------------------------------------------------------------------------------------ audits
ext_keys = set()
try:
    links = pq.read_table(os.path.join(ROOT, A.knowledge, "external_reference_spectra", "external_scorer_sid_links.parquet")).to_pandas()
    ext_keys = set(links.loc[links.sid.notna(), "scorer_key"].astype(str))
except Exception as e: print("external links unavailable:", repr(e))
truth_keys = dict(zip(sol.molecule_id, sol.scorer_key))
# C2 leak audit on E0's side: rows of the truth identity that remain in the run's train.parquet (0 expected), + structure-level pool membership
train_remaining = {}
train_path = run_inputs.get("train") if run_inputs else None
if train_path and os.path.exists(train_path) and not A.skip_train_scan:
    try:
        keys_tab = pq.read_table(os.path.join(ROOT, "data/processed/train_scorer_keys.parquet"), columns=["inchikey14", "scorer_ik14"]).to_pandas()
        want = set(truth_keys.values()); k2off = {a_: b_ for a_, b_ in zip(keys_tab.inchikey14, keys_tab.scorer_ik14) if b_ in want}
        cnt = {}
        pf = pq.ParquetFile(train_path)
        for b in pf.iter_batches(batch_size=1 << 17, columns=["inchikey14"]):
            vals, c = np.unique(np.asarray(b.column(0).to_pylist(), dtype=object), return_counts=True)
            for v, n in zip(vals, c):
                if v in k2off: cnt[k2off[v]] = cnt.get(k2off[v], 0) + int(n)
        train_remaining = cnt; print(f"train scan {train_path}: identities with remaining rows {len(cnt)}")
    except Exception as e: print("train scan failed:", repr(e))
pool_sid = {}
try:
    pm = pq.read_table(os.path.join(ROOT, "data/external/v2_pool/pool_meta.parquet"), columns=["key", "train_sid"]).to_pandas()
    want = set(truth_keys.values()); pm = pm[pm.key.isin(want)]; pool_sid = dict(zip(pm.key, pm.train_sid))
except Exception as e: print("pool_meta unavailable:", repr(e))
pool_pop = None     # E0's pool-popularity prior (cell 12: log1p SID + log1p PMID by pool id) -> prior_score of engine-1 window candidates
try:
    _pp = os.path.join(ROOT, "data/external/pubchem_popularity"); pool_pop = np.load(os.path.join(_pp, "pool_lsid.npy")).astype(float) + np.load(os.path.join(_pp, "pool_lpmid.npy")).astype(float)
except Exception as e: print("pool popularity unavailable:", repr(e))
fold_of = {}
try:
    sp = pq.read_table(os.path.join(ROOT, "data/external/fold_safe_fpnet/split.parquet")).to_pandas()
    kc = [c for c in sp.columns if "key" in c.lower() or "inchikey" in c.lower()]; fc = [c for c in sp.columns if "fold" in c.lower()]
    if kc and fc: fold_of = dict(zip(sp[kc[0]].astype(str), sp[fc[0]]))
except Exception as e: print("fold split unavailable:", repr(e))

# ------------------------------------------------------------------------------------------------------------------ per molecule
ledger, stages, cands, gates = [], [], [], []
for r in sol.itertuples(index=False):
    m, T = r.molecule_id, r.scorer_key
    mi = mols.loc[m] if m in mols.index else None
    get = lambda c, d=None: (mi[c] if (mi is not None and c in mi.index and pd.notna(mi[c])) else d)
    adds = add_of.get(m, []); cov = coverage(adds); ce_frac, ce_units = ce_of.get(m, (np.nan, ""))
    nref_bin = str(pd.cut([int(get("n_spectra_lib", -1))], [-1, 2, 5, 10, 10 ** 6], labels=["1-2", "3-5", "6-10", "11+"])[0])
    common = dict(run_id=RUN_ID, view=A.view, molecule_id=m, official_identity=T, split_role=f"{r.set}/{r.group}", set=r.set, group=r.group, query_lib=r.lib,
                  identity_group=int(get("identity_group", -1)), stratum_coverage=cov, stratum_nref_bin=nref_bin, n_spectra_lib=int(get("n_spectra_lib", -1)), instruments=inst_of.get(m, ""),
                  query_rows=json.dumps(q_rows.get(m, [])), query_rows_hash=sha(json.dumps(q_rows.get(m, []))), n_query=len(q_rows.get(m, [])), adducts="|".join(adds), polarity=mode_of.get(m, ""),
                  ce_present_frac=ce_frac, ce_units=ce_units, truth_in_e0_external_refs=T in ext_keys,
                  truth_in_pool_as_train_struct=bool(pool_sid.get(T, -1) is not None and pool_sid.get(T, -1) >= 0), truth_fpnet_fold=fold_of.get(m, "unknown"))
    # ---------------- E0 stages
    e1 = e1c_by.get(m); e1_keys = list(e1.key.astype(str)) if e1 is not None else []
    e1_truth = e1[e1.key.astype(str) == T] if e1 is not None else None
    r_window = int(e1_truth.ranker_rank.min()) if e1_truth is not None and len(e1_truth) else None
    e0_ranks = {}
    stages.append(dict(run_id=RUN_ID, system="E0", molecule_id=m, view=A.view, stage="e1_window", stage_order=0, n_in=None, n_out=len(e1_keys) if e1 is not None else None,
                       n_identities_out=len(set(e1_keys)) if e1 is not None else None, identity_source="E0 score_key", truth_present=(T in e1_keys) if e1 is not None else None,
                       truth_rank=r_window, top1_identity=(str(e1.sort_values("ranker_rank").key.iloc[0]) if e1 is not None and len(e1) else None), top25_identities=None,
                       rr25=rr(r_window) if e1 is not None else None, ranked=True, failure_reason=None if e1 is not None else "engine-1 candidate audit missing", elapsed_s=cell_s(12), elapsed_scope="run", note=None))
    prev = None
    for order, (name, fn) in enumerate(E0_LISTS, 1):
        lst = fn(m) or []; ids = idents(lst); rk = rank_in(ids, T); e0_ranks[name] = rk
        stages.append(dict(run_id=RUN_ID, system="E0", molecule_id=m, view=A.view, stage=name, stage_order=order, n_in=prev, n_out=len(lst), n_identities_out=len(ids), identity_source="official",
                           truth_present=T in ids, truth_rank=rk, top1_identity=ids[0] if ids else None, top25_identities="|".join(ids[:25]), rr25=(None if name in UNRANKED_E0 else rr(rk)),
                           ranked=name not in UNRANKED_E0, failure_reason=None if lst else ("no PubChem list (gate / channel)" if name.startswith("pc_") else "empty list"),
                           elapsed_s=cell_s(E0_STAGE_CELL[name]), elapsed_scope="run", note=None))
        prev = len(lst)
    r_final = e0_ranks["final_rank2_c22"]; in_any = any(e0_ranks[k] is not None for k in ("e1_base60", "e2_list40", "pc_list25")) or r_window is not None
    e0_stage = "rank1" if r_final == 1 else ("rank>1" if r_final is not None and r_final <= 25 else ("lost_merge_fusion" if in_any else ("not_generated" if (e1 is not None or base.get(m)) else "not_processed")))
    # loss classification (Codex 016): candidate absent / dropped at shortlist / forward missing / re-ranked lower / pushed down by a merge
    if r_final == 1: e0_loss = "none"
    elif r_window is None and all(e0_ranks[k] is None for k in ("e1_base60", "e2_list40", "pc_list25")): e0_loss = "candidate_absent"
    elif e0_ranks["e1_base60"] is None and r_window is not None and e0_ranks["e2_list40"] is None and e0_ranks["pc_list25"] is None: e0_loss = "dropped_at_shortlist(top60)"
    elif e0_ranks["merge_prefusion_c14"] is None and (e0_ranks["e1_base60"] is not None or e0_ranks["pc_list25"] is not None): e0_loss = "pushed_down_by_merge(c14)"
    elif r_final is None: e0_loss = "dropped_in_fusion_overlays(c15-c22)"
    elif n_finite(gl.get(m)) == 0 and n_finite(ice.get(m)) == 0: e0_loss = "forward_missing_reranked_lower"
    else: e0_loss = "reranked_lower"
    md = merge_pm.get(m, {}); p = pcl.get(m) or {}
    # gates: merge/promote (c14), metric fusion (c18), E006 branch (c21), rank-2 insert (c22)
    pf_ids = idents(cand_in.get("prefusion", {}).get(m, [])); base_ids = idents((base.get(m) or {}).get("smiles", [])[:25]); pc_ids = idents(p.get("pc", []))
    gates.append(dict(run_id=RUN_ID, system="E0", molecule_id=m, gate_name="c14_pubchem_merge", candidate_identity=pc_ids[0] if pc_ids else None, lib_max=md.get("lib_max"), rel=md.get("rel"), S=md.get("S"),
                      top_pop=md.get("top_pop"), fired=bool(md.get("promoted", False)), selected_channel=("base" if md.get("branch") in ("untouched", "no_pc") else ("pubchem_lead" if md.get("promoted") else f"interleave_{md.get('branch')}")),
                      action=("promote" if md.get("promoted") else ("none" if md.get("branch") in ("untouched", "no_pc") else "insert")), truth_rank_before=rank_in(base_ids, T), truth_rank_after=rank_in(pf_ids, T),
                      norm_set_count=len(p.get("pc", [])), norm_set_hash=sha("|".join(map(str, p.get("pc_keys", [])))), note=md.get("branch")))
    if mfus is not None and m in mfus.index:
        gates.append(dict(run_id=RUN_ID, system="E0", molecule_id=m, gate_name="c18_metric_fusion", candidate_identity=None, lib_max=None, rel=None, S=None, top_pop=None, fired=bool(mfus.loc[m].get("changed", False)),
                          selected_channel="e1+e2 reciprocal rank (alpha 0.6, k 3)", action="fuse", truth_rank_before=e0_ranks["tail_dedup_c17"], truth_rank_after=e0_ranks["metric_fusion_c18"],
                          norm_set_count=None, norm_set_hash=None, note=f"collapsed_votes={mfus.loc[m].get('collapsed_source_votes')}"))
    if fact is not None and m in fact.index:
        fr = fact.loc[m]
        gates.append(dict(run_id=RUN_ID, system="E0", molecule_id=m, gate_name="c21_e006_forward_rerank", candidate_identity=None, lib_max=None, rel=None, S=None, top_pop=None, fired=bool(fr.get("changed", False)),
                          selected_channel=str(fr.get("branch")), action="rerank", truth_rank_before=e0_ranks["metric_fusion_c18"], truth_rank_after=e0_ranks["e006_overlay_c21"],
                          norm_set_count=int(fr.get("candidate_count", 0)), norm_set_hash=None, note=f"ice_finite={fr.get('ice_finite_count')} gl_finite={fr.get('gl_finite_count')} n1={fr.get('n1_proxy')}"))
    e2_top = idents((eng.get(m) or {}).get("smiles", [])[:1]); fin_ids = idents(E0_FINAL.get(m, [])); pre_ids = idents(SUB_C21.get(m, []))
    gates.append(dict(run_id=RUN_ID, system="E0", molecule_id=m, gate_name="c22_rank2_insert", candidate_identity=e2_top[0] if e2_top else None, lib_max=None, rel=None, S=None, top_pop=None,
                      fired=bool(e2_top and len(fin_ids) > 1 and fin_ids[1] == e2_top[0] and (len(pre_ids) < 2 or pre_ids[1] != e2_top[0])), selected_channel="engine2_top", action="insert_rank2",
                      truth_rank_before=e0_ranks["e006_overlay_c21"], truth_rank_after=r_final, norm_set_count=None, norm_set_hash=None, note=None))
    # candidates (3): engine-1 window rows (+ engine-2 / PubChem channel lists) with later-stage membership / ranks; forward scores by SMILES
    glm, icem = gl.get(m) or {}, ice.get(m) or {}
    stage_ranks = {name: {k: i + 1 for i, k in enumerate(idents(fn(m) or []))} for name, fn in E0_LISTS}
    rank_cols = lambda k: {f"rank_{n}": stage_ranks[n].get(k) for n in stage_ranks}
    if e1 is not None:
        has = set(e1.columns)
        for row in e1.itertuples(index=False):
            k = str(row.key); g_ = glm.get(row.smiles); i_ = icem.get(row.smiles)
            cands.append(dict(run_id=RUN_ID, system="E0", molecule_id=m, stage="e1_window", candidate_identity=k, smiles=row.smiles, is_truth=(k == T),
                              source=("generated" if row.pid < 0 else ("pool+train_struct" if row.train_sid >= 0 else "pool")), pid=int(row.pid), train_sid=int(row.train_sid),
                              fp_score=float(row.fz) if "fz" in has else None, lib_sim=float(row.lib_max) if "lib_max" in has else None, lib_nspec=float(row.lib_nspec) if "lib_nspec" in has else None,
                              analog_score=float(row.ap) if "ap" in has else None, mass_ppm=float(row.mass_ppm) if "mass_ppm" in has else None,
                              prior_score=(float(pool_pop[row.pid]) if pool_pop is not None and 0 <= row.pid < len(pool_pop) else None),
                              gl_score=g_ if finite(g_) else None, gl_finite=finite(g_), ice_score=i_ if finite(i_) else None, ice_finite=finite(i_), ranker_score=float(row.ranker_score),
                              rank_window=int(row.ranker_rank), **rank_cols(k), in_shortlist=stage_ranks["e1_base60"].get(k) is not None,
                              exclusion_reason=(None if stage_ranks["final_rank2_c22"].get(k) else ("not in top-60" if stage_ranks["e1_base60"].get(k) is None else "dropped by merge / fusion / tail"))))
    for extra_stage, lst in (("e2_list40", (eng.get(m) or {}).get("smiles", [])), ("pc_list25", p.get("pc", []))):
        fz = p.get("pc_fz") or []
        for i, s_ in enumerate(lst or []):
            k = key(s_); g_ = glm.get(s_); i_ = icem.get(s_)
            cands.append(dict(run_id=RUN_ID, system="E0", molecule_id=m, stage=extra_stage, candidate_identity=k, smiles=s_, is_truth=(k == T), source=("engine2" if extra_stage == "e2_list40" else "pubchem_channel"),
                              pid=None, train_sid=None, fp_score=(float(fz[i]) if extra_stage == "pc_list25" and i < len(fz) and fz[i] is not None else None), lib_sim=None, lib_nspec=None, analog_score=None, mass_ppm=None,
                              prior_score=None, gl_score=g_ if finite(g_) else None, gl_finite=finite(g_), ice_score=i_ if finite(i_) else None, ice_finite=finite(i_), ranker_score=None, rank_window=None,
                              **rank_cols(k), in_shortlist=None, exclusion_reason=None))
    # ---------------- B1 stages
    g = cand_by.get(m); b_keys = list(g.key.astype(str)) if g is not None else []
    truth_row = g[g.key.astype(str) == T] if g is not None else None
    win = get("window_any", None); win_known = str(win) in ("True", "False")
    n_window = float(stage.loc[m, "n_window"]) if m in stage.index and pd.notna(stage.loc[m, "n_window"]) else None
    sec = float(stage.loc[m, "seconds"]) if m in stage.index else None
    stages.append(dict(run_id=RUN_ID, system="B1", molecule_id=m, view=A.view, stage="window", stage_order=0, n_in=None, n_out=n_window, n_identities_out=float(stage.loc[m, "n_unique"]) if m in stage.index else None,
                       identity_source="official", truth_present=(str(win) == "True") if win_known else None, truth_rank=None, top1_identity=None, top25_identities=None, rr25=None, ranked=False,
                       failure_reason=None if win_known else "window flag not recorded for this set", elapsed_s=sec, elapsed_scope="molecule(features)", note=None))
    sl_rank = None
    if g is not None and len(g):
        gs = g.sort_values("fp", ascending=False, kind="stable"); sl_rank = {k: i + 1 for i, k in enumerate(gs.key.astype(str))}.get(T)
    stages.append(dict(run_id=RUN_ID, system="B1", molecule_id=m, view=A.view, stage="shortlist", stage_order=1, n_in=n_window, n_out=len(b_keys), n_identities_out=len(set(b_keys)), identity_source="official",
                       truth_present=T in b_keys, truth_rank=sl_rank, top1_identity=None, top25_identities=None, rr25=None, ranked=False, failure_reason=None if b_keys else "empty shortlist",
                       elapsed_s=sec, elapsed_scope="molecule(features)", note="truth_rank = position by FPNet score inside the shortlist (membership stage)"))
    ins_ids, main_ids = idents(b1_ins.get(m, [])), idents(b1_main.get(m, [])); r_ins, r_main = rank_in(ins_ids, T), rank_in(main_ids, T)
    for order, (name, ids_, lst) in enumerate((("fixed_libpri_insurance", ins_ids, b1_ins.get(m, [])), ("main_blend21_fallback", main_ids, b1_main.get(m, []))), 2):
        rk = rank_in(ids_, T)
        stages.append(dict(run_id=RUN_ID, system="B1", molecule_id=m, view=A.view, stage=name, stage_order=order, n_in=len(b_keys), n_out=len(lst), n_identities_out=len(ids_), identity_source="official",
                           truth_present=T in ids_, truth_rank=rk, top1_identity=ids_[0] if ids_ else None, top25_identities="|".join(ids_[:25]), rr25=rr(rk), ranked=True,
                           failure_reason=None if lst else "empty output", elapsed_s=b1_man.get("seconds"), elapsed_scope="run", note=None))
    b1_stage = "rank1" if r_main == 1 else ("rank>1" if r_main is not None and r_main <= 25 else ("lost_fusion" if T in b_keys else ("not_in_window" if (win_known and str(win) == "False") else "not_in_shortlist")))
    glb, iceb = b1_gl.get(m) or {}, b1_ice.get(m) or {}
    gl_fin = sum(1 for s_ in (g.smiles if g is not None else []) if finite(glb.get(s_)))
    cover = gl_fin / len(b_keys) if b_keys else 0.0
    lib_vals = np.sort(g.lib.to_numpy(float))[::-1] if g is not None and len(g) else np.zeros(0)
    lib_max_b1 = float(lib_vals[0]) if len(lib_vals) else 0.0; lib_2nd = float(lib_vals[1]) if len(lib_vals) > 1 else 0.0
    libpri_fired = lib_max_b1 >= TAU and (lib_max_b1 - lib_2nd) >= MARGIN
    lib_top = str(g.sort_values("lib", ascending=False, kind="stable").key.iloc[0]) if g is not None and len(g) else None
    gates.append(dict(run_id=RUN_ID, system="B1", molecule_id=m, gate_name="libpri_reference_priority", candidate_identity=lib_top, lib_max=lib_max_b1, rel=lib_max_b1 - lib_2nd, S=None, top_pop=None, fired=bool(libpri_fired),
                      selected_channel="reference" if libpri_fired else "fixed_rule", action="protect_rank1" if libpri_fired else "none", truth_rank_before=None, truth_rank_after=r_ins, norm_set_count=len(b_keys),
                      norm_set_hash=sha("|".join(b_keys)), note=f"tau={TAU} margin={MARGIN}; insurance top1={ins_ids[0] if ins_ids else None}"))
    gates.append(dict(run_id=RUN_ID, system="B1", molecule_id=m, gate_name="gl_cover_fallback", candidate_identity=None, lib_max=None, rel=cover, S=None, top_pop=None, fired=bool(cover < MIN_COVER),
                      selected_channel="insurance" if cover < MIN_COVER else "blend21", action="fallback" if cover < MIN_COVER else "none", truth_rank_before=None, truth_rank_after=r_main,
                      norm_set_count=len(b_keys), norm_set_hash=sha("|".join(b_keys)), note=f"gl_finite={gl_fin}/{len(b_keys)} min_gl_cover={MIN_COVER}; main==insurance: {main_ids == ins_ids}"))
    if g is not None:
        ins_rank = {k: i + 1 for i, k in enumerate(ins_ids)}; main_rank = {k: i + 1 for i, k in enumerate(main_ids)}
        for row in g.itertuples(index=False):
            k = str(row.key); g_ = glb.get(row.smiles); i_ = iceb.get(row.smiles)
            cands.append(dict(run_id=RUN_ID, system="B1", molecule_id=m, stage="shortlist", candidate_identity=k, smiles=row.smiles, is_truth=(k == T),
                              source=("tier" if bool(row.in_tier) else ("coconut" if bool(row.in_coconut) else "pool")) + ("+train" if bool(row.in_train) else ""), pid=None, train_sid=None,
                              fp_score=float(row.fp), lib_sim=float(row.lib), lib_nspec=float(row.lib_nref), analog_score=None, mass_ppm=float(row.ppm_err), prior_score=float(row.pop),
                              gl_score=g_ if finite(g_) else None, gl_finite=finite(g_), ice_score=i_ if finite(i_) else None, ice_finite=finite(i_), ranker_score=None,
                              rank_window=int(row.fp_rank_window) if pd.notna(row.fp_rank_window) else None, rank_fixed_libpri_insurance=ins_rank.get(k), rank_main_blend21_fallback=main_rank.get(k),
                              in_shortlist=True, exclusion_reason=None if main_rank.get(k) else "not in main top-25"))
    # ---------------- ledger row
    tr_ok = e1_truth is not None and len(e1_truth) > 0
    ledger.append(dict(common,
        e0_code_hash=(port.get("cells") or {}).get("12", {}).get("sha256_original"), e0_launcher_hash=(audit.get("code") or {}).get("launcher"),
        e0_models="v4b ranker + FPNet full1 (engine 1) / A+B+fold0-4 (PubChem channel) / v3 engine 2 / ICEBERG, GLACIER (MSG)",
        e0_overlap_fp="yes (FPNet A/B/full1 and the 5 fold models were trained on train.parquet, which contains this molecule)", e0_overlap_ranker="yes (simulation rows from train.parquet)",
        e0_overlap_analog_struct=("yes (the truth is a pool train structure = member of the analog set)" if common["truth_in_pool_as_train_struct"] else "no (truth is not a pool train structure)"),
        e0_overlap_gl="unknown (MassSpecGym-trained)", e0_overlap_ice="unknown (MassSpecGym-trained)", e0_external_ref_contains_truth=common["truth_in_e0_external_refs"],
        e0_train_rows_remaining=(train_remaining.get(T, 0) if train_remaining or train_path else None), e0_truth_lib_nspec=(float(e1_truth.lib_nspec.max()) if tr_ok and "lib_nspec" in e1_truth.columns else None),
        e0_truth_lib_max=(float(e1_truth.lib_max.max()) if tr_ok and "lib_max" in e1_truth.columns else None),
        b1_code_hash=b1_man.get("learned_model"), b1_params=json.dumps(b1_params, sort_keys=True), b1_overlap_fp=f"fold-safe fold0 model; molecule fold {fold_of.get(m, 'unknown')}",
        b1_overlap_ranker=("yes (fit group)" if r.group == "fit" else "no (held-out group)"), b1_overlap_gl="unknown (MassSpecGym-trained)", b1_overlap_ice="unknown",
        b1_truth_lib_nref=(float(truth_row.lib_nref.iloc[0]) if truth_row is not None and len(truth_row) else None), b1_truth_in_train_flag=(bool(truth_row.in_train.iloc[0]) if truth_row is not None and len(truth_row) else None),
        b1_truth_lib_sim=(float(truth_row.lib.iloc[0]) if truth_row is not None and len(truth_row) else None), reference_mask_hashes=json.dumps(masks),
        e0_lib_max=md.get("lib_max", (base.get(m) or {}).get("lib_max")), e0_merge_branch=md.get("branch"), e0_promoted=bool(md.get("promoted", False)), e0_rel=md.get("rel"), e0_S=md.get("S"), e0_top_pop=md.get("top_pop"),
        e0_gl_finite=n_finite(glm), e0_ice_finite=n_finite(icem), e0_n1_proxy=m in set(n1.get("n1_gl_mids", [])), e0_frag_gap=m in frag,
        e0_e006_branch=(str(fact.loc[m, "branch"]) if fact is not None and m in fact.index else None), e0_runner_status=json.dumps({k: (v or {}).get("meta", {}).get("status") for k, v in (port.get("forward") or {}).items()}),
        e0_budget_cutoff=json.dumps(audit.get("budget_cutoff")), b1_lib_max=lib_max_b1, b1_lib_margin=lib_max_b1 - lib_2nd, b1_libpri_fired=bool(libpri_fired), b1_gl_finite=gl_fin, b1_gl_cover=cover,
        b1_fallback_insurance=bool(cover < MIN_COVER), b1_n_shortlist=len(b_keys), b1_n_window=n_window, b1_lib_max_stage=float(stage.loc[m, "lib_max"]) if m in stage.index else None,
        e0_rank_window=r_window, **{f"e0_rank_{k}": v for k, v in e0_ranks.items()}, e0_rank_final=r_final, rr_e0=rr(r_final), e0_stage=e0_stage, e0_loss_class=e0_loss,
        b1_window_any=win, b1_in_shortlist=T in b_keys, b1_rank_shortlist_fp=sl_rank, b1_rank_main=r_main, rr_b1_main=rr(r_main), b1_rank_ins=r_ins, rr_b1_ins=rr(r_ins), b1_stage=b1_stage,
        rr_b1_main_eval=float(evalpm.loc[m, "rr"]) if evalpm is not None and m in evalpm.index else np.nan, rr_b1_fixed_eval=float(evalpm.loc[m, "rr_fixed"]) if evalpm is not None and m in evalpm.index else np.nan))

df = pd.DataFrame(ledger); df["d_main"] = df.rr_e0 - df.rr_b1_main; df["d_ins"] = df.rr_e0 - df.rr_b1_ins
df.to_csv(os.path.join(A.out, "ledger.csv"), index=False); pd.DataFrame(stages).to_csv(os.path.join(A.out, "stages.csv"), index=False)
pd.DataFrame(gates).to_csv(os.path.join(A.out, "gates.csv"), index=False)
if cands: pq.write_table(pa.Table.from_pandas(pd.DataFrame(cands), preserve_index=False), os.path.join(A.out, "candidates.parquet"))
missing_e0 = sorted(set(df.molecule_id) - set(E0_FINAL)); D = df[df.molecule_id.isin(set(E0_FINAL))].copy()
if missing_e0: print(f"WARNING: {len(missing_e0)} molecules without an E0 final list are excluded from the paired statistics", missing_e0[:5])


# ------------------------------------------------------------------------------------------------------------------ summaries
def paired(sub):
    lo, hi = boot_ci(sub.d_main.values)
    return dict(n=int(len(sub)), e0=round(float(sub.rr_e0.mean()), 4), b1_main=round(float(sub.rr_b1_main.mean()), 4), b1_ins=round(float(sub.rr_b1_ins.mean()), 4), delta_main=round(float(sub.d_main.mean()), 4),
                ci_main=[round(lo, 4), round(hi, 4)], delta_ins=round(float(sub.d_ins.mean()), 4), wins=int((sub.d_main > 0).sum()), losses=int((sub.d_main < 0).sum()), ties=int((sub.d_main == 0).sum()))


def by(col, order=None):
    vals = order or sorted(D[col].astype(str).unique()); return {str(v): paired(D[D[col].astype(str) == str(v)]) for v in vals if (D[col].astype(str) == str(v)).any()}


S = dict(run_id=RUN_ID, view=A.view, e0_run=E0, b1_run=B1, n_solution=int(len(df)), n_paired=int(len(D)), missing_e0=missing_e0, generated=time.strftime("%Y-%m-%dT%H:%M:%S"),
         e0_stage_mrr={name: round(float(np.mean([rr(rank_in(idents(fn(m) or []), t)) for m, t in zip(D.molecule_id, D.official_identity)])), 4) for name, fn in E0_LISTS if name not in UNRANKED_E0},
         e0_channel_recall={"e1_window": round(float(D.e0_rank_window.notna().mean()), 4), "e1_base60_top25": round(float((D.e0_rank_e1_base60 <= 25).mean()), 4), "e1_base60_any": round(float(D.e0_rank_e1_base60.notna().mean()), 4),
                            "e2_list40_top25": round(float((D.e0_rank_e2_list40 <= 25).mean()), 4), "pc_list25": round(float(D.e0_rank_pc_list25.notna().mean()), 4)},
         b1_recall={"window_any": round(float((D.b1_window_any.astype(str) == "True").mean()), 4), "shortlist": round(float(D.b1_in_shortlist.mean()), 4)},
         c2_leak_audit=dict(e0_train_rows_remaining_max=(float(D.e0_train_rows_remaining.max()) if D.e0_train_rows_remaining.notna().any() else None), e0_truth_lib_nspec_max=(float(D.e0_truth_lib_nspec.max()) if D.e0_truth_lib_nspec.notna().any() else None),
                            e0_truth_in_external_refs=int(D.truth_in_e0_external_refs.sum()), e0_truth_in_pool_as_train_struct=int(D.truth_in_pool_as_train_struct.sum()),
                            b1_truth_lib_nref_max=(float(D.b1_truth_lib_nref.max()) if D.b1_truth_lib_nref.notna().any() else None), b1_truth_in_train_flag_any=bool(D.b1_truth_in_train_flag.fillna(False).astype(bool).any())),
         overall=paired(D), by_set=by("set"), by_lib=by("query_lib"), by_coverage=by("stratum_coverage"), by_nref_bin=by("stratum_nref_bin", ["1-2", "3-5", "6-10", "11+"]), by_group=by("group"),
         by_external_ref_flag=by("truth_in_e0_external_refs"), by_e0_merge_branch=by("e0_merge_branch"), by_e0_loss_class=by("e0_loss_class"), by_b1_stage=by("b1_stage"),
         by_e0_gl_cover={"e0_gl_finite>0": paired(D[D.e0_gl_finite > 0]), "e0_gl_finite=0": paired(D[D.e0_gl_finite == 0])},
         by_b1_fallback={str(v): paired(D[D.b1_fallback_insurance == v]) for v in (False, True) if (D.b1_fallback_insurance == v).any()},
         cross_stage={}, e0_wins_by_b1_stage={}, e0_losses_by_e0_loss_class={}, only_e0_right_by_b1_stage={}, only_b1_right_by_e0_loss_class={},
         e0_forward=port.get("forward"), e0_budgets=port.get("budgets"), e0_coverage=audit.get("coverage"), b1_manifest_fusion=b1_man.get("fusion"), b1_consistency={})
for es in ["rank1", "rank>1", "lost_merge_fusion", "not_generated", "not_processed"]:
    for bs in ["rank1", "rank>1", "lost_fusion", "not_in_shortlist", "not_in_window"]:
        sub = D[(D.e0_stage == es) & (D.b1_stage == bs)]
        if len(sub): S["cross_stage"][f"E0 {es} | B1 {bs}"] = dict(n=int(len(sub)), sum_delta_main=round(float(sub.d_main.sum()), 3), mean_delta_main=round(float(sub.d_main.mean()), 4))
W, L = D[D.d_main > 0], D[D.d_main < 0]
S["e0_wins_by_b1_stage"] = {bs: dict(n=int((W.b1_stage == bs).sum()), sum_delta=round(float(W[W.b1_stage == bs].d_main.sum()), 3)) for bs in sorted(W.b1_stage.unique())}
S["e0_losses_by_e0_loss_class"] = {c: dict(n=int((L.e0_loss_class == c).sum()), sum_delta=round(float(L[L.e0_loss_class == c].d_main.sum()), 3)) for c in sorted(L.e0_loss_class.unique())}
OE = D[(D.rr_e0 == 1.0) & (D.rr_b1_main < 1.0)]; OB = D[(D.rr_b1_main == 1.0) & (D.rr_e0 < 1.0)]
S["only_e0_right_by_b1_stage"] = {bs: int((OE.b1_stage == bs).sum()) for bs in sorted(OE.b1_stage.unique())}
S["only_b1_right_by_e0_loss_class"] = {c: int((OB.e0_loss_class == c).sum()) for c in sorted(OB.e0_loss_class.unique())}
if evalpm is not None:
    S["b1_consistency"] = dict(main_abs_diff_max=round(float((D.rr_b1_main - D.rr_b1_main_eval).abs().max()), 4), fixed_abs_diff_max=round(float((D.rr_b1_ins - D.rr_b1_fixed_eval).abs().max()), 4),
                               note="RR recomputed here (official-key equality on the submission SMILES) vs the pipeline evaluator's per-molecule RR")
json.dump(S, open(os.path.join(A.out, "summary.json"), "w"), indent=1, default=str)


# ------------------------------------------------------------------------------------------------------------------ report
def tbl(d, title):
    out = [f"### {title}", "", "| stratum | n | E0 final | B1 main | B1 insurance | E0 − B1 main [95% CI] | E0 − B1 ins | wins / losses / ties |", "|---|---:|---:|---:|---:|---|---:|---|"]
    for k, v in d.items(): out.append(f"| {k} | {v['n']} | {v['e0']:.4f} | {v['b1_main']:.4f} | {v['b1_ins']:.4f} | {v['delta_main']:+.4f} [{v['ci_main'][0]:+.4f}, {v['ci_main'][1]:+.4f}] | {v['delta_ins']:+.4f} | {v['wins']} / {v['losses']} / {v['ties']} |")
    return "\n".join(out) + "\n"


R = [f"# E0 (offline, public 0.464 lineage) vs B1 — {A.view.upper()} proxy, {len(D)} paired molecules (`{RUN_ID}`)", "",
     f"Generated {S['generated']}. E0 run `{E0}`; B1 run `{B1}` (main = {b1_params.get('main', '?')} with GL-coverage fallback; insurance = fixed + libpri τ{TAU}). Identities: official scorer key "
     f"(src/metric.py). RR over the top 25, unreached truth = 0, final outputs scored as-is. Paired bootstrap CI ({A.boot} resamples). Tables: ledger.csv (molecule × view), stages.csv (molecule × system × stage), "
     "candidates.parquet (per-stage candidates with provenance / scores / ranks), gates.csv (merge and gate operations).", "",
     "**Reading rules.** Same query spectra, same proxy view on both sides. Weight-level training exposure cannot be removed: E0's FPNet A/B/full1 + fold models and ranker were trained on train.parquet, "
     "which contains every molecule here (ledger `e0_overlap_*`); B1's ranker saw the `fit` groups (`b1_overlap_ranker`). `truth_in_e0_external_refs` = the identity is in E0's external reference library "
     "(knowledge table) and can be matched by spectrum even in the C2 proxy -> diagnostic only for the class-2 question. `truth_in_pool_as_train_struct` = the truth stays a pool structure "
     "(DB candidate; allowed) but also a member of E0's analog-structure set (structure-level membership, not removable without rebuilding pinned assets).", "",
     f"C2 leak audit: {json.dumps(S['c2_leak_audit'])}", "", f"E0 forward runners: {json.dumps(S['e0_forward'], default=str)[:700]}", f"E0 budgets {json.dumps(S['e0_budgets'])}; coverage {json.dumps(S['e0_coverage'])}", "",
     f"B1 fusion counts: {json.dumps(S['b1_manifest_fusion'])}", "", "### E0 stage MRR (same molecules; ranked outputs only)", "", "| list | MRR@25 |", "|---|---:|"] + \
    [f"| {k} | {v:.4f} |" for k, v in S["e0_stage_mrr"].items()] + ["", f"E0 channel recall: {json.dumps(S['e0_channel_recall'])}; B1 recall: {json.dumps(S['b1_recall'])}", "",
     tbl({"all": S["overall"]}, "Overall"), tbl(S["by_set"], "By set"), tbl(S["by_group"], "By split role (fit = B1 ranker training groups)"), tbl(S["by_lib"], "By selection library"),
     tbl(S["by_coverage"], "By forward-model adduct coverage of the query spectra"), tbl(S["by_nref_bin"], "By number of spectra of the truth in its library (molecule property)"),
     tbl(S["by_external_ref_flag"], "By 'identity in E0's external reference library' (True = diagnostic only)"), tbl(S["by_e0_merge_branch"], "By E0 merge branch"),
     tbl(S["by_e0_loss_class"], "By E0 loss class"), tbl(S["by_b1_stage"], "By B1 stage"), tbl(S["by_e0_gl_cover"], "By E0 GLACIER coverage"), tbl(S["by_b1_fallback"], "By B1 GL-cover fallback (True = insurance list emitted)"),
     "### Cross table: E0 stage × B1 stage (n, Σ ΔRR = E0 − B1 main)", "", "| cell | n | Σ Δ | mean Δ |", "|---|---:|---:|---:|"] + \
    [f"| {k} | {v['n']} | {v['sum_delta_main']:+.3f} | {v['mean_delta_main']:+.4f} |" for k, v in S["cross_stage"].items()] + [
     "", f"Molecules only E0 gets right (top-1), by the B1 stage that lost them: {json.dumps(S['only_e0_right_by_b1_stage'])}",
     f"Molecules only B1 gets right (top-1), by E0 loss class: {json.dumps(S['only_b1_right_by_e0_loss_class'])}", "",
     f"E0 wins by B1 stage: {json.dumps(S['e0_wins_by_b1_stage'])}", f"E0 losses by E0 loss class: {json.dumps(S['e0_losses_by_e0_loss_class'])}", "",
     f"B1 consistency (recomputed vs evaluator RR): {json.dumps(S['b1_consistency'])}", "",
     "### Largest paired differences", "", "| molecule | set/group | lib | coverage | nref | ext_ref | E0 lib_max / branch | E0 ranks window/base/e2/pc → final | E0 loss class | B1 win/short → main / ins | Δ main |", "|---|---|---|---|---:|---|---|---|---|---|---:|"]
f_ = lambda x: "-" if x is None or (isinstance(x, float) and np.isnan(x)) else (int(x) if isinstance(x, float) else x)
for r_ in D.reindex(D.d_main.abs().sort_values(ascending=False).index).head(40).itertuples(index=False):
    R.append(f"| {r_.molecule_id} | {r_.split_role} | {r_.query_lib} | {r_.stratum_coverage} | {r_.n_spectra_lib} | {r_.truth_in_e0_external_refs} | {('-' if r_.e0_lib_max is None else round(float(r_.e0_lib_max), 3))} / {r_.e0_merge_branch}{' (promoted)' if r_.e0_promoted else ''} | "
             f"{f_(r_.e0_rank_window)}/{f_(r_.e0_rank_e1_base60)}/{f_(r_.e0_rank_e2_list40)}/{f_(r_.e0_rank_pc_list25)} → {f_(r_.e0_rank_final)} | {r_.e0_loss_class} | {r_.b1_window_any}/{r_.b1_in_shortlist} → {f_(r_.b1_rank_main)} / {f_(r_.b1_rank_ins)} | {r_.d_main:+.3f} |")
open(os.path.join(A.out, "report.md"), "w", encoding="utf-8").write("\n".join(R) + "\n")
print(f"done {time.time() - t0:.0f}s ->", A.out); print("overall", json.dumps(S["overall"])); print("by set", json.dumps(S["by_set"])); print("leak audit", json.dumps(S["c2_leak_audit"]))
