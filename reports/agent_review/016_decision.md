# 016 判断: (c) は受理(補修を実施)、p2 の層定義は query 基準に作り直してから locked2 を固定、D は残す、各 100 を基本

作成: 2026-10-25 07:40 JST(Claude Code)。依頼 `016_request.md`、回答 `016_codex.md`。

## 1. 採否(すべて受け入れ)
| 論点 | 判断・実施 |
|---|---|
| (c) 再構築の証跡 | **補修済み**: `spark_select_queries_check.sh` は凍結 manifest の max_spectra(8)で再構築し、`compare_eval_test_dirs.py` が条件(max_spectra/sets/limit/電子質量規約)と全ファイルを比較、不一致・欠落で非 0 終了;シェルは `pipefail` + 各段の終了値で `FAILED` を出し、成功時のみ `SELECT_CHECK_DONE`。保存ログ `logs/spark_select_queries_check.log`(07:35): selector PASS、`TEST.PARQUET IDENTICAL`、exclude/solution 同一、mask は集合同一、`COMPARE PASS`、exit 0。 |
| (c) 入力条件の検査 | `select_queries` は呼出側が test adduct 以外を渡すと assert;評価器は生成 query が選択ライブラリ・test adduct に属することを assert、パイプラインは本数と adduct を assert、builder は選択行がライブラリ・adduct 条件と max_spectra を満たすことを assert。記述は「ソートと選択の共通化」と「前処理全体の事故防止(assert による検知)」を分けて書く。 |
| Q1 層定義 | **query 基準で再定義してから版を上げる**(現 `p2_dev/locked` は暫定 v1、locked2 は未開封のまま破棄可)。C: query ライブラリ候補を列挙 → query 側を除いた同極性・重複除外・cap 前の他ライブラリ参照数を条件にし、native forward 可(query に H/Na 正イオン)を主群・不可を副群。G: query ライブラリは enveda-180 固定、他ライブラリ参照の有無・同極性可用性を記録し少/多参照を分ける。E/F: 選択後の query で判定(E = 全負イオン、F = 正イオンあり・H/Na なし;F は NH4/一段脱水(proxy 対象)と K/その他を区別)。D: 独立した真の参照が無い群として残す。C の query ライブラリは条件を満たすライブラリからの固定 seed 選択(ライブラリ別偏りを記録)、同数 tie-break を固定。主ラベル + 副ラベル(参照数・被覆・装置)。各段階の適格数(除外前/後、層割当て前/後)を manifest に保存し、条件を黙って緩めない。 |
| 母集団の訂正 | 「NP かつ timsTOF はパネル以外に無い」は census 定義では不成立(`in_nplib & has_timstof` 717 raw key、参照 ≥20・複数ライブラリ 310、除外後の C/G 交差 53 group)。NP ライブラリ所属・NP 構造注釈(COCONUT)・query 装置を分けて記録し、交差を捨てない。 |
| prior の層 | `pool_meta.parquet` の pid と `pool_*.npy` から公式 identity 整列の注釈表を作れる。lpmid/lsid/lsynonyms/pop_public を一律に「文献数」と呼ばない;欠損と真の 0 を分け、分位境界は dev 側で固定。事後層別では真が shortlist に無い分子も分母に残す。 |
| Q2 | D は残し、各 100 × dev2/locked2 を基本(F は適格 241 group で 150×2 は不可能)。N=100 の paired ΔRR(SD 0.25)の 95% 半幅 ≈ 0.049;主要比較・保護層・許容損失を開封前に決め、区間が広ければ未確定。 |
| 分割方式の記述 | 実装どおり「seed 5 の一つの並べ替えから先頭 100 = dev2、次の 100 = locked2」と書く(seed 5/6 ではない)。manifest に候補数の各段階・採用数・主/副層・query ライブラリ方針・除外 CSV/fold/census/selector の hash・group 交差チェックを残す。除外ファイルの読込失敗は黙ってスキップしない(census の try/except を除去)。 |
| Q3 | 賛成。E/F では `n_gl_finite`・被覆・`fallback_reason`・学習器呼出件数を記録し、本命と保険の順序付き出力の一致を確認。差 0 は「学習が無価値」ではなく分岐で未使用の結果。生 ranker の強制適用は別の診断。F の proxy on/off 比較(同 query・同候補、MSG 非重複、実際に H 無し)は有効な検証;adduct 別に適用数・新規採点数・RR 差・保険→learned 移行効果を記録。 |
| E0 担当への列要件 | 別エージェントに送付済み(07:33、07:36 に「実装に無い重複排除を追加しない」の訂正を送付)。 |

## 2. 次の実装(この順)
1. `p2_select.py` v2: query 基準の層定義、段階別適格数、hash 付き manifest、tie-break 固定、主/副ラベル、群交差チェック → `eval_set2/v2/`、`locked_eval2/v2/`(未開封)。
2. dev2 v2 の test ファイル(共通 selector、max 8)→ `spark_p2dev_chain.sh`(E0 の GPU 使用後)。
3. 注釈表(公式 identity 整列の prior 列)を作成し、事後層別に使う。
