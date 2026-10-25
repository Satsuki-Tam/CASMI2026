# 021 判断: full_rk を今日開始(GO 条件 4 つを実測で確認)、ranker の一対比較は full_rk 上で旧 v4b vs 新 ranker、今夜の提出候補とは切り離す

作成: 2026-10-25 14:10 JST(Claude Code)。依頼 `021_request.md`、回答 `021_codex.md`。

## 1. 採否
| 論点 | 判断・実施 |
|---|---|
| 開始判断 | **開始する**(full_eval 終了直後に自動起動、`train_fivefold_win2.py`、tag full_rk、新規初期化、segment は 20:20 まで)。目的は「同じ FPNet で学習済み identity の独立 query(C1-seen)と未見 identity(C2)の ranker 学習例を作る」ことで、「ranker が律速と証明された」ためではない(パネル C1 は登録出力が既に 0.882、full1 で 0.926;C2 は learned ≈ blend21)。 |
| GO 条件 | (i) 除外と `Data.tr` の交差 = **0**(trainer 自身の data object から算出、`gocheck_full_rk.py`;gate の値も実測値で上書き);(ii) 新規初期化(別 run・別 tag、resume 無し);(iii) C1-seen の群を評価前に固定(`query_identity_exposure.csv`: eval_c1 seen 281 / unseen 19、W7 seen 84 / unseen 516、パネル seen 250);(iv) 20:20 自己停止・保存、20:50 以降の自動再開なし。 |
| 重複基準 | 同 adduct・5 mDa・0.95 は取得独立性の証明ではない → 「学習済み identity・query 由来の重複を除外した C1 代理」と呼ぶ。検索は identity group 全体(重複 1,430 行を除外)。 |
| ranker の行 | p1_run1 の C2(未見 C2 代理)と C1(C1-unseen)、W7/eval_c1 の C1(C1-seen;fit 群のみ、既存の fit/tune/eval を維持)。W7/eval_c1 の C2 行は記憶残存なので学習・評価から外す(trainer にその設定を追加する)。C1 比率の変化(約 46% → 約 56%)は性能を見る前に固定して記録。パネルは学習に入れない。W7 A の C1-seen は少ない(timsTOF の C1-seen を十分学習したとは言わない)。 |
| 比較 | 主比較 `full_rk + 旧 v4b` vs `full_rk + 新 ranker`(同じ特徴表・候補・forward・blend21/fallback、固定 params)。採用比較は別途凍結 M2x を対照に。`full_eval + 旧` と `full_rk + 新` の直接比較はしない。 |
| 提出時の FPNet | 学習表を作った full_rk そのもの(最後の全量再学習は必須ではない)。 |
| 今夜の提出 | 既定どおり「現行 M2x + full_eval のみ」と「M2x + pool60 のみ」を別々に評価して判断(020 の規則)。full_rk の開始はこれらの承認と結び付けない。 |
| 並行診断 | 保存済み結果から、同じ N・C2 資格・候補集合で FP / FP+prior / 固定 / learned / blend / fallback の順位変化を比べる(`fp_reach_compare` は strict C2 の外部構造資格を適用していないので、その差を ranker の損失としない;同窓の確認は identity 集合の hash まで)。 |
