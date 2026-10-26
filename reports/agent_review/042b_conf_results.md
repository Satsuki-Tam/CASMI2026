# 042b 確認集合の結果(一回だけ読んだ、17:15 JST)と判断

確認 = conf3(D 80)、conffit(C 21 / E 100 / F 63 / G 72)、conffit2(D 150 / E 200);fold-0 表(identity 未見)、主出力 M2x + anaw0.5、b1_gen v2 ef8c856a、gen_eval2 67d113ec。表: `diag/geneval2_conf3.md`、`diag/geneval2_conffit.md`、`diag/geneval2_conffit2.md`、要約 `diag/geneval2_conf_summary.csv`(identity 単位 bootstrap 区間)。

| 規則 | C3 NP マクロ(和集合マスク) | C2 NP マクロ | C1/C2 の最悪層 | −0.01 未満の層 | 損益分岐 w3*(G を ×0.5 / ×0.25) | 判定 |
|---|---:|---:|---|---:|---|---|
| **gk3**(登録した選択) | +0.0313 | −0.0063 | conffit C の C2 −0.0127(n 21)、conffit2 E の C2 −0.0107(n 200)、conffit F の C1 −0.0103(n 26) | 3/12 | 0.139(0.244 / 0.392) | **不合格**(条件 b) |
| gt3(参考、選択されていない) | +0.0268 | −0.0039 | conffit F の C1 −0.0098 | 0/12 | 0.106(0.192 / 0.322) | 判定対象外 |
| **dv1** | 0 | **+0.0087** | conffit G の C2 −0.0069 | 0/12 | — | **合格** |

- gk3 の C3 利得は確認集合でも正(D +0.054 / +0.051、E +0.040 / +0.027、F +0.016、C 0)。損失は 3 層で −0.01 を僅かに超えた。事前登録の規則に従い、**gk3 は Public に出さない**。
- gt3 は確認集合で条件を満たす値だったが、これを見て gt3 に乗り換えると事後選択になる。**gt3 を新しい候補として登録し、生成の選択に未使用の別集合(W7 = eval_set p1 A_timstof / B_nplib、fold-0 表 = identity 未見)で一回だけ確認する**(043、結果の前に固定)。
- **dv1 は合格** → kernel v2(凍結 `experiments/b1_gen042b`、parity PASS)を作り、smoke の後、Public の一変更比較(基準 0.379、読みは 042b のまま)。
