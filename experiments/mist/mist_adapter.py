"""MIST input adapter for new spectra (CASMI): one (spectrum, neutral precursor formula, adduct) -> the compact-cache row MIST's model reads.
Uses MIST's own functions only (featurizers.merge_ms_spectrum on an .ms-style text, featurizers.assign_subformulae at 20 ppm, chem_utils), and
the compact layout of build_all_cache.py: W = max_peaks + 1 = 11 rows, the top-10 assigned fragments by intensity then the CLS row
(root formula, root adduct, intensity 1.0, peak_type 3), zero padding after, intensities stored as float16, length = fragments + 1.
Adducts outside MIST's ION_LST raise; elements outside its 18-element vocabulary raise (callers record these as design-missing).
The instrument index is stored but unused by the model (embed_instrument=False)."""
import numpy as np
from mist.data import featurizers as F
from mist.utils import chem_utils as C
W = 11
def ms_text(mzs, intens, prec_mz):
    return f">parentmass {float(prec_mz)!r}\n" + "\n".join(f"{float(m)!r} {float(i)!r}" for m, i in zip(mzs, intens))
def featurize(mzs, intens, prec_mz, formula, adduct, instrument="unknown", max_peaks=10):
    if adduct not in C.ION_LST: raise KeyError(f"adduct {adduct!r} not in MIST ION_LST")
    merged = F.merge_ms_spectrum(ms_text(mzs, intens, prec_mz))
    tree = F.assign_subformulae({"cand_form": formula, "cand_ion": adduct,
                                 "output_tbl": ({"mz": merged[:, 0].tolist(), "ms2_inten": merged[:, 1].tolist()} if len(merged) else None)}, 20.0)
    tab = tree["output_tbl"]
    if tab is None: frags, ints, ions = [], [], []
    else:
        o = np.argsort(np.asarray(tab["ms2_inten"], dtype=float))[::-1][:max_peaks]
        frags = np.asarray(tab["formula"], dtype=str)[o].tolist(); ints = np.asarray(tab["ms2_inten"], dtype=float)[o].tolist(); ions = np.asarray(tab["ions"], dtype=str)[o].tolist()
    n = len(frags) + 1
    form = np.zeros((W, len(C.VALID_ELEMENTS) if hasattr(C, "VALID_ELEMENTS") else 18), dtype=np.int16)
    rows = [C.formula_to_dense(f) for f in frags] + [C.formula_to_dense(formula)]
    for k, r in enumerate(rows): form[k, :len(r)] = r
    ion = np.zeros(W, dtype=np.uint8); ion[:n] = [C.get_ion_idx(x) for x in ions] + [C.get_ion_idx(adduct)]
    it = np.zeros(W, dtype=np.float16); it[:n] = np.asarray(ints + [1.0], dtype=np.float16)
    pt = np.zeros(W, dtype=np.uint8); pt[:n] = [0] * len(frags) + [3]
    return dict(form_vec=form, ion_vec=ion, intens=it, peak_type=pt, lengths=np.uint8(n), instruments=np.uint8(C.get_instr_idx(instrument)))
def collate(rows):
    import torch
    return {"form_vec": torch.from_numpy(np.stack([r["form_vec"] for r in rows]).astype(np.float32)),
            "ion_vec": torch.from_numpy(np.stack([r["ion_vec"] for r in rows]).astype(np.int64)),
            "intens": torch.from_numpy(np.stack([r["intens"] for r in rows]).astype(np.float32)),
            "types": torch.from_numpy(np.stack([r["peak_type"] for r in rows]).astype(np.int64)),
            "num_peaks": torch.from_numpy(np.asarray([r["lengths"] for r in rows], dtype=np.int64)),
            "instruments": torch.from_numpy(np.asarray([r["instruments"] for r in rows], dtype=np.int64))}
