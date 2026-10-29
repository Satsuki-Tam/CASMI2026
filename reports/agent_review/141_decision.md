# 141 決定(2026-10-30 08:3x JST、Claude Code)— GL の識別目的(A3)を Codex 141 の設計で進める

Codex 141 を採用する。登録は、次の技術確認の後に `141_prereg_gl_retrieval.md` として書く。

- **仮説**: 未見の分子のうち、GL が使える分子で、同じ式の識別を改善する(GL の対象外の層は対象外)。
- **負例**:
  - 学習スペクトルごとに、その条件(CE / 付加体 / 装置)での C0' の GL の上位 K = 7。真と同じ neutral_formula で、公式 key の重複を除く。真の alias と identity group は除く。
  - 負例の分子入力は、それ自身の構造から作る。負例も学習露出に数え、評価・locked・保留の identity は公式 key と共通の group で除く。
  - K 未満なら実在する分だけを使い、padding は mask する。学習の前に一覧を固定する。
  - 全ての同式候補を C0' で採点すると予算を超える場合は、固定した上限の Tanimoto で事前選別してから C0' の上位 K を取る(学習の前に決める)。
- **損失**: `s_j = −cos_loss_sparse(pred_j, observed)`、`L_ret = −log softmax_true(s / τ)`、`L = L_A2_positive + λ · L_ret`。τ = 0.1、λ = 0.1(固定した一候補)。各項は query 単位で平均する。
  - GLACIER の既存の対照学習の入力経路(IntenContrDataset、joint_model の target / decoy の forward)は再利用する。Sinkhorn の損失、frag の損失、scheduler は混ぜない。
- **範囲・データ**: inten3(A2 と同じ)。tims_s1 の train 4,614 スペクトル(val 521 は負例の選択にも学習にも使わない)、1,500 update、positive batch 16、C0' から開始する。
- **比較**: A3 − A2(目的の効果)、A3 − C0'(実用の増分)、A2 − C0'(記述)。開発は f1G + f2G と、NP / D の保護(panel の rr_gl も保護として残す)。locked G は実体を確認してから、凍結した一候補で一回だけ開ける(locked 単独の読みを必ず別に示す)。
- **GPU の順序**: (1) A3 の短い技術確認(入力の対応、損失の符号、有限で非 0 の勾配、inten3 以外の不変、export / reload、時間・メモリ)→ (2) W135 の比較(確認集合が決まった場合)→ (3) 負例の採点 → A3 の学習 → 開発の比較 → (4) locked。
