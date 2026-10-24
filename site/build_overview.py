"""Build site/overview.html -- a panel-style picture of the task: what comes in, what we do with it, what goes out, and where it is hard.
Usage: python -X utf8 site/build_overview.py
"""
import base64, datetime as dt, html, io, os, sys
import numpy as np, polars as pl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SITE = os.path.join(ROOT, "site")
sys.path.insert(0, os.path.join(ROOT, "experiments", "b1_baseline")); sys.path.insert(0, SITE)
from b1_common import clean_peaks, entropy_similarity, ADDUCT_SHIFT  # noqa: E402
from build_site import page  # noqa: E402

for fam in ("Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP", "Hiragino Sans"):
    if any(f.name == fam for f in font_manager.fontManager.ttflist): plt.rcParams["font.family"] = fam; break
plt.rcParams["axes.unicode_minus"] = False
LOSSES = {"−H2O": 18.010565, "−CO": 27.994915, "−CO2": 43.989830, "−H2O−CO": 46.005480, "−2CO": 55.989830, "−CH3": 15.023475, "−NH3": 17.026549, "−C2H2O": 42.010565, "−C3H4O2": 72.021129}


def png(fig, dpi=110):
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight"); plt.close(fig)
    return '<img src="data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode() + '" style="max-width:100%">'


def mol_svg(smiles, size=(220, 170), legend=""):
    from rdkit import Chem
    from rdkit.Chem.Draw import rdMolDraw2D
    m = Chem.MolFromSmiles(smiles); d = rdMolDraw2D.MolDraw2DSVG(*size); d.DrawMolecule(m, legend=legend); d.FinishDrawing()
    return d.GetDrawingText().replace("<?xml version='1.0' encoding='iso-8859-1'?>\n", "")


CSS_EXTRA = """
<style>
.flow{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;align-items:stretch}
.panel{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;position:relative}
.panel .num{display:inline-flex;width:26px;height:26px;border-radius:50%;background:var(--acc);color:#fff;align-items:center;justify-content:center;font-weight:700;margin-right:8px}
.panel h3{display:flex;align-items:center;margin:0 0 8px;font-size:1.02rem}.panel .io{font-size:.85rem;color:var(--muted);margin:6px 0}
.panel .io b{color:var(--ink)}.arrow{text-align:center;font-size:1.6rem;color:var(--muted);align-self:center}
.p1{border-top:4px solid #2563eb}.p2{border-top:4px solid #0b6e4f}.p3{border-top:4px solid #b45309}.p4{border-top:4px solid #7c3aed}
.chips span{display:inline-block;background:#f3f4f6;border-radius:6px;padding:2px 8px;margin:2px;font-size:.85rem}
.issue{border-left:4px solid var(--bad);padding-left:12px}.big{font-size:1.4rem;font-weight:700}
</style>
"""


def main():
    keys = pl.read_parquet(os.path.join(ROOT, "data/processed/train_scorer_keys.parquet"))
    store = os.path.join(ROOT, "data/processed/spectra_store")
    S_MZ = np.load(f"{store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{store}/spec_off.npy")
    smeta = pl.read_parquet(f"{store}/spec_meta.parquet")

    def spec(row):
        s_, e_ = int(S_OFF[row]), int(S_OFF[row + 1]); return np.asarray(S_MZ[s_:e_], float), np.asarray(S_IT[s_:e_], float)

    IK_A, IK_B = "IYRMWMYZSQPJKC", "IQPNAANSBPBGFQ"           # kaempferol, luteolin (C15H10O6)
    smi_a = keys.filter(pl.col("inchikey14") == IK_A)["normalized_smiles"][0]; smi_b = keys.filter(pl.col("inchikey14") == IK_B)["normalized_smiles"][0]
    rows = smeta.filter((pl.col("inchikey14") == IK_A) & (pl.col("ingest_lib") == "massbank") & (pl.col("adduct") == "[M+H]+") & ((pl.col("ce_mean") - 40).abs() < 0.6))
    best = None
    for row, prec in zip(rows["row"].to_list(), rows["precursor_mz"].to_list()):
        c = clean_peaks(*spec(int(row)), float(prec))
        if best is None or len(c[0]) > len(best[2][0]): best = (int(row), float(prec), c)
    row, prec, (cmz, cit) = best
    # ---- panel 1 figure: the raw spectrum with the precursor and a few annotated neutral losses
    fig, ax = plt.subplots(figsize=(4.2, 2.6)); mz, it = spec(row); it = it / it.max()
    ax.vlines(mz, 0, it, color="#2563eb", lw=1.0); ax.axvline(prec, color="#999", ls="--", lw=0.8); ax.text(prec, 1.02, f"プリカーサ\n{prec:.3f}", ha="center", fontsize=7, color="#555")
    top = np.argsort(-it)[:12]; labelled = 0
    for i in top:
        d = prec - mz[i]
        for name, mass in LOSSES.items():
            if abs(d - mass) < 0.004 and labelled < 4:
                ax.annotate(f"{name}\n{mz[i]:.3f}", (mz[i], it[i]), xytext=(mz[i] - 25, min(it[i] + 0.25, 0.95)), fontsize=7, color="#b45309", arrowprops=dict(arrowstyle="->", color="#b45309", lw=0.7)); labelled += 1
    ax.set_xlim(40, prec + 15); ax.set_ylim(0, 1.15); ax.set_xlabel("m/z", fontsize=8); ax.set_ylabel("相対強度", fontsize=8); ax.tick_params(labelsize=7)
    ax.set_title("MS/MS スペクトル(ケンフェロール [M+H]+ 40 eV)", fontsize=8); fig.tight_layout(); fig_in = png(fig, 120)
    # ---- panel 2 figure: candidate funnel
    fig, ax = plt.subplots(figsize=(4.2, 2.4))
    st = [("PubChem", 105_875_489), ("質量窓 ±10 ppm", 10_184), ("同じ分子式", 2_638), ("shortlist", 115), ("提出 25", 25)]
    ax.barh([s[0] for s in st][::-1], [s[1] for s in st][::-1], color=["#e5e7eb", "#2563eb", "#0b6e4f", "#b45309", "#6b7280"][::-1]); ax.set_xscale("log")
    for i, (n_, v) in enumerate(st[::-1]): ax.text(v * 1.2, i, f"{v:,}", va="center", fontsize=7)
    ax.set_xlim(5, 1e10); ax.tick_params(labelsize=7); ax.set_title("1 分子あたりの候補数(中央値)", fontsize=8); fig.tight_layout(); fig_funnel = png(fig, 120)
    # ---- panel 3 figure: three kinds of evidence (schematic)
    fig, axes = plt.subplots(1, 3, figsize=(7.5, 2.2))
    rng = np.random.default_rng(1)
    bits_pred = rng.random(40); bits_true = (bits_pred + rng.normal(0, 0.25, 40) > 0.5).astype(float); bits_dec = (rng.random(40) > 0.5).astype(float)
    axes[0].imshow(np.vstack([bits_pred, bits_true, bits_dec]), aspect="auto", cmap="Greens", vmin=0, vmax=1); axes[0].set_yticks([0, 1, 2]); axes[0].set_yticklabels(["予測指紋", "正解の指紋", "別候補の指紋"], fontsize=7); axes[0].set_xticks([])
    axes[0].set_title("① 指紋予測(FPNet)\nスペクトル→指紋ビットを予測し候補と照合", fontsize=7.5)
    xs = np.linspace(50, 280, 30); axes[1].vlines(xs, 0, rng.random(30), color="#0b6e4f", lw=1, label="実測"); axes[1].vlines(xs + 2, 0, rng.random(30) * 0.9, color="#b45309", lw=1, label="候補から予測")
    axes[1].set_xticks([]); axes[1].set_yticks([]); axes[1].legend(fontsize=6, loc="upper right"); axes[1].set_title("② 順方向モデル(GLACIER/ICEBERG)\n候補構造→スペクトルを予測し実測と比較", fontsize=7.5)
    axes[2].vlines(xs, 0, rng.random(30), color="#2563eb", lw=1, label="実測"); axes[2].vlines(xs + 2, 0, rng.random(30), color="#6b7280", lw=1, label="ライブラリの既知スペクトル")
    axes[2].set_xticks([]); axes[2].set_yticks([]); axes[2].legend(fontsize=6, loc="upper right"); axes[2].set_title("③ ライブラリ検索 + 文献 prior\n既知スペクトルとの類似度、文献数", fontsize=7.5)
    fig.tight_layout(); fig_ev = png(fig, 120)
    # similarities for the difficulty section
    rows_b = smeta.filter((pl.col("inchikey14") == IK_B) & (pl.col("ingest_lib") == "massbank") & (pl.col("adduct") == "[M+H]+") & ((pl.col("ce_mean") - 40).abs() < 0.6))
    bb = None
    for r2, p2 in zip(rows_b["row"].to_list(), rows_b["precursor_mz"].to_list()):
        c = clean_peaks(*spec(int(r2)), float(p2))
        if bb is None or len(c[0]) > len(bb[0]): bb = c
    rows_a50 = smeta.filter((pl.col("inchikey14") == IK_A) & (pl.col("ingest_lib") == "massbank") & (pl.col("adduct") == "[M+H]+") & ((pl.col("ce_mean") - 50).abs() < 0.6))
    a50 = None
    for r2, p2 in zip(rows_a50["row"].to_list(), rows_a50["precursor_mz"].to_list()):
        c = clean_peaks(*spec(int(r2)), float(p2))
        if a50 is None or len(c[0]) > len(a50[0]): a50 = c
    sim_iso = entropy_similarity(*best[2], *bb) if bb else float("nan"); sim_same = entropy_similarity(*best[2], *a50) if a50 else float("nan")
    M = prec + ADDUCT_SHIFT["[M+H]+"]

    body = CSS_EXTRA + f"""
<article>
<h1>スペクトル → 候補 → 順位付け → 構造:この課題の全体像</h1>
<p>1 つの未知分子について測った質量スペクトルから、その分子の構造を当てます。下の 4 段が「何が入って、何をして、何を出すか」です。</p>
<div class="flow">
 <div class="panel p1"><h3><span class="num">1</span>入力:スペクトル</h3>{fig_in}
  <div class="io"><b>データ</b>: 破片の (m/z, 強度) の並び、1 分子につき 1〜16 本(CE や アダクトが違う)</div>
  <div class="chips"><span>プリカーサ m/z {prec:.3f}</span><span>アダクト [M+H]+</span><span>極性 +</span><span>CE 40 eV</span><span>装置 QTOF</span></div>
  <div class="io">ピークは分子が壊れてできた断片。プリカーサとの差から「水 1 個が取れた(−H2O)」などの<b>中性脱離</b>が読める(図の注釈)。ただし答えの構造そのものは書かれていない。</div></div>
 <div class="panel p2"><h3><span class="num">2</span>候補を集める</h3>{fig_funnel}
  <div class="io"><b>処理</b>: プリカーサ m/z とアダクトから分子の質量を計算(287.055 − 1.007 = <b>{M:.3f}</b>)。質量が ±10 ppm で一致する構造を PubChem(1 億)と学習構造+COCONUT(71 万)から集める。</div>
  <div class="io"><b>出力</b>: 候補構造が約 1 万個。うち同じ分子式が数千。正解がこの中に無ければ(Class 3)この先は 0 点。</div></div>
 <div class="panel p3"><h3><span class="num">3</span>証拠で順位付け</h3>{fig_ev}
  <div class="io"><b>処理</b>: 3 種類の証拠で候補を採点し、まず指紋で上位 100 に絞り(shortlist)、重い順方向モデルは shortlist だけに使う。最後に z 標準化した和(または学習した順位付けモデル)で並べる。</div>
  <div class="io"><b>出力</b>: 候補ごとの総合スコア。</div></div>
 <div class="panel p4"><h3><span class="num">4</span>出力:構造 25 件</h3>
  <div class="grid" style="grid-template-columns:1fr 1fr;gap:6px">{mol_svg(smi_a, (190, 150), "1 位(正解)")}{mol_svg(smi_b, (190, 150), "2 位(異性体)")}</div>
  <div class="io"><b>提出</b>: 分子ごとに SMILES を 25 件まで「;」区切りで並べる。<b>採点</b>: 正解の順位 r で 1/r(25 位以内)。全分子の平均 = MRR@25。同一性は立体を除きタウトマーを正規化した InChIKey 先頭 14 文字。</div>
  <div class="io">例: 1 位なら 1.0、2 位なら 0.5、圏外なら 0。</div></div>
</div>
</article>

<article>
<h1>どこが難しいのか(数で見る)</h1>
<div class="grid">
 <div class="card issue"><h2>① 候補の中に答えが無い(Class 3)</h2><p class="big">推定 30〜70%</p><p>隠しテストの一部は PubChem にも COCONUT にも無い新規構造。検索では原理的に 0 点で、構造を<b>生成</b>する別の技術が要る。公開解法でも誰も得点できていない。比率が非公開なので、到達できる上限が分からない。</p></div>
 <div class="card issue"><h2>② 同じ組成の異性体を見分ける(Class 2)</h2><p class="big">同分子式 2,638 個(中央値)</p><p>質量は完全に同じなので、壊れ方の違いだけが頼り。しかもスペクトルは同じ分子でも CE で変わる。実測の例: ケンフェロール 40 eV と 50 eV の類似度 <b>{sim_same:.2f}</b>、ケンフェロール 40 eV と異性体ルテオリン 40 eV の類似度 <b>{sim_iso:.2f}</b>(異性体の方が似て見える)。指紋モデルは分子式までは決められるが(上位 25 の 24 件が同じ分子式)、異性体識別は順方向モデルとの組合せで 0.47 → 0.72(timsTOF 300 分子の MRR)。</p></div>
 <div class="card issue"><h2>③ 装置とデータの分布が違う(Class 1 でも)</h2><p class="big">timsTOF vs Orbitrap/QTOF</p><p>隠しテストは Bruker timsTOF の天然物。学習ライブラリの天然物スペクトルは Orbitrap や QTOF で測られ、同じ分子でも破片の強度が変わる。さらに公開ライブラリには同じスペクトルの再登録(複製)が多く、検証で「できたつもり」になりやすい(新評価集合 B の 160 分子で複製参照 101 件を検出・除外)。</p></div>
 <div class="card issue"><h2>④ 計算予算</h2><p class="big">9 時間 / 400 分子 / 4 CPU + T4</p><p>1 億構造からの候補取得、1 万候補の指紋照合、順方向モデルの予測(1 候補あたり数十ミリ秒)を Kaggle の制約内で終える必要がある。精度と時間の配分が設計の一部。</p></div>
</div>
<p class="small muted">用語: <b>m/z</b> = 質量/電荷(1 価イオンではほぼ質量)。<b>プリカーサ</b> = 壊す前のイオン。<b>アダクト</b> = イオン化で付いたもの([M+H]+ はプロトン、[M+Na]+ はナトリウム、[M-H]- は負モード)。<b>CE</b> = 衝突エネルギー(壊す強さ)。<b>SMILES</b> = 構造を文字列で表した形式。<b>指紋</b> = 構造の部分構造の有無を並べたビット列。</p>
<p class="small muted">より詳しい分布やライブラリの内訳は <a href="eda.html">データと課題</a>、手法と結果は <a href="b1.html">B1 設計</a>・<a href="experiments.html">実験</a>。</p>
</article>"""
    open(os.path.join(SITE, "overview.html"), "w", encoding="utf-8").write(page("課題の全体像", body, "overview.html"))
    print("overview built", dt.datetime.now().strftime("%H:%M:%S"), f"| sim same {sim_same:.3f} iso {sim_iso:.3f} | M {M:.4f}")


if __name__ == "__main__":
    main()
