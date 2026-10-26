# 045 判断(第 3 段の結果を見る前、21:54 JST)

## ggt3(別日の比較候補、提出前の追加作業)
1. **parity の検査範囲を全 query に**: 評価器の選択・分岐から期待リストを組み立て(GL 経路 = その生成物、fallback = gt3 の生成物、棄権 = 基準リスト)、全対象 query の公式 key の順序付き top-25・ID 集合・件数・重複を比較し、全工程の非ゼロ終了を最終判定へ伝播する(`gen_parity4.py` を作る)。尺度不成立・生成 GL 全欠測・DB 3 位だけ GL 欠測・heavy filter・候補数 3 未満の例を含める。保存済みの候補・GL・基準リストを使い GPU は再実行しない。
2. **deadline を実際の上限に**: 追加 GL は remaining = deadline − 経過 − 予約(900 s)が 300 s 未満なら起動せず gt3 へ戻す、起動時の予算は min(gen_gl_budget, remaining)。修正版は別 hash で凍結し、分岐を CPU の小例で確認。
3. **manifest に実行記録**: 実効予算、経過時間、選択候補数、有限に採点できた候補・分子数、未対応・失敗・deadline 棄権、gt3 fallback 数、入力・出力 hash。
4. **比較の対象と条件(ggt3 のスコアを見る前に固定)**: 次の Public 比較では ggt3 − gt3 と ggt3 − 0.379 の両方を記録。gt3 が Public で「未確定」でも ggt3 は出してよい(gt3 と同じ基準からの一変更 + GL 段;読みは 042b と同じ境界)、gt3 が「不採用」(≤ −0.015)なら ggt3 は出さず生成全体を点検。ggt3 の dev2 での累積 D(M2x 比)を記録してから提出。
5. 確認の上積み +0.0042 は 400 分子中 8 改善・3 悪化の結果で、再現性が強く確定したとは扱わない。

## 第 3 段(045 事前登録の補足、結果の前)
- **確認の主比較 = 選択候補 − ref_star**。ref_star = 第 2 段の開発で保護合格かつ C3 最大の規則 = **ggt3(アナログ親だけ)**。確認では fold-2 locked で ggt3(`gen_eval4 --db_parents 0`)と選択候補(`--db_parents 10`)を同じ入力・同じ GL 設定で計算し、分子単位で差を取る。同じ gate の親追加前後の差(例 gt3b − gt3)は副比較として併記するだけ。確認を見て対照を切り替えない。
- 開封前の確認: (i) `gen_eval4 --db_parents 0` が修正版 gen_eval3 と main・gt3・ggt3 で一致、(ii) `--db_parents 10` を明示し成果物に記録、(iii) `--rules` は未知の規則名を拒否、(iv) 選ばれた DB 親の公式 key が view のマスク外であることを検査、(v) 親の一意な identity 数と DB 親の sim=1.0(固定の親スコア)を規則の一部として記録、(vi) 生成 → FP 上位 1/5 → GL 採点可能な上位 5 → 挿入 → 最終 RR の漏斗を記録。c3n は主実験から外す(DB 親に和集合マスクを適用していないため)。
- fold-2 locked は第 3 段で開封した後、新 ranker の確認には再利用しない。

## ranker の学習 pool
- 最初の比較: 旧 v4b の学習行 + fold-3/4 の新 pool を**固定パラメータ**(`--params_from rank_v4b/rank_results.json`)で学習した候補 vs 旧レシピの再現、同じ特徴・drop・C1 反復・blend21・fallback。新 pool は `RUN:CSV:fit` で明示的に fit に割り当てる。層 × view × fold の重みと、実際に学習に入る query group 数(正解到達・GL 被覆・C1 usable)を性能を見る前に記録。
- C1 ×3 は重みであり「identity 既見・query 未見」の学習条件ではない。その条件(query 取得群を除外し同 identity の独立取得を残すモデル)が作れれば追加学習の第一候補、できなければ未見行の追加実験として進めパネル C1 clean で保護する。
- fpnet_fold3/4 は fold-0/1/2 の identity を学習している → fold-1/2 での評価は「ranker の fit 行と評価 group が重ならない開発比較」であり、全モデル未見の独立確認とは呼ばない。各特徴の checkpoint・除外 fold・露出を台帳に記録。

## ggt3 の累積 D(提出前の記録、22:04)
- dev2 v2 の D/C2: ggt3 − anaw0.5 = **+0.000000**(変化した分子 0)、M2x 比の累積は anaw0.5 と同じ −0.022733(gt3 は −0.000738、累積 −0.023471)。→ ggt3 は D の追加損失なし。035 の例外(anaw0.5 自体の累積未達)は既知のリスクとして引き継ぐ。
