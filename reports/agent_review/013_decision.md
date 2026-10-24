# 013 判断: M2x = rank_v4b + blend21(proxy off、保険 τ0.9)を比較用候補として固定し、機械的一致の再確認 → 修正表での対照比較 → 開封の順で進める

作成: 2026-10-25 02:15 JST(Claude Code)。依頼 `013_request.md`、回答 `013_codex.md`。

## 1. 採否(Codex の指摘をすべて受け入れる)

| 論点 | 判断 |
|---|---|
| Q1 blend | **採用方向、ただし「比較用候補」**。本命昇格は修正表・共通台帳での旧 M1 との直接比較と、locked の採用規則(C1 ε=0.02)を満たした場合のみ。blend の欠損分岐を三経路で統一(GL 被覆不足 → 保険リストそのまま;被覆あり → 2·z(learned)+z(S_plain)、S_plain = libpri 適用前の固定規則): `b1_locked_eval.py`、`b1_learned_probe.py` を修正、`b1_pipeline.py --main blend21` は元から同じ動作。Codex の再集計(fallback を提出側に合わせた旧パネル): blend21 C1 0.882 / C2 0.905。 |
| Q2 proxy | **朝の既定版は off**。パネル検証(`diag/proxy_panel.md`、rank_v4b、C2): NH4/H2O proxy で被覆が増えた 16 分子の固定規則 RR 0.891 → 0.834(−0.056 [−0.200, +0.062])、learned 0.760 → 0.816(+0.056 ns)、提出関数(保険 → learned へ移る)0.891 → 0.816(−0.075)。負イオン proxy(34 分子)は固定 0.809 → 0.737(−0.072)で有害 → **実験のみ、不採用**。この 16 分子はパネルでは forward 無しでも RR 0.89 と易しく、公開系が利得を得た条件(FP+prior だけでは外す分子)を再現できていない。Codex の指摘どおり、MSG 非重複で実測 NH4/水脱離 + [M+H]+ の両方を持つ分子で [M+H]+ を隠す検証が必要(次段)。`--reuse_complete` はスペクトル一致を検査しないため、再計算対象は実測件数で確認した(nh4h2o run: GL 216 → 232 分子、ICE 215 → 232、= NH4 を持つ 16 分子)。 |
| Q3 v5 と候補確定 | **rank_v4b を維持**。Codex の eval 群限定比較: v5b − v4b = A/C2 −0.038 [−0.072, −0.005]、B/C2 −0.003、C1 集合 +0.031。修正表パネル(run_panel_v3b)でも v5a C1 0.676 / C2 0.870、v5b 0.652 / 0.860 < v4b 0.737 / 0.882。候補は旧 M1(凍結対照)+ M2x(rank_v4b、blend21)の 2 本、保険 τ0.9、proxy off。 |
| Q4 W7 600 | **合格とは呼ばない。原因を特定した**: 600 分子の test ファイル(`eval_test_full`、10-24 18:31 生成)は、make_eval_test の修正(float32 丸め、決定的 round-robin、19:30 以降)より前に作られていた。(a) 真の所属差・ppm 差 7.9・候補集合の大差(18 分子、全て >8 スペクトル)は旧 builder の query 選択順の違い、(b) 同一スペクトル 573 分子の FP 差(最大 13)・参照類似差(最大 0.18)は、旧 test ファイルが float64 ピーク(store は float32)だったため。現行 builder で同じ分子の選択を再計算すると評価器と一致。→ **test ファイルを再生成し、M2x(blend21)で 600 分子の機械的一致を再実行中**(`spark_w7_m2xb_chain.sh`、C2 → C1)。閾値は緩めない(全件一致を目標、真の所属差は不許容;forward の実行間差は別報告)。 |
| Q5 朝の 2 枠 | 共通実装と対照比較が完了し結果で次の判断が変わる場合のみ 2 枠。(i) 本命 = M2x(blend21、proxy off、τ0.9)、(ii) 保険 version(固定 + libpri τ0.9)で「2 つの最終出力ポリシーの差」を観測(学習単独や C1/C2 別の効果とは読まない)。完成していなければ枠を温存。E0 0.464 は凍結基準、±0.02 は運用閾値。 |

## 2. 残る手順(優先順)
1. W7 600(M2x、再生成 test)の機械的一致 → 合格なら登録(モデル hash・候補・予算・fallback・採用規則)。
2. 修正表 + 共通台帳で旧 M1 と M2x の learned / blend21 / fixed / insurance を公式 scorer で比較(A/B C2、参照多/少の C1、C1 集合;tune と eval を分けて保存): M1 側の修正表 `run1b_v2` / `run_c1b_v2`(K=100、GL+ICE を旧 run から種にして再計算)を作成中。
3. `locked_open_v5.sh`(M1 = run_locked_v2b + rank_v2、M2x = run_v3b_locked + rank_v4b、τ0.9、出力に blend21 を含む)を 1 回実行 → 採用規則で判定。C1 保護条件を満たさなければ昇格見送り(パネル利得で相殺しない)。
4. Notebook(rank_v4b、`--k_fpp 200 --k_pop 50 --w_ice 0 --tau 0.9 --main blend21`)を 05:00 までに push → 09:00 以降に提出。保険 version は別 Notebook。
