# 017 判断: 公開ダミーに基づく「隠しテスト」の推論を撤回、GL なし ranker は不採用、次は rank_v4b vs「fold 0 の G 型 72 群を追加」の一対比較

作成: 2026-10-25 09:15 JST(Claude Code)。依頼 `017_request.md`(§4・§5 追記含む)、回答 `017_codex.md`。

## 1. 採否(すべて受け入れ、実施状況)
| 論点 | 判断・実施 |
|---|---|
| 公開ダミーの取り違え | **撤回・訂正済み**(`docs/validation_design.md`、朝の報告、memory に教訓を保存)。`test.parquet` = 公開ダミー(train 由来、採点時に置換)。kernel 出力の被覆統計もダミー。隠しテストについて使えるのは公式の「timsTOF query、約 400 分子、3 クラス」のみ。以後の集計に `data_role` と入力 ID hash を付ける。 |
| 表記の訂正 | `r_pipeline` ≠ 登録主出力。登録主出力は `r_blend21`(G/C1 0.600、G/C2 0.637)。保険は `r_fguard0.9_0.2`(近似を撤回)。strict 分母に統一(E/C2 0.308 / 0.367 / 0.235、F/C2 0.264 / 0.265 / 0.229)。fallback 発生数は全分子分母(E 99+1、F 100、G 8)。 |
| 提案 1(GL なし ranker) | **不採用**(パネル GL 不足 C1 0.809 → 0.402、探索的 CI −0.407 [−0.535, −0.270])。fallback は保険のまま(理由は「置き換え候補が保護条件を満たさない」)。 |
| 順序 | (4) E0 段階比較(c2_full3 実行中)を先行・並行 → (2) rank_v4b vs「G 72 群追加」の一対比較(query・shortlist・特徴・hyperparameter・C1 重み・blend21/fallback 規則を固定)→ (3) 条件付き guard は 2 の残存失敗に対する一比較。 |
| 提案 2 の実装 | `b1_rank_train.py` の固定 `("A_timstof","B_nplib")` を run 内の特徴表と eval CSV の集合から自動検出に変更(済み)。使用 identity / C1・C2 群数 / positive を含む群数の出力を追加する。fit pool の特徴生成は **G 72 群のみ**に限定して再キュー(E/D/F/C を混ぜると G 追加の効果と分布変更が分離できない)。 |
| 保護条件(事前登録) | 主確認: dev2 G/C1 の主出力 blend21。保護: G/C2、C/D の C2、既存 A/B の C2 と C1 評価集合、パネル両 view;E/F と G・パネルの fallback 出力の同一性。ε = 0.02(点推定 −0.02 未満の悪化なし、非劣性宣言は区間下限 ≥ −0.02)。利得で他層の損失を相殺しない。同 identity の C1/C2 を独立標本として合算しない。locked2 開封前に固定。 |
| fold 拡張(§5) | 保留。配布 fold k モデル(k≠0)は fold 0 を学習に含むため、fold 0 の dev2/locked2 への未見性が FP 特徴経由で崩れる。厳密には「fold 0 と fold k を両方除外した」モデルが必要。まず fold 0 モデル + G 72 群で仮説を検証。校正・実装要件(query の fold でモデル選択、候補生成からの作り直し、fold 別の recall/FP-only MRR 記録、提出 FPNet は fold 0 のまま)は拡張時に適用。 |
| E0 gate | 「同じ τ だから gate は差を説明しない」を撤回。E0 の `lib_max ≥ 0.9` は BASE 全体の維持で、B1 保険の margin 付き lib 優先とは別規則。段階比較で BASE 前後・最終 merge 前後の順位差を残す。 |
| D の読み | 「順位付けの余地は小さい」を撤回。shortlist 到達 42/100 だが同 shortlist でも上限 0.420 まで約 0.153 の差。 |
| 報告の表現 | Codex の文案を採用(朝の報告に追記済み)。表には run / モデル / 主出力列 / 全 N / shortlist 内 N / GL 不足の分母 / strict か条件付きかを明記。 |

## 2. 次の実装(この順)
1. `b1_rank_train.py` に USED 台帳(run × set: identity 数、C1/C2 群数、positive を含む群数)を出力 → Spark 同期。
2. fit pool G 72 群の特徴表(`run_fitpool_v3`、パネル pipeline run の後に自動開始)→ `rank_v6g` = rank_v4b の設定 + G 72 群(C1 と対応 C2)→ dev2(C/D/E/F/G)・A/B・パネルで登録評価器(`b1_locked_eval.py` 相当、blend21 主出力)により一対比較。
3. E0 段階比較(c2_full3 → c1_full3 → パネル)の結果を読み、D/E/F/G で E0 の候補窓・shortlist・engine・BASE・merge の挙動を確認(018)。
