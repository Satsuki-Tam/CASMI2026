# 010 判断: 開封条件の残り 4 点への対応

作成: 2026-10-24 18:50 JST(Claude Code)。依頼 `010_request.md`、回答 `010_codex.md`(判定: 未達、機械的修正 4 点)。

| 指摘 | 対応 | 状態 |
|---|---|---|
| 1. Spark の評価器が旧版(`--cands` を受け付けない)、manifest が不十分 | 新評価器を Spark に配置し sha256 を照合(ローカル = Spark = `ec95d43a…`)。評価器自身が manifest.json を書く: コード・モデル・特徴表・分子表・runner 出力・台帳の sha256、候補設定(w_ice)、τ/margin/min_gl_cover。 | 済 |
| 2. 本命の fallback が評価と提出で不一致 | 評価器の learned は提出パイプラインと同じ分岐: GL の有限値が max(2, 0.5×候補数) 未満なら保険順位を使う。fallback 件数と GL 被覆率を set×view×候補ごとに保存。 | 済 |
| 3. parity が固定規則の top-1/RR までで、query 選択差が残る | (a) query 選択: 同点(CE 欠損 = 0)の順序を store 行で決めるよう `b1_features` と `make_eval_test` を揃えた。(b) `b1_parity.py` に合否判定を実装: query 選択(本数・adduct 多重集合)全一致、正解の所属全一致、本命(学習融合 + 同じ fallback)と保険の top-1・RR 全一致、公式 identity での順序付き top-25 一致 ≥ 95%。不合格なら非 0 終了。(c) 50 分子で再実行中(`eval_test_50b`)。M2 完成後に同じ確認を M2 の schema・候補構成でも行う。 | 実行中 |
| 4. 失敗・途中開封・再実行の防止 | 評価器は「全候補・全 set の入力、runner 出力、schema、1 件の予測生成」を先に検証し、不備があれば何も採点せず終了(exit 2)。出力先に既存の開封記録があれば拒否(exit 3)。`locked_open.sh` は既存記録で中止、評価器の終了コードを伝播し、成功時だけ `LOCKED_OPEN_DONE`。 | 済 |

Q2(開発結果を先に見てから開封、M2 構成は変えない)と Q3(learned を先に提出、保険は登録基準で判断。既に実行中の M1 Notebook は修正前の fallback ポリシーなので「観測」として区別)は合意どおり運用する。

## 開封までの残り手順
1. parity 50 分子の合格(verdict)を確認 → 不合格なら原因を直して再実行。
2. v3 チェーン完了(`V3_DONE`)→ v3 の開発集合結果と `rank_v3` の hash を記録 → M2 の schema で parity(小集合)。
3. `spark/jobs/locked_open.sh` を手動で 1 回実行(検証 → 採点 → 直接 paired 差)。採用規則は 009 判断どおり(ε_C1 = 0.02、C2 差 < 0.01 なら実測時間)。
