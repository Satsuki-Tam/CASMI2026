# 016 依頼: (c) query 選択の共通関数化の完了報告、(a) E0 自前分子実行の開始、(b) 検証集合の層追加(p2 / locked 2)の設計確認

作成: 2026-10-25 07:05 JST(Claude Code)。前回 `015_decision.md`。kernel 2 本(本命 v4 / 保険 v1)は 04:11 から実行中(07:00 時点 RUNNING)。提出は 09:00 以降。

## 1. (c) 完了(`docs/validation_design.md` 末尾、commit f92ca5f)
- `b1_common.select_queries` を新設し、評価器 `b1_features.py`・パイプライン `b1_pipeline.py`・builder `make_eval_test.py` の 3 実装を置換。方針不変(test adduct のみ、[M+H]+ → adduct 名、adduct 内 CE(欠損→0)→ 入力順、round-robin、max_q)。
- `test_select_queries.py`(Spark、実データ): 旧 3 実装(逐語コピー)との差 0(評価器 600 分子 ×(8,16)、builder(8,16)、パイプライン経路 600)、**パイプライン(8) と評価器(8) の順序付き store 行 600/600 一致**。`eval_test_full3` を新 builder で再構築 → `test.parquet` 2,107 行・全列同一、exclude/solution 同一、mask は行集合同一(リスト順のみ;以後ソート出力)。

## 2. (a) 開始
E0(公開 0.464 系譜、24 セル)の Spark 移植を 06:45 に開始(別エージェント)。順序: W7 600 分子の C2 代理(自分子の train 行を除去)→ C1 代理 → パネル 250。段階別出力(engine/PubChem チャネル/ICE・GL/参照 merge/最終)を保存し、`e0_vs_b1_stages.py` で公式 identity 結合 → 段階表・層別 paired Δ。起動後に PID・予定時刻を報告する。

## 3. (b) 層の追加: 母集団の調査(`strata_census.py`、store 全体、MSG 28,929 + 開発済み identity 3,001 を除外 → 自由分子 237,009)

| 層(自由分子) | 全体 | timsTOF あり(= enveda-180) | NP ライブラリ |
|---|---:|---:|---:|
| 参照 1–2 本 | 29,939 | 12,240 | 13,179 |
| 参照 3–9 | 187,225 | 162,061 | 8,714 |
| 参照 10–19 | 15,072 | 3,563 | 3,521 |
| 参照 ≥20 | 4,773 | 650 | 2,260 |
| 参照 ≥20 かつ ≥2 ライブラリ(パネル型) | 2,440 | 645 | 2,105 |
| ≥2 ライブラリ(他ライブラリ参照 = クラス 1 条件が可能) | 10,584 | 2,160 | 9,130 |
| 単一ライブラリ・1 本 | 13,185 | 1,843 | 8,035 |
| 負イオンのみ | 17,873 | 9,911 | 3,092 |
| NH4 のみ | 3,633 | 716 | 302 |
| 被覆正イオン([M+H]+/[M+Na]+)なし | 22,895 | 10,778 | 4,243 |
| 〃 かつ正イオンあり(NH4/K/脱水のみ) | 5,035 | 867 | 1,164 |

事実: (i) 既存 A/B・locked は **[M+H]+ 正イオン spectra を持つ分子からのみ**選んでいる(`p1_select.py` は `adduct == [M+H]+` で母集団を作る)→ 負イオンのみ・NH4 のみの分子は開発集合に 0。(ii) timsTOF を持つ自由分子は enveda-180(合成化学)のみ;NP かつ timsTOF はパネル 250 以外に無い。(iii) 文献数(popularity)は `pubchem_popularity/` に表形式が無く、選択時の層にできない → 候補表の prior 特徴(lsynonyms/pop)で事後層別にする。

### 提案(p2: dev2 = seed 5、locked2 = seed 6、identity group 非重複、fold_identity 0、各層 100 分子 × 2、query は共通関数 max 8、view は C2 / C1)
| 層 | 定義 | 測るもの |
|---|---|---|
| C_np_crosslib | NP ライブラリ、参照 ≥20、≥2 ライブラリ;query ライブラリ = その分子の spectra が最多の NP ライブラリ | パネル体制(他ライブラリ参照多数・NP 化学)でのクラス 1 — 崩壊の再現性 |
| D_np_single | NP、単一ライブラリ、参照 ≤2 | 参照なし体制(両 view で参照 0)、NP 化学 |
| E_np_negonly | NP、負イオンのみ | forward 不在(ICE/GL 0)での最終 merge・fallback |
| F_np_uncovered | NP、正イオンあり・被覆正イオンなし(NH4/K/脱水のみ) | proxy 検証の場(H を隠す比較は不要:本当に H が無い分子) |
| G_tims_crosslib | enveda-180(timsTOF query)、≥2 ライブラリ | 同装置 query + 他装置参照(隠しテストのクラス 1 条件、化学は合成) |
| (事後層)文献数 | 候補表の lsynonyms/pop 分位 | prior の効きすぎ/不足 |

読みの規則(案): 層ごとに paired Δ と CI のみ報告、層の重み付け(隠しクラス比率の推定)はしない。dev2 で手を加えた構成は locked2 で 1 回だけ最終確認(seed 4 の locked は凍結済み)。

**Q1** 層の定義・サイズ(各 100 × dev2/locked2)に異論・追加は。特に C と G の「query ライブラリ」の決め方(最多 spectra のライブラリ vs 乱択)。
**Q2** D(参照 0)は B_nplib と重複が大きいので落として C/E/F/G を 150 ずつにする案はどうか。
**Q3** E/F は forward が無いので learned ranker(GL/ICE 特徴を使う)の挙動が未定義域に入る。これらの層では「保険(固定 + libpri)」も同時に採点し、出力ポリシーの差として読む — で良いか。
