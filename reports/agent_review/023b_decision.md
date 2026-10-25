# 023b 判断: 診断提出は pool / Pc の二本、三本目の枠は保留。T の kernel は削除

作成: 2026-10-25 18:45 JST(Claude Code)。依頼 `023b_request.md`、回答 `023b_codex.md`(023 の判断 `023_decision.md` は維持)。

## 1. 採否
| 論点 | 判断 |
|---|---|
| 本数 | **pool と Pc の二本**(今回の問い「PubChem tier のみの候補を除くと改善するか」と pool/Pc 間の取り違え)。三本目は保留(実装不一致の再実行か、容量が解決した場合の full_eval 直接比較に残す)。T の kernel(`casmi26-b1-probe-t` v2、実行中)は不要になったので削除して GPU 枠を空けた(コードは git にある)。 |
| 撤回 | 「P_pool − P_T ≈ COCONUT 側の寄与」は撤回(pool 出力での T 真値の順位損失が逆符号で混ざる)。「Public でしか決まらない」は強すぎた → ローカルでも C1/C2 × COCONUT 所属で条件付き効果を記録し、隠しへの移し替えは感度分析とする。パネルの真の COCONUT 所属は 100% ではなく **249/250 = 99.6%**。 |
| 代数 | K = T ∪ C(pool)、P = その補集合(Pc = train にも COCONUT にも無い候補 = PubChem tier のみ)。`M = M_K + M_P`、`P_pool = M_K + G_K`、`P_Pc = M_P + G_P`。**`P_pool − M = G_K − M_P`**(Pc を除く純効果)、`P_pool + P_Pc − M = G_K + G_P`(固定順位で所属を完全に選べた場合の回収量;学習可能な量ではない)、`max(0, M − P_pool) ≤ M_P ≤ min(M, P_Pc)`。0.354 は別 run なので近似。 |
| 所属の定義 | 提出版(埋め込み sha 1bc93dda…)の所属は「その run の候補の出典」(window 内 pool の train / COCONUT bit と COCONUT store を公式 identity で OR)。global な DB 所属とは呼ばない。global train 台帳との差は開発表の shortlist 候補 310,993 件中 22 件(真は 0 件)。 |

## 2. Public の読み(提出前に固定)
| 観測 | 判断 | その観測だけでは言えないこと |
|---|---|---|
| P_pool ≥ 0.374 | この固定フィルタは Public で純改善 → Pc を弱める案の開発根拠にする(本命昇格はしない;dev2 C2 の大幅悪化という反証が残るので、条件付きの案を保護層で確認) | Pc の真が少ない、Pc 経路が不要、private でも改善 |
| P_pool ≤ 0.334 | この固定フィルタは Public で悪化;元の Pc 側寄与は少なくとも約 0.02 | 全 PubChem 資産を維持すべき、soft gate も無効 |
| P_Pc ≤ 0.02 | 元出力の Pc 側の得点寄与は最大でも約 0.02 | Pc の真が少ない(未到達・低順位でも同じ結果) |
- ±0.02 は運用上の目安で、有意差の境界ではない。Public の一集計から隠しクラス 2 の COCONUT 所属率を逆算しない。

## 3. 提出前の確認(Codex 5)
- 埋め込みコードの確定: pool v2(実行中)と Pc(未 push)はどちらも pipeline sha **1bc93dda…**(v4 7e84ed6 + probe + コンペ置き場所の探索)。global 版(056d6971…)は使わない。
- Pc 側の検証: パネルは真がほぼ COCONUT なので不足 → **dev2 の 40 分子(各層 8)を両 view で提出版そのもので実行**し、`validate_probes.py` で所属・接頭辞順序・分割・RR の関係(真が群内なら RR_g ≥ RR_main、群外なら 0)・Pc 候補が全て tier・空リスト数・26 位以下からの救済数を分子別に検査(`spark_probe_val40.sh`)。
- wrapper: `rc == 0` を assert、全 ID・行数・形式を検査してから EMIT、各出力の sha256・埋め込み sha・EMIT を `submission_meta.json` に保存(Pc の notebook に適用。pool v2 は旧 wrapper なので、提出前に commit run のログで rc 0 と行数を確認する)。
- ローカル分解の未一致 SMILES(C/C2 2、E/C2 1、W7 B/C2 1)は top-25 の保存リストを絞る版の制約(26 位以下を救済できない下限)として記録し、提出版と同一実験とは扱わない。

## 4. 検証結果(18:45、`spark_probe_val40.sh`、提出版 pipeline sha 1bc93dda… そのもの、dev2 40 分子 = 各層 8)
| view | main | T | N | C のみ | Pc | pool | 違反(所属・接頭辞・分割・RR 関係・Pc の tier・未知 SMILES) | 真の群 | 空リスト(T/N/C/Pc/pool) | 26 位以下からの救済 |
|---|---:|---:|---:|---:|---:|---:|---|---|---|---|
| C1 | 0.573 | 0.692 | 0 | 0 | 0 | 0.677 | すべて 0 | T 22・T&C 14・不在 4 | 2/1/3/4/1 | T 3・pool 3 |
| C2(真の identity を隠す) | 0.429 | 0 | 0.474 | 0.267 | 0.250 | 0.202 | すべて 0 | Pc 16・C のみ 14・不在 10 | 9/1/3/4/1 | C のみ 2・pool 1 |
- C2 view で pool + Pc = 0.452 ≥ main 0.429(G_K + G_P = +0.023)。両 view とも VALIDATION PASS → Pc の kernel(`casmi26-b1-probe-p` v1、新 wrapper)を 18:45 に push。pool(v2、旧 wrapper)は提出前に commit run のログで rc 0 と行数を確認する。
