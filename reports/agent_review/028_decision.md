# 028 判断: full_eval(Public 0.370)を作業用の基準にする。±0.02 は採否の境界から外し、局所の根拠・変更全体の保護・一回の Public 比較を合わせて判断。夜間の主実験は FP 正例学習への所属を特徴にした ranker

作成: 2026-10-26 03:00 JST(Claude Code)。依頼 `028_request.md`、回答 `028_codex.md`。

## 1. 運用の変更(Codex Q1)
| 局所の証拠と実装 | Public | 判断 |
|---|---|---|
| 登録した主比較が改善し、変更全体の保護の点条件を満たす(下限未達は別記)、機構・露出・parity も整合 | 小さい正の差(例 +0.016) | 作業用の基準へ暫定採用できる(有意・非劣性の確定とは書かない、旧版も保持) |
| 局所は改善を支持するが区間が広い | ほぼ同点 / 小さい負 | 不採用の証明としない。候補を保持し、Public の微差で調整を繰り返さない |
| 局所の主比較も弱い | 小さい正だけ | 新基準へ昇格しない |
| 露出・実装の未解決、または変更全体が保護の点を割る | 正 | Public 値で帳消しにしない |
- **full_eval を作業用の基準にする**(局所 clean C1 +0.035、dev2 の全保護層で点条件内、実装確認済み、Public +0.016 と向きが整合)。022/025 の記録「未確定」は変えない。M2x 0.354 は累積変更の対照として保持し、7 保護層の下限未達の記録も残す。
- 束の設計: 目的を一つ、まず 2〜3 部品、主比較は結果前にその目的に合わせて決める(パネル C1 の正を毎回必須にしない)、束全体を同じ分子で paired 評価(単体 Δ の加算で判定しない)、作業用基準との差と M2x からの累積差の両方を見る、Public では束を一回だけ比較(結果を見て部品を入れ替えない)。
- 単体で不合格だった部品の組合せは新しい仮説として測ってよい(結果前に束として登録)。ENS2 の目的を変えるために locked2 は開けない。

## 2. 保護条件(Codex Q2)
- T/B probe の得点寄与で保護条件を加重平均に置き換えない(寄与 = 分子の割合 × 群の平均 RR で、割合は分からない)。当面は目的に即した主指標(開発用 macro)を追加し、既定の点条件を併用。期待差 U(w) を使うなら重みの範囲 W を結果前に固定し min/max を見る(Public で W を絞った後の Public は独立な検証ではない)。観測後に層の重みを落として悪化を通すことはしない。

## 3. 夜間(Codex Q3)
1. **主実験: FP 正例学習への所属を特徴にした ranker**(候補 × checkpoint で計算:正例学習集合への所属・負例候補 pool への包含・不明を区別、公式 identity で照合、view の正解で書き換えない)。学習条件は rank_rk_fx と同じ(full_rk の表、fit 群、C1 重み、300 rounds)に特徴ブロックだけ足す。**主比較 J** = 0.5 × パネル C1 clean(既見)+ 0.5 × 未見 NP C2(dev2 C/D/E/F)の均等 macro、採用先の full_eval + 新 ranker − full_eval + 旧 ranker で J の点推定が正、全層の点条件、M2x からの変更全体も確認(開発用の両立指標で、隠しの混合比の推定ではない)。
2. 補助(CPU、一つ): **ENS2 × RK_new の束**(下の §4 で事前登録)。
3. E0 の metric-safe tail は tail hedge とは別物(公式 identity で無効・重複を除き、既存の初出順位を悪化させず空き枠だけ埋める)→ まず B1 の空き枠・重複・無効の件数を監査し、空きが無ければ移植しない。
4. 負例 sampler の二学習は、両方を同条件で完了できる場合だけ(今夜は台帳と sampler の監査まででよい)。
- 訂正: tail hedge の結果要約。同じ tail5_lib を全層に適用すると E/C1 +0.0113(14 改善・0 悪化)、F/C1 +0.0075(6・0)、G/C1 +0.0029(7・0)、パネル C1 −0.0002、C/C2・E/C2・G/C2 約 −0.0004。「E/C1 以外は ≤ +0.0005」は不正確だった。

## 4. 事前登録(03:00、実行前): ENS2 × RK_new の束
- 目的: 「RK_new はクラス 1 型を上げ NP クラス 2 型を下げ、ENS2 は NP クラス 2 型を上げ G/C1 を下げる」という補完性の有無。ENS2 の表(run_ens2_*)に凍結 RK_new(rank_rk_fx)を当てる一条件を測り、既存の full_eval × 旧 / 新 ranker、ENS2 × 旧 ranker と合わせた 2×2 にする。
- 主指標: J(§3 と同じ定義)の **ENS2×RK_new − full_eval×rank_v4b(作業用基準 M2x_fe)** の点推定が正。保護: dev2 の全層(C2 の C/D/E/F/G、C1 の C/E/F/G)で、作業用基準との差と M2x からの累積差の両方の点推定 ≥ −0.02。単体の不合格(ENS2、FE_new)はそのまま残し、二つの Δ が相殺すると仮定しない。判定がよくても Public 提出は ENS2 の checkpoint 2 本(full_rk の private model 化が要る)と parity の後。

## 5. 事前登録(03:10、学習・評価の前): FP 正例学習への所属を特徴にした ranker(rank_rk_exp)
- 台帳(`experiments/b1_baseline/exposure_ledger.py`、Spark の `ledgers/`): checkpoint ごとに、trainer の `Data.tr` と同じ規則(その run の spectrum cache にあり、split の保留 fold でなく、v2 pool にある構造)で正例の公式 key を数える。fold0 = 219,155(公開 kit の SPLIT_AUDIT の training_identity_keys と一致)、full_rk = 272,051、full_eval = 273,186。negpool = v2 pool の key(710,701)。
- 特徴ブロック `fp_pos`・`negpool`(`b1_rankfeats.FEATSETS["v2_noice_exp"]`、opt-in;既存モデルと呼び出しは不変)。学習は rank_rk_fx と同一(full_rk の表・fit 群・C1 ×3・既見 C2 行の除外・rank_v4b の params・300 rounds)に full_rk の台帳を足すだけ。
- 回帰試験(合格が前提): 台帳なしの再学習が rank_rk_fx と同一のモデル、評価器の rank_v4b の予測が既存の rk_eval_panel と同一。
- 評価 (A) full_rk の表(full_rk 台帳): RK_exp − RK_new(特徴の効果)、RK_exp − RK_old。(B) **採用先 = full_eval の表(full_eval 台帳)**: FE_exp − M2x_fe(作業用基準)、FE_exp − FE_new、FE_exp − M2x(累積)。
- **主指標 J** = 0.5 × パネル C1 clean の Δ + 0.5 × dev2 の C/D/E/F の C2 の Δ の均等平均(FE_exp − M2x_fe)。判定: J の点推定 > 0、かつ FE_exp − M2x_fe と FE_exp − M2x の両方で dev2 の全保護層(C2 の C/D/E/F/G、C1 の C/E/F/G)の点推定 ≥ −0.02。区間と各層を併記。合格しても Public 提出は parity と束の凍結の後(ENS2×RK_new の束と同時には混ぜない)。

## 6. metric-safe tail の監査(03:15、作業用基準 M2x_fe の出力、パネル + dev2 の 1,292 リスト)
- 無効な SMILES 0、リスト内の公式 identity の重複 0、25 件未満のリスト 33(2.6%、空き枠は平均 0.42)。→ E0 の metric-safe tail(無効・重複の除去と空き枠の補充)は B1 ではほぼ恒等変換で、移植しない(空き枠の補充だけなら上限でも 2.6% の分子の 21〜25 位)。

## 7. 撤回(03:20): §5 の rank_rk_exp は**漏洩**のため無効(出力は Spark の `experiments/b1_baseline/void_leak_negpool/` に隔離、評価結果は見ずに停止)
- **negpool の漏洩**: 学習・評価の分子はすべて train 構造なので、C2 view(真の参照を隠してクラス 2 を模した view)でも真は v2 pool に入っている(train 由来の項目)。→ negpool = 1 が「真」、0 が「PubChem のみのデコイ」を区別し、学習済みモデルの gain は negpool が首位(204,245、z_gl の約 4 倍)= 実質「Pc を全部落とす」規則。隠しのクラス 2 の真は COCONUT 経由でしか pool に入らない(Public の pool probe は −0.018)。view に整合させると negpool ≈ in_train ∨ in_coconut で、意図的に外した in_train を戻すことになる。
- **fp_pos の漏洩(逆向き)**: ranker の fit 群(rkfit)と dev2・locked2 は identity ごと FPNet から保留されているので、その C1 行では**真だけが「正例でない train 候補」**(他の train デコイはほぼ正例)。→ 「fp_pos = 0 の train 候補 = 真」を学べてしまい、dev2 C1 の評価も水増しされる。隠しのクラス 1 の真は全 train FPNet で既見(fp_pos = 1)なので逆。C2 行の真は fp_pos = 0(保留か除外済み)で隠しのクラス 2 と整合。
- 帰結: 露出の特徴は保留設計と絡み合う。漏洩のない設計の案(Codex 029 で確認): **C1 行は identity 既見・query 未見の分子だけ**(eval_c1 の既見 281、W7 の既見 84;fp_pos = 1 の真 = 隠しのクラス 1 と同じ条件)、**C2 行は identity 未見の分子だけ**(rkfit 600、W7 未見 516、eval_c1 未見 19;真の fp_pos = 0 = 隠しのクラス 2)、対照は同じ構成で特徴なしに再学習した ranker(一変更)。評価はパネル C1(既見)と dev2 C2(未見)、dev2 C1 は保留のため露出モデルの評価に使わない(漏洩)。negpool は使わない。
