"""Learned-similarity analogs (040): the same representative store and masks as b1_analog.Store, but analogs are chosen and weighted by
the cosine of the ls_train.py embeddings (an estimate of the structures' Tanimoto) instead of the entropy similarity.
"""
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F
from b1_common import ADDUCT_SHIFT, ELECTRON


class Enc(nn.Module):
    def __init__(s, nb):
        super().__init__(); s.net = nn.Sequential(nn.Linear(nb + 1, 1024), nn.BatchNorm1d(1024), nn.LeakyReLU(), nn.Dropout(0.2), nn.Linear(1024, 512), nn.BatchNorm1d(512), nn.LeakyReLU(), nn.Dropout(0.2), nn.Linear(512, 256))
    def forward(s, x): return F.normalize(s.net(x), dim=1)


class LSEmbedder:
    def __init__(self, model_path, device="cuda"):
        ck = torch.load(model_path, map_location=device, weights_only=False)
        self.nb, self.mz0, self.bw, self.topk = ck["nb"], ck["mz0"], ck["bw"], ck["topk"]; self.dev = device
        self.enc = Enc(self.nb).to(device); self.enc.load_state_dict(ck["state"]); self.enc.eval()

    def vec(self, mz, it, positive):
        mz = np.asarray(mz, np.float64); it = np.asarray(it, np.float64)
        ok = (mz >= self.mz0) & (mz < self.mz0 + self.nb * self.bw) & np.isfinite(it) & (it > 0); mz, it = mz[ok], it[ok]
        x = np.zeros(self.nb + 1, np.float32); x[self.nb] = 1.0 if positive else 0.0
        if len(it):
            if len(it) > self.topk:
                o = np.argsort(-it)[:self.topk]; mz, it = mz[o], it[o]
            b = ((mz - self.mz0) / self.bw).astype(np.int64); v = np.sqrt(it / it.max())
            np.maximum.at(x, b, v.astype(np.float32)); n = np.linalg.norm(x[:self.nb]); x[:self.nb] /= (n + 1e-9)
        return x

    @torch.no_grad()
    def embed(self, X):
        out = []
        for s0 in range(0, len(X), 4096):
            out.append(self.enc(torch.tensor(np.asarray(X[s0:s0 + 4096]), device=self.dev)).half().cpu().numpy())
        return np.concatenate(out) if out else np.zeros((0, 256), np.float16)


class LSAnalogs:
    """built on an existing b1_analog.Store `st` (its representative rows per mode, sorted by neutral mass)."""

    def __init__(self, store, embedder, spectrum, log=print):
        self.S, self.E, self.st, self.spectrum = {}, embedder, store, spectrum
        for md, d in store.S.items():   # chunked: a dense matrix of every representative would not fit in memory
            parts = []
            for s0 in range(0, len(d["row"]), 8192):
                parts.append(embedder.embed(np.stack([self._vec_row(int(x)) for x in d["row"][s0:s0 + 8192]])))
            self.S[md] = np.concatenate(parts) if parts else np.zeros((0, 256), np.float16); log(f"ls embeddings {md}: {len(self.S[md]):,}")

    def _vec_row(self, x):
        st = self.st; mz, it = self.spectrum(x); sh = ELECTRON if (st.lib[x] == "enveda-180" and st.mode[x] == "positive") else 0.0
        return self.E.vec(np.asarray(mz, np.float64) - sh, it, st.mode[x] == "positive")

    def analogs(self, qspec, query_rows=(), drop_keys=(), relib=None, key_rows=None, n_analog=80, win=200.0):
        st = self.st; qset = set(int(x) for x in query_rows); best = {}
        drop_ix = {st.kix[k] for k in drop_keys if k in st.kix}; re_ix = st.kix.get(relib[0]) if relib else None
        qv = []
        for s in qspec:
            v = self.E.vec(s["mz"], s["it"], s["mode"] == "positive"); qv.append((s, self.E.embed(v[None, :])[0].astype(np.float32)))
        for s, e in qv:
            d = st.S.get(s["mode"]); emb = self.S.get(s["mode"])
            if d is None or not len(d["M"]): continue
            Mq = float(s["prec"]) + ADDUCT_SHIFT[s["adduct"]]
            lo = int(np.searchsorted(d["M"], Mq - win, "left")); hi = int(np.searchsorted(d["M"], Mq + win, "right"))
            if hi <= lo: continue
            sims = emb[lo:hi].astype(np.float32) @ e
            for kk in np.flatnonzero(sims > 0.05):
                r = lo + int(kk)
                if int(d["row"][r]) in qset: continue
                ki = int(d["key"][r])
                if ki in drop_ix or ki == re_ix: continue
                v_ = float(sims[kk])
                if v_ > best.get(ki, 0.0): best[ki] = v_
        if relib and re_ix is not None and key_rows is not None and relib[0] not in drop_keys:
            alt = [int(x) for x in key_rows.get(relib[0], []) if st.lib[x] != relib[1] and int(x) not in qset and st.add[x] in ADDUCT_SHIFT]
            v_ = 0.0
            for md in ("positive", "negative"):
                reps = st.pick([x for x in alt if st.mode[x] == md])
                if not reps: continue
                E2 = self.E.embed(np.stack([self._vec_row(int(y)) for y in reps])).astype(np.float32)
                for s, e in qv:
                    if s["mode"] == md: v_ = max(v_, float((E2 @ e).max()))
            if v_ > 0.05: best[re_ix] = v_
        top = sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))[:n_analog]
        return [(st.keys[k], v) for k, v in top]
