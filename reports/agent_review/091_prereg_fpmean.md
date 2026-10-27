# 091 事前登録: FPNet を「spectra の merge 入力」でなく「1 本ずつの予測の logit 平均」で使う(開発の評価の前に固定)

作成: 2026-10-27 19:37 JST(Claude Code)。根拠: 089 の診断(同じ候補集合の pool 窓で、COCONUT 正解 identity の Fs − F = fold 1 +0.0112 [+0.0082, +0.0145]、fold 2 +0.0084 [+0.0054, +0.0115]、4〜8 本の単位に集中)。FPNet は学習時の入力の 7 割が単スペクトル(merge_p 0.3)なので、1 本ずつの方が分布内という機構の説明もつく。
- **変更(一つ)**: 主出力 v7f(rank_v7a_pc、固定則・保険・fallback は不変)の FP 列を、同じ checkpoint・同じ query spectra(b1_features と同じ選択)での **単スペクトル logit の平均(極性群は本数で重み付け)** に置き換える(fp_mean_score.py → gen_eval2fd --fp_override)。候補行は表に保存された shortlist の和集合に固定(本番では shortlist も変わり得る = 未評価の近似)。窓内順位の特徴 fp_rank_window は「shortlist 内の新しい順位に、表の窓内順位を昇順に割り当てる」近似。ranker は merge 入力の特徴で学習済み(分布のずれは未補正)。
- **対照**: 同じ評価器・同じ ranker の override 無しの main(090 の R0 = 本番 merge 入力)。
- **主指標**: f1/f2 dev の NP 層(C/D/E/F、fold は等重み block)の strict C2 の Δ。**副指標**: 053 dev C2(NP_H/X/N)、正解 COCONUT / 非 COCONUT、スペクトル本数(1 / 2〜3 / 4+)、GL 経路 / fallback。
- **保護(非劣性の確認 L ≥ −0.01)**: G C1(f1/f2)、053 NP C1、パネル C1 clean。
- **本番実装へ進む条件**: 主指標 ≥ **+0.003**(変更の費用がほぼ無く原理的な修正のため、通常の +0.005 より低い;理由をここに固定)、fold 1・2 とも > 0、結合の 95% 下限 > 0、保護すべて非劣性。満たせば b1_pipeline に --fp_mode mean を足し、評価器との parity → kernel → Public の一変更比較(対照 v7f 0.390)の候補にする。満たさなければ記録のみ。
- 一つの checkpoint 対応: run_np053_f1dev / run_f1dev ← fpnet_fold1(1739d568)、run_np053_f2dev / run_f2dev ← fpnet_fold2(257062cb)、run_panel_fe / run_p2dev_fe ← full_eval(5b8d1c31)。fp_mean_score の merge 再計算は表の fp と照合する(parity)。
