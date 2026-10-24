"""Build site/eda.html -- what the data looks like and what the task is, for a reader new to mass-spectrometry competitions.

Figures are rendered with matplotlib (PNG, base64-embedded) and RDKit (SVG); statistics come from data/processed/train_meta.parquet,
data/raw/test.parquet and the spectra store. Pure static HTML, no external assets.
Usage: python -X utf8 site/build_eda.py
"""
import base64, datetime as dt, html, io, json, os, sys
import numpy as np, polars as pl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SITE = os.path.join(ROOT, "site")
sys.path.insert(0, os.path.join(ROOT, "experiments", "b1_baseline"))
from b1_common import clean_peaks, entropy_similarity  # noqa: E402
sys.path.insert(0, SITE)
from build_site import page  # noqa: E402

# Japanese font for matplotlib (Windows: Yu Gothic / Meiryo; fall back silently)
for fam in ("Yu Gothic", "Meiryo", "MS Gothic", "Noto Sans CJK JP", "Hiragino Sans"):
    if any(f.name == fam for f in font_manager.fontManager.ttflist): plt.rcParams["font.family"] = fam; break
plt.rcParams["axes.unicode_minus"] = False


def png(fig):
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=110, bbox_inches="tight"); plt.close(fig)
    return '<img src="data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode() + '" style="max-width:100%">'


def mol_svg(smiles, size=(260, 200), legend=""):
    from rdkit import Chem
    from rdkit.Chem.Draw import rdMolDraw2D
    m = Chem.MolFromSmiles(smiles); d = rdMolDraw2D.MolDraw2DSVG(*size); d.DrawMolecule(m, legend=legend); d.FinishDrawing()
    return d.GetDrawingText().replace("<?xml version='1.0' encoding='iso-8859-1'?>\n", "")


def fmt(n): return f"{n:,}"


def main():
    meta = pl.read_parquet(os.path.join(ROOT, "data/processed/train_meta.parquet"))
    keys = pl.read_parquet(os.path.join(ROOT, "data/processed/train_scorer_keys.parquet"))
    test = pl.read_parquet(os.path.join(ROOT, "data/raw/test.parquet"), columns=["molecule_id", "adduct", "ionization_mode", "precursor_mz", "ms2_mzs"])
    store = os.path.join(ROOT, "data/processed/spectra_store")
    S_MZ = np.load(f"{store}/spec_mz.npy", mmap_mode="r"); S_IT = np.load(f"{store}/spec_int.npy", mmap_mode="r"); S_OFF = np.load(f"{store}/spec_off.npy")
    smeta = pl.read_parquet(f"{store}/spec_meta.parquet")
    n_spec, n_mol, n_lib = meta.height, meta["inchikey14"].n_unique(), meta["ingest_lib"].n_unique()
    n_official = keys["scorer_ik14"].n_unique()
    parts = []

    # ------------------------------------------------------------------ 1. the task in one picture: quercetin
    smi_q = keys.filter(pl.col("inchikey14") == "REFJWTPEDVJJIY")["normalized_smiles"][0]
    smi_m = keys.filter(pl.col("inchikey14") == "YXOLAZRVSSWPPT")["normalized_smiles"][0]

    def spectra_of(ik, lib="riken", adduct="[M+H]+", inst="QTOF"):
        rows = smeta.filter((pl.col("inchikey14") == ik) & (pl.col("ingest_lib") == lib) & (pl.col("adduct") == adduct) & (pl.col("instrument_type") == inst)).sort("ce_mean")
        return rows

    def spec(row):
        s, e = int(S_OFF[row]), int(S_OFF[row + 1]); return np.asarray(S_MZ[s:e], float), np.asarray(S_IT[s:e], float)

    rows_q = spectra_of("REFJWTPEDVJJIY"); rows_m = spectra_of("YXOLAZRVSSWPPT")
    pick = {}
    for ce in (10.0, 20.0, 40.0):
        rq = rows_q.filter((pl.col("ce_mean") - ce).abs() < 0.6); rm = rows_m.filter((pl.col("ce_mean") - ce).abs() < 0.6)
        if rq.height and rm.height: pick[ce] = (int(rq["row"][0]), float(rq["precursor_mz"][0]), int(rm["row"][0]), float(rm["precursor_mz"][0]))
    fig, axes = plt.subplots(len(pick), 2, figsize=(11, 2.6 * len(pick)), sharex=True)
    axes = np.atleast_2d(axes)
    for i, (ce, (rq, pq, rm, pm)) in enumerate(pick.items()):
        for j, (row, prec, name) in enumerate(((rq, pq, "ケルセチン"), (rm, pm, "モリン"))):
            mz, it = spec(row); ax = axes[i, j]
            ax.vlines(mz, 0, it / it.max(), color="#0b6e4f" if j == 0 else "#b45309", lw=1.2)
            ax.axvline(prec, color="#999", ls="--", lw=0.8); ax.set_ylim(0, 1.08); ax.set_xlim(40, 330)
            ax.set_title(f"{name}  [M+H]+  衝突エネルギー {ce:g} eV(QTOF、riken)", fontsize=10); ax.set_ylabel("相対強度")
    axes[-1, 0].set_xlabel("m/z(質量/電荷)"); axes[-1, 1].set_xlabel("m/z")
    fig.tight_layout(); fig_iso = png(fig)
    # similarities: same molecule across CE vs isomers at the same CE
    sims = {}
    if 20.0 in pick and 40.0 in pick:
        q20 = clean_peaks(*spec(pick[20.0][0]), pick[20.0][1]); q40 = clean_peaks(*spec(pick[40.0][0]), pick[40.0][1]); m40 = clean_peaks(*spec(pick[40.0][2]), pick[40.0][3]); m20 = clean_peaks(*spec(pick[20.0][2]), pick[20.0][3])
        sims = {"ケルセチン 20 eV vs ケルセチン 40 eV(同じ分子、CE 違い)": entropy_similarity(*q20, *q40), "ケルセチン 40 eV vs モリン 40 eV(異性体、同じ CE)": entropy_similarity(*q40, *m40),
                "ケルセチン 20 eV vs モリン 20 eV(異性体、同じ CE)": entropy_similarity(*q20, *m20)}
    sim_rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{v:.3f}</td></tr>" for k, v in sims.items())
    parts.append(f"""
<article><h1>1. この課題は何をするのか</h1>
<p><b>入力</b>は 1 つの未知分子について測った 1〜16 本のタンデム質量スペクトル(MS/MS)です。各スペクトルは「分子をイオン化して壊したときに出る破片(フラグメント)の質量/電荷 m/z と相対強度の並び」で、
あわせて壊す前のイオンの m/z(プリカーサ)、イオン化の形(アダクト、例 [M+H]+ はプロトンが付いた形)、正負の極性、壊す強さ(衝突エネルギー、CE)が付きます。<br>
<b>出力</b>はその分子の 2 次元構造(SMILES)を 25 件まで順位付けしたリスト。<b>評価</b>は MRR@25: 正解が 1 位なら 1 点、2 位なら 1/2、…、25 位なら 1/25、入っていなければ 0 点の平均です。
構造の同一性は立体を除き、互変異性体(タウトマー)を正規化した InChIKey の先頭 14 文字で判定します。</p>
<div class="grid"><div class="card">{mol_svg(smi_q, legend="ケルセチン C15H10O7(質量 302.0427)")}</div><div class="card">{mol_svg(smi_m, legend="モリン C15H10O7(質量 302.0427、ケルセチンの異性体)")}</div></div>
<p>下の図は、学習データにある <b>ケルセチン</b>(左、ポリフェノールの一種)と、原子の組成がまったく同じ <b>モリン</b>(右)のスペクトルです。縦の線が破片、点線がプリカーサの位置。衝突エネルギーを上げると大きな破片が減り小さな破片が増えます。
同じ分子なら CE が違っても共通する破片が多く、異性体どうしは一見似ていますが細部が違います。この「組成が同じで構造だけ違う候補を見分ける」ことが Class 2 の本質的な難しさです。</p>
{fig_iso}
<table style="max-width:640px"><tr><th>スペクトル類似度(エントロピー類似度、1 = 同一)</th><th>値</th></tr>{sim_rows}</table>
<p class="small muted">質量だけでは異性体を区別できない(両方 302.0427)。PubChem には同じ組成の構造が数百〜数千あるため、スペクトルの「壊れ方」の情報で絞り込む必要がある。</p>
</article>""")

    # ------------------------------------------------------------------ 2. the data
    lib = meta.group_by("ingest_lib").agg(pl.len().alias("spectra"), pl.col("inchikey14").n_unique().alias("molecules"), (pl.col("ce_min").is_not_null()).mean().alias("ce_known"),
                                          pl.col("instrument_type").drop_nulls().mode().first().alias("main_instrument")).sort("spectra", descending=True)
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.barh(lib["ingest_lib"].to_list()[::-1], lib["spectra"].to_list()[::-1], color="#0b6e4f"); ax.set_xscale("log"); ax.set_xlabel("スペクトル数(対数)")
    for i, (n, mcount) in enumerate(zip(lib["spectra"].to_list()[::-1], lib["molecules"].to_list()[::-1])): ax.text(n * 1.1, i, f"{n:,} 本 / {mcount:,} 分子", va="center", fontsize=8)
    ax.set_xlim(3e2, 2e7); ax.set_title("学習データ: 11 のスペクトルライブラリ"); fig.tight_layout(); fig_lib = png(fig)
    lib_rows = "".join(f"<tr><td>{r['ingest_lib']}</td><td>{fmt(r['spectra'])}</td><td>{fmt(r['molecules'])}</td><td>{r['ce_known']*100:.0f}%</td><td>{html.escape(str(r['main_instrument']))}</td></tr>" for r in lib.iter_rows(named=True))
    add = meta.group_by("adduct").agg(pl.len()).sort("len", descending=True).head(12)
    per_mol = meta.group_by("inchikey14").agg(pl.len().alias("n"))["n"].to_numpy()
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.3))
    axes[0].barh(add["adduct"].to_list()[::-1], add["len"].to_list()[::-1], color="#2563eb"); axes[0].set_xscale("log"); axes[0].set_title("アダクト(上位 12)"); axes[0].set_xlabel("スペクトル数")
    axes[1].hist(np.clip(per_mol, 1, 60), bins=60, color="#0b6e4f"); axes[1].set_yscale("log"); axes[1].set_title("1 分子あたりのスペクトル数(60 で切り詰め)"); axes[1].set_xlabel("本数")
    prec = meta["precursor_mz"].to_numpy(); axes[2].hist(prec[(prec > 50) & (prec < 1600)], bins=80, color="#b45309"); axes[2].set_title("プリカーサ m/z の分布"); axes[2].set_xlabel("m/z")
    fig.tight_layout(); fig_dist = png(fig)
    npk = meta["num_peaks"].to_numpy()
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))
    axes[0].hist(np.clip(npk, 0, 300), bins=60, color="#6b7280"); axes[0].set_title("1 スペクトルのピーク数(300 で切り詰め)"); axes[0].set_yscale("log")
    pol = meta.group_by("ionization_mode").agg(pl.len()).sort("len", descending=True); axes[1].bar(pol["ionization_mode"].to_list(), pol["len"].to_list(), color=["#0b6e4f", "#b45309"]); axes[1].set_title("極性")
    fig.tight_layout(); fig_peaks = png(fig)
    tg = test.group_by("molecule_id").agg(pl.len().alias("n"), pl.col("adduct").n_unique().alias("na"))
    tadd = test.group_by("adduct").agg(pl.len()).sort("len", descending=True)
    parts.append(f"""
<article><h1>2. データの中身</h1>
<p>学習データは <b>{fmt(n_spec)} 本のスペクトル</b>、<b>{fmt(n_mol)} 種類の分子</b>(公式の同一性では {fmt(n_official)} 種類)、{n_lib} のライブラリから集められています。最大のライブラリ enveda-180 は主催者が timsTOF 装置で測った合成化合物ライブラリで、
天然物のスペクトルは riken / gnps / massbank / mona などの公開ライブラリにあります(装置は Orbitrap や QTOF)。隠しテストは天然物約 400 分子・timsTOF なので、<b>学習データと装置・化学の分布が違う</b>のがこの課題の特徴です。</p>
{fig_lib}
<table><tr><th>ライブラリ</th><th>スペクトル</th><th>分子</th><th>CE が分かる割合</th><th>主な装置</th></tr>{lib_rows}</table>
<p>アダクトは [M+H]+ が最多で、負モード [M-H]- も多い。1 分子あたりのスペクトル数は中央値 {int(np.median(per_mol))} 本(同じ分子を複数の CE・アダクト・装置で測っている)。プリカーサ m/z は 100〜600 に集中。</p>
{fig_dist}
{fig_peaks}
<h2>テストデータ</h2>
<p>公開されているローカルの test.parquet は {fmt(tg.height)} 分子・{fmt(test.height)} 本で、スペクトル/分子の中央値 {int(tg['n'].median())}(最大 {int(tg['n'].max())})、アダクト種/分子の中央値 {int(tg['na'].median())}。
ただしこれは学習データ(enveda-180)の抜き出しで、本番の採点に使われる<b>隠しテスト</b>は別物です: 天然物 約 400 分子、約 1,500 本、1〜16 本/分子(中央値 3)、10 種のアダクト(水損失アダクトを含む)、質量 157〜1,159 Da。
ローカル test のアダクト: {", ".join(f"{a} {n}" for a, n in zip(tadd["adduct"].to_list(), tadd["len"].to_list()))}。</p>
</article>""")

    # ------------------------------------------------------------------ 3. the three classes and the funnel
    fun = {}
    try:
        import pandas as pd
        d = pd.read_csv(os.path.join(ROOT, "experiments/p1_baseline/run1/p1_funnel_A_timstof.csv"))
        fun = dict(window=int(d.n_unique.median()), ext=int(d.n_unique_external_only.median()), short=int(d.n_shortlist_official.median()))
        m2 = pd.read_csv(os.path.join(ROOT, "experiments/p1_baseline/run1/p1_molecules.csv")); fun["same_formula"] = int(m2[m2.set == "A_timstof"].n_tier_same_formula.median())
    except Exception:
        fun = dict(window=10184, ext=10092, same_formula=2638, short=115)
    fig, ax = plt.subplots(figsize=(9, 3.0))
    stages = [("PubChem 全体", 105_875_489), ("質量窓 ±10 ppm", fun["window"]), ("同じ分子式", fun["same_formula"]), ("指紋モデルで絞った shortlist", fun["short"]), ("提出(上位 25)", 25), ("正解", 1)]
    ax.barh([s[0] for s in stages][::-1], [s[1] for s in stages][::-1], color=["#e5e7eb", "#2563eb", "#0b6e4f", "#b45309", "#6b7280", "#b91c1c"][::-1]); ax.set_xscale("log")
    for i, (n_, v) in enumerate(stages[::-1]): ax.text(v * 1.15, i, f"{v:,}", va="center", fontsize=9)
    ax.set_xlim(0.7, 5e9); ax.set_title("1 分子あたりの候補の絞り込み(timsTOF 300 分子の中央値)"); fig.tight_layout(); fig_funnel = png(fig)
    parts.append(f"""
<article><h1>3. 3 つのクラスと「候補の漏斗」</h1>
<p>隠しテストの分子は、答えがどこにあるかで 3 つに分かれます(比率は非公開)。</p>
<div class="grid">
<div class="card"><h2>Class 1: ライブラリに参照あり</h2><p>同じ分子のスペクトルが学習ライブラリにある。<b>スペクトル同士の類似度検索</b>でほぼ解ける(公開解法で 0.95 超)。ただし本番は timsTOF、参照は Orbitrap/QTOF が多く、装置差で類似度が下がる。</p></div>
<div class="card"><h2>Class 2: 構造は PubChem/COCONUT にあるがスペクトルは無い</h2><p>質量から候補を集め(数千〜数万)、<b>スペクトルの壊れ方と構造の整合</b>で順位付けする。同じ分子式の異性体の識別が本質。指紋予測モデル(FPNet)と順方向モデル(構造からスペクトルを予測する ICEBERG/GLACIER)を組み合わせる。</p></div>
<div class="card"><h2>Class 3: どのデータベースにも無い新規構造</h2><p>候補を<b>生成</b>しなければ 0 点。公開解法でも誰も LB を動かせていない。比率が 3〜7 割と推定が割れていて、到達できる上限を左右する。</p></div>
</div>
<p>Class 2 の典型的な流れ。質量 ±10 ppm の窓に 1 万個の構造があり、同じ分子式だけでも数千。指紋モデルが分子式をほぼ決め(上位 25 の 24 個が正解と同じ分子式)、残る異性体の識別を順方向モデルが担う。</p>
{fig_funnel}
<h2>評価 MRR@25 の例</h2>
<table style="max-width:560px"><tr><th>分子</th><th>正解の順位</th><th>得点</th></tr><tr><td>A</td><td>1 位</td><td>1.000</td></tr><tr><td>B</td><td>2 位</td><td>0.500</td></tr><tr><td>C</td><td>4 位</td><td>0.250</td></tr><tr><td>D</td><td>26 位以下(入らず)</td><td>0.000</td></tr><tr><td colspan="2"><b>MRR@25</b>(平均)</td><td><b>0.438</b></td></tr></table>
<p class="small muted">金圏の目安 0.473、首位 0.504(10/24 朝)。Class 3 が 4 割なら残り 6 割で 0.8 を取っても 0.48 にしかならない、という計算になる。</p>
</article>""")

    # ------------------------------------------------------------------ 4. our pipeline
    parts.append("""
<article><h1>4. 自前ベースライン B1 の処理の流れ</h1>
<div class="grid">
<div class="card"><h2>① 候補取得</h2><p>各スペクトルのプリカーサ m/z とアダクトから中性質量を計算し、±10 ppm の窓で PubChem(1.06 億構造)、学習構造 + COCONUT(71 万)から候補を集める。</p></div>
<div class="card"><h2>② 安いスコア</h2><p>指紋予測モデル FPNet(スペクトル → 分子指紋の予測、候補の指紋との内積)、文献 prior(PubChem の文献数など)、ライブラリ類似度(学習スペクトルとのエントロピー類似度)。</p></div>
<div class="card"><h2>③ shortlist</h2><p>FPNet 上位 100 ∪ FPNet+prior 上位 100 ∪ 類似度上位 20 を公式同一性でまとめる(約 115 件)。</p></div>
<div class="card"><h2>④ 順方向モデル</h2><p>GLACIER / ICEBERG が候補構造から MS/MS を予測し、実測との類似度を出す(重い計算なので shortlist だけ)。</p></div>
<div class="card"><h2>⑤ 融合</h2><p>固定規則 S = z(FP) + 2·z(GL) + z(ICE) + 0.5·prior(z は候補内の標準化)、または学習した順位付けモデル(LambdaRank)で並べ替え、上位 25 を提出。</p></div>
<div class="card"><h2>検証</h2><p>学習に使っていない分子を凍結し、「参照を隠す(Class 2 模擬)」「他ライブラリの参照を残す(Class 1 模擬)」の 2 条件で、到達不能な正解を 0 点とする strict な MRR で比べる。</p></div>
</div>
<p class="small muted">詳細は <a href="b1.html">B1 設計</a>、結果の推移は <a href="experiments.html">実験</a> と <a href="index.html">いま</a> のページ。</p>
</article>""")

    body = "".join(parts)
    open(os.path.join(SITE, "eda.html"), "w", encoding="utf-8").write(page("データと課題", body, "eda.html"))
    print("eda built", dt.datetime.now().strftime("%H:%M:%S"), "| libs", lib.height, "| isomer CEs", list(pick))


if __name__ == "__main__":
    main()
