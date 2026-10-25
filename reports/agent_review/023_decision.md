# 023 判断: full_eval は「比較可能だが資源配分により保留」、クラス分解の probe を実施、full_rk の次段を固定

作成: 2026-10-25 18:25 JST(Claude Code)。依頼 `023_request.md`(+ 追加 `023b_request.md`)、回答 `023_codex.md`。

## 1. full_eval
| 論点 | 判断 |
|---|---|
| 判定 | 022 の 2 行目「非劣性未確定の一回の比較提出として可」で確定(Codex が clean 202 の Δ +0.035033 [+0.008969, +0.062041]、uncertain、parity 16/16 を独立に再集計・確認)。 |
| 提出 | **比較可能な候補として記録し、資源配分により保留**(checkpoint を Kaggle に置く手段 = private 容量 29 MB の問題がユーザー判断待ち)。「期待利得がほぼ 0 なので無価値」とは書かない — Codex の指摘どおり、重み全体が変わるので既見 C1・train 外 C1・C2/3 でも順位は変わり、私の 0.2 × p1 × Δ の見積もりは感度シナリオに過ぎない(上限ではない)。容量が解決すれば一回の直接比較を優先する。 |
| 既見性 | 「元の学習対象の約 80% は fold-0 FPNet に既見、開発・評価は未見 identity 中心」は事実として記録。隠しクラス 1 への移し替え(公開参照あり = この train にある、一様抽出)は仮定であり、隠しテストの既見率としては使わない。 |

## 2. クラス分解の probe(診断、候補ではない)
- 定義: **T = 候補の公式 identity が train 構造**(実装は window 内 pool の train bit を公式 identity で OR)。Codex 指摘の global 集合(`train_scorer_keys.parquet` の 274,195 key)との差は pool の train bit に無い 9 key だけで、開発表の shortlist 候補 310,993 件では不一致 22 件(すべて window 側の取りこぼし、真は 0 件)→ 実質同一として、kernel に入れた window 版をそのまま使う(global 版は `experiments/b1_probe023/b1_pipeline_globalkeys.py` に保存)。T/N は C1/C2 のラベルではない(train 外の公開参照を持つ C1 は N 側)。
- 代数(Codex): `P_T = M_T + G_T`、`P_N = M_N + G_N`、`P_T + P_N − M = G_T + G_N` = 候補と群内順位を固定したまま真の所属を知る oracle の改善量。`max(0, M−P_N) ≤ M_T ≤ min(M, P_T)`、`P_T ≤ p_T ≤ 1 − P_N`。Public の 0.354 とは隠し再実行が別なので近似。
- 読みの表は Codex の置き換え版を採用(「B1 が T 中心だから E0 との差も C1」という帰結は削除)。
- 空のリスト: エタノール("CCO"、46 Da)で埋める。隠しテストの質量は 157〜1,159 Da なので正解にならない。空になった分子数を run manifest に記録(`probe_empty_*`)。
- 実装確認: パネル 16 分子(Spark)で、v4 の pipeline そのもの + probe の主出力が現行 pipeline と 16/16 一致、C1 view で T ≥ main・N = 0、C2 view(真の identity を隠す反実仮想)で N ≥ main・T = 0、pool + Pc ≥ main、T ≥ pool(C1)を分子別に確認。
- 版の選択(T / pool / Pc の 3 版か、T / N か)は 023b の回答で確定する。kernel `casmi26-b1-probe-t` v2 と `casmi26-b1-probe-pool` v2 は 18:14 に push 済み(Kaggle の新しい notebook ではコンペのデータが `/kaggle/input/competitions/<slug>` に置かれるため v1 は test.parquet が見つからず失敗 → 置き場所を探す処理だけ追加した v2)。commit 実行は約 3 時間。

## 3. full_rk(Codex Q4)
1. 学習完了(19:25 頃)後、`handoff_full_rk.sh` が final checkpoint・sha256・学習記録・露出台帳を Spark に渡し READY を書く。20:50 までにローカル処理を終える条件は維持(20:45 で打ち切り)。
2. `spark_fullrk_chain.sh`(Spark、READY 待ちで起動済み): full_rk で p1 run1(rkfit 保留)・W7・eval_c1・dev2・パネルの特徴表を作り(GL は既存 run から seed)、ranker を rank_v4b の params/rounds のまま学習。**C2 行は露出台帳で FPNet 既見の分子だけ落とす**(`b1_rank_train.py --c2_drop_exposure`;W7 の 516 分子・eval_c1 の 19 分子は query 除去後に学習取得 0 = 未見なので C2 行を残す)。C1 行は既見・未見の両方を残し、評価で分けて読む。対照に同じ表で落とさない版(rank_rk_fx0)。
3. 主比較 **full_rk + 旧 v4b(RK_old)対 full_rk + 新 ranker(RK_new)**、採用の対照として凍結 M2x を併記。dev2(未見)、パネル(C1 既見)、W7(fit 群は学習に使ったので tune/eval 群で読む)。T/N gate・pool60・PCL はこの比較に混ぜない。
4. fold-0 への移植は別の一対比較(fold0 + 旧 vs fold0 + 新)が必要。今夜はしない。
