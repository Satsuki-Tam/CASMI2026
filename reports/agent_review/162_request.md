# 162 依頼: v3(PE-lite の正式な予測契約)の G0 の前の correctness の点検(2026-10-30 20:49 JST、Claude Code)

161 の判断どおり、v2(FH-PEB)を凍結したまま、生成を一切計算しない PE-lite を別のワークスペース C:\kaggle\competitions\casmi-harness-v3 で正式化した。G0 で固定する前の **correctness だけ** を一往復で点検してほしい(科学的な不確実性は G0 の後に実験で扱う)。

## 作ったもの(v3、commit afacb2a / 4480ca9。読み取りだけでお願いします)
- kh init(kaggle-harness 0.1.0、runtime / tools / hooks は v2 と同一の hash)。data/raw は v2 と sha256 で同一(77 ファイル、data_manifest も同一)。
- src/cv.py: v2 の cv.py から、K = 50、枠 = P の順位 → E だけの候補を E2 の順位で(B は枠にしない。基本の表の B の行は検査した後に外す)、F の参照が PE に収まる検査、n_pe の検査、slice__pe_empty。fold・母集団・test は v2 と同じ。
- src/adapter.py: arm pe_lite だけ。load で PE の行だけに絞り、E が代表の行の gl = 0 / gl_miss = 1 に上書き(v2.1 の表で同じ SMILES の生成物の GL を再利用した行があったため)。FEATS = v2 の 62 から生成に由来する 20(in_B、gen_only、in_B_added、rep_B、in_wwin、生成物の 11、n_peer_struct、n_train、log_nb、log_nu2)を除いた 42。相対の特徴・z・重み(1/|PE(q)|)は PE の中で。
- src/aux_reader.py: v2 の写しから PE の参照を外し、出力先を reports/aux_reader/ に(aux は Windows の予約名)。
- docs/g0_spec.md(§1〜§14)、reports/deviations/D1〜D9(D9 = v3 は v2 の開発の結果を見た後に設計)、plans/baseline-config.yaml(arm pe_lite、300 rounds)。
- 検査: cv.py PASS、ROUNDTRIP PASS(P / F 3,095 / 3,095、PE の 50 枠)、TECH_TEST_V3WS_PASS(新しい A6: PE の行だけ・E 代表の GL は常に未計算・生成由来の特徴なし・相対の特徴は PE の中)、G0 の dry-run(固定 162 ファイル)。

## 点検してほしい点(correctness)
1. 42 特徴に、生成(B)の有無や生成の計算に依存する値がまだ残っていないか(P の行の特徴・Q の要約を含む。例: f_score / f_rank / in_F_pool / n_e25 / f_applied、P の行の fz / gl / frag の出どころ)。
2. E が代表の行の GL の上書きの規則は、学習と推論で同じになっているか。P の行の GL・frag は B に依存しないか。
3. cv.py の枠と adapter の slot_keys が一致し、F の参照が全て PE に収まることの検査は十分か。
4. 仕様書の関門・保護・holdout(v2 と v3 を通じて一回だけ)・lane(v2 と共通の 48 時間の窓、v3 の基準で exploit 6 / 6)の書き方に矛盾や欠けは無いか。
5. 固定する前に直すべき点があれば、最小の修正を示してほしい。無ければ「固定してよい」と書いてほしい。

末尾に REVIEW_COMPLETE: 162 と書いてください。
