# 071 事前登録: P1 第一段 — ranker の学習群を増やす(v8w のレシピ固定)

作成: 2026-10-27 09:14 JST(学習・評価の前、Claude Code)。背景: 069(E0 の本体の強み = 推論と同じ候補生成・特徴の模擬 query を大量に学習)、070(P1 の設計、Codex 回答待ち)。
計算: 手元の PC(Spark は利用者が使用中)。PC での学習の再現: v8w を同じ入力・引数で再学習 → 木の構造(分割特徴・子)は完全一致、数値の差 107 箇所で最大相対差 2.9e-4(Spark b8706359 / PC b113197e)。

## 条件(rank_v4b のパラメータ固定 --params_from、feats v2_noice、drop lib_nref in_train、v3 系 run の C1 ×3 — すべて v8w と同一)
- **v9a** = v8w の入力 + `run_tp_f3b` + `run_tp_f4b`(fold 3/4、全 set C〜G、:fit、C1 ×1 = v8w の pool と同じ扱い)。3b/4b は 056 の確認で開封済み → 確認集合の役は終わったので学習へ転用。
- **v9b** = v9a + `run_np061_f3pool`(fold 3 の COCONUT 収載正解 NP_H 600 / NP_X 200 / NP_N 200、どの集合とも identity 素、未使用、:fit、C1 ×1)。
- C1 比率は揃えない(pool はすべて v8w と同じ ×1 を優先)、学習ログの c1 share と群数を記録する。

## 評価(開発。gen_eval2 --parents 0、主出力 anaw0.5 で ranker だけ置換;比較の基準は rank_v4b = 0.379 の ranker)
- **主指標**: 053 dev の **NP_H C2**(COCONUT 収載正解、[M+H]+/[M+Na]+ の query あり = ranker の経路)の一対差、f1dev / f2dev の block 等重み。τ = +0.005。
  NP_X / NP_N は GL の無い fallback 経路で ranker を使わない → Δ ≡ 0 になるはずで、記録のみ(0 でなければ実装の点検)。
- **主保護**(ε = 0.01、三状態、identity 単位の paired bootstrap 95%): (1) パネル C1 clean(full_eval の表 = 採用時の既見 regime)、(2) f1dev / f2dev の NP C2(C/D/E/F 等重み、block 等重み = 056 の主指標;COCONUT 非収載の正解を含む → COCONUT 寄りの prior の移動による損失を見る)。
- **副次**: v9X − v8w(規模の増分)を同じ量で併記。v9b − v9a(NP 正解の学習群の効果)も併記。
- **stress**(監視、拘束しない): f1/f2 の G C1/C2、NP C1 の各層、dev2 の各層、053 NP_H C1、EXT 60(GPU が空いてから)。
- **選択**: 主保護で U < −ε が無く、主指標の点推定 ≥ τ の条件の中で主指標が最大の一つ(主保護が未確定でも開発では残す;「保護合格」とは書かない)。
- **確認**(一回だけ読む): 053 の **NP_H conf**(f1conf / f2conf、未開封)。合格 = 主指標(NP_H C2、block 等重み)の点推定 > 0 かつ下限 > −0.01、加えてパネル C1 clean の下限 > −0.01(056 と同型)。NP_N conf は Δ ≡ 0 の点検に使う。
- 確認の後: 064 型の交差(full_eval の表で同じ比較)と 0.379 の pipeline での parity → Public 一変更(10/28 の v8w の結果を先に読む)。

## 環境の点検(結果を読む前)
- PC の gen_eval2 で rank_v4b の f1dev を再計算し、Spark の `diag/r047_rank_v4b_f1dev.csv` と分子ごとの main が一致することを確認する。一致しなければ評価を止めて原因を調べる。

## 未確定の点
- Codex 070 の回答(OOF 特徴と本番 FPNet のずれ、class 比率 = 暗黙の prior、G 型、最初の規模)で設計を変える場合は、結果を読む前にここへ追記する。

## 追記(2026-10-27 09:22 JST、Codex 070 を受けて、結果を読む前 — 評価は実行中だが出力は未読)
- **主比較を v8w 比に変える**: P1 の問い(群数を増やすと効くか)の主比較は **v9a − v8w_pc**(構成を揃えた追加 = tp_f3b/f4b は f3a/f4a と同じ選択の予約半分、層 C〜G・source・view の構成が同じ)。対照は PC で再学習した v8w(rank_v8w_pc、Spark 版との差は木の閾値の 1e-4 程度)を同じ環境で評価し、**v8w_pc − v8w(再現差)を先に分けて**記録する。τ = +0.005 は **v8w_pc 比**。
- **v9b − v9a は「COCONUT 収載正解を厚くする重み変更」**として別に読む(群数の効果とは混ぜない;c1 share も 0.452 → 0.409 に動いている)。
- **学習曲線**: v9h = v8w + tp_f3b のみ(fold 3、約 800 identity、v9a に入れ子)を追加で学習・評価する(B500 ⊂ B1000 の代わり;半分の切り方が fold 単位である点を記録)。
- **主指標は 053 dev の NP_H C2 のまま**(隠しに近い条件 = COCONUT 収載・GL 経路)。ただしこの主張は「COCONUT 収載・非 timsTOF・GL 対応 query」の条件に限る(Codex 070)。併記: f1/f2 dev の NP C2 マクロ(C/D/E/F)、非収載 C2(f1/f2 の C/D で正解が COCONUT に無い分子)、G C1/C2、パネル clean C1、dev2。端から端の MRR に加え、GL 経路内(gl_ok)で真が shortlist にある群の順位の改善を併記。
- **台帳**(効果を開く前に作る): 学習群を run × 層 × view × GL 経路(本番の gl_ok = GL 被覆 ≥ max(2, 0.5 × 候補数))× 正例が shortlist にあるか × 正解 COCONUT 収載 で数え、v8w と追加分の構成を並べる。
- **Public 候補としての読み**(v9X − v4b、確認 = NP_H conf の一回)は従来どおりだが、確認で言えるのは上の限定条件まで。C/D/G を含む広い主張はしない。053 X・3b/4b・locked2 を新しい独立確認に数え直さない。

### 台帳(`experiments/b1_baseline/ledger071.py` → `diag/ledger071.csv`、C1 複製の前、学習で作られる群)
| 区分 | 群 | 正例が shortlist にある群 | うち GL 経路(本番で ranker が動く) | C1 群 | 正解 COCONUT 収載 |
|---|---:|---:|---:|---:|---:|
| v3 系(fit) | 1,096 | 902 | 897 | 201 | 151 |
| v8w の pool(f3a/f4a) | 3,177 | 2,627 | 1,560 | 1,200 | 864 |
| 追加 A(f3b/f4b、v9a) | 2,519 | 2,083 | **1,312** | 929 | 571 |
| 追加 B(np061 f3pool、v9b) | 1,155 | 1,035 | **597** | 163 | 1,038 |
- 本番で ranker が使われる「正例あり・GL 経路」の群は v8w の 2,457 → v9a 3,769(+53%)→ v9b 4,366。E/F/NP_X/NP_N の群(GL 無し)は学習には入るが本番では ranker を通らない(v8w と同じ扱いを維持;「GL 経路の群だけで学習」は別の実験)。
- 追加 A の層構成は v8w の pool とほぼ同じ(F の C2 だけ 151 vs 400 と少ない)。
