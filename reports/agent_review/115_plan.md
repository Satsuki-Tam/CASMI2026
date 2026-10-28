# 115 計画(草稿、未登録): GLACIER の模擬スペクトルで FPNet の学習データを補う — Codex 115 の設計に沿った段階

作成: 2026-10-28 22:44 JST(Claude Code)。GPU は 110 / 111 の直列の鎖が終わるまで使わない(Codex 115:今夜の稼働中 GPU へ生成を足さない)。MIST(aug / noaug)の比較は利用者の導入許可があれば先に行う。

## 動機(既存データの監査、結果の前)
- P の C2 の誤り(正解が候補内、560 件)で、表の FP が正解を P の誤った 1 位より上に置くのは 34.6% だけ(diag/x_fpgap.md)、FP の bit 衝突は 0 件(diag/x_fpcoll.md)→ 誤りの多数は FP 予測そのものの誤り。誤った 1 位が train 構造(既見)のとき FP の得点差は −5.5(diag/x_seenbias.md: train 構造は C2 リストの 3.4% だが誤った 1 位の 41.5%)。
- 公開 fold-safe FPNet の NP 例の top-1 33%(一般の held-out 68%;条件は揃っていない)。

## 比較(Codex 115 Q2 / Q3)
- **主比較 = 本番に対応した版**: 評価のラベルと独立に固定した公開カタログ(COCONUT のみの pool 構造、固定 hash による部分集合)を模擬学習する。読む能力は「実スペクトル未見だが DB の構造から模擬学習できる検索」で、「未見構造への汎化」とは呼ばない。正解を補充しない、正解だけ多く生成しない。真・decoy について実正例 / 模擬正例 / teacher の実学習の露出を別列に記録し、「真が模擬対象内 / 外」で分けて読む。
- 三出力: **P0**(凍結した現行)、**R**(fold-1 公開 FPNet を実測だけで固定更新数の微調整)、**A**(同じ初期値・更新数・batch・optimizer・損失・負例で、**陽イオン H / Na の実測枠の 25% を模擬に置換**)。登録する主比較は A − R、採用には A − P0 も確認。混合率は実際の学習入力の割合で管理(明示的な sampler)し、実数を記録。
- 模擬スペクトル: QTOF の装置 token、[M+H]+ / [M+Na]+、CE 20 / 40 / 60 eV を**個別に**保存(sum にまとめない)、陰イオンへ付け替えない。FPNet 入力の precursor は理論 m/z(GLACIER 内部の precursor 0 を写さない)、Enveda の電子補正を重ねない。
- 評価は実スペクトルだけ: 110 と同じ段階 1(FP 代理)→ 段階 3(shortlist 再生成・共有 GLACIER・凍結 ranker)、保護(NP_N C2 等の未対応側、既存 C1、c1dev)。

## 段階(各段の合否で次へ;性能を見る前に固定する数値は速度測定の後に登録)
1. **書き出しの往復**(experiments/e115/gl_simtest.py): 学習側の表(run_tp_f3a 等)から固定 hash で 150 分子、同じプロセス内で runner の採点と、保存 → 読み戻したピークでの採点が全組で一致(差 0)。予測の失敗数・ピーク数・1 予測あたりの秒数を記録して生成予算を見積もる。
2. **pool との対応**: 模擬構造の FP bit 順・中性質量・分子式 / 元素の目標・pool pid・global identity を揃え、Data が sid2pid の無い正例を黙って落とさないことを確認。稼働中の harness_work は変更せず別版の入力を作る。
3. **模擬と実測の対応**(学習側の NP 群、最終確認とは別): 付加体・CE・装置を合わせた真の模擬スペクトルと実測の類似度、同分子式 decoy との差、質量帯別の失敗・ピーク数・強度分布。teacher の実学習露出で分ける。
4. ~~小さな R / A(1〜2 万構造)の結果で 40 万へ拡大するか決める~~ → **Codex 118 で役割を変更(下の v2 節が優先)**: cat15k は技術確認と転移の記述だけ、登録上の主比較は COCONUT 全体のカタログ M_all。

## 技術段階の記録(2026-10-29 01:12 JST、CPU のみ;GPU は 110 / 111 の鎖が使用中、性能は読んでいない)
- 段階 1 の小試験(CPU、4 分子・40 候補・150 予測): 書き出し → 読み戻しで runner の採点が全組一致(最大差 0.0、None の不一致 0)、予測失敗 0、CPU で 0.076 秒 / 予測(6 スレッド未満)。gl_simulate.py も 12 ジョブで失敗 0。登録どおりの 150 分子版を CPU で実行中(experiments/e115/stage1_cpu)。
- **段階 2(pool との対応、experiments/e115/stage2_check.py)**: 初回は 1 件 FAIL — カタログの 1 構造(QJCAHUHGEGJAFK、bilirubin の互変異性の別表記 = fold 3 の identity の alias)が既知 identity の key に一致(Codex 112 の alias 行と同種)。sim_jobs.py に「既知 identity の key / alias を除く」規則を足して作り直し(該当 14 行を除外、カタログは hash 順の次の 1 構造と入れ替わっただけ;旧版は cat15k_v1_alias に保存)。再検査は全項目 PASS: 学習側 pool と同一(sha 82b8c403…)、pid = 行番号、カタログ 15,000 行が pool 行と一致・すべて COCONUT のみ、FP の正解 bit が再計算と一致(2,000 構造、不一致 0)、既知 identity との一致 0、開発・確認の選択 CSV との重なり 0(記録のみ)。
- CPU での生成速度から、9 万ジョブは CPU だけで約 2 時間の見込み(GPU を使わずに段階 3 以降の生成を前倒しできる)。生成の開始は Codex の判断を待つ。

## Codex 117 を受けた追記(2026-10-29 01:36 JST、性能の前)
- **カタログの意味(登録上の区別が必要)**: 現 cat15k は COCONUT のみ(src = 2)に加えて既知 identity の key / alias をすべて除くので、**評価の真はどれも模擬対象に入らない**。よって cat15k での A − R が測るのは「別の公開構造の模擬スペクトルを足すと、模擬されていない評価分子へ転移するか」(**転移試験**)で、本番で想定する「実 query は未見だが、その構造は公開 DB から模擬学習できる検索」の直接の利得は測れない(隠しの C2 の真は COCONUT / PubChem にあり、本番のカタログに含まれ得る)。
- 後者を測る主比較は別に用意する: 公開 COCONUT の所属(train ∩ COCONUT を含む)から**全構造に同じ固定 hash・割合**で一様に選び、保留 fold の構造も模擬対象になり得るカタログ(実測 query の保留は維持、正解の狙い撃ちの補充はしない、alias は一貫した identity 処理)。一様抽出で評価の真を十分な数だけ含むにはカタログが大きく(COCONUT 全体なら約 250 万予測)、規模と費用は別に見積もる。どちらを 115 の登録上の主比較にするかは性能を読む前に決める。cat15k の NO だけで「構造が模擬学習済みの場合の利得」は否定しない。
- **段階 3 の分割**: 3a = 学習側の固定集合で既存の GLACIER 得点による識別診断(全分子 → 真が shortlist 内 → 対応 query あり → 真と比較 decoy の得点が有限、の件数;margin = 同じ条件で得点のある同式 decoy の最大との差、decoy 数と質量帯を併記;MSG 既見 / 未見は identity / alias で判定;評価群・確認群は使わない)。3b = 生成した個別スペクトル(QTOF × H/Na × CE 個別)と実測の条件別対応 = **未確認**として残す(既存の runner 得点は複数 query の平均・CE 不明時の統合なので復元できない)。
- **cat15k の CPU 生成**(準備、性能・採否とは切り離す): 150 分子の段階 1 が技術的に完了・合格してから開始(ジョブ自身が検査)、--device cpu 明示、1 プロセス・6 スレッド・nice、5,000 ジョブごとの shard、入力・コード・環境の hash を manifest に記録、meta が無い shard 群は完成品として扱わない。学習の更新速度と空きメモリを監視し、競合すれば止める。生成済みを理由に 115 の順番を繰り上げない。ジョブ: experiments/e115/cat15k_sim_cpu_run.sh(Spark では experiments/e115/cat15k_sim_cpu/run.sh)。
- 01:42 段階 1(登録どおり 150 分子、CPU 6 スレッド): **合格** — 候補 5,842、予測 20,153、失敗 0、書き出し → 読み戻しの採点が全組一致(最大差 0.0、None の不一致 0)、CPU で 0.083 秒 / 予測。その間の FPNet の更新速度は約 2.48 it/s(単独時 2.57)= 約 3.5% 低下 → cat15k の生成は 4 スレッドに下げて 01:42 に開始(9 万ジョブ、約 2〜3 時間の見込み)。

## v2(Codex 118 を反映、2026-10-29 02:04 JST、性能の前;**本節が上の記述より優先**)
- **役割**: cat15k(COCONUT のみ・既知 identity を除外)= 学習経路の技術確認と「別構造の模擬からの転移」の記述だけ(判定に使わない)。**登録上の主比較 = M_all**: 公開 COCONUT 所属の全 identity(src 2 / 3、alias 表記は既知 identity の正規の pool 行へ対応付けて identity を保持)、150〜1,200 Da、runner の構造規則で受理。評価ラベル・所属は読まない。
- **主比較の問い**: 「公開 DB の構造を模擬学習したモデルが、未見の実測 query を検索できるか」。保留 fold の構造も COCONUT 所属なら模擬で正例になる(実スペクトルの保留は維持)= 本番で隠しの B 群の真が COCONUT の模擬で学習済みになるのと同じ規則。ただし「np053 は全て COCONUT」だけで全 query の真を模擬学習済みとしない(質量・受理・生成失敗・巡回の未選択で露出が無い場合がある)→ 実際の露出の台帳で層別。構造未見の汎化とは呼ばない。
- **関門**: 段階 1(FP 代理)で A − R と A − P0 の両方が > 0;段階 3 で A − R と A − P0 の両方について主指標 ≥ +0.005・95% 下限 > 0、A / D 各ブロックと既存の保護(旧 B、G C1、NP C1、c1dev pooled)の下限 ≥ −0.01。bootstrap は三群で同じ identity の対応。R が悪化して A が戻しただけの結果は採用しない。
- **sampler(性能の前に固定)**: identity を固定 hash 順で巡回(cycle r の順 = sha256(salt|r|key))、各 identity の 6 条件([M+H]+ / [M+Na]+ × CE 20 / 40 / 60、QTOF)は固定の置換で r 番目の条件。**全体で一つの巡回**(worker 共有のカウンタ)、置換率 α = 0.25 は H / Na の実測正例枠に対して。生成は巡回が使う (identity, 条件) だけ(2 巡なら約 89 万予測)。更新数 S は sampler の試走で対象枠の割合 e を測ってから S ≈ rN / (Bαe)(r = 2 巡)で登録し、final だけを読む。
- **学習コードの修正(experiments/e115/train_fpaug2.py、make_simplan.py)**: 負例は公開の規則(全 pool の ±10 ppm 窓から一様、窓 < 8 は半分を無作為)で、評価所属に依存しない — 正例自身の identity(正規行と alias 表記)だけを除く(v1 の「保留 group を負例から除外」は M_all では評価構造への特権になるので廃止);模擬は shard ごとに一度だけ読み込む flat 配列;生成の完了(meta)・job index の範囲 / 重複 / 欠落・有限ピークを検査し、計画の位置の 1% 超が欠ければ停止(A が黙って R にならない);消費した模擬入力を main loop で数える台帳(job ごと、構造ごとの露出 0 / 1 / 2 / 3+);置換・模擬の augmentation・負例の RNG を (seed, 用途, worker, batch, 枠) で分離;模擬にも公開の augmentation(CE を 10% で不明に)を適用。
- **表現の訂正(Codex 118)**: x_errtypes の「57%」は**同分子式の誤り 254 件のうち 145 件**(天然物の誤り全 279 件では約 52%);同じ Murcko 骨格は「近い異性体」を必ずしも保証しない;x_scafswap の損益分岐は代理評価での値で、隠しの class 1 比率の推定ではない;B 群に絞った Public probe の約 0.20 は B の比率でも通常出力への寄与でもない。A − R が正でも、効果を「記憶の偏りの解消」の一つに帰さない。
- **本番への接続**: 通過したら fold 2 の初期値で同じ固定レシピを再現 → 本番は full_eval 相当の初期 FPNet に同じ A の微調整(最初からの再学習は不要)。ranker は凍結(FP 分布の変化で利得が出なければ端から端の NO)。
- **順序(Codex 118 Q4 / Q5)**: 110 / 111 の正式通過の fold 2 再現 > MIST の小比較(許可・準備が整えば) > 115 主比較。生成は中断できる GPU の空き時間に入れてよい(評価・GL と同居させない)。GB10 の生成速度は固定小標本で測ってから枠を確保(T4 の 74.7 予測 / 秒なら 89 万予測で約 3.3 時間)。

## v2 の固定値(2026-10-29 02:10 JST、学習・性能の前)
- 更新数 **S = 24,000**(R / A 共通、final だけを読む):e = 0.577(fold-1 split の公開 sampler の対象枠の割合、メタデータから計算;CPU の 3 更新の小試験では 0.531)、B = 256、α = 0.25、N = 447,245 → 期待される模擬の消費 = 24,000 × 256 × 0.25 × 0.577 ≈ 88.6 万 ≈ 計画 894,490 の 0.99(約 2 巡)。
- レシピ(R / A 共通): 初期値 = 公開 fpnet_fold1(sha 1739d568…、weights_only)、新しい AdamW(lr 1e-4、wd 0.01、betas 0.9 / 0.98、bias / norm は減衰なし)、warmup 500、各 run の S で 2% まで cosine、batch 256、K 63、merge_p 0.3、公開の augmentation(模擬にも同じ、CE を 10% で不明に)、w_bce 1、w_el 0.1、seed 0、loader 6、holdout 'hold,np'(f1s1 と同じ split)。A は --sim_frac 0.25、--sim_dir experiments/e115/mall、--sim_out = mall_sim の生成 prefix(複数可、範囲の完全被覆を検査)。
- 実行順(Codex 118 Q4): 110 / 111 の正式通過があればその fold 2 再現が先。R は模擬を使わないので、GPU が空けば生成の完了を待たずに先に学習してよい;A は生成の完了検査を通ってから。

## Codex 119 を受けた修正と技術試験(02:51 JST、性能は読んでいない)
- **train_fpaug2.py**: 学習 step の batch ID ごとに実測の ID(公開の sample_ids、RNG [seed, 1, b])・対象枠・置換枠・模擬の計画位置を学習前に確定、worker w は b ≡ w (mod W) の batch を自分の queue へ、main は b 順に消費(R / A の実測入力と未置換枠の負例が batch ID ごとに一致、計画は順番どおり消費、worker の停止は学習の停止)。負例は窓内で正例の identity を除いた有効行から一様に抽出(空なら global、raw 窓 < 8 は後半 global の公開規則)。identity は公式 key 優先、衝突は停止。CE の augmentation は公開と同じ(値を残しフラグだけ 0)。入力ゲート(初期値 sha、fp_bits sha、split の監査、新しい出力先)、生成物の検査(jobs の sha、範囲・被覆・offset・正の強度・記録された失敗だけを最大 1% 除外)、台帳は optimizer 更新の後に加算。
- **make_simplan.py**: 一つの canonical 規則(identity group の train 行の最小 pid)、公式 key 優先(互変異性の正準化が冪等でない UWVKGDFRNQQIBO を記録)、alias / 同 group の第二行 25 件を監査表(mall_alias_audit.csv)、各巡回で全 pid を 1 回、条件の重複なし。2 巡で同じ付加体になる identity は 40.0%(「全構造で両付加体」ではない)。
- **gl_simulate.py / mall_gen.sh**: 最後の meta も原子的、範囲の検査、既存 prefix の上書き拒否、jobs / teacher / runner / コードの sha と失敗・除外 index を meta に記録;生成は 2 プロセス × 2 スレッド(計 4)で、計画ファイルの一致と jobs = plan = 2N を確認してから開始(cat15k の生成の後に自動開始)。
- **技術試験(CPU、小さな計画 300 identity / 600 予測を 2 つの prefix で生成)**: R と A の 4 batch の比較で、実測 ID が全 batch で一致、未置換枠の正例・負例が一致、置換枠の正例 = 計画の pid、模擬の消費 = 計画の先頭から順番どおり(19 件 = 予定 19 件)、台帳の露出 19 構造 × 1 回、alias 監査 25 行が identity 一致。停止条件: 範囲の欠落、重複、同じ tag の再利用、初期値 sha の不一致はいずれも STOP。
- 観察(記述、判定に使わない): 初期の fold-1 FPNet は模擬スペクトルの正例を窓の 64 候補中 1 位に置く割合が約 36%、rank 損失は 1 件あたり約 20(実測の学習構造は 0.08)。模擬と実測の分布差、または未学習の COCONUT 構造であることの両方を含む値で、A の学習がこれを実測 query へどこまで移せるかは主比較で読む。

## 読み取りの固定(2026-10-29 02:54 JST、R / A の学習・性能の前)
- 段階 1: experiments/b1_baseline/x115_stage1.py(P0 / R / A の表を同じコード・同じ系で作り直す;ck115 の PASS と final の sha、manifest の一致、窓・到達・query の一致を検査;関門 = dFP(A − R) > 0 かつ dFP(A − P0) > 0;真の M_all 所属と A での模擬露出は記述のみ)。
- 段階 3: experiments/b1_baseline/x115_stage3.py(GLACIER の監査・共有値の一致、行の完全性、P0 が既存の main(r102 / r111_base_c1bankdev)を全行再現しなければ exit 2;A − R と A − P0 の両方が主指標 ≥ +0.005・下限 > 0、ブロック・保護(旧 B、G C1、NP C1、c1dev pooled)の下限 ≥ −0.01;bootstrap は同じ再標本で二つの比較を対応させる、seed 1151 / 1152 / 1157 / 1158)。
- 表は run_<tag>_{p0,r,a}e115(slot の fpnet_fold0.pt を各 arm の checkpoint に)、main は diag/r115_<arm>_<tag>.csv、tag は f1dev / np053f1dev / c1bankdev。実行ジョブは学習の後に作り、Codex の点検を受ける。

## 結果の前の記述: 開発の真の M_all 所属(2026-10-29 05:10 JST、R / A の学習前、性能は読んでいない)
- scorer_key → pool pid → M_all の catalog で数えた(x115_stage1 の診断列と同じ対応)。pool 所属はすべて 1.0。
- **M_all 所属の割合**: np053f1dev NP_H 0.955、NP_N 0.967、NP_X 1.000。f1dev D_np_single **0.16**、C 0.32、E 0.41、F 0.48、G 0.00。c1bankdev C1_pos_few 0.134、C1_neg_few 0.231、C1_neg_many 0.154。
- 読み方(判定は変えない): 主指標の重みの半分を占める D では、A が真の模擬を見ているのは約 16% だけ。D の A − R は主に「模擬を学習データに足す一般の効果」を測り、「隠しの B 群と同じく、真を模擬で見ている」効果は主に NP_H / NP_N に現れる。段階 1 の診断列(truth_sim_exposure)で、この二つを分けて記述する(判定には使わない)。

## Codex 120 を受けた修正(2026-10-29 05:32 JST、R / A の学習前、性能は読んでいない;commit 3318925、9b63f16)
- **学習ジョブ**(spark_e115_train.sh): 共有の GPU 排他ロック(spark/gpu.lock、flock をジョブ全体で保持。wrapper の同時通過を防ぐ)を追加した。起動条件に次を加えた:
  - GPU の compute process が一つもないこと(nvidia-smi --query-compute-apps。CPU だけの M_all 生成は対象外)。
  - 名前の拒否に x115、b1_features、--device cpu 以外の gl_simulate を追加。
  - コード manifest(casmi パッケージ・b1_common・trainer・完了検査)と入力 manifest(runR / runA の work 全ファイル。R / A の入力が同一であることも兼ねる)の照合。
  - split 監査の結び付け: passed、held_out_fold 1、監査の split sha = 現在の work/split.parquet = 登録済みの 93b6a595…。
- **評価ジョブ**(spark_x115.sh):
  - 同じロックと GPU process の検査を行う。run は新規のものだけ作る(既存の run があれば拒否する。REBUILD=1 のときは退避し、削除はしない)。
  - 開始時に、R / A の現在の final の hash が完了検査と同じことを確かめる。3 slot の bits も検査する。環境(workers・版・GPU)を manifest に記録する。凍結した既存の GL cache の入出力も hash で固定する。表の一致比較の失敗でもジョブを止める。
  - **GL は和集合で一回だけ採点する**: 既存の run の値を凍結した cache とし、3 群の未計算の候補を gl_union.py で和集合にする(query の一致が必要。分子と SMILES はソートし、群の名前は順序に入らない)。これを一回だけ採点し、各群は「既存の cache + 和集合の結果」から merge する(残りがあれば停止)。表の並列数は FEAT_PAR(既定 3。110 の作り直しのメモリ実測で決める)。状態は X115_DONE_PASS / X115_DONE_NO。
- **段階 1 の読み取り**:
  - R / A の final の現在の hash を確かめる。3 tag すべての manifest と slot の bits を検査する。選択 CSV に対する完全性(欠け・余り・重複)も検査する。
  - **露出は identity 単位**で数える(make_simplan と同じ規則: 評価の identity_group → train_structs の公式 key の pool 行の最小 pid → catalog)。状態は「解決・catalog 内」「解決・catalog 外」「未解決(NA、別に数える)」の 3 つ。計画の入出力の hash と、A の receipt の台帳 hash に結び付ける。
  - 判定 JSON(diag/x115_stage1_decision.json)を書く。
- **段階 3 の読み取り**:
  - 段階 1 の判定 JSON(PASS、hash が現在のファイルと一致)に結び付ける。
  - 3 tag の表が各群の checkpoint から作られたことを検査する。GL は 3 群すべてについて、分子の query が一致することを確かめたうえで、(分子, SMILES) ごとに値が一つであることを検査する(有限 / null の食い違いも停止)。
  - ledger の identity_group が選択 CSV と一致することを検査する。
  - 基準(r102 / r111_base)は hash を記録し、有限で [0, 1] に入ることを検査する。行 key の不一致は exit 2(再現の失敗)とする。
  - **--allow_repro は廃止**した。pooled の bank では identity が一意であることを検査する。判定 JSON を書く。
- 空試験: 段階 1 は、既存の表を全群に当て、偽の台帳と receipt を使って最後まで動いた(露出の状態は全分子が「解決」、catalog 所属は前節の値と同じ)。段階 3 の空試験は、c1 群の GL と r111_base ができる 111 の鎖の後に行う。gl_union.py は合成入力で、ソート・和集合・query 不一致での停止を確認した。両ジョブとも、GPU process がある間は起動を拒否することを Spark で確認した。

## Codex 120b(Q7)を受けた読み方の訂正(2026-10-29 05:32 JST、性能は読んでいない)
- 関門は変えない(Codex も同意)。主指標 NP_H/4 + NP_N/4 + D/2、ブロック、保護、A − R と A − P0 の両方、段階 1 の関門はそのまま。
- この関門は、真の露出が多い NP 側の改善を薄めて測る。例えば D の差が 0 なら、主指標 +0.005 に NP_H / NP_N の平均で +0.010 が要る。NP_N も 0 なら NP_H に +0.020 が要る。そのため **NO を「真の模擬を学ぶ仕組み自体が無効」とは読まない**。層別で良かった部分を使って NO を救済することもしない。
- 前々節の表現を次のように訂正する:
  - 「D では A が真の模擬を見ているのは約 16%」ではなく、「**現在の対応規則で、D の約 16% が生成の対象に入る**」。実際の露出は、生成の成功・消費された job・query の条件を経て初めて言える。NP_N の真が対象に入っていても、生成は陽イオン H / Na だけなので、陰イオンの query の条件を再現した学習とは限らない。
  - 「D の A − R は主に一般の効果」ではなく、「**D は、直接の露出が少ない混合集合**」。所属率を p とすると ΔD = p × Δ(所属内) + (1 − p) × Δ(所属外) なので、D の増分が少数の所属内から来ることもあり得る。
- 所属率の確定: identity 単位の対応(x115_stage1 の修正版、make_simplan と同じ規則)で数え直しても、key → pid による値と同じだった(未解決 0)。記述では、各 cell の全件の成績と分母を先に出し、その下に所属・実露出ごとの件数、対応のある差、救済 / 損失を示す。露出の有無で分けた群の差を、因果効果とは呼ばない。
