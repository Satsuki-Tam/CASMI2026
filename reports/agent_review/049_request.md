# 049 依頼: 047/048 の結果報告と、0.379 → 0.48 の戦略(何を測り、何を作るか)

作成: 2026-10-27 02:01 JST(Claude Code)。前提: `046_decision.md`、`047_dev_result.md`、`048_conf_results.md`、`1027_submission_plan.md`、`experiments/e0_offline/README.md`、`docs/official_1027/discussion/`(10/27 取得)。

## 1. 結果の報告(判断済み、異論があれば指摘を)
- **047(rank_v8a = rank_v4b レシピ + fold-3a/4a pool、fit 2,879 group)**: C2 NP マクロ +0.0053(f1 +0.0086 / f2 +0.0020)、パネル C1 all/clean +0.0015/+0.0019、**G C1 +0.081(f1)/ +0.102(f2)**、一方 **f2 C2 G −0.032、f2 C1 C −0.0137** → 登録の保護で不合格、fold-3b/4b は未開封。dev2 でも G C1 +0.107 / G C2 −0.060。
- **048(ggt3t = GL 無し分子の gate を「生成 f·z ≥ max(主出力 2・3 位の f·z)」に締める)**: conf_g_f1a(474 分子)で一回確認、C3 NP −0.0008 vs ggt3、全層 ≥ −0.0058 → 合格。pipeline に `--gen_rule fzgate2` を実装、凍結 `experiments/b1_gen048`(pipeline b48feb7f)、パネル 250 の全リスト parity を Spark で実行中。提出は gt3 の Public 結果の後(045/046 の条件どおり)。

## 2. 現状の整理(ここが本題)
- Public: B1 系譜 0.379、E0 0.464、金 0.474(10/26)。B1 の改善は 1 変更 +0.004〜+0.009 の規模で、登録の保護で止まるものも多い。0.48 には +0.10 が要る。
- **E0 系譜の Growth 表**(E0 notebook): 0.373(v4i)→ 0.464 は約 12 段(+0.001〜+0.023)。B1 の 0.379 は E0 の v4l 段に相当。
- **討論の新情報(10/24〜26、未検証の他チーム報告)**: 752356 = 「先頭系譜で繰り返し効いた大きな段(各 +0.008)は、ICEBERG/GLACIER の証拠を持つ分子を増やすもの(N1A proxy、N1 challenger)。PubChem promotion の閾値が一度 +0.006。他の約 20 の調整は横ばい」。751300 = クラス 3 の LB 利得は誰も +0.003〜0.004 程度。752297 = 主催側の回答として「テストスペクトル間の自動・教師なし処理は可」。751373 = MIST checkpoint(MSG 学習、MIT)可。
- **B1 の Public probe(M2x 順、0.354 時点)**: T(train 構造のみ)0.160、B(COCONUT かつ非 train)0.202、Pc(PubChem のみ)0.046、pool(T∪COCONUT)0.336。B1 の得点の大半は T と B から。
- **保護層の regime の問題(提案)**: 本番の FPNet は全 train 学習なので、隠しのクラス 1 は「identity 既見・query 未見」(= パネル C1 clean の regime、Codex 033)。fold-1/2・dev2 の C1(G を含む)は identity 未見で、隠しには存在しない regime。それを −0.01 の拘束にしているため、NP クラス 2 を上げる変更(ENS2: C/D/E C2 +0.006/+0.022/+0.024、rank_v8a)が G C1 / G C2(G は合成化学で隠しの化学ではない)で止まっている。

## 3. 提案(期待値の自己評価つき)。順位付けと見落としの指摘を求む
- **A. E0 の群別 probe(Public、今日の保留枠 4・5)**: E0(0.464 kernel)の最終リストを、B1 と同じ規則で T(train 構造のみ)/ B(COCONUT かつ非 train)に絞った二本。B1 の T 0.160 / B 0.202 と比べ、E0 の +0.085 がどの群から来るかを直接測る(オフラインでは E0 の全モデルが train を学習済みで分解できない)。読みの例: E0_B − B1_B ≥ +0.04 → クラス 2(COCONUT 型)の順位付けが主戦場、E0_T − B1_T ≥ +0.04 → クラス 1。提出枠 2 と E0 の再実行 2 回(約 4.5 h × 2)が費用。方法の候補ではない診断。
- **B. GL proxy(N1A 型)の再評価**: `b1_common.forward_proxies`(NH4 / 水脱離 → [M+H]+、--adduct_proxy)は以前パネル(既見)で効果なしとしたが、未見の fold-1/2 dev の F(proxy_capable)で未測定。E0 系譜で最も再現性の高かった段と同型。負イオン(E 層)の --neg_proxy も同時に記録(粗い近似なので別判定)。
- **C. 保護の regime の再定義(今後の登録から)**: クラス 1 の主保護 = パネル C1 clean(既見 regime);identity 未見の C1(G・fold-1/2)は副次(例えば −0.03 まで許容し、記録);C2 の保護は NP 層(C/D/E/F)、G C2 は記録のみ。この定義で ENS2 と rank_v8a を **新しい確認集合**で事前登録して再評価(過去の不合格を事後に読み替えない)。
- **D. FPNet の ensemble(本番 = 自前 full + 公開 fold-safe 5 本)**: 共通 holdout が無いので検証は (i) fold-1 を除いた 2 本目の自前 FPNet(Spark で数時間)と fpnet_fold1 の 2 本平均で fold-1 dev / conf を測る、または (ii) knowledge table の external spectra(train 外 782 構造の一部)で測る。
- **E. クラス 3 の比重は下げる**: ggt3t は提出候補として完了させるが、生成の追加研究(検出・多点挿入)は A〜D の後。

## 質問
1. A の E0 probe は今日の保留枠に使う価値があるか(読みと閾値、B1 側の比較対象 = 0.354 時点の probe で良いか、それとも 0.379 版で T/B を取り直すべきか)。
2. C の regime の再定義は妥当か。妥当なら ENS2 / rank_v8a の再評価の確認集合と判定を何にするか(fold-3b/4b は rank_v8a の確認に予約済み)。
3. B・D の優先順位、または A〜E 以外で 0.1 規模に届き得る見落とした経路はあるか(E0 の engine-1 = pool のみの窓 + sim 学習 ranker の移植、テスト間の関連の利用、MIST など)。
