# 065 EXT ベンチ(2026-10-27 06:51 JST): train に無く MassSpecGym にも無い外部構造 60 分子(GNPS 39 / MassBank 13 / MoNA 8、74 スペクトル)

- 全モデル(FPNet full_eval・公開 fold・ranker・ライブラリ・GLACIER)に未見の、小さいが清潔な集合。正解が PubChem/COCONUT にあるか(到達)も測定に含まれる(クラス 2/3 の混合)。作成: `make_ext_test.py`(E0 の knowledge table の external_delta、delta_kind = structure_without_train_spectrum、試験の adduct、質量検査が診断閾値内)。
| 構成(0.379 の pipeline、b1_ana035) | MRR@25 | 固定規則 | GNPS | MassBank |
|---|---:|---:|---:|---:|
| rank_v4b(現行) | **0.5054** | 0.4632 | 0.614 | 0.106 |
| rank_v8w | 0.5012(−0.004) | 0.4632 | 0.625 | 0.106 |
- v8w は EXT で ≈0(n 60 なので ±0.03 程度は判別できない)。v8w の証拠をまとめると: fold-safe の f1/f2 dev +0.013、予約 3b/4b +0.0067、dev2 ≈0(−0.002)、EXT −0.004 → **真の効果は小さい正(+0.005 前後)と見るのが妥当**。Public での判別は難しい規模。
- FPNet の選択(F / P = 公開 5 本 / fold0 単体)を EXT で比較中(066)。
