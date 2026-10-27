# 091 事前登録: FPNet を「spectra の merge 入力」でなく「1 本ずつの予測の logit 平均」で使う(開発の評価の前に固定)

作成: 2026-10-27 19:37 JST(Claude Code)。根拠: 089 の診断(同じ候補集合の pool 窓で、COCONUT 正解 identity の Fs − F = fold 1 +0.0112 [+0.0082, +0.0145]、fold 2 +0.0084 [+0.0054, +0.0115]、4〜8 本の単位に集中)。FPNet は学習時の入力の 7 割が単スペクトル(merge_p 0.3)なので、1 本ずつの方が分布内という機構の説明もつく。
- **変更(一つ)**: 主出力 v7f(rank_v7a_pc、固定則・保険・fallback は不変)の FP 列を、同じ checkpoint・同じ query spectra(b1_features と同じ選択)での **単スペクトル logit の平均(極性群は本数で重み付け)** に置き換える(fp_mean_score.py → gen_eval2fd --fp_override)。候補行は表に保存された shortlist の和集合に固定(本番では shortlist も変わり得る = 未評価の近似)。窓内順位の特徴 fp_rank_window は「shortlist 内の新しい順位に、表の窓内順位を昇順に割り当てる」近似。ranker は merge 入力の特徴で学習済み(分布のずれは未補正)。
- **対照**: 同じ評価器・同じ ranker の override 無しの main(090 の R0 = 本番 merge 入力)。
- **主指標**: f1/f2 dev の NP 層(C/D/E/F、fold は等重み block)の strict C2 の Δ。**副指標**: 053 dev C2(NP_H/X/N)、正解 COCONUT / 非 COCONUT、スペクトル本数(1 / 2〜3 / 4+)、GL 経路 / fallback。
- **保護(非劣性の確認 L ≥ −0.01)**: G C1(f1/f2)、053 NP C1、パネル C1 clean。
- **本番実装へ進む条件**: 主指標 ≥ **+0.003**(変更の費用がほぼ無く原理的な修正のため、通常の +0.005 より低い;理由をここに固定)、fold 1・2 とも > 0、結合の 95% 下限 > 0、保護すべて非劣性。満たせば b1_pipeline に --fp_mode mean を足し、評価器との parity → kernel → Public の一変更比較(対照 v7f 0.390)の候補にする。満たさなければ記録のみ。
- 一つの checkpoint 対応: run_np053_f1dev / run_f1dev ← fpnet_fold1(1739d568)、run_np053_f2dev / run_f2dev ← fpnet_fold2(257062cb)、run_panel_fe / run_p2dev_fe ← full_eval(5b8d1c31)。fp_mean_score の merge 再計算は表の fp と照合する(parity)。

## 追記(19:39、結果未読): 環境差の対照を主比較にする
- fp_mean_score の merge 再計算と表の fp の一致(np053 f1dev): 分子の 314/319 で相対差の中央値 < 0.05(全体の中央値 0.003)、5 分子で 0.05〜0.26(bf16 と Spark/PC の FPNet の数値差;値の絶対差は 1 前後)。表の fp(Spark で作った表を含む)を対照にすると環境差が混ざる。
- **主比較を「同じ PC で再計算した merge 入力(fp_m、窓内順位も同じ近似で移す)」対「Fs(fp_s)」に変更**(pc_fpmean091m.sh で fp_m の override の pass を追加;評価器・ranker・候補行は同一)。判定の指標・閾値・保護は登録どおりで、Δ = (fp_s の main) − (fp_m の main)。表の main(override 無し)との差は環境差を含む参考として併記。

## 追記(19:50、結果未読;Codex 091)
- 閾値 +0.003 の理由を訂正: 「費用が無い原理的な修正」ではなく **「追加の実装検証へ進むための、開発費用の低さを見込んだ基準」**(FPNet の forward は行数分に増える;merge 入力も学習で使われており Fs が必ず正しいとは言えない)。
- 091 は 089 と identity が重なる(fold 1/2 の COCONUT identity)ので **独立な確認ではなく、探索で見つけた集約の「主出力への移り方」を測る開発比較**。089 の不合格は救済しない。
- **段階**: ① 本比較(同じ PC・固定候補行、merge 対照)→ ② 出力の対応の点検(表 → PC merge → PC Fs の二つの差;各極性 1 本以下の分子は Fs = merge で差 0 のはず)→ ③ **窓全体で F と Fs を採点した正確な窓内順位**で再評価(順位の割当て近似を外す)→ ④ **Fs で shortlist を作り直した全体比較**(新候補の GL も定義どおり、到達の 4 区分を全分母で)→ ⑤ 本番 parity と実行費用。①の合格だけで kernel へ進まない。
- 報告の層を追加: 選択後の正 / 負イオンの本数、極性内の adduct 種数(診断)。
