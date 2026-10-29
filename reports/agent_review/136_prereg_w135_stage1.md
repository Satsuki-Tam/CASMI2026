# 136 事前登録(2026-10-30 00:0x JST、Claude Code)— W135 段階 1: 共通の世界での class 3 の到達と oracle 上限

135_decision.md(Codex 135 を採用)の段階 1 である。**到達・oracle の数字は、この登録と Codex の確認の前には一つも計算しない。** これまでに計算したのは、母集団・バッチの数、世界の構築、world P、速度試験(生成物の数と時間)だけである。速度試験は真・クラス・P の順位を読まない。

## 1. 目的
予測した親(train の analog + 同じバッチの他 query の P の 1 位)から b1_gen で生成するとき、class 3 の正解に届く余地がどれだけあるかを、正しい情報条件で測る。その結果で、selector への投資を決める(Codex 135 (iv))。

## 2. 集合(固定済み)
- **設計・選択用(fold 1)**: fold 1 の COCONUT 真の母集団 1,937 identity(MSG 外・panel 外。query library のある 1,925)。
  - バッチは家族 dF1・dF2・dF3(Butina 0.5、Morgan r2 2048。家族あたり最大 8、27〜34 家族)と、無作為 dR1・dR2・dR3(家族バッチに極性・質量帯・library で一対一に対応させた)。各 N = 100。
  - 一つの identity group は全バッチで一回だけ。家族はバッチ間で共有しない。
  - `experiments/w135/batches/d_manifest.json`(sha ffca5c58…)。CSV の sha は dF1 93489af6…、dF2 744ef399…、dF3 d16111c0…、dR1 c5c06a03…、dR2 e452accf…、dR3 ce886e5e…。
- **確認用(fold 2、閉じたまま)**: cF1(家族)、cR1(無作為、対応付き)、cU1(未使用 identity だけの無作為。C1 の適格者は 1 なので実質 C2 / C3)。`c_manifest.json`(sha 6b9dac9d…)。段階 2 の方策を登録するまで開かない。
  - 注記: fold 2 の多くは以前の B1 開発で使われた(used 列に記録)。W135 の設計は fold 1 だけで行う。Codex 135 の「fold 2 だけでは独立確認にならない」に対しては、cU1(未使用だけ)を厳しい下位確認とする。この扱いでよいかを Codex に確認する。
- **規則の事前固定**(`experiments/w135/w135_census.md`、census の実行前に書いた):
  - 家族は Butina 0.5 とする。0.5 で家族所属が 300 未満なら 0.4(実際は 1,019 なので 0.5)。
  - query library: timsTOF の identity が 1,000 以上なら timsTOF を使う。実際は fold 1 の母集団で 12 しかないので、全員を p3_select_np の方策(timsTOF 以外)にする。
- **クラス**(`wclass_p0 / p30 / p60`、hash 順、π3 間で入れ子): C3 = 先頭 round(πN)。残りの半分を C1(独立な参照のある者に限る)、他を C2。dF1 の p30 は C1 28 / C2 42 / C3 30(他のバッチは manifest を参照)。

## 3. 世界(固定。コードと parity)
- `experiments/w135/b1_world.py`: b1_features.py の写しにバッチ単位の mask を加えた。
  - C3: 全 source から構造を除く(raw / pool / identity group / tautomer の alias / 公式 key)。
  - C2: train 所属を隠し、全 query の参照を除く。
  - C1: 自分の選択 library の参照と、自分の query スペクトルの他 library の複製を、全 query から除く。
  - 一つの world view を c1 / c2 の両方の列に書く。
  - **parity: `--parity_c2` で既存の run_np053_f1dev NP_H の 12 分子(2,231 行、33 列)と完全一致した**。
  - world mode では、shortlist に C3 の公式 key が残れば停止する。
- `experiments/w135/w135_p.py`: P = rank_v8w7a。gen_eval2fd の主経路(v7f、view c2)を写し、analog は world mask(C2 / C3 の key を除く。C1 は選択 library と複製の外から代表を選び直す)の下で計算する。
  - **parity: NP_H 200 / NP_X 60 で、main・gl_ok・top-25 の順序の hash が r133_P と完全一致した**(fallback 経路を含む)。
- GL: 公開 GLACIER(released)、開発 run と同じ runner の設定。
- 実行: `spark/jobs/spark_w135_world.sh BATCH PI`。b1_world → GL → world P の順で、manifest を書く。dF1 p30 は構築済み(tables 397 s、GL 253 s(64/100 分子が被覆)、P 59 s)。

## 4. 生成(速度試験の後、到達を見る前に固定)
- **親**: train analog は最大 10(world の analog 一覧の順、train 構造)。peer は最大 10。peer は同じバッチの他 query の world P の 1 位のうち、質量差が b1_gen の編集で届くもの(`b1_gen.matching` が空でない)を、query 間の MS/MS 類似度(同じ極性のスペクトル対で、shifted entropy の最大)の降順で選ぶ(同値は hash)。親は公式 key で重複除去する。
- **編集と上限**: b1_gen v2 のまま(1〜2 段、親あたり 300、予算 600)。query の中性質量は付加体ごとの中央値。
- **事前選別**: 生成物のうち、P の top 25 に無いもの('window' = world DB の 25 位より下、'novel' = world DB に無い)を f.z の降順で並べる(同値は親得点、key)。**B = 50** までを採点の対象にする。
- **速度試験**(dF1 p30、真は読んでいない): 生成物は中央値 46(四分位 7〜175、90% 点 509、最大 1,491)。B = 50 で切られる query は 48/100。生成物 0 は 12。生成時間は中央値 5.9 s、90% 点 106 s、最大 349 s(1 コア)。
  - B = 50 は、推論時に一 query 50 個の GL 採点(400 分子で約 8 万 job)が Kaggle の時間に収まる大きさとして決めた。Kaggle に組み込むときは、別に一 query あたりの時間上限を登録する。

## 5. 測定と読み(reader `experiments/w135/w135_read.py`、この登録と同時に固定)
- **U(π)** = バッチの全 query の平均で、1[真が B 個の事前選別に入る]。
  - これは許された最良の action(真を 1 位に挿入)の利得である。真は構成上 P の top 25 の外にいる。
  - C3 救済(C3)と DB 内の取り逃がし救済(C1 / C2)に分ける。arm は both(train + peer)と train(train の親だけ、同じ B)。
- **到達 h**: クラス別に、生成段(真が生成物にある)と事前選別段(B 内)で見る。真の f.z 順位の分布(1 / 3 / 10 / 50 位以内)も記述する。
- **CI**: 家族(Butina 0.5 の label。無作為バッチの単独は自分だけの家族)を単位にした cluster bootstrap。各バッチの中で家族を復元抽出し、query で重み付けする。4,000 回、seed 136。
- **停止条件**: バッチの分子に生成の行が無い。C3 の真が 'short' / 'window'(world DB にある = 漏れ)。world の manifest と不一致。
- **判断(登録)**: π3 = 0.3、設計 6 バッチ(dF1-3 + dR1-3)を合算、arm both、B = 50。

  | U(点推定) | 判断 |
  |---|---|
  | ≥ +0.04 | INVEST: 小さな selector の学習を一度(段階 2 として別に登録) |
  | +0.02〜+0.04 | LIMITED: 限定した試験に留める |
  | < +0.02 かつ 95% 上限 < +0.02 | STOP: この生成設定(親・編集・予算)を止める。親と編集範囲のどちらが限界かを記録する |
  | < +0.02 かつ 95% 上限 ≥ +0.02 | UNDETERMINED: 登録済みの拡張(dF4-6 / dR4-6 を π = 0.3 で追加)を行い、同じ規則で読み直す |

- **記述(判断に使わない)**:
  - π3 = 0 / 0.6 の世界(π = 0.3 の後に作る。π ごとに mask・P・親・生成を作り直す)。
  - 家族 / 無作為の別。B ∈ {10, 25, 100, 全部} での U。peer の数。生成物の数。
  - 家族の U だけを隠しテストの予測値にしない。同じ元バッチの π 違いは独立標本として数えない。
- **機構の読み方**(Codex 135): 予測した親で h が低い → selector を大きくしない。h は高いが事前選別で消える → その段が課題。B 内にあるが f.z の順位が低い → selector / gate が課題。真の親を与える補助診断は、段階 1 では行わない(性能にも上限にも含めない)。

## 6. 順序
1. この登録を Codex に確認する(136_request.md)。
2. 待つ間に、残りの設計世界(dF2・dF3・dR1・dR2・dR3 の p30)を構築する。到達は計算しない。
3. Codex の確認後、6 世界の full mode の生成 → w135_read.py --pi 30 --decide。
4. 記述用の p0 / p60。
