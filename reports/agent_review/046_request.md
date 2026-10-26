# 046 依頼: hybrid ggt3h の確認不合格と gt3 の新しい観察、ranker の pool 拡張の事前登録

作成: 2026-10-27 00:16 JST(Claude Code)。前提: `045_decision.md`、`045_dev_result.md`、`046_prereg_hybrid.md`、`046_dev_selection.md`、`046_conf_results.md`、`047_prereg_ranker_pool.md`、`043_presub_audit.md`。

## 1. 第 3 段と hybrid
- 第 3 段(gt3b / ggt3b、親 = アナログ + DB 近縁)は開発の保護(fold-1 C2 E −0.0116)で登録どおり不採用(`045_dev_result.md`)。
- hybrid ggt3h(DB 近縁の親は GL 経路だけ)を事前登録 → 開発で選択(C3 +0.0271 vs ggt3 +0.0204、保護の最悪 −0.0069、gen_eval5 の gt3/ggt3 が第 2/3 段と全行一致)→ **fold-2 locked で一回確認: (a) +0.0008(僅かに正)、(b) C1 F −0.0126(n 50)で不合格**。
- **gt3 の新しい観察**: F(GL 無し)では ggt3h も ggt3 も gt3 の f·z の gate になるので、C1 F の −0.0126 は gt3 自体の損失(正解が 3〜13 位の 10 分子が 1 つずつ下がり、改善 0)。fold-1 locked の gt3 C1 F は −0.0022、W7 は 0。登録された gt3 の判定ではないが、GL の無い分子で f·z の gate がゆるいという弱点を示す。

## 2. gt3 の提出(10/27 枠 3)
- 全リスト parity(パネル 250 × 2 view、全 query の top-25)は PASS(`043_presub_audit.md` 追記)。上の観察を踏まえても、登録済みの判断どおり提出し、Public の読みの解釈(GL の無い分子での損失の可能性)に含める予定。異論があれば朝までにください。

## 3. ggt3(別日の候補)
- 045 の修正(deadline を上限に、manifest に記録)を入れた凍結 `experiments/b1_gen045`(pipeline a7f3f756)で、パネル 250 の parity: C2 は基準リスト・全リスト(gen_parity4)・GL 規則(gen_parity3)とも PASS、manifest に生成 GL の記録(予算・秒・有限に採点できた構造数・完了の有無・入出力 hash)。C1 は実行中。ggt3 の累積 D は追加損失なし(045_decision に記録)。
- 提出条件(045_decision): gt3 が「未確定」以上なら出す、「不採用」なら出さず点検。

## 4. ranker の pool 拡張(047 事前登録)
- rank_v4b のレシピ + fold-3a/4a の pool を fit に追加、パラメータ固定(--params_from)。開発 = fold-1/2 dev の C2 NP マクロ、保護 = fold-1/2 dev・dev2・パネル C1 clean。確認 = fold-3b/4b(新 ranker の学習に入れない)。fold-4a の GL 完了後(~00:45)に学習・評価を始める。

## 質問
1. gt3 の C1 F の観察を踏まえ、明日の gt3 提出に異論はあるか。
2. GL の無い分子の f·z gate を締める案(例: GL の無い分子では gt3 を使わない、または f·z が主出力 2 位以上のときだけ)を次の仮説にする場合の確認集合(fold-1/2 locked は開封済み、fold-3/4 の b 半分は ranker の確認に予約)。
3. 047 の設計に見落としは無いか。
