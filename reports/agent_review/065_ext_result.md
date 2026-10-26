# 065 EXT ベンチ(2026-10-27 06:51 JST): train に無く MassSpecGym にも無い外部構造 60 分子(GNPS 39 / MassBank 13 / MoNA 8、74 スペクトル)

- 全モデル(FPNet full_eval・公開 fold・ranker・ライブラリ・GLACIER)に未見の、小さいが清潔な集合。正解が PubChem/COCONUT にあるか(到達)も測定に含まれる(クラス 2/3 の混合)。作成: `make_ext_test.py`(E0 の knowledge table の external_delta、delta_kind = structure_without_train_spectrum、試験の adduct、質量検査が診断閾値内)。
| 構成(0.379 の pipeline、b1_ana035) | MRR@25 | 固定規則 | GNPS | MassBank |
|---|---:|---:|---:|---:|
| rank_v4b(現行) | **0.5054** | 0.4632 | 0.614 | 0.106 |
| rank_v8w | 0.5012(−0.004) | 0.4632 | 0.625 | 0.106 |
- v8w は EXT で ≈0(n 60 なので ±0.03 程度は判別できない)。v8w の証拠をまとめると: fold-safe の f1/f2 dev +0.013、予約 3b/4b +0.0067、dev2 ≈0(−0.002)、EXT −0.004 → **真の効果は小さい正(+0.005 前後)と見るのが妥当**。Public での判別は難しい規模。
- FPNet の選択(F / P = 公開 5 本 / fold0 単体)を EXT で比較中(066)。

## 066: FPNet の選択(rank_v4b 固定、EXT 60 分子、paired、2026-10-27 07:04)
| 構成 | MRR@25 | 対 F の差 [95%] | 改善 / 悪化 |
|---|---:|---|---|
| F = 自前 full_eval(本番) | 0.5054 | — | — |
| P = 公開 fold 5 本の logit 平均 | 0.5250 | +0.0196 [−0.0226, +0.0674] | 7 / 8 |
| 公開 fold0 単体 | **0.5436** | **+0.0383 [+0.0030, +0.0806]** | 8 / 5 |
- **全モデルに未見の分子では、公開 fold0(rank_v4b の学習表と同じ FPNet)が本番の full_eval より良い**(区間はぎりぎり 0 を含まない、n 60)。一方 064 の dev2(fold0 と full_eval の両方に未見)では full_eval の方が C C2 +0.026、G C2 +0.020、D C2 −0.011 — 集合で向きが違う(dev2 は full_eval の採用判断に使った集合)。
- 含意(仮説): full_eval の Public の利得(0.354 → 0.370)は既見のクラス 1 の記憶によるもので、未見のクラス 2 では full_eval が公開 fold モデルより劣る可能性がある。本番の候補として「0.5F + 0.5P」(既見は F の記憶、未見は P の汎化)を、係数を先に固定して評価する価値がある(Codex 062 の Q3 と同じ形)。EXT は小さいので、追加の清潔な未見集合が要る。
