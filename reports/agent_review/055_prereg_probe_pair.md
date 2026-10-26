# 055 事前登録: B 群の一対 probe(E0_B と現行 0.379 の B1_B)— 診断、方法の候補ではない

作成: 2026-10-27 02:37 JST(結果の前)。根拠: Codex 049 Q1(今日の保留枠を使うなら E0_B と現行 B1_B の一対、旧 0.354 の B 0.202 は履歴として併記のみ)。

## 仕様(両 kernel で同一のセル、`kernels/make_e0_probe.py`)
- 元の版: E0 = `kernels/baseline-v18`(0.464 の再現版、入力資産・全処理を固定)、B1 = `kernels/b1-fpnet-analog` v1(57650023 = 0.379)。どちらも最後に一つのセルを足すだけ。
- 最終 submission.csv の各リストから B 群だけを残す(相対順序保持、追加候補での補充なし、空なら CCO)。B = 公式 key(RemoveStereochemistry → TautomerEnumerator → InChIKey14)が v2 pool の COCONUT ビット(src 2/3)にある、または raw InChIKey14 が COCONUT store にある、かつ T でない(T = v2 pool の train ビット src 1/3、T 優先で排他)。
- オフライン試験(E0 のパネル出力 250 リスト): T 1,076 / B 2,485 候補を保持、例外なし。
- 記録: 両 kernel のログに保持候補数・空でないリスト数(`E0_PROBE` 行)。

## 読み(連続値で記録、Codex 049 の目安)
- 量 = 「B 群に絞った方策の MRR」(元の全体スコアへの B の寄与ではない;群内で順位が詰まる)。E0_T/B の差を 0.085 へ配分しない、class 比率と読まない。
- **Δ = E0_B − B1_B(0.379)**。Δ ≥ +0.04: COCONUT 非 train 候補の経路(候補到達・順位・forward 被覆)の調査を最優先(E0 の pool 窓・ranker の分解をオフラインで)。−0.02 < Δ < +0.04: B 経路は主因でない可能性 → T と群間の融合を別日に一対で。Δ ≤ −0.02: B 内では B1 が上 → E0 の優位は他(T・Pc・群間)。
- 有意差や帰属の境界には使わない。Public で閾値・重みを調整しない。
