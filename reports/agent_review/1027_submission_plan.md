# 10/27 の提出(09:00 JST 以降、039 / 043 / 043_presub_audit の判断どおり)

基準: 57650023(FE + anaw0.5)= 0.379 の同一凍結出力。三つとも一変更比較(相互に独立な再現ではない)、+0.008 / −0.015 は運用上の境界。全結果を記録し、先に返った候補で後続の判定基準を変えない。

| 枠 | kernel | 読み(結果前に固定済み) |
|---|---|---|
| 1 | hayatetaf/casmi26-b1-fpnet-v7f v1 | 038/037b の分岐 B: ≥ +0.008 で anaw0.5 を置き換え、−0.015〜+0.008 は維持、≤ −0.015 は維持して点検 |
| 2 | hayatetaf/casmi26-b1-probe-prior(smoke 済み版) | 039 の限定診断: ≥ 0.25 prior 中心の順位にも有用な信号 / ≤ 0.10 この方策の MRR が低い(原因未分解、LAM は変えない)/ 中間は記録のみ |
| 3 | hayatetaf/casmi26-b1-fpnet-gt3 v1 | 042b/043: ≥ +0.008 暫定採用の資格(累積 D は 043_decision で受容済み)/ −0.015〜+0.008 未確定 / ≤ −0.015 不採用 |

コマンド(version: v7f v1、probe-prior v1、gt3 v1 — いずれも smoke 済みの版):
```
kaggle competitions submit enveda-CASMI26-molecule-id-mass-spectra -k hayatetaf/casmi26-b1-fpnet-v7f -v 1 -f submission.csv -m "Codex 038/039 one-change comparison vs 0.379 (FE + anaw0.5): v7f = analog-feature ranker rank_v7a (600 trees) on GL-covered molecules, insurance + 1 z(ap) + 1 z(MetFrag-lite) on GL-fallback; pipeline 6e3b4d04; branch-B reading fixed in 038_decision"
kaggle competitions submit enveda-CASMI26-molecule-id-mass-spectra -k hayatetaf/casmi26-b1-probe-prior -v 1 -f submission.csv -m "DIAGNOSTIC (Codex 039): working-baseline shortlist (full_eval, k_fpp 200, k_pop 50) ordered by the prior alone (FP tie-break), no forward models; measures this fixed policy only"
kaggle competitions submit enveda-CASMI26-molecule-id-mass-spectra -k hayatetaf/casmi26-b1-fpnet-gt3 -v 1 -f submission.csv -m "Codex 043 one-change comparison vs 0.379 (FE + anaw0.5): + one generated analog derivative (own b1_gen v2 ef8c856a; top-10 analog parents, 1-2 biosynthetic edits, query-derived mass, raw-window absence) at rank 3 if its FPNet f.z >= the main rank-3 f.z; pipeline 8d0c415e"
```
