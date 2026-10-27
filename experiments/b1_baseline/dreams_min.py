# Copied unchanged (below this header) from dreams_minimal_model.py of the Kaggle dataset hengck23/hengck23-dreams-enveda-casmi26
# (MIT licence per the dataset card; DreaMS: Bushuiev et al., Nat. Biotechnol. 2025, github.com/pluskal-lab/DreaMS, MIT).
# Inference-only DreaMS embedding model (torch + numpy). ONE modification (marked '(modified)'): the parameter-free graphormer
# attention bias sum_k (f_ik - f_jk) is computed as s_i - s_j from row sums (exact identity; avoids a [B,N,N,980] tensor); weights = embedding_model_state_dict.pt of the same dataset, loaded with weights_only=True.

"""
Minimal DreaMS embedding inference.

External dependencies:
    torch
    numpy

This file extracts only the inference path of the released DreaMS embedding
model. It does NOT depend on:
    pytorch_lightning
    pandas
    h5py
    matchms
    rdkit
    dreams

The architecture and preprocessing below are taken from the released DreaMS
repository/model configuration:

    n_layers = 7
    n_heads = 8
    d_peak = 44
    d_fourier = 980
    d_model = 1024
    ff_peak_depth = 1
    ff_fourier_depth = 5
    ff_fourier_d = 512
    Fourier strategy = lin_float_int
    pre_norm = True
    graphormer_mz_diffs = True
    graphormer_parametrized = False
    transformer bias = False
    max_mz = 1000
    n_highest_peaks = 100
    precursor intensity = 1.1

The input for one spectrum is:
    mzs:         shape [N]
    intensities: shape [N]
    precursor_mz: scalar

The returned DreaMS embedding has shape [1024].

Checkpoint loading
------------------
The easiest robust route is to save the Lightning checkpoint's "state_dict"
once as a plain PyTorch file:

    ckpt = torch.load("embedding_model.ckpt", map_location="cpu",
                      weights_only=False)
    torch.save(ckpt["state_dict"], "embedding_model_state_dict.pt")

Then this standalone file only needs torch + numpy:

    model = load_model("embedding_model_state_dict.pt")
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Mapping

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F


# =============================================================================
# Released DreaMS embedding model configuration
# =============================================================================

N_LAYERS = 7
N_HEADS = 8

D_PEAK = 44
D_FOURIER = 980
D_MODEL = D_PEAK + D_FOURIER

FF_FOURIER_D = 512
FF_FOURIER_DEPTH = 5

ATT_DROPOUT = 0.1
RESIDUAL_DROPOUT = 0.1
FF_DROPOUT = 0.1

MAX_MZ = 1000.0
FOURIER_X_MIN = 1e-4
FOURIER_X_MAX = 1000.0

N_HIGHEST_PEAKS = 100
PRECURSOR_INTENSITY = 1.1


# =============================================================================
# Small building blocks
# =============================================================================

class DenseFeedForward(nn.Module):
    """
    DreaMS input feed-forward block.

    Matches dreams.models.layers.feed_forward.FeedForward.
    """

    def __init__(
        self,
        in_dim: int,
        out_dim: int,
        hidden_dim: int,
        depth: int,
        dropout: float = 0.0,
        bias: bool = True,
    ):
        super().__init__()

        layers = []

        for i in range(depth):
            d1 = in_dim if i == 0 else hidden_dim
            d2 = out_dim if i == depth - 1 else hidden_dim

            layers.append(nn.Linear(d1, d2, bias=bias))

            if i != depth - 1:
                layers.append(nn.Dropout(dropout))

            # Original DreaMS FeedForward uses act_last=True by default.
            layers.append(nn.ReLU())

        self.ff = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.ff(x)


class FourierFeatures(nn.Module):
    """
    DreaMS Fourier feature encoder with strategy='lin_float_int'.
    """

    def __init__(self):
        super().__init__()

        # Exact construction from DreaMS:
        #
        # [1 / (x_min * i) for i in range(2, ceil(1/x_min), 2)]
        # +
        # [1 / i for i in range(2, ceil(x_max), 1)]
        b = (
            [
                1.0 / (FOURIER_X_MIN * i)
                for i in range(2, math.ceil(1.0 / FOURIER_X_MIN), 2)
            ]
            +
            [
                1.0 / i
                for i in range(2, math.ceil(FOURIER_X_MAX))
            ]
        )

        b = torch.tensor(b, dtype=torch.float32).unsqueeze(0)

        # In the released model --fourier_trainable was not set, therefore
        # this tensor is normally non-trainable. We still register it as a
        # Parameter so state_dict names/shapes match DreaMS.
        self.b = nn.Parameter(b, requires_grad=False)

    @property
    def num_features(self) -> int:
        return 2 * self.b.shape[1]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = 2.0 * torch.pi * (x @ self.b)
        return torch.cat((torch.cos(x), torch.sin(x)), dim=-1)


class MultiheadAttention(nn.Module):
    """
    Exact inference-relevant DreaMS custom multi-head attention.

    The released model uses:
        attention mechanism = dot-product
        transformer bias = False
        graphormer_parametrized = False
    """

    def __init__(self):
        super().__init__()

        self.d_model = D_MODEL
        self.n_heads = N_HEADS
        self.dropout = ATT_DROPOUT

        if self.d_model % self.n_heads != 0:
            raise ValueError("D_MODEL must be divisible by N_HEADS")

        self.head_dim = self.d_model // self.n_heads
        self.scale = self.head_dim ** -0.5

        # Original DreaMS packs Q, K, V, output matrices into one parameter.
        self.weights = nn.Parameter(
            torch.empty(4 * self.d_model, self.d_model)
        )

    def _proj(
        self,
        x: torch.Tensor,
        start: int = 0,
        end: int | None = None,
    ) -> torch.Tensor:
        return F.linear(
            x,
            weight=self.weights[start:end],
            bias=None,
        )

    def proj_qkv(
        self,
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
    ):
        # Self-attention is the only inference path needed here.
        qkv = self._proj(
            q,
            end=3 * self.d_model,
        )
        return qkv.chunk(3, dim=-1)

    def proj_o(self, x: torch.Tensor) -> torch.Tensor:
        return self._proj(
            x,
            start=3 * self.d_model,
        )

    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor | None,
        graphormer_dists: torch.Tensor | None,
    ) -> torch.Tensor:
        bs, n, _ = x.shape

        q, k, v = self.proj_qkv(x, x, x)

        q = q.reshape(
            bs,
            n,
            self.n_heads,
            self.head_dim,
        ).transpose(1, 2)

        k = k.reshape(
            bs,
            n,
            self.n_heads,
            self.head_dim,
        ).transpose(1, 2)

        v = v.reshape(
            bs,
            n,
            self.n_heads,
            self.head_dim,
        ).transpose(1, 2)

        att_weights = torch.einsum(
            "bhnd,bhdm->bhnm",
            q,
            k.transpose(-2, -1),
        )

        att_weights = att_weights * self.scale

        if graphormer_dists is not None:
            # Released model has graphormer_parametrized=False:
            # sum feature differences, then broadcast over heads.
            # (modified, exact identity) graphormer_dists holds s_i = sum_k f_ik, [B, N]; the original summed
            # f_ik - f_jk over k, i.e. s_i - s_j, from a materialised [B, N, N, 980] tensor
            att_bias = (graphormer_dists.unsqueeze(2) - graphormer_dists.unsqueeze(1)).unsqueeze(1)
            att_weights = att_weights + att_bias

        if mask is not None:
            # Preserve the exact masking orientation used by DreaMS.
            att_weights.masked_fill_(
                mask.unsqueeze(1).unsqueeze(-1),
                -1e9,
            )

        att_weights = F.softmax(
            att_weights,
            dim=-1,
        )

        att_weights = F.dropout(
            att_weights,
            p=self.dropout,
            training=self.training,
        )

        att_flat = att_weights.reshape(
            bs * self.n_heads,
            n,
            n,
        )

        v_flat = v.reshape(
            bs * self.n_heads,
            n,
            self.head_dim,
        )

        out = torch.bmm(
            att_flat,
            v_flat,
        )

        out = (
            out
            .reshape(
                bs,
                self.n_heads,
                n,
                self.head_dim,
            )
            .transpose(1, 2)
            .reshape(
                bs,
                n,
                self.d_model,
            )
        )

        return self.proj_o(out)


class TransformerFeedForward(nn.Module):
    """
    DreaMS Transformer FFN.
    """

    def __init__(self):
        super().__init__()

        ff_dim = 4 * D_MODEL

        self.in_proj = nn.Linear(
            D_MODEL,
            ff_dim,
            bias=False,
        )

        self.out_proj = nn.Linear(
            ff_dim,
            D_MODEL,
            bias=False,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.in_proj(x))

        x = F.dropout(
            x,
            p=FF_DROPOUT,
            training=self.training,
        )

        return self.out_proj(x)


class TransformerEncoder(nn.Module):
    """
    Seven-layer pre-norm DreaMS Transformer encoder.
    """

    def __init__(self):
        super().__init__()

        self.atts = nn.ModuleList(
            [
                MultiheadAttention()
                for _ in range(N_LAYERS)
            ]
        )

        self.ffs = nn.ModuleList(
            [
                TransformerFeedForward()
                for _ in range(N_LAYERS)
            ]
        )

        # pre_norm=True -> 2*n_layers + 1 normalization modules.
        self.scales = nn.ModuleList(
            [
                nn.LayerNorm(D_MODEL)
                for _ in range(2 * N_LAYERS + 1)
            ]
        )

    def _layer_forward(
        self,
        i: int,
        x: torch.Tensor,
        src_mask: torch.Tensor | None,
        graphormer_dists: torch.Tensor | None,
    ) -> torch.Tensor:

        att = self.atts[i]
        ff = self.ffs[i]

        att_norm = self.scales[2 * i]
        ff_norm = self.scales[2 * i + 1]

        residual = x
        x = att_norm(x)

        x = att(
            x=x,
            mask=src_mask,
            graphormer_dists=graphormer_dists,
        )

        x = residual + F.dropout(
            x,
            p=RESIDUAL_DROPOUT,
            training=self.training,
        )

        residual = x
        x = ff_norm(x)
        x = ff(x)

        x = residual + F.dropout(
            x,
            p=RESIDUAL_DROPOUT,
            training=self.training,
        )

        return x

    def forward(
        self,
        x: torch.Tensor,
        src_mask: torch.Tensor | None,
        graphormer_dists: torch.Tensor | None = None,
    ) -> torch.Tensor:

        x = F.dropout(
            x,
            p=RESIDUAL_DROPOUT,
            training=self.training,
        )

        for i in range(N_LAYERS):
            x = self._layer_forward(
                i,
                x,
                src_mask,
                graphormer_dists,
            )

        return self.scales[-1](x)


# =============================================================================
# DreaMS backbone + embedding head
# =============================================================================

class DreaMSBackbone(nn.Module):

    def __init__(self):
        super().__init__()

        # Input token is [m/z, intensity].
        self.ff_peak = DenseFeedForward(
            in_dim=2,
            out_dim=D_PEAK,
            hidden_dim=D_PEAK,
            depth=1,
            dropout=0.1,
            bias=True,
        )

        self.fourier_enc = FourierFeatures()

        self.ff_fourier = DenseFeedForward(
            in_dim=self.fourier_enc.num_features,
            out_dim=D_FOURIER,
            hidden_dim=FF_FOURIER_D,
            depth=FF_FOURIER_DEPTH,
            dropout=0.1,
            bias=True,
        )

        self.transformer_encoder = TransformerEncoder()

    def forward(
        self,
        spec: torch.Tensor,
    ) -> torch.Tensor:
        """
        Parameters
        ----------
        spec:
            [B, N, 2], where the last dimension is [m/z, intensity].

            m/z is raw m/z, not pre-normalized.
            intensity is expected to already be relative to the base peak.

        Returns
        -------
        Tensor [B, N, 1024]
        """
        padding_mask = spec[:, :, 0] == 0

        norm = spec.new_tensor(
            [MAX_MZ, 1.0]
        )

        peak_embs = self.ff_peak(
            spec / norm
        )

        fourier_features = self.ff_fourier(
            self.fourier_enc(
                spec[..., [0]]
            )
        )

        x = torch.cat(
            [
                peak_embs,
                fourier_features,
            ],
            dim=-1,
        )

        graphormer_dists = fourier_features.sum(dim=-1)   # (modified) [B, N] row sums, see MultiheadAttention.forward

        return self.transformer_encoder(
            x,
            padding_mask,
            graphormer_dists,
        )


class DreaMSEmbeddingModel(nn.Module):
    """
    ContrastiveHead inference path:

        backbone(spec)
        -> precursor token [:, 0]
        -> Linear(1024, 1024)
    """

    def __init__(self):
        super().__init__()

        self.backbone = DreaMSBackbone()

        self.head = nn.Linear(
            D_MODEL,
            D_MODEL,
            bias=True,
        )

    def forward(
        self,
        spec: torch.Tensor,
    ) -> torch.Tensor:

        x = self.backbone(spec)

        # DreaMS uses the prepended precursor token as the spectrum token.
        x = x[:, 0, :]

        return self.head(x)


# =============================================================================
# Spectrum preprocessing
# =============================================================================

def preprocess_spectrum(
    mzs: np.ndarray,
    intensities: np.ndarray,
    precursor_mz: float,
    n_highest_peaks: int = N_HIGHEST_PEAKS,
    precursor_intensity: float = PRECURSOR_INTENSITY,
) -> np.ndarray:
    """
    Minimal NumPy implementation of the inference preprocessing used by
    DreaMS SpectrumPreprocessor(DataFormatA(), n_highest_peaks=100).

    Steps:
      1. keep the 100 highest-intensity fragment peaks;
      2. preserve their original ordering;
      3. zero-pad fragments to 100 entries;
      4. normalize fragment intensities by the base peak;
      5. prepend [precursor_mz, 1.1].

    Returns
    -------
    float32 array of shape [101, 2].
    """
    mzs = np.asarray(
        mzs,
        dtype=np.float32,
    ).reshape(-1)

    intensities = np.asarray(
        intensities,
        dtype=np.float32,
    ).reshape(-1)

    if len(mzs) != len(intensities):
        raise ValueError(
            "mzs and intensities must have equal length"
        )

    if len(mzs) == 0:
        raise ValueError(
            "Spectrum contains no fragment peaks"
        )

    # Equivalent to DreaMS trim_peak_list():
    # choose highest intensities, then restore original order.
    if len(mzs) > n_highest_peaks:
        idx = np.argsort(
            intensities,
        )[-n_highest_peaks:]

        idx = np.sort(idx)

        mzs = mzs[idx]
        intensities = intensities[idx]

    # Normalize by base peak before adding the precursor token.
    max_intensity = float(
        intensities.max()
    )

    if max_intensity <= 0:
        raise ValueError(
            "Maximum fragment intensity must be > 0"
        )

    intensities = (
        intensities
        /
        max_intensity
    )

    n = len(mzs)

    fragments = np.zeros(
        (n_highest_peaks, 2),
        dtype=np.float32,
    )

    fragments[:n, 0] = mzs
    fragments[:n, 1] = intensities

    precursor = np.array(
        [
            [
                float(precursor_mz),
                float(precursor_intensity),
            ]
        ],
        dtype=np.float32,
    )

    return np.concatenate(
        [
            precursor,
            fragments,
        ],
        axis=0,
    )


def preprocess_batch(
    spectra: list[
        tuple[np.ndarray, np.ndarray, float]
    ],
) -> np.ndarray:
    """
    Convenience function.

    Each item is:
        (mzs, intensities, precursor_mz)

    Returns
    -------
    [B, 101, 2] float32 NumPy array.
    """
    return np.stack(
        [
            preprocess_spectrum(
                mzs,
                intensities,
                precursor_mz,
            )
            for mzs, intensities, precursor_mz in spectra
        ],
        axis=0,
    )


# =============================================================================
# State-dict loading
# =============================================================================

def _unwrap_state_dict(
    obj,
) -> Mapping[str, torch.Tensor]:
    """
    Accept either:
      - a plain state_dict
      - a Lightning checkpoint dictionary containing "state_dict"
    """
    if (
        isinstance(obj, dict)
        and
        "state_dict" in obj
    ):
        obj = obj["state_dict"]

    if not isinstance(obj, Mapping):
        raise TypeError(
            "Checkpoint does not contain a state_dict mapping"
        )

    return obj


def _clean_state_dict(
    state_dict: Mapping[str, torch.Tensor],
) -> dict[str, torch.Tensor]:
    """
    Keep only the embedding model inference weights.

    Released ContrastiveHead keys are expected to look like:
        backbone.ff_peak....
        backbone.fourier_enc.b
        backbone.ff_fourier....
        backbone.transformer_encoder....
        head.weight
        head.bias
    """
    out = {}

    allowed_prefixes = (
        "backbone.ff_peak.",
        "backbone.fourier_enc.",
        "backbone.ff_fourier.",
        "backbone.transformer_encoder.",
        "head.",
    )

    for key, value in state_dict.items():

        # Common optional wrappers.
        for prefix in (
            "model.",
            "module.",
        ):
            if key.startswith(prefix):
                key = key[len(prefix):]

        if key.startswith(
            allowed_prefixes
        ):
            out[key] = value

    return out


def load_model(
    state_dict_path: str | Path,
    device: str | torch.device = "cuda",
) -> DreaMSEmbeddingModel:
    """
    Load a plain state_dict file.

    Recommended:
        torch.save(
            ckpt["state_dict"],
            "embedding_model_state_dict.pt",
        )

    Then:
        model = load_model(
            "embedding_model_state_dict.pt"
        )
    """
    device = torch.device(device)

    obj = torch.load(
        state_dict_path,
        map_location="cpu",
        weights_only=True,
    )

    state_dict = _clean_state_dict(
        _unwrap_state_dict(obj)
    )

    model = DreaMSEmbeddingModel()

    missing, unexpected = model.load_state_dict(
        state_dict,
        strict=False,
    )

    # Fourier b is deterministic, but normally is also present in the
    # checkpoint. Everything else should match.
    important_missing = [
        k
        for k in missing
        if k != "backbone.fourier_enc.b"
    ]

    if important_missing:
        raise RuntimeError(
            "Missing model parameters:\n"
            +
            "\n".join(important_missing)
        )

    if unexpected:
        print(
            "Ignored unexpected checkpoint keys:",
            unexpected,
        )

    model = model.to(device)
    model.eval()

    return model


# =============================================================================
# Inference
# =============================================================================

@torch.inference_mode()
def embed_preprocessed(
    model: DreaMSEmbeddingModel,
    spec: np.ndarray | torch.Tensor,
) -> np.ndarray:
    """
    spec:
        [101, 2] or [B, 101, 2]

    returns:
        [1024] or [B, 1024]
    """
    single = False

    if isinstance(spec, np.ndarray):
        x = torch.from_numpy(
            spec.astype(
                np.float32,
                copy=False,
            )
        )
    else:
        x = spec

    if x.ndim == 2:
        x = x.unsqueeze(0)
        single = True

    if x.ndim != 3:
        raise ValueError(
            "Expected [N,2] or [B,N,2]"
        )

    device = next(
        model.parameters()
    ).device

    x = x.to(
        device=device,
        dtype=torch.float32,
    )

    emb = model(x)

    emb = (
        emb
        .detach()
        .cpu()
        .numpy()
    )

    return emb[0] if single else emb


@torch.inference_mode()
def embed_spectrum(
    model: DreaMSEmbeddingModel,
    mzs: np.ndarray,
    intensities: np.ndarray,
    precursor_mz: float,
) -> np.ndarray:
    """
    End-to-end embedding for one raw spectrum.
    """
    spec = preprocess_spectrum(
        mzs,
        intensities,
        precursor_mz,
    )

    return embed_preprocessed(
        model,
        spec,
    )


# =============================================================================
# Optional one-time checkpoint extraction
# =============================================================================

def extract_lightning_state_dict(
    lightning_ckpt: str | Path,
    output_path: str | Path,
):
    """
    One-time helper.

    Run this in an environment where the original DreaMS checkpoint can be
    deserialized. The output is a plain tensor state_dict that thereafter
    requires only torch + numpy.

    Example:
        extract_lightning_state_dict(
            "embedding_model.ckpt",
            "embedding_model_state_dict.pt",
        )

    NOTE:
    Old Lightning checkpoints can contain pickled Python objects in their
    hyperparameters. Therefore torch.load(..., weights_only=False) may require
    the DreaMS package to be importable for THIS ONE-TIME conversion.

    Only use weights_only=False for the trusted official DreaMS checkpoint.
    """
    ckpt = torch.load(
        lightning_ckpt,
        map_location="cpu",
        weights_only=False,
    )

    state_dict = _clean_state_dict(
        _unwrap_state_dict(ckpt)
    )

    torch.save(
        state_dict,
        output_path,
    )

    print(
        "saved:",
        output_path,
    )
