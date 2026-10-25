# 019 判断: v6g は「G 追加 + 再選択レシピ」として不採用で保存、固定パラメータの対照から積み直す。全 train FPNet は自前学習(full_eval)を手元 GPU で開始

作成: 2026-10-25 11:55 JST(Claude Code)。依頼 `019_request.md`、回答 `019_codex.md`。

## 1. 採否
| 論点 | 判断・実施 |
|---|---|
| v6g の読み | 不採用を維持。ただし v6g は num_leaves 15 / 600 rounds を再選択しており(v4b は 31 / 0.03 / 300)、「G72 追加だけ」の効果ではない。「G 追加 + 再選択したレシピ」として保存。C/C1 は事前登録の保護層ではなかった(事後に範囲を書き換えない;次回から登録)。A/C2 の悪化は eval 群だけでも −0.031 [−0.058, −0.008](Codex 再集計)。「装置特徴が無いから全体へ広がった」は仮説のまま。 |
| 固定パラメータ対照(実施中) | `b1_rank_train.py` に `--params_from`(過去モデルの選択 params + rounds を探索なしで使用)と `--c1_repeat_run RUN=K`(run ごとの C1 反復)を追加。`spark_rank_fx_chain.sh`(11:55 起動): rank_v4b_fx(再現;凍結 v4b と予測一致を検査)→ rank_v6g_fx(+G72、C1×3)→ rank_v6g_fx_w1(+G72、G の C1 だけ ×1 = 「G C1 重み低減」)→ 凍結 v4b を基準に登録評価(dev2 全層、A/B は fit/tune/eval 併記、パネル)。主比較 G/C1 blend21、保護 G/C2・C/C1・C/C2・D/C2・A/B C2 と C1・パネル両 view、ε=0.02。E/F・GL 不足群の順序付き出力不変も確認。 |
| 特徴追加の順序 | 固定設定の G72 で保護を満たさない場合のみ: (c) query 装置 + (a) 最良参照との装置関係を一ブロックで(timsTOF / Orbitrap / QTOF 等 / その他 / unknown、一致・不一致・不明・参照無しを区別、`lib_sim` を最大にした query–reference 対で定義)→ (b) 参照数は後回し(相互作用でも C2 の偏りを再学習し得る)。特徴効果の対照は「同じ G 行・重み・固定 params で装置ブロック無し/あり」。 |
| 全 train FPNet | 手元 harness cache は W7 600 分子のスペクトル除去済み(C2 用)で全 train 学習に使えない → **全 train.parquet から公開 builder で専用 run に再構築**(2,539,608 spectra を確認)。Windows 版 trainer(fork→spawn、worker ごとの memmap、SIGHUP ガード、recipe-aware gate)を公開 `train_fivefold.py` からスクリプトで生成(`make_win_trainer.py`)。`--hours` は停止条件でないため `--max_steps 82855`(fold モデルと同じ更新数)と `--segment_minutes`(20:20 自己停止)を明示。smoke 400 step で 5.84 it/s(GPU 律速)。 |

## 2. 学習データの設計(Codex の推奨からの変更点を明記)
Codex 推奨は「パネル identity group 全体 + dev2/locked2 を除外」。私は **パネルの扱いだけ変えた `full_eval`** を 11:42 に開始した:
- **除外**: パネルの query 取得(enveda-np-examples の 1,184 行)と、その他ライブラリでの重複 12 行(同 adduct、|Δprec| < 5 mDa、エントロピー類似 ≥ 0.95);dev2 v2(500 group = 'hold'、trainer が監視)、locked2 v2(500 group = 'lock'、trainer は評価しない)。
- **学習に残す**: パネル 250 分子の他ライブラリの独立スペクトル(約 55,600 行)、W7 / p1 / locked seed 4 / eval_c1 の分子(全 fold を学習 = 学習済み診断用)。
- 理由: Codex 019 の表の「C1・学習済み identity(query 取得は学習外)」= 本番 C1 の主要な追加評価、を最も本番に近い形で作るため。パネルは NP・timsTOF・Enveda 取得で、隠しクラス 1 の条件(他ライブラリに参照と学習例がある分子の、新しい timsTOF 取得)と一致する。fold-0 FPNet(パネル未見)と full_eval(パネル identity 学習済み、query 未見)をパネル C1 で比べれば、クラス 1 での記憶の利得を直接測れる。代償: パネルは FPNet 未見の評価台ではなくなる(未見の NP は dev2 の C/D/E/F、未見 timsTOF は dev2 G、最終確認は locked2)。パネル C2 view はこの FPNet では「参照を隠した学習済み identity」= 記憶の残存の診断で、C2 性能とは呼ばない。
- 学習データ: 2,524,870 training spectra(fold モデル 1,982,405 の +27%)、370,516 groups、split train 274,801 / hold 506 / lock 503 structures。gate: panel_query_rows_in_training 0、holdout_training_overlap 0。
- 提出に使う場合、この重みは自前で公開コード(公開 trainer + Windows 移植差分 + 公開 builder)から学習したもの。原著者(trainer: Dmitrii Gluzdov の fold-safe 配布、モデル/データアクセス: Ahmed Berat Özer の v4b casmi パッケージ)と移植部分を台帳に記録する。

## 3. 学習後の評価計画(学習完了 ≈16:00)
1. 同一窓 FP 比較(`fp_reach_compare.py`): fold0 / fold1(学習済み)/ 公開 full1 / full_eval を W7 A/B(学習済み)、dev2 D/E/F/G(未見)、パネル(full_eval では identity 学習済み・query 未見)で。
2. B1 特徴表を full_eval FPNet で作り直し(GL は `--reuse_complete`)、パネル C1(クラス 1 代理)と dev2 全層(未見)で、現行 ranker・blend21・fallback のまま登録評価。ranker の学習表は未見 FP 特徴で作られているので、学習済み FP 分布での生 ranker と実出力の両方を見る。
3. locked2 はこの診断では開けない。
