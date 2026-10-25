2026-10-25。**poolは、報告された完成物の確認を前提に、rcログ取得だけを待ってPublicの解釈を止める必要はない。容量制約が解消したfull_evalの直接比較を支持する。smoke付きv1も、下記のcommit実行証拠を確認できれば一回の比較提出として可とする。** ただし、`manifest.molecules`の一致では全件処理を確認できず、低いPublic値だけからsmoke誤作動と断定することもできない。

埋め込みpipelineを展開し、parity合格版`f88c49a`との差分を確認した。`4dc9e7b3…`の変更はコンペ入力の探索と診断出力の追加で、主出力の順位付けに変更はなかった。commonとrankfeatsも同commitの内容と一致した。手元のprivate Model用checkpointは198,792,173 bytes、SHA256 `5b8d1c311d1171089374379c10cb82fdcc36457a7ab02ec0dddc6f12059b616d`で一致している。

**Q1：完成物の証拠としては十分。rc=0を直接確認した、とだけは書かない。**

このpipelineでは全出力とmanifestを書いた後に最終ログを出し、`--solution`なしならその後に採点処理は走らない。従って同一commit runの完成したmanifest・最終ログ・提出ファイル・kernel COMPLETEが揃うことは、今回必要な出力の完成を強く裏付ける。終了コードそのものの証明と、提出した完成物の妥当性は別である。

rc待ちより先に、保存済み出力で次を確認する。

- 最終`submission.csv`のSHA256が`submission_probe_pool.csv`と一致し、EMITがpoolであること。行数・ID・≤25だけではmainを誤提出していても通る。
- 出力を取得したkernel versionが提出ID 57630176のv2であること。埋め込みコード・rankerのhashと、そのrunのmanifestを結びつける。
- 全400分子を処理した記録があること。GLの部分被覆と既定fallbackは許容するが、入力の一部を処理しなかった状態とは分ける。

これを満たせば、rcの未取得だけを理由にpoolの値へ追加の保留条件を付けない。記録は「完成物と最終処理到達を確認、子プロセスrcは直接未確認」とする。手元のpool notebookには`print('pipeline rc', rc, ...)`があるため、v2がこのwrapperなら、正確には「構造化したmetaには未記録、notebook stdoutは未取得」である。429解消後のログ取得は補完でよい。

今回、pool/Pcのcommit完成物そのものは手元の標準出力ディレクトリに見つからなかったため、この部分の判断は依頼文の実行証跡と独立に確認した制御フローに基づく。Pcの`pipeline_rc=0`やhash照合を、こちらでも再取得済みとは扱っていない。

**Q2：smoke節約は妥当。v1は条件付きで提出可だが、二つのリスク説明を修正する。**

notebookから判定部分だけを取り出してCPUで実行したところ、次の分岐を確認できた。

| 再実行環境変数 | spectrum ID署名 | 動作 |
|---|---|---|
| 未設定 | 既知ダミーと一致 | smoke 12 |
| 設定あり | 一致 | 全件 |
| 未設定／設定あり | 不一致 | 全件 |

`"false"`や`"0"`も現在の`bool(os.getenv(...))`では設定ありとして全件になる。この点はGPU節約に失敗する可能性であり、隠しを12件に制限する方向の不具合ではない。手元の可視testは1,213 spectra・400分子で、ID署名`654e030e4173780e945252b4a5adf70b`も一致した。

一方、**署名はID集合だけなので、同じIDのままスペクトル内容が置き換わり、かつ環境変数が未設定なら誤判定する。** E0と同じ方式という事実は実用上の根拠だが、この組合せを否定する証明にはならない。次版では既知ダミーの内容も照合し、不一致・不明は全件へ倒す。手元`data/raw/test.parquet`のファイルSHA256は`2fa29c4aa06e93b48e0cd6619fd2de3f4e956f0019d242141678b7287f2b43e0`。Kaggleで同じバイト列かを確認したうえで既知ダミーのallowlistに使える。再保存等でhashが変わっても全件になる設計なら、誤ったsmokeにはならない。

もう一つは、**全件処理のassert対象を変えること。** 埋め込み`load_test`だけを実行すると、limit=0は処理対象400・all_ids 400、limit=12は処理対象12・all_ids 400だった。manifestの`molecules=len(all_ids)`とsubmissionの400行は、どちらもsmokeでも成立する。

次版の最低限の防護は以下とする。順位付けは変更しない。

1. wrapperが判定に使った`COMP_TEST`をpipelineの`--test`へ明示し、sampleも同じコンペディレクトリから読む。現状はwrapperのglobとpipelineの`comp_dir()`が別々に選ぶため、複数マウントがある場合の不一致を除く。
2. fullモードでは`--limit`／`--limit=…`が無いことに加え、`b1_stage_stats.csv`の一意な処理済みID集合がtestのID集合と一致することをassertする。現実装では候補ゼロでもstatsと`feats[mid]=[]`が残るので、manifestの`scored=len(feats)`も全ID数と照合できる。候補ゼロと未処理を混同しない。smokeでは明示した12件だけ処理したことを記録する。
3. 実際にロードしたcheckpointの完全なSHA256、ranker、EMIT、rc=0を検証し、入力署名・モード・処理件数・出力hashを保存する。入力assetが曖昧なら先に止め、別checkpointへ自動的にフォールバックさせない。

なお、2のassertを`if not SMOKE`で実行するだけでは、1段目のモード誤判定そのものは検出できない。内容による既知ダミー確認と、全件モード内の処理完了確認は別の防護である。

**今回のv1は、commit smokeが完了し、実際にマウントされたcheckpointのSHAが一致し、12件の処理・rc=0・mainの出力・forward/fallbackの記録を確認してから、一回比較として提出してよい。** 上のCPU分岐確認と既存parityがあるため、防護未追加だけで今夜の比較を止める必要はない。ただし400分子の新checkpointでの時間リハーサルは未実施、と記録する。候補数が近くても候補の内容・forward所要時間・時間切れ時の被覆は変わり得るので、「一分子当たりの時間は不変」は保証しない。また、まだ結果待ちのpool/Pcについて、commitの400分子完走を隠し再実行の完走とは書かない。

「smokeならPublic≈0.01〜0.03で判別可能」は撤回する。130分子の単純平均、CCOの偶然正解なしなら、12件しか処理しなかった場合の上限は12/130≈0.0923であり、0.01〜0.03は一つの期待値にすぎない。低得点は別の実装問題や実際の性能悪化でも起こる。**低い値を不具合として除外するには実行証拠が必要で、得点だけなら原因未確定とする。**

private Modelとprivate Datasetが別枠である方針はKaggle staffの公式案内と整合する。今回のmodel sourceはinstance/versionまで指定されており、格納手段の変更自体は手法の変更に数えなくてよい。ただしロードした内容のhash確認は必要である。[Kaggle公式の容量案内](https://www.kaggle.com/product-announcements/512322)

**Q3：まず実行妥当性、次にfull_eval、最後に固定baselineのpool/Pc診断を読む。**

| 比較 | 問い | 読み方 |
|---|---|---|
| full_eval − 0.354 | FPNet置換全体が実際の隠し混合で改善したか | 020/022の運用閾値を維持。≥+0.02は暫定候補、−0.02<Δ<+0.02は未確定、≤−0.02は見送り。7保護層の下限未確定はそのまま |
| P_pool − 0.354 | baselineのPc候補を全て除く純効果 | 023b/024の表どおり。正でもhard poolを本命へ昇格させない |
| P_poolとP_Pcの組 | baselineの群間競合と元Pc寄与の範囲 | 同一順位を再現できる範囲で下式を使う。クラス比率は同定しない |

`max(0, 0.354−P_pool) ≤ 元baselineのPc寄与 ≤ min(0.354, P_Pc)`

`P_pool + P_Pc − 0.354 = 固定baselineで真の所属群を完全に選べた場合の回収量`（別run差・丸めを含む近似）

和がbaselineを明瞭に下回る、または1を超える場合は、所属・出力・実行差を点検し、構成比を解釈しない。full_evalの得点をこの式の0.354へ代入してはいけない。probeは旧FPNetの順位列から作られ、full_evalとは候補・順位が異なるためである。

「独立に読む」は、異なる介入として扱う意味なら正しい。同じPublic分子を採点しているため、統計的に独立な三実験ではない。また三つの値だけではFPNet×Pc降格の相互作用を測れない。full_evalもpoolも改善したから利得を加算できる、full_evalが改善したからbaselineの競合量の何割を解消した、といった読みはしない。採用先のFPNet・ranker上での2×2が必要である。

**Q4：full_rkは対照と新rankerの二本を一組にする。GPU予算が一本だけなら、目的を明示して完成候補を優先する。**

まずfull_rkの学習・除外・teacher露出監査、主比較、保護条件、実装一致を確認する。`full_rk＋RK_new`が`full_rk＋RK_old`より良いだけでなく、現行本命に対する端から端の比較でも許容できることが必要である。full_evalとfull_rkは除外設計の違うcheckpointなので、今夜のfull_eval＋RK_oldをfull_rk＋RK_oldの対照に代用しない。

| 明日の資源条件 | 推奨する提出順 |
|---|---|
| 二本を完了できる | **full_rk＋RK_old → full_rk＋RK_new**。両レシピを結果前に凍結し、一組の比較とする。前者はFPNet変更、後者との差は同じFPNet上のranker変更を測る |
| 一本しか優先できない | ローカル条件を満たす**full_rk＋RK_new**。完成したシステムの改善を測る目的とし、0.354との差はcheckpoint＋rankerの複合変更と明記する。ranker単独のPublic効果は未測定のまま残す |
| full_rk側の監査・保護・実装が未達 | その候補の提出を急がず、今夜のfull_eval判断と現行本命を維持する |

二本を一組にする場合、最初のPublic値を見て新rankerの重みや融合を変更しない。実行不良があれば修正を優先する。同じ特徴とforwardに対する旧／新rankerのローカル再採点は安価なので、そこで不要な候補を減らす。一方、Kaggleへの二つの提出が隠し推論の計算を共有するとは見積もらない。Kaggle staffは提出時にnotebookを最初から再実行すると説明している。[Kaggle staffによる再実行の説明](https://www.kaggle.com/discussions/product-feedback/440750)

**Pc弱め案はその後。** 024_decisionの既見パネルでw=0.5の利得が約+0.001という結果は、優先度を下げる根拠になる。ただし「C1利得は未見に限られる」「常に(1−q_seen)倍になる」は一つのパネル・checkpointからの一般化であり、断定しない。pool≥0.374でも、採用するfull_rk＋RK_new上のw=0.5追加効果が局所比較で消えていれば提出しない。再びw≥1や不合格ゲートをPublicだけで候補へ戻さない。

明朝の提出枠回復と週GPU枠は別である。推定「20時間使用」だけでなく、残量と進行中sessionの予約を見て二本を完了できるか決める。公式docsも週GPU枠は30時間または資源状況に応じた値としており、現在のアカウント表示を確認するのが確実である。五枠を使い切る必要はない。[Kaggle公式GPU利用案内](https://www.kaggle.com/docs/efficient-gpu-usage)

確認資料：共同作業規約、025依頼、023回答、023b/024判断、full_evalとpool notebookのwrapper、full_eval notebookの埋め込みソースと`f88c49a`との差分、Model metadata・ローカルcheckpoint、可視test。追加確認はCPUによる分岐・入力読込の検査とhash照合のみ。GPU実行、Kaggleへの書込み・提出、Claude Codeの呼出しは行っていない。

REVIEW_COMPLETE: 025
