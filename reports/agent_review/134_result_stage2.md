# 134 段階 2 の結果(2026-10-29 23:17 JST 読み出し)— GLACIER A2(timsTOF 適応)は **NO**

登録: `134_prereg_glt_stage2.md` v2(§5)。reader `experiments/glt/x134_read.py`(sha 01518c0d…、未変更)、評価器 `gl_only_eval.py` v2.1(下記の技術修正)。記録は `experiments/glt/readout134/`(reading md/json、manifest v2 と現行、manifest_change.txt、A2_scope.json、check10.json)。

## 実行の記録
- A2 = `inten_encoder` / `inten_decoder` / `output_map` だけを学習(110 tensor、元から学習可能なものに限る)。end-to-end の強度損失。data/glt/tims_s1(2,000 identity、5,135 スペクトル、fold 3/4)。1,500 updates、lr 1e-4、batch 16、warmup 100、seed 0。
- CUDA 事前検査は PASS(22:40)。学習は 123 s(state_dict b257f41e…)。export の検査: 凍結部分は bit 一致、学習対象 110/110 が変化、runner での strict reload が成功、C0' と比べて 10 分子 2,320 組の全得点が異なる。
- 採点: 4 cell とも、C0' と同じ runner 入力・同じ meta(panel 216/250、f1G 92/100 partial は C0' と同数、npH 199/199、f1D 100/100)。
- **技術修正(v2 → v2.1、結果を読む前)**: 最初の reader 実行は、f1G の要約行を書く途中で止まった。原因は `r.empty` が pandas の `DataFrame.empty`(bool)を指し、列を読んでいなかったこと。列を `r['empty']` で読むように直した。v2 が止まる前に書いた分子ごとの表(`v2crash/read_f1G.csv`、読まずに退避)と、v2.1 の表の sha256 は一致した(81aa6859…)。したがって計算は変わっていない。manifest では評価器の行だけを更新し、元の manifest と経緯を残した。

## 結果(view c2、全 roster、identity bootstrap 4,000、seed 134)

| 指標 | A2 − C0' | 95% | n | 関門 |
|---|---:|---|---:|---|
| **主: f1G(timsTOF、base と適応のどちらも未見)rr_form** | **+0.0437** | **[−0.0132, +0.1023]** | 100 | ≥ +0.01 かつ下限 > 0 → **下限で不成立** |
| 費用: rr_form npH | −0.0205 | [−0.0478, +0.0049] | 200 | 下限 ≥ −0.01 → 不成立 |
| 費用: rr_form f1D | +0.0030 | [−0.0207, +0.0264] | 100 | 不成立 |
| 費用: rr_gl f1G | +0.0498 | [−0.0097, +0.1101] | 100 | 成立 |
| 費用: rr_gl npH | −0.0183 | [−0.0464, +0.0088] | 200 | 不成立 |
| 費用: rr_gl f1D | +0.0083 | [−0.0165, +0.0336] | 100 | 不成立 |
| 費用: rr_gl panel | −0.0090 | [−0.0397, +0.0226] | 250 | 不成立 |
| 記述: rr_form panel | −0.0117 | [−0.0424, +0.0192] | 250 | (補償に使わない) |

**関門: NO。** 登録どおり A2 は止める。lr・step・学習範囲の選び直しはしない。段階 3(GL の交換、ranker の再学習)には進まない。

## 記述(判断には使わない)
- f1G(timsTOF): top1_form は 0.48 → 0.53。margin_form(真と同じ式の最良デコイとの差、n 84)は +0.0128 [+0.0045, +0.0215]。点推定はどれも改善方向だが、n = 100 では区間が広く、0 も +0.10 も否定できない。
- NP_H(timsTOF 以外): rr_form 0.360 → 0.339、top1_form 0.285 → 0.255。timsTOF 以外では、わずかに悪い方向。
- panel(timsTOF の NP、226/250 は base GLACIER の学習 MSG に含まれる): rr_gl 0.422 → 0.413。base が記憶している分の優位を、適応が少し削った可能性がある。ただし panel の大半は既見なので、未見の隠しテストの代理にはならない。
- 読み(Codex 136 Q1 で訂正): 主指標の区間が広く、登録した有効性と非劣性を確認できなかった。真の利得があり、検出力だけが足りなかったとまでは分からない。NP の負の点推定も、害の確定ではない。「装置への適応による利得と忘却」という説明は、仮説として残す。

## 次(Codex 135 Q3 の分岐「134 が性能上 NO」)
- A2 は登録どおり止める。class 3(W135)の上限が十分なら、selector への投資を優先する。
- GL に次の投資をするなら、別の仮説として新しく登録する(例: 同じ式の hard negative を使う retrieval 目的での学習)。A2 の lr / step を少しずつ変えて選び直すことはしない。
- 設計上の教訓(新しい結果を見る前の記録): 隠しテストはすべて timsTOF である。将来の GL 仮説の主指標は、timsTOF の未見分子で検出力を確保した集合(例: f1G・f2G・locked G を合わせた約 300 分子)で事前に決める。A2 を同じ集合で読み直して救済することはしない(同じ候補で関門を後から変えることになるため)。
