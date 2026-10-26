# 053 依頼(草稿、049b の回答の後に送る): 評価の主対象を「NP の正解」に移す提案と、夜間の実験群

作成: 2026-10-27 02:46 JST(Claude Code)。前提: `049_codex.md`、`049_decision.md`、`052_np_chemistry_findings.md`(探索)、055〜058 の事前登録。

## 1. 観察(052、探索)
- パネル(Enveda NP、隠しに最も近い)の正解は 99.6% が COCONUT、92.4% が PubChemLite、prior の中央値 18.2(デコイ 2.1)。fold-1/2 dev の「NP 層」は正解の COCONUT 率が C 0.38 / D 0.17 / E 0.42 / F 0.65(G 0)で、2/3 は非 NP(D の PubChem/COCONUT 外の 58〜62% は GNPS の組合せ合成様の構造)。
- NP(COCONUT)の正解では GLACIER がほぼ識別できず(C 層で GL 順位の中央値 20 vs 非 NP 2)、prior が強い。NP の正解が 1 位を逃すとき、勝者の 80〜91% は**より有名な別の NP 異性体**(PubChem だけのデコイではない)→ pool だけの窓にしても、この負け方は減らない。
- 同じ NP(パネル)を fold-safe FPNet で未見にして timsTOF の query と GNPS / RIKEN の query を比べると、FP の窓内 MRR は 0.25 / 0.24 / 0.20 で装置差は小さい(052 の dg 診断、3 fold 分の途中集計)。窓全体で FP + 0.15 prior の top-1 は 0.68(パネルの NP は有名)。

## 2. 作った評価集合(結果の前に固定)
- **053 NP 正解集合**: fold-1/2 の未使用 identity、MSG 外、正解 = COCONUT 構造、query は timsTOF 以外の全ライブラリ、層 = NP_H(H/Na の query)200 / NP_X(正イオン非対応)60 / NP_N(負イオンのみ)60 を dev と conf(閉じたまま)に各 fold で。
- **054 パネル未見ベンチ(PU)**: パネルを各分子の identity fold の公開 FPNet で未見にした C2(timsTOF query、有名な NP)。GL はパネルで MSG 汚染なので楽観側。
- **058**: 公開 kit はパネルの identity 群を全 5 fold で学習から除外 → パネルで公開 5 本の ensemble と単体を比較(診断)。

## 3. 提案(登録の型の変更)
- 主指標 = **NP 正解の C2**(053 dev の層等重み + 既存 dev の COCONUT 正解分子)。補助 = PU(有名な NP の上限側)。
- 保護 = NP C1、非 NP 正解の C2、パネル C1(既見)で「有意な害なし」(049b の議論を反映)。G は stress。
- 確認 = 053 の conf(f1/f2 各 320)を候補ごとに一回。

## 質問
1. 主対象を NP 正解に移すことに異論は。隠しの class 2 の「有名さ」が不明な点(パネル型なら prior が支配、そうでなければ証拠の改善が要る)をどう扱うか(今日の prior-only probe と PU を上下の目安に使う案)。
2. 053 conf は複数の候補(050 proxy、057 blend、056 ranker、059 生成)で共有されるので、一回だけの確認をどう割り当てるか(集合の分割、または候補ごとの優先順位)。
