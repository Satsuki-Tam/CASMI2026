"""W135 step 1 (135_decision.md; rules fixed in w135_census.md / 136): batches and proxy-class assignments -- reads only the census population
(structure / fold / library / spectrum metadata), never a candidate, model or generation output.
Per identity: query library chosen as p3_select_np.py (libraries with test-adduct spectra minus enveda-180 / enveda-np-examples, a fixed-seed
choice among them), queries = select_queries (max 8); C1 eligibility = at least one other-library reference of a query polarity after the
p3_select_np de-duplication (adduct, precursor 3 dp, CE 1 dp, n_peaks) minus query copies; C2 eligibility = truth in a non-train structure DB
(true for the whole population: COCONUT truth). Families = Butina 0.5 labels (fam50) of the census.
Batches (N = 100, one identity per identity group over ALL batches of a fold, families never split across batches):
  family batch  : families of size >= 2 in hash order, members in hash order, at most 8 per family, greedy fill (a family that does not fit
                  is truncated only when >= 2 members fit, else skipped for this batch);
  random batch  : matched to one family batch member by member on (query polarity, neutral-mass band, query library), fallback (polarity,
                  band), then (polarity); drawn in hash order from identities whose family touches no family batch.
Proxy classes per batch and pi3 in {0, 0.3, 0.6}: identities in hash order; the first round(pi3 N) are C3 (nested over pi3); of the rest,
C1 = the first floor(rest / 2) C1-eligible identities in hash order, the others C2 (actual counts recorded).
Usage (Spark, repo root): .venv/bin/python -X utf8 experiments/w135/w135_batches.py --fold 1 --n_family 3 --n_random 3 --tag d
                          .venv/bin/python -X utf8 experiments/w135/w135_batches.py --fold 2 --n_family 1 --n_random 1 --n_random_unused 1 --tag c"""
import argparse, hashlib, json, os, sys
import numpy as np, polars as pl
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); B = os.path.join(ROOT, "experiments/b1_baseline"); sys.path.insert(0, B)
from b1_common import ADDUCT_SHIFT, select_queries
ap = argparse.ArgumentParser(); ap.add_argument("--fold", type=int, required=True); ap.add_argument("--n_family", type=int, default=3); ap.add_argument("--n_random", type=int, default=3)
ap.add_argument("--n_random_unused", type=int, default=0); ap.add_argument("--N", type=int, default=100); ap.add_argument("--fam_cap", type=int, default=8); ap.add_argument("--seed", type=int, default=135)
ap.add_argument("--tag", required=True); ap.add_argument("--max_spectra", type=int, default=8); a = ap.parse_args()
NO_QUERY_LIBS = {"enveda-180", "enveda-np-examples"}; PIS = (0.0, 0.3, 0.6)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
H = lambda s: hashlib.sha256(s.encode()).hexdigest()
popf = os.path.join(ROOT, "experiments/w135", "census" + ("" if a.fold == 1 else f"_fold{a.fold}"), "population.parquet")
P = pl.read_parquet(popf)
OUT = os.path.join(ROOT, "experiments/w135/batches"); os.makedirs(OUT, exist_ok=True)
if any(f.startswith(f"{a.tag}_") for f in os.listdir(OUT)): sys.exit(f"REFUSED: batches with tag {a.tag} exist")
meta = pl.read_parquet(os.path.join(ROOT, "data/processed/spectra_store/spec_meta.parquet")).filter(pl.col("adduct").is_in(list(ADDUCT_SHIFT)) & pl.col("inchikey14").is_in(P["inchikey14"].to_list()))
meta = meta.with_columns(pl.col("ce_mean").fill_null(-1.0).round(1).alias("ce_r"), pl.col("precursor_mz").round(3).alias("prec_r"))
rows_of = {}
for ik, lib, add, mode, ce, pr, npk, row in meta.select("inchikey14", "ingest_lib", "adduct", "ionization_mode", "ce_r", "prec_r", "n_peaks", "row").iter_rows():
    rows_of.setdefault(ik, []).append(dict(lib=lib, adduct=add, mode=mode, ce=ce, prec=pr, npk=npk, row=row))
rng = np.random.default_rng(a.seed)


def analyse(ik, L):   # = p3_select_np.analyse
    rs = rows_of.get(ik, []); qrows = sorted((r for r in rs if r["lib"] == L), key=lambda r: r["row"])
    if not qrows: return None
    q = select_queries(qrows, a.max_spectra, lambda r: r["adduct"], lambda r: (None if r["ce"] < 0 else r["ce"]))
    modes = {r["mode"] for r in q}; adds = {r["adduct"] for r in q}; qkeys = {(r["adduct"], r["prec"], r["ce"], r["npk"]) for r in q}
    other = [r for r in rs if r["lib"] != L and r["mode"] in modes]
    dedup = {(r["adduct"], r["prec"], r["ce"], r["npk"]) for r in other} - qkeys
    pol = "mix" if len(modes) > 1 else ("pos" if "positive" in modes else "neg")
    return dict(n_q=len(q), q_adducts="|".join(sorted(adds)), pol=pol, n_ref_other_samepol_dedup=len(dedup), n_libs_other=len({r["lib"] for r in other}))


recs = []
for r in P.sort("inchikey14").iter_rows(named=True):
    ik = r["inchikey14"]; libs = sorted({x["lib"] for x in rows_of.get(ik, [])} - NO_QUERY_LIBS); qual = [(L, A) for L in libs for A in [analyse(ik, L)] if A and A["n_q"] >= 1]
    if not qual: continue
    L, A = qual[int(rng.integers(len(qual)))] if len(qual) > 1 else qual[0]
    band = "<300" if r["mass"] < 300 else ("300-500" if r["mass"] < 500 else ("500-800" if r["mass"] < 800 else ">=800"))
    recs.append(dict(molecule=ik, scorer_key=r["scorer_key"] or ik, raw_key=ik, lib=L, identity_group=int(r["identity_group"]), fam=int(r["fam50"]), used=bool(r["used"]), mass=float(r["mass"]),
                     band=band, murcko_generic=r["murcko_generic"], c1_eligible=A["n_ref_other_samepol_dedup"] >= 1, n_qualifying_libs=len(qual), **A))
D = pl.DataFrame(recs); counts = dict(population=P.height, with_query_library=D.height)
fsize = D.group_by("fam").len().rename({"len": "fam_size"}); D = D.join(fsize, on="fam")
taken_groups, taken_fams, batches = set(), set(), {}
# ---- family batches
fams = sorted([f for f, s in zip(fsize["fam"], fsize["fam_size"]) if s >= 2], key=lambda f: H(f"w135fam|{a.fold}|{min(D.filter(pl.col('fam') == f)['molecule'])}"))
members = {f: sorted(D.filter(pl.col("fam") == f)["molecule"].to_list(), key=lambda m: H(f"w135mem|{m}")) for f in fams}
G = dict(zip(D["molecule"], D["identity_group"]))
fi = 0
for b in range(a.n_family):
    name = f"{a.tag}F{b + 1}"; cur = []
    while len(cur) < a.N and fi < len(fams):
        f = fams[fi]; fi += 1
        mem = [m for m in members[f] if G[m] not in taken_groups]
        seen_g, mem2 = set(), []
        for m in mem:
            if G[m] not in seen_g: seen_g.add(G[m]); mem2.append(m)
        mem2 = mem2[:a.fam_cap]
        room = a.N - len(cur)
        if len(mem2) < 2: continue
        if len(mem2) > room:
            if room >= 2: mem2 = mem2[:room]
            else: fi -= 1; break
        cur += mem2; taken_fams.add(f); taken_groups |= {G[m] for m in mem2}
    batches[name] = dict(kind="family", molecules=cur)
# ---- random batches (matched to the family batches in order)
pool = sorted([m for m, f in zip(D["molecule"], D["fam"]) if f not in taken_fams], key=lambda m: H(f"w135rnd|{m}"))
info = {r["molecule"]: r for r in D.iter_rows(named=True)}
fam_batch = {f: None for f in taken_fams}   # family -> batch (None = a family batch); random batches never share a family with another batch
def draw(ref, name, used_only=False):
    for level, keyf in ((0, lambda x: (x["pol"], x["band"], x["lib"])), (1, lambda x: (x["pol"], x["band"])), (2, lambda x: (x["pol"],))):
        for m in pool:
            x = info[m]
            if x["identity_group"] in taken_groups or (used_only and x["used"]): continue
            if x["fam"] in fam_batch and fam_batch[x["fam"]] != name: continue
            if keyf(x) == keyf(info[ref]): return m, level
    return None, None
fam_names = [n for n in batches if batches[n]["kind"] == "family"]
for kind, nb in (("random", a.n_random), ("random_unused", a.n_random_unused)):
    for b in range(nb):
        name = f"{a.tag}{'R' if kind == 'random' else 'U'}{b + 1}"; ref_batch = fam_names[b % len(fam_names)] if fam_names else None; cur, lv = [], []
        refs = batches[ref_batch]["molecules"] if ref_batch else []
        for ref in refs:
            m, l_ = draw(ref, name, used_only=(kind == "random_unused"))
            if m is None: continue
            cur.append(m); lv.append(l_); taken_groups.add(info[m]["identity_group"]); fam_batch[info[m]["fam"]] = name
        batches[name] = dict(kind=kind, molecules=cur, matched_to=ref_batch, match_levels={str(k): lv.count(k) for k in (0, 1, 2)})
# ---- classes and outputs
for name, bt in batches.items():
    ms = sorted(bt["molecules"], key=lambda m: H(f"w135cls|{name}|{m}")); N = len(ms); out = []
    cls = {}
    for pi in PIS:
        n3 = int(round(pi * N)); c3 = ms[:n3]; rest = ms[n3:]; n1 = len(rest) // 2
        c1 = [m for m in rest if info[m]["c1_eligible"]][:n1]; c = {m: "C3" for m in c3}; c.update({m: ("C1" if m in set(c1) else "C2") for m in rest}); cls[pi] = c
    for m in ms:
        x = info[m]; out.append(dict(set=name, group="eval", molecule=m, scorer_key=x["scorer_key"], raw_key=x["raw_key"], lib=x["lib"], identity_group=x["identity_group"], fam=x["fam"],
                                     fam_size=x["fam_size"], used=x["used"], c1_eligible=x["c1_eligible"], pol=x["pol"], band=x["band"], mass=x["mass"], n_q=x["n_q"], q_adducts=x["q_adducts"],
                                     n_ref_other_samepol_dedup=x["n_ref_other_samepol_dedup"], murcko_generic=x["murcko_generic"], **{f"wclass_p{int(pi * 100)}": cls[pi][m] for pi in PIS}))
    df = pl.DataFrame(out); df.write_csv(os.path.join(OUT, f"{name}.csv"))
    bt["n"] = N; bt["classes"] = {f"p{int(pi * 100)}": {k: int((df[f"wclass_p{int(pi * 100)}"] == k).sum()) for k in ("C1", "C2", "C3")} for pi in PIS}
    bt["n_families"] = int(df["fam"].n_unique()); bt["fam_ge2_in_batch"] = int((df.group_by("fam").len()["len"] >= 2).sum()); bt["used"] = int(df["used"].sum())
    bt["pol"] = {k: int(v) for k, v in zip(*np.unique(df["pol"].to_numpy(), return_counts=True))}; bt["band"] = {k: int(v) for k, v in zip(*np.unique(df["band"].to_numpy(), return_counts=True))}
    bt["c1_eligible"] = int(df["c1_eligible"].sum()); bt["molecules"] = sorted(bt["molecules"])
allm = [m for bt in batches.values() for m in bt["molecules"]]
checks = dict(no_identity_overlap=len(allm) == len(set(allm)), one_per_group=len({info[m]["identity_group"] for m in allm}) == len(allm),
              families_disjoint=all(not (set(info[m]["fam"] for m in batches[x]["molecules"]) & set(info[m]["fam"] for m in batches[y]["molecules"])) for x in batches for y in batches if x < y))
man = dict(fold=a.fold, tag=a.tag, seed=a.seed, N=a.N, fam_cap=a.fam_cap, family_rule="Butina 0.5 Morgan r2 2048 (census fam50)", counts=counts, checks=checks,
           batches={k: {kk: vv for kk, vv in v.items() if kk != "molecules"} for k, v in batches.items()},
           inputs_sha256=dict(population=sha(popf), script=sha(os.path.abspath(__file__)), spec_meta=sha(os.path.join(ROOT, "data/processed/spectra_store/spec_meta.parquet"))))
json.dump(man, open(os.path.join(OUT, f"{a.tag}_manifest.json"), "w"), indent=1); print(json.dumps(man, indent=1)[:4000])
assert all(checks.values()), checks
