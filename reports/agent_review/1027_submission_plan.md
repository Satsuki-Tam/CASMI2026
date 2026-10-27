# 10/27 の提出(09:00 JST 以降、039 / 043 / 043_presub_audit の判断どおり)

基準: 57650023(FE + anaw0.5)= 0.379 の同一凍結出力。三つとも一変更比較(相互に独立な再現ではない)、+0.008 / −0.015 は運用上の境界。全結果を記録し、先に返った候補で後続の判定基準を変えない。

| 枠 | kernel | 読み(結果前に固定済み) |
|---|---|---|
| 1 | hayatetaf/casmi26-b1-fpnet-v7f v1 | 038/037b の分岐 B: ≥ +0.008 で anaw0.5 を置き換え、−0.015〜+0.008 は維持、≤ −0.015 は維持して点検 |
| 2 | hayatetaf/casmi26-b1-probe-prior(smoke 済み版) | 039 の限定診断: ≥ 0.25 prior 中心の順位にも有用な信号 / ≤ 0.10 この方策の MRR が低い(原因未分解、LAM は変えない)/ 中間は記録のみ |
| 3 | hayatetaf/casmi26-b1-fpnet-gt3 v1 | 042b/043: ≥ +0.008 暫定採用の資格(累積 D は 043_decision で受容済み)/ −0.015〜+0.008 未確定 / ≤ −0.015 不採用 |
| 4 | hayatetaf/casmi26-e0-probe-b v1 | 055(診断の一対、Codex 049): E0 の最終リストを B 群(COCONUT かつ非 train)に絞る |
| 5 | hayatetaf/casmi26-b1-probe-b379 v1 | 055: 現行 0.379 の B1 を同じ規則で B 群に絞る。読み = Δ = E0_B − B1_B(055_prereg_probe_pair.md) |

コマンド(version: v7f v1、probe-prior v1、gt3 v1 — いずれも smoke 済みの版):
```
kaggle competitions submit enveda-CASMI26-molecule-id-mass-spectra -k hayatetaf/casmi26-b1-fpnet-v7f -v 1 -f submission.csv -m "Codex 038/039 one-change comparison vs 0.379 (FE + anaw0.5): v7f = analog-feature ranker rank_v7a (600 trees) on GL-covered molecules, insurance + 1 z(ap) + 1 z(MetFrag-lite) on GL-fallback; pipeline 6e3b4d04; branch-B reading fixed in 038_decision"
kaggle competitions submit enveda-CASMI26-molecule-id-mass-spectra -k hayatetaf/casmi26-b1-probe-prior -v 1 -f submission.csv -m "DIAGNOSTIC (Codex 039): working-baseline shortlist (full_eval, k_fpp 200, k_pop 50) ordered by the prior alone (FP tie-break), no forward models; measures this fixed policy only"
kaggle competitions submit enveda-CASMI26-molecule-id-mass-spectra -k hayatetaf/casmi26-b1-fpnet-gt3 -v 1 -f submission.csv -m "Codex 043 one-change comparison vs 0.379 (FE + anaw0.5): + one generated analog derivative (own b1_gen v2 ef8c856a; top-10 analog parents, 1-2 biosynthetic edits, query-derived mass, raw-window absence) at rank 3 if its FPNet f.z >= the main rank-3 f.z; pipeline 8d0c415e"
```

(02:37 追加、Codex 049 Q1)枠 4・5 のコマンド(commit run の完了を確認してから):
```
kaggle competitions submit enveda-CASMI26-molecule-id-mass-spectra -k hayatetaf/casmi26-e0-probe-b -v 1 -f submission.csv -m "DIAGNOSTIC pair (Codex 049, 055): E0 (0.464 reproduction) final list restricted to group B = COCONUT and not training (official key; T-priority exclusive), order kept, no refill, empty -> CCO; not a method candidate"
kaggle competitions submit enveda-CASMI26-molecule-id-mass-spectra -k hayatetaf/casmi26-b1-probe-b379 -v 1 -f submission.csv -m "DIAGNOSTIC pair (Codex 049, 055): current B1 0.379 (57650023 kernel) final list restricted to group B with the identical appended cell; not a method candidate"
```

## 提出の記録(09:01〜09:03 JST、`1027_submit.sh`)
| 枠 | kernel | ref |
|---|---|---|
| 1 | casmi26-b1-fpnet-v7f v1 | 57681793 |
| 2 | casmi26-b1-probe-prior v1 | 57681864 |
| 3 | casmi26-b1-fpnet-gt3 v1 | 57681941 |
| 4 | casmi26-e0-probe-b v1 | 57682008 |
| 5 | casmi26-b1-probe-b379 v1 | 57682054 |

## 結果(固定した読みで記録)
| 枠 | ref | Public | 読み |
|---|---|---:|---|
| 2 prior-only probe | 57681864 | **0.135** | 039 の読みで中間(0.10〜0.25)→ 数値を診断として残すだけ。参考: 全体の 0.379 に対し prior だけの順位は 36%。パネル(prior だけで 7 割が 1 位)より隠しの正解は有名でない側(開発の NP 集合に近い)と整合 — 有名さの比率の推定には使わない(11:37 記録) |
| 5 B1_B probe | 57682054 | **0.204** | 055: E0_B が出てから Δ = E0_B − B1_B で読む(単独では読まない)。参考: 旧 M2x 版の B 群 probe 0.202(12:35 記録) |
| 1 v7f | 57681793 | **0.390** | 038 の分岐 B: 0.379 比 +0.011 ≥ +0.008 → **anaw0.5 を v7f に置き換え、作業基準 = v7f(0.390)**。一つの Public 比較(約 1.4 分子分)であり有意差の確立ではない(12:44 記録) |
