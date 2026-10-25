# 022 依頼: pool60 の不採用報告と、「M2x + full_eval のみ」の今夜の比較提出の判定基準(評価は 17:40 頃完了)

作成: 2026-10-25 15:45 JST(Claude Code)。前回 `021_decision.md`。

## 1. 報告
- **pool60 は不採用**(`docs/validation_design.md` 末尾): C2 資格を修正した端から端の比較で C1 の利得なし(全層 0 〜負)、dev2 G C1 −0.040 [−0.069, −0.013]、G C2 −0.021。修正版 W7 の再実行と parity は不要として停止(Spark GPU を full_eval の評価へ)。
- **full_eval の学習完了**(15:33、82,855 更新、3.84 h;dev2 保留 MRR 0.712、学習 0.979;sha256 5b8d1c31…)。Spark で `spark_fulleval_chain.sh` が実行中: 現行 M2x の構成・rank_v4b・blend21 + fallback のまま FPNet だけ full_eval に替えた特徴表を、パネル(C1 = 学習済み identity・query 未見)、dev2 全層(未見)、W7(学習済み = 診断)で作り、登録評価(M2x vs M2x_fe)と同一窓の FP 比較を出す。パネルは評価前に固定した監査群(clean 202 / uncertain 48)で分けて報告する。
- **full_rk の学習を開始**(15:34、20:19 自己停止;GO 条件 4 つを実測で確認、`021_decision.md`)。
- **E0 vs B1 のパネル**: C2 同等(0.906 vs 0.905)、C1 E0 +0.066(E0 は query まで学習済み)。

## 2. 質問: 今夜「M2x + full_eval のみ」を比較提出してよい条件
私案(020 の規則を full_eval に適用):
1. **主に改善を見る**: パネル C1(clean 群と uncertain 群を別々に;clean 群の Δ が正であること)、dev2 C1(C/E/F/G)。
2. **保護**: dev2 の C2 全層(C/D/E/F/G)と C1 で、点推定 ≥ −0.02 かつ 95% 区間下限 ≥ −0.02(ε=0.02)。W7 は学習済みなので保護に使わない(診断のみ)。
3. **実装**: 提出パイプラインの `--fpnet_ckpt` で同じ checkpoint(sha256 一致)を読み、W7 50 分子程度で評価器との機械的一致(shared cache)を確認する — 時間が足りなければ「パイプラインが評価器と同じ特徴(FP 値)を出す」ことの小規模確認で代える。
4. 合格なら private dataset(自前 checkpoint + 学習記録 + 出典・ライセンス README)を作成し、新しい private kernel で実行して提出。Public の読みは 020 の事前登録(基準 0.354、±0.02)。
**Q1** この基準でよいか。dev2 の区間が広く「未確定」になった場合、比較提出(本命昇格ではない)として出してよいか。**Q2** 3 の実装確認の最低限は何か。**Q3** full_eval の重みを Kaggle に private dataset としてアップロードすることに、規則・記録上の追加要件はあるか(018 の attribution 表に沿って README を用意済み:`kernels/fpnet-fulleval-dataset/README.md`)。
