# 093 事前登録: v7f + v8w7a(P)+ EA(E)の 4 構成の局所比較(Codex 092 の段取り;開発、結果の前に固定)

作成: 2026-10-27 21:51 JST(Claude Code)。
- **構成**: V = v7f(rank_v7a、gen_eval2pv の main)、V+E = その ea0.5w1(θ 0.5、w 1、登録済みの EA)、V+P = rank_v8w7a の main、V+P+E = rank_v8w7a の ea0.5w1。同じ評価器(gen_eval2pv、v7f 主出力)・同じ表・同じ query・shortlist。V / V+E は 086 の出力(e086_v7f_*)、V+P / V+P+E は同じ評価器で rank_v8w7a を一回(e093_*)。
- **集合**: 053 dev f1/f2(NP_H/X/N)、f1dev / f2dev(C〜G)、パネル(run_panel_fe)。
- **主比較(P の上に E を足す)**: PE − P。主指標 = 053 NP C2(H, N 等重み、f1/f2 block)= 076/080 と同じ集約。**次段(新しい確認集合)へ進む条件**: PE − P ≥ +0.005 かつ下限 > 0、C1 の PE − P(053 NP C1、パネル C1 clean、G C1)が ε 0.01 で非劣性(L ≥ −0.01)。
- **併記**: PE − E(E の上に P を足す)、相互作用 I = PE − P − E + V(identity ごと)、C2 で PE < P の行の有無(EA は C2 の真を罰しない構造なので負の行は実装の点検)、f1/f2 NP C2・C1、非 COCONUT。
- 新しい確認集合は fold 0/3 の未使用 identity から別に予約する(073・053 conf・083 は使用済み = 開発・stress として扱う)。

## 追記(22:29、結果の前): 計算を Spark へ移動
- 利用者の指示(22:30、Spark が空いた)で、093 の評価は **Spark で V / V+E(rank_v7a)と V+P / V+P+E(rank_v8w7a)の両方を同じ環境で再計算**する(e093s_*;PC の e086 出力は 093 には使わない)。PC で途中まで走らせた e093 は停止(結果は未読)。
