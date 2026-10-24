# 006 判断記録(Claude Code、2026-10-24 12:45 JST)

対象: `006_request.md` と `006_codex.md`。

## 採用(実装に反映、`b1_features.py` v2 ほか)

1. **C1/C2 別の shortlist**: 参照枠を各視点の類似度(lib_c1 / lib_c2)で別に作り、保存表は和集合(順方向モデルは 1 回)+ 所属フラグ `in_short_c1` / `in_short_c2`。評価・学習はその視点の所属行だけを使い、z もその集合で計算する。C2 で正解が C1 の参照枠からだけ入っていた経路(B 7 分子、MRR 寄与 0.0097)を塞ぐ。
2. **B1 自身の窓による到達フラグ** `reach_external_b1`(正解の raw 鍵またはタウトマー別名が tier/COCONUT 出典の候補として窓内にある)を strict マスクに使う。選定時の `window_external` は参考値に降格。
3. **重複参照の 2 段階**: 確実な複製(同アダクト・|Δprec| < 5 mDa・cleaned ピーク列が一致)は常に除外。疑い(|Δprec| < 5 mDa・類似度 ≥ 0.98)は主類似度から除外し、保持版 `lib_sim_*_keepdup` も併記して結論の依存を調べる。非正解側で消した参照数も記録。MAX_REF(24)は分類の後に適用。C1 の分母は「処理後に使える参照が残る分子」`c1_usable`。
4. **出典なし候補の除去**(C2 視点)は評価と学習の両方で適用(学習側は実装済み、評価側に追加)。空候補の分子は分母に残して 0。paired delta は strict でも報告。fit/tune/eval 間の identity group 共有を assert。
5. **λ の分離**: shortlist は 0.15(評価した条件)、最終融合は 0.5。提出パイプラインも同じ分離。query 選択(アダクト round-robin、最大 8)と候補源(tier + pool + prvsiyan COCONUT)を評価と提出で揃える(Kaggle カーネルに `prvsiyan/coconut-casmi26-candidates` を追加)。
6. **アダクト窓をまたぐ SMILES の重複を指紋計算の前に除去**(同じ構造を複数回指紋化していた)。
7. **eval_set は開発集合**(固定規則の比較と prior 選択に使った)。採用判断は別途凍結する locked eval(A/B 各 300、未使用 group)で 1 回だけ行う。LambdaRank の fit = P1 600 分子 + eval_set の fit 群、tune = eval_set の tune 群。
8. **参照優先規則**: 固定基準は「参照優先なし、prior 0.5」。ただし Class 1 対応を省く判断ではない。重複除外後の同じ候補集合で S(0.5) / 参照のみ / 固定参照規則 / LambdaRank を並べ、「C1 で参照が正解首位だった分子を融合が落とした件数」「C2 で誤った高類似参照を昇格させた件数」を別に出す。
9. **prior 0.5**: A は paired 区間が 0 を含む(+0.007 [−0.005, +0.019])、B は有意(+0.034 [+0.018, +0.051])。「A/B とも同方向」までの表現にし、A で安定した改善とは言わない。
10. **時間予算の優先順位**: 段階別時間 → 窓の重複除去(本件で実装) → 部分指紋の pass-1 → forward の K 縮小/優先順位 → ppm 窓縮小(最後)。Kaggle の実測が取れたら(認証復旧後)段階別に記録。

## 保留

- 「確実な複製」の判定に accession/USI は無いためピーク列一致で代用。装置・CE・アダクトで層別した過剰除外の確認は、重複除外版の結果が出た後に行う。
- 一致ピーク数・説明強度・複数 query 間の整合の特徴は次段。
- 公式 scorer(`src/metric.py`)で最終順位を採点する検証は、B1 の提出前に組み込む。

## 次の一巡

Spark で `eval_set`、`eval_c1`、P1 600 分子の特徴表を v2 コードで再構築 → GL/ICE → 固定規則(視点別 shortlist・strict)と LambdaRank(fit = P1 + eval_set fit、tune = eval_set tune)を同じ候補集合で比較 → locked eval の凍結 → B1 Notebook v2(λ 分離、COCONUT 追加、学習融合同梱)の push(Kaggle 認証復旧後)。
