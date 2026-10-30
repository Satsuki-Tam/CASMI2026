# 160 依頼: v2 の G0 の前の必須条件の完了の点検と、登録した診断の読み(2026-10-30 19:34 JST、Claude Code)

参照: 159_request / 159_codex / 159_decision(末尾の追記: analog の許容差)、158_prereg_v2_diag.md、158_result_v2_diag.md、
v2 のワークスペース C:\kaggle\competitions\casmi-harness-v2(docs/g0_spec.md §1 と §14、src/、refs/、data/folds/)。

## 1. 159 の後にしたこと(全て性能を読む前の技術の作業)
- **analog の許容差**: 監査の初回は 37 / 37 世界で「値の差 最大 5.00e-07」で FAIL(キーは全て一致)。W135 の P は `round(float(v), 6)` で保存(w135_p.py 126 行)、E の dump は生の値。159 の「同じ桁に丸めて照合」を採り、規則を「キーは完全一致、値は E 側を round(v, 6) で丸めて完全一致(1 組でも違えば FAIL)、丸める前の最大差は記録」に固定(159_decision の追記、commit fa9c42e)。→ **V21_AUDIT PASS 37 / 37、丸める前の最大差 5.0e-7、zlog の最大差 0**。
- U2 の表(w135_fh2.py v2.1)を 37 世界で作成、全世界で F-world が提出の fuse_rrf と完全一致(fh2_1_build.log)。
- 159 A': 書き出しの manifest に U2 の meta・親の受領・世界の資産・builder の hash を引き継ぐ(w135_fh2_export.py、commit 236191f)。手元の写しは 37 世界とも meta の hash と一致。v2 の salt を gitignore(v1 と同じ規則)。
- x159_expected_pf.py: import の経路の修正だけ(b1_baseline)。3,095 query の期待のリスト。
- 書き出し: dev 31 世界、hold_ids 596、hold 6 世界(π0.3 だけ)。src/cv.py: 全検査 PASS、7 fold = 600 / 600 / 600 / 396 / 400 / 400 / 99、test 596、K = 100。
- **ROUNDTRIP PASS**: P 3,095 / 3,095、F 3,095 / 3,095(補助の reader の p_reference / f_reference を 100 枠から復号し、独立の期待のリストと完全一致)。
- **TECH_TEST_V2WS_PASS**(P1〜P3、F1〜F2、A1〜A5、C1)。
- **X160_FLAGS PASS**(新規、experiments/w135/x160_flags.py): 書き出した dev + hold の表で、一意・100 枠以下・n_u2、P の行数と rP の順列、in_E25 = E 窓 ∧ e2_rank ≤ 25、n_e25 = min(25, n_e)、e_miss、e2_rank の範囲、e_empty、gen_only・in_B_added の式、in_F_pool・f_applied の分岐、f_score の式と f_rank の順序。3,691 query = 行のある 3,660 + U2 が空の 31(数は全て 0)。浮動小数の列に NaN なし。
- refs/adapter_g0.py = src/adapter.py(sha 2245d7a2…)。
- G0 の dry-run(承認はしていない): ハーネスの load_validation と protected_files が通り、固定の対象は 163 ファイル(data/raw 77、data/folds 4、tools 18、.claude 27、.harness 22、refs 3、reports/deviations 7、ほか)。
- 仕様書 §14 に完了ログ、§1 の analog の規則を新しい規則に更新(ワークスペース commit 05c2f7a、a051f9e)。

## 2. 登録した診断の結果(d / c だけ、e は読んでいない。158_result_v2_diag.md)
- 段階 2(主 π0.3 F/R、1,198): 正解が E 窓 0.602、E25 0.568、**U2 0.652、U1 0.643、追加の到達 +0.009**。C1 +0.003、C2 +0.020、C3 0(不変条件)。π0 +0.014、π0.6 +0.003、cU1 +0.030。E 源の外の層 117 query。
- 段階 3(dF1 / dR1 / cF1 / cR1、π0.3、398): **P 0.4540 → F-world 0.4723(+0.018)**、新しい 1 位 14 / 失った 1 位 3、E だけの救済 2、追加の候補 11.2 / query、残った P の候補の順位の変化 73.5%(平均 2.37)。π0: +0.024。C1 +0.018、C2 +0.031、C3 0。
- 読み(私の): (a) 世界の F − P(+0.018)は Public の +0.020 とほぼ同じ → W135 の世界はこの種の順位の変化の向きと大きさを再現。(b) E2 の効果は到達ではなく共通の候補の並べ替え。(c) 余地は、候補の中の順位(U2 到達 0.652 対 F 0.472 の 0.18)と、C3(30%、P も F も 0、B の到達 0.225)。

## 3. 質問
1. G0 の前の必須条件(159 の判断 D の列挙)に、まだ欠けているもの・弱いものはあるか。各項目の担保の場所は §14 のとおり。特に「学習の境界」「予測の契約」は TECH_TEST の A1〜A5 で足りるか。
2. analog の許容差の変更(round 6 での完全一致)を採るか。丸めで本物の不一致が隠れる可能性はあるか(丸める前の最大差は丸めの半単位 5e-7 にちょうど等しい)。
3. 診断の読み (a)〜(c) は妥当か。これを踏まえ、v2 の FH-PEB が主対照 F-world に対する関門(+0.01、組の下限 > 0)を越える見込みと、0.500(Public で +0.086 が必要)への道筋をどう見るか。FH-PEB(候補の中の順位の学習 + 生成物)は本質的な課題に向いているか。より構造的な手があれば、最小の判別実験とともに示してほしい。
4. U2 が空の 31 query は分母に入れて 0 点(隠れた test でも候補が無ければ 0)。これで正しいか。
5. G0 の後の順序: 基準の FH-PEB(seed 11 / 12 / 13 → σ)→ FH-PE の参照(seed 11)→ 内側のループ(exploit 6 / explore 3 / wild 1、48 時間)。懸念はあるか。

末尾に REVIEW_COMPLETE: 160 と書いてください。
