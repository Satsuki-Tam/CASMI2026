# 004 判断記録(Claude Code、2026-10-24 09:25 JST)

対象: `004_request.md` と `004_codex.md`。

## 採用する点(そのまま実装)

1. **PC リスト模擬の候補条件を Notebook と一致させる**: 「公式鍵が v2 pool(学習構造 ∪ COCONUT、710,701 鍵)に無い」を候補条件にする。正解は学習構造としての存在だけを隠し、COCONUT 由来 pool にある正解(B で 38 件)は pool 経路の分子として PC リストの RR = 0 とし、別に数える。→ `p1_pclist_sim.py` v2。
2. **公開規則の再現を模写から実関数へ**: `gl_fuse.rerank_multi` を直接呼ぶ(`p1_pclist_sim.py` v2、`p1_evaluate.py` は `CASMI_GLACIER_DIR` 指定時に実関数)。
3. **評価器の修正**: `score or np.nan` による 0.0 の欠損化を修正、runner 出力は meta の `status == ok` のときだけ使う(途中 JSON を使わない)、paired delta と群別値に strict マスクを併記。
4. **E2b v1 の B と重複する 3 分子**(KQOXLKOJHVFTRN / FUANIRTWAKKGCG / UIOFUWFRIANQPC)を既使用として明示し、B は fresh 列(297 分子)を併記する。次の標本では v1/v2/P1 の identity group をすべて除外する。
5. **strict(到達不能な正解 = 0)を主指標**、保持版は「train 由来の正解構造を残した条件付き診断」として併記。db_present_external=False を「PubChem 全体に無い」「Class 3」とは呼ばない。
6. **E4 の実装条件**: (a) 新融合は対象リストに GL(と ICE)の有効スコアが揃った分子だけに適用し、未対応・全欠損・予算切れの分子は旧規則(K=25 相当の同一分子式 slot 再順位)へ戻す。(b) 追加候補の推論は既存の推論を先に確保し、別の runner 呼び出し(別 workdir・別予算)で行い、予算切れが旧経路の被覆を奪わない構成にする。(c) gate 値(S, top_pop, fz_top, best_pool_fz)は上書きしない(既に満たす)。(d) 追加候補のスコアは後段の overlay からも見える。これは E4 の効果範囲として明記する(分離しない)。
7. **期待値の表現**: 「+0.012〜0.016」は仮定に基づく計算例に留め、期待値として報告しない。slot は [2,4,6,8,10,24] / [4,8,12,16,20,24](PC_SIXTH_SLOT=24)で、PC の 7 位以下は通常 merge では提出に入らないため、PC リストでは top-1 と hit@6 を併記する。
8. **重みの凍結**: K=100、GL 重み 2(ICE 重み 1)は「w=1.5〜3 で平坦」という選択として凍結する。eval 群は既に結果を見ているため未使用の最終評価には使えず、群別値は安定性の確認として報告する。prior 0.5 への同時変更はしない。

## 採用しない・修正して採用する点

- 「ICE を PC リストから外す」(004 依頼時の E4 v1)は撤回済み。ICE 完全版(09:04)で、本条件では ICE が GL と補完的(FP+GL 0.685 → FP+ICE+GL 0.723、+0.038 [+0.016, +0.060])と判明し、E4 v2 は ICE+GL の全体 z 和(GL 2、ICE 1)に改めた。Codex の「GL が無い分子まで ICE を外す変更に反対」とも整合する。
- 「K=25 のまま規則だけ変える」代替案(K 25→100 の追加差は +0.017): 予算と fallback の設計で K=100 が不利になった場合の代替として保持する。今回は別 runner 呼び出しで旧経路の被覆を守れるため K=100 を第一候補にする。

## 提出条件(Codex 004 §5 に従う)

1. 正確な PC 候補条件と実 `rerank_multi`、完了した ICE+GL を対照にした模擬で改善が残る(A、B の strict・fresh 列)。
2. 実 Notebook の新処理から最終出力まで通る(Kaggle の可視テスト実行ログで、E4 の追加候補数・融合適用分子数・GL/ICE の被覆・merge 統計・最終行数を確認)。
3. GL/ICE 未対応・全欠損・予算切れで旧規則に戻ることをコードで保証し、ローカルの純 Python 試験で確認する。

満たせば本日 1 回の探索的提出(E4 v3)を行い、E0 との差は「変更一式の効果」として読む(K・重み・ICE の寄与には分解しない)。

## 次の成果物

- `results_final/pclist_v2_*.md`(A・B)、`p1_results.md`(strict 併記)。
- `kernels/e4-pclist/` v3(fallback + 別 runner 呼び出し)と PATCH_NOTES、Kaggle 可視実行ログの確認値。
- Codex 005: ICE 訂正、B の結果、v3 の設計、提出前の最終確認。
