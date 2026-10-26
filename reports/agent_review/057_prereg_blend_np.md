# 057 事前登録: NP 化学での blend の重み(GL と prior の比重)

作成: 2026-10-27 02:42 JST(結果の読み出し前)。根拠: 052(NP の正解では GLACIER が弱く prior が強い;開発集合の NP 層は正解の 2/3 が非 NP)、Codex 049(主対象 = 未見 NP クラス 2)。

## 候補(主出力 anaw0.5 の blend だけを変える;ranker・候補・analog は不変)
- blend = a·z(learned) + z(S)、S = z(FP) + wg·z(GL) + wp·pop。登録の現行 = (a, wg, wp) = (2, 2, 0.5)。
- 格子: (2,1,0.5) (2,0.5,0.5) (2,1,1) (2,2,1) (3,2,0.5) (1,1,0.5) (2,0.5,1)。評価器 `gen_eval2v.py`(gen_eval2 の複製 + v<a:wg:wp> 列、main は gen_eval2 と一致を確認)。

## 開発(選択)
- 開発集合: fold-1/2 dev(既存 run_f1dev/run_f2dev、未見 FPNet)の全層、dev2(full_eval、未見)、パネル(既見)、**053 の NP 正解 dev(f1/f2 各 320、表の完成後)**。
- 主指標: **NP 正解(COCONUT 構造)の C2 MRR の Δ**(053 dev の NP_H/X/N 等重みと、f1/f2 dev の COCONUT 正解分子のプール、の平均)。
- 保護: 非 NP 正解の C2(f1/f2 dev の COCONUT 外の正解)、NP C1(053 dev と f1/f2 dev)、パネル C1/C2 で、プールした paired bootstrap の有意な害(95% 上限 < 0)が無いこと。G は stress として記録。
- 選択: 主指標が +0.01 以上で保護合格の中で最大の一つ。
## 確認
- 053 の NP 正解 conf(f1/f2 各 320、閉じたまま)で一回: 主指標 Δ > 0 かつ保護合格(同じ規則)。合格すれば pipeline の blend 重みの一変更として Public 比較の候補。
