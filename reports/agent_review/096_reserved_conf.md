# 096 予約: 095(B 群専用 ranker、位置を保つ並べ替え)の確認集合 — fold 0 の COCONUT 正解 800 分子(作成のみ、未開封)

作成: 2026-10-27 23:32 JST(Claude Code)。
- 選択: p3_select_np.py(Spark)、fold 0、seed 960、NP_H 600 / NP_N 200(NP_X は 0)、MSG に無い、正解 = COCONUT 構造。**除外 = experiments/b1_baseline 以下の既存の全選択 CSV(38 ファイル:学習 pool・開発・確認・073・083 を含む)とパネル**の identity group。fold 3 の COCONUT 正解は残り 8 で尽きている。fold 0 の候補: NP_H 624、NP_N 280。出力 np096_f0conf/p2_molecules.csv(800)。spare 90 は使わない。
- FPNet: 公開 fold-safe fpnet_fold0(fold 0 の identity に未見)。ranker の学習(v3 = fold 0 の別 identity、pool = fold 3/4)とは identity group が素。
- 表: Spark で b1_features(--k 100 --k_fpp 200 --k_pop 50、gen dump つき)+ GLACIER(NP_H、NP_N)、run_np096_f0conf。表が出来ても主出力・差分は計算しない。
- **用途: 095 の候補(rank_b095 + 位置を保つ並べ替え、GL 経路のみ)の確認に一回だけ**。条件(結果の前に固定): 主 = NP_H C2(600、strict)の bpp − main ≥ +0.005 かつ identity bootstrap の下限 > 0;NP_N は GL 経路の分子だけが変わり得る(診断);点検 = 正解が B でない行と C1 の差 0。
- 093 の確認には使わない(093 用は別に予約する;fold 0 の COCONUT 正解はほぼ使い切ったので、093 の C1 費用の層の設計と合わせて Codex と相談)。
