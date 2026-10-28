"""111 (Codex 111): own dual-encoder head on the fold-safe FPNet.
Spectrum side = the FPNet encoder (public architecture, casmi/fpnet.py) initialised from a fold-safe checkpoint; its pooled embedding (cls + mean,
2d) goes through a new projection to a unit vector s. Molecule side = the same 10,226 fingerprint bits the FPNet predicts, through a new MLP to a
unit vector m. Score N = cos(s, m) (inference: mean over the query spectra of the per-spectrum cosine; no FP term). The FPNet's own FP head stays
in the model and is trained only as an auxiliary loss."""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

CFG_KEYS = ("nbits", "d", "layers", "heads", "d_out", "hid")


class N111(nn.Module):
    def __init__(self, fpnet_module, fpnet_model, d_out=256, hid=1024, drop=0.1):
        super().__init__()
        self.fp = fpnet_model; nbits = fpnet_model.nbits; d2 = 2 * fpnet_model.d
        self.cfg = dict(nbits=nbits, d=fpnet_model.d, layers=fpnet_model.layers, heads=fpnet_model.heads, d_out=d_out, hid=hid)
        self.sproj = nn.Sequential(nn.Linear(d2, hid), nn.GELU(), nn.Linear(hid, d_out))
        self.mol = nn.Sequential(nn.Linear(nbits, hid), nn.GELU(), nn.Dropout(drop), nn.Linear(hid, d_out))
        self.logit_scale = nn.Parameter(torch.tensor(math.log(1 / 0.07)))

    def spectrum(self, *inp):
        """FP logits z, element head, unit spectrum embedding s."""
        z, el, emb = self.fp(*inp, return_emb=True)
        return z, el, F.normalize(self.sproj(emb.float()), dim=-1)

    def molecule(self, bits):
        """bits: (..., nbits) float {0,1} -> unit molecule embedding."""
        return F.normalize(self.mol(bits.float()), dim=-1)

    def scale(self):
        return self.logit_scale.exp().clamp(1.0, 100.0)


def save(path, model, step, extra=None):
    d = dict(state=model.state_dict(), cfg=model.cfg, step=int(step))
    if extra: d.update(extra)
    torch.save(d, path)


def load(path, fpnet_module, device="cuda"):
    ck = torch.load(path, map_location="cpu", weights_only=True)
    c = ck["cfg"]; base = fpnet_module.FPNet(c["nbits"], d=c["d"], layers=c["layers"], heads=c["heads"])
    m = N111(fpnet_module, base, d_out=c["d_out"], hid=c["hid"]); m.load_state_dict(ck["state"])
    return m.to(device).eval(), ck
