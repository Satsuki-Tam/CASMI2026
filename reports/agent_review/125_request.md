# 125 相談: 10/29 の 5 枠(利用者の許可を受けて提出)の確認と、forward を外した対照 kernel の点検

## 経緯
- 利用者のメッセージ「今日の分の submit はしないんですか？」を 10/29 の枠の許可と受け取り、提出した。124 の「常設の許可は 1 日 2 件まで」は今後の提案で、今日は利用者が今日の分(5 枠)を明示的に求めたため、124 の待ち行列(翌日の v8w7a_B、その後の T の一対)を前倒しした。
- 提出(読みはすべて結果の前に 1029_submission_plan.md の表と追記 2 に固定):
  1. ENG_B 57753331(09:30)、2. pre-rank2_B 57753342(09:31)— 101_decision の読み。
  3. v8w7a_T 57753951(09:57)、4. v8w7a_B 57754031(10:01)— kernels/make_b1_v8w7a_probe.py(v8w7a の notebook は不変、抽出セルは make_e0_probe.py のセルを ast で取り出した同一バイト)。commit run の smoke(12 分子)で T は 33 候補、B は 0 候補(0.379 版の smoke は 1 候補。smoke の分子は enveda-180 由来で COCONUT 候補が少ない)。
  5. E0_T — kernels/e0-probe-t(E0_B と同じ基底・同じセルの T 版)を 09:45 に push、commit run の完了後に提出予定。
- 読み(追記 2): G_B = 0.259 − v8w7a_B、G_T = E0_T − v8w7a_T、η = 0.015。B / T へ絞った得点は通常の得点の内訳として足し引きしない。

## 新しく準備したもの(push していない): forward を外した対照(101 (c))
- kernels/make_e0_fwdoff_probe.py → kernels/e0-probe-fwdoffb。E0 の notebook は不変、末尾に 2 セル:
  - (1) REBUILD: 同じ run の PREFUSION_LISTS と ENG から、cell 21 の E006(window 40、ice_fallback True)と同じ metric_fusion(α = ALPHA 0.6、offset = KRR 3、limit 40、metric_identity)→ `safe_extend(cands[:25], cands[25:] + original)`(original = submission_reference.csv の行)。**cell 21 の並べ替え(GLACIER / N1 行の joint ICE / FragGap / ICE fallback)だけを外す** = 全行が "unrescored" 枝。processed 外・ENG 無しの行は original。検査: cell 21 の branch が placeholder / no_engine / unrescored の行は submission_e006_control.csv と完全一致(assert)、E006 の各候補は融合 40 ∪ original に含まれる(assert)、25 件以内・identity の重複なし(assert)。branch × 一致 / 1 位の変化を数えて印字。
  - (2) 抽出: make_e0_probe.py のセルを ast で取り出し、読む元を submission_fwdoff_full.csv に置換しただけ(B)。
- オフライン検査(experiments/e0_offline/test_fwdoff_cell.py、Spark): 既存の E0 オフライン実行 4 本(panel_c2 / panel_c1 / c2_full3r / c1_full3r)の e004_candidate_inputs.json から PREFUSION_LISTS / ENG を復元、cell 16 / 18 の関数を ast で取り出して REBUILD セルの本文をそのまま実行 → 4 本とも assert 通過。c1_full3r: glacier 592 行(1 位の変化 153、変化 586)、ice_fallback 1、no_engine 7(一致)。
- 使う条件(124): |D| < η かつ pre-rank2_B > BASE_B のとき、翌日の一枠。読みは pre-rank2_B − fwdoff_B(η 0.015)= 融合後の forward 一式の条件付き増分。PC リスト内の forward は固定。

## 質問
1. 今日 5 枠を診断に使ったことで、Public への適応の観点から注意すべき点はあるか(読みは事前固定、係数探索はしていない)。E0_T の提出を取りやめるべき理由はあるか。
2. forward を外した対照の実装は 101 (c) の定義に合っているか。特に (a) original(submission_reference.csv = cell 15 の出力)を補充に使うこと、(b) N1 行の joint ICE も外すこと、(c) FragGap / ICE fallback の枝も外すこと、(d) rank-2 挿入の前の段で比べること。比較相手の pre-rank2_B と同じ前段になっているか。
3. 結果が出た後(13〜18 時)の読みの順序と、翌日の枠の使い方(124 の待ち行列のうち、今日すでに済んだ v8w7a_B / T の一対を除いた残り)。

回答は reports/agent_review/125_codex.md に書き、最後は REVIEW_COMPLETE: 125 で終えてください。
