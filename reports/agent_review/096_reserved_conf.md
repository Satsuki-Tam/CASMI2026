# 096 予約: 095(B 群専用 ranker、位置を保つ並べ替え)の確認集合 — fold 0 の COCONUT 正解 800 分子(作成のみ、未開封)

作成: 2026-10-27 23:32 JST(Claude Code)。
- 選択: p3_select_np.py(Spark)、fold 0、seed 960、NP_H 600 / NP_N 200(NP_X は 0)、MSG に無い、正解 = COCONUT 構造。**除外 = experiments/b1_baseline 以下の既存の全選択 CSV(38 ファイル:学習 pool・開発・確認・073・083 を含む)とパネル**の identity group。fold 3 の COCONUT 正解は残り 8 で尽きている。fold 0 の候補: NP_H 624、NP_N 280。出力 np096_f0conf/p2_molecules.csv(800)。spare 90 は使わない。
- FPNet: 公開 fold-safe fpnet_fold0(fold 0 の identity に未見)。ranker の学習(v3 = fold 0 の別 identity、pool = fold 3/4)とは identity group が素。
- 表: Spark で b1_features(--k 100 --k_fpp 200 --k_pop 50、gen dump つき)+ GLACIER(NP_H、NP_N)、run_np096_f0conf。表が出来ても主出力・差分は計算しない。
- **用途: 095 の候補(rank_b095 + 位置を保つ並べ替え、GL 経路のみ)の確認に一回だけ**。条件(結果の前に固定): 主 = NP_H C2(600、strict)の bpp − main ≥ +0.005 かつ identity bootstrap の下限 > 0;NP_N は GL 経路の分子だけが変わり得る(診断);点検 = 正解が B でない行と C1 の差 0。
- 093 の確認には使わない(093 用は別に予約する;fold 0 の COCONUT 正解はほぼ使い切ったので、093 の C1 費用の層の設計と合わせて Codex と相談)。

## 予約の変更(2026-10-28 00:07、未開封のまま;Codex 097)
- **再配分**: 予約 CSV(sha cd6ccbf2)の NP_H 600 を **ファイル順(selector の seed 960 の並び)の先頭 400 = 095 の確認**(np096_conf095、sha 1122fc7a)、**残り NP_H 200 + NP_N 200 = 093 の確認の C2 部分**(np096_conf093、sha f70fa504)に分ける(identity group の重複 0)。spare(H12 / N77 / X1)は使わない。表(run_np096_f0conf)は 800 分子で作成中のまま、評価時に各 CSV の分子だけを読む。
- **095 の確認条件(変更)**: NP_N は GL が無く並べ替えが構造上働かないので、**NP_H だけで bpp − main ≥ +0.010(H/N 等重みの +0.005 に相当)かつ identity bootstrap の下限 > 0**。H/N 等重みの値は併記しない(この割当てに NP_N は無い)。点検: 正解が B でない行と C1 の差 0(順序の位置でも確認)。件数 400 で判定できない場合は保留。
- **093 の確認条件**: C2 = np096_conf093 の H/N 等重みで PE − P ≥ +0.005 かつ下限 > 0;C1 費用 = 別に予約する新しい fold 0 の G 型 400 と NP の C/E/F 400(C200 / E100 / F100)で、それぞれ PE − P の下限 ≥ −0.01(非劣性)。093 の開発の関門を通らなければ開かない。
- **alias の集約**: 096 の表は開発表(053 dev 等)と同じ和集合の集約(--alias_perview なし)で作る = 095 を開発した条件と同じ。本番 pipeline は view ごとの集約(082b で差は稀な alias 事例に限ると確認済み)— 限界として記録。
- truth_B の列(評価器)は「shortlist の B 候補の中に真がある」= 到達込みの flag。B 内 MRR は到達した行に条件付きの値として読む。
