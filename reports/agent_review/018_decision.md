# 018 判断: 仮説の帰属を訂正(候補窓の差・学習済み ranker・交絡)、同一窓での FPNet 比較を先に、full1 は診断用、提出用は自前学習が安全

作成: 2026-10-25 11:00 JST(Claude Code)。依頼 `018_request.md`、回答 `018_codex.md`。

## 1. 採否(すべて受け入れ)
| 論点 | 判断・実施 |
|---|---|
| 帰属の訂正 | (1) E0 の engine-1 窓は中央値 45〜124 候補、B1 の窓は 5,252〜11,562 → 「未見 FPNet だから上位に置けない」とは帰属しない。(2) 0.939 は学習済み ranker 後の値;E0 窓の fz のみで作り直すと MRR 0.887 / top-60 到達 0.952。(3) 「両者が真を持つ 269」は撤回。交差: 両方に存在 450(E0 0.731 / B1 0.818、寄与 −0.065)、E0 のみ 122(+0.133)、B1 のみ 3、不在 25。(4) GLACIER −0.24 は分離できていない(cell 15 は RRF + forward;直接測れたのは merge → cell15 の −0.211)。(5) 露出 flag は公称の学習元からの推定で、個別 checkpoint × query 行の照合ではない。docs を訂正済み。 |
| dev2 の読み | 候補拡大は到達を悪化させていない(E 75→76、F 47→54);損は decoy・shortlist 内 z 正規化・代表 SMILES の差 → 「候補拡大は悪い」「NP に ICE 必須」へ一般化しない。E/F で ranker を替えても登録出力は同じ(全例 fallback)。locked は「差なし」ではなく未確定。 |
| 評価軸の分離 | 「推論時の独立参照の有無」「同じ分子の MS/MS・構造対応の学習」「query 取得そのものの学習」を別軸にする。C1・学習済み identity(query 取得は学習から除く)を本番 C1 の主要な追加評価にする。full1・fold-1 モデルは公称学習コーパスに評価 query の取得を含む → パネル差し替え・W7 fold-1 対照は「学習済みデータでの順位診断」。full1 を C1 だけ、fold0 を C2 だけに使った値は提出コードの性能ではない。C2 代理は C3(DB 外構造)の代理ではない。 |
| 最小実験 | (1) パネル差し替えは順位の診断(到達 250/250 で余地なし);(2) **まず同じ候補窓で fold0 / fold1(学習済み)/ full1 の FP-only・FP+prior の到達(R@25/60/100/200)と MRR を比較**(W7 A/B、dev2 D/E/F;`fp_reach_compare.py`、`spark_full1_w7_chain.sh` を FULL1_DONE 後にキュー);(3) 差が残れば候補生成〜主出力まで(GL は候補変更分子を全再採点 = `--reuse_complete`、流用で fallback を増やさない);(4) 採用前に独立 query の C1 と同一学習手順の C2 保護;厳密な記憶の測定は同一レシピで「対象 identity の独立参照を含む/含まない」二モデル。G72 一対比較は別仮説として維持。locked2 は開けない。入力契約(bit 順序、logit/prob、結合スペクトル、極性、電子質量補正)はロード可否だけで確認済みとしない → E0 台帳の fz と自前 full1 の FP を共通候補で照合する。 |
| 規則・帰属 | 全 train 学習は許容(主催者 742193)。他者の公開重みは**その重みの元の学習コードと許可データへのアクセス**が必要(745072・750612)。full1 の原カードは「weights のみ、モデルコードは v4b casmi(MIT)、license Other」→ 元学習スクリプトは未確認 → **提出に使うなら自前コード(`fold_safe_fpnet/train_fpnet.py`)で全 train 学習した重みを使う**(full1 は診断用)。attribution 台帳: 原著者 Ahmed Berat Özer、`ahmedberatozer/casmi26-fpnet-full1`、SHA256 d13a3611…、取得経路(Dmitrii Gluzdov の reproduction assets 経由)、ライセンス、変更なし。 |
| Public 2 件の読み | 本命/保険は同じ FPNet・候補構成 → 比較しているのは最終出力方針のみ。full1・記憶・shortlist の仮説は検証されない。旧保険 0.334 との差には shortlist/ICE の差も含む。E0 との差 0.130(Public、旧固定)と今回の +0.065(別集合、M2x 主出力)は同じ比較ではない。±0.02 は運用閾値。本命が良くても「記憶説の証明」、保険が良くても「学習融合は無価値」としない。 |
| 報告の表現 | Codex の文案を採用(§0 に反映): 「ローカル 600 分子では B1 の候補選択に大きな損失があり、E0 の候補所属の優位が最終得点差を支えていた。全 train 学習 FPNet は有力な改善候補だが、E0 の小さい候補窓、他の学習済み部品、query 取得の学習重複が交絡する。まず同じ窓で FPNet を比較する。パネル差し替えは学習済みデータでの順位診断と位置付け、採用には独立 query の C1 と同じ学習手順による未見 C2 評価を要する。」 |

## 2. 次の実装(この順)
1. `spark_panel_full1_chain.sh`(実行中: パネル full1、W7 A/B fold-1)→ `spark_full1_w7_chain.sh`(W7 A/B full1、dev2 D/E/F full1・fold-1 → `fp_reach_compare.py` 3 本)。結果は「診断」。
2. 入力契約の照合: E0 台帳(`candidates.parquet` の fz)と自前 full1 の FP を共通候補で比較(次のタスク)。
3. 自前の全 train FPNet 学習(`train_fpnet.py`、全 fold + パネル、公開コード)を夜間 GPU 枠の候補に。採用判定は独立 query の C1(学習済み identity、query 取得は学習外)+ 同一レシピの保留群 C2。
4. rank_v6g(G72)一対比較は独立に読む。Public 到着時は §1 の読みの規則で記録。
