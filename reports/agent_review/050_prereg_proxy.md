# 050 事前登録: forward-model proxy(GLACIER の証拠を持つ分子を増やす)の未見 identity での測定

作成: 2026-10-27 02:05 JST(結果を見る前)。背景: `049_request.md` §2(先頭系譜で再現性の高かった段 = forward の被覆拡大、討論 752356)。B1 は `b1_common.forward_proxies` を実装済みだが、評価はパネル(既見)だけで「効果なし」だった。未見の F/E 層では未測定。

## 変更(一つ)
- 主出力(rank_v4b blend21 + GL-cover fallback + anaw0.5、現行の作業用基準 0.379 と同じ規則)はそのまま。**covered な正イオン([M+H]+ / [M+Na]+)を持たない分子だけ**、query を [M+H]+ の proxy に写して GLACIER を掛ける。
  - arm a: [M+NH4]+ → [M+H]+(前駆体を移し、新前駆体 −1.5 未満の断片だけ)、[M-H2O+H]+ → [M+H]+(= pipeline の `--adduct_proxy`)。
  - arm n: arm a + 負イオン → 正の軸(断片 +2 proton、粗い近似 = `--neg_proxy`)。
- proxy を得た分子は GL 経路(learned blend)に入り、得なかった分子・covered な分子は不変(機械的に確認: 原 GL のある分子への上書きは assert で禁止)。

## 測定(`spark/jobs/spark_px050_dev.sh`)
- 集合: fold-1 dev / fold-2 dev(fpnet_fold1/2、identity 未見)、dev2(full_eval、identity 未見)、パネル 250(既見、stress)。層は E_np_negonly、F_np_uncovered(パネルは全体、変わるのは非 covered の分子だけ)。
- 表は再計算しない(保存済み runner 入力に proxy を足し、その分子だけ GL を実行して run の複製に合成)。基準も同じコードで再評価(`diag/px050_<set>_base`)。

## 判定(開発)
- 主指標: **arm a は F の C2、arm n は E の C2**(fold-1 と fold-2 の等重み平均の Δ = arm − base)。dev2 は補助(同じ向きか)。
- 保護: 各 fold の E/F の C1 で Δ ≥ −0.01、arm a の E は不変であること(E は正イオンを持たないので arm a では proxy が付かない;付いたら実装の誤り)。パネルは非 covered 分子の C1/C2 を記録(n 小、拘束しない)。
- 開発で選ぶ条件: 主指標 ≥ +0.010 かつ保護合格。両 arm が合格した場合は別々の候補として扱う(n は E と F の両方を変えるので、F への上乗せは a と n の F の差で記録)。
- 確認: 合格した arm だけ、結果を見る前に作る新しい E/F 確認集合(fold-1/2 の未使用 identity、各 fold の fold-safe FPNet、層別の件数は選択時に固定)で一回。確認の合格 = 主指標 Δ > 0 かつ保護合格。
- 合格した場合の扱い: pipeline の既存フラグ(`--adduct_proxy`、arm n なら `--neg_proxy` も)の一変更として提出候補にする(GL 予算・deadline の確認と parity を経て)。

## 追記(2026-10-27 03:15、確認集合の割り当て — 確認の結果は未読)
- 新しい E/F 確認集合を fold-1/2 の未使用 identity から作ったところ、**F 層は fold-1 で 0 分子**(登録の F の定義 = NP ライブラリの正イオン非対応 query は使い切り)。E は fold-1 で 200 分子(pxconf_f1、表と GL 作成済み、未評価)。
- そこで確認は次の割り当てにする(結果の前に固定): **arm a = 053 の NP 正解 conf の NP_X 層**(fold-1 60 + fold-2 60、NP の化学で隠しに最も近い、未開封)、**arm n = pxconf の E 層**(fold-1/2)。053 conf の NP_H 層は 057(blend)の確認に割り当て、NP_X / NP_N 層は 057 の確認に使わない。
- 確認の判定(登録どおり): 主指標 Δ > 0(arm a は NP_X の C2、block = fold-1/2 の等重み)かつ保護(C1 Δ ≥ −0.01、各 fold)。049b の三状態は併記。

## 追記(2026-10-27 04:18、確認の監査 — MRR は未読)
- fold-1 conf の NP_X: 60 分子、proxy が付いたのは 59(NH4 303 スペクトル、水脱離 11)、C2 で正解が候補に入るのは 60/60、**C1 usable は 3 分子のみ** → 確認集合では C1 の保護は実質測れない(三状態では未確定になる)。保護の根拠は開発の F C1(+0.041 / +0.106)とパネル(px050 の panel arm a、計算中)の診断として報告し、「主対象の held-out 確認 + 既知集合での保護診断」と範囲を明記する(Codex 049b/053)。
