# B1(v8w7a)の外部依存と生成経路の台帳(Codex 124 の手順 1;時刻は git の commit 時刻)

目的: 賞の適格性の論点(運営 745072・742265、未回答の 753662)に備え、v8w7a の kernel が実際に読むファイルと、それを作ったコード・元データを一か所にまとめる。**現在 B1 が失格だという証拠は無い**(運営 10/9: 公開データセットでの開発は問題ない)。重みについては運営の回答が明確(第三者の重みは元の学習コードが無ければ賞の対象外、自前の再学習は可)。

| # | 使っているもの | 入手元 | v8w7a での役割 | 作った人 / 生成・学習コード | 状態と次の作業 |
|---|---|---|---|---|---|
| 1 | train.parquet / test.parquet | 競技データ | 参照スペクトル・学習 | 運営(train は open source 扱い、10/9) | 問題なし |
| 2 | FPNet 重み `full_eval_final.pt` | hayatetaf/casmi26-b1-fpnet-fulleval(自前の private model) | FP 予測 | **自前で学習**(experiments/fpnet_full: prep_full_eval.py、train_fivefold_win*.py、学習 manifest) | 学習コードあり。提出物には入力版・split・bits・環境の対応を添える |
| 3 | LambdaRank `lambdarank.txt`(rank_v8w7a) | notebook に埋め込み | 主リストの ranker | **自前で学習**(experiments/b1_baseline の学習スクリプト) | 学習コードあり |
| 4 | `fp_bits.npy` | dmitriigluzdov/casmi26-fold-safe-fpnet | FPNet の出力 bit の定義 | fold-safe kit(学習記録・manifest は同梱、bit 選択の生成コードは**未確認**) | 生成コードの所在を確認。無ければ train から bit 選択を自前で再現できるか調べる。現行の pipeline は bits のディレクトリを `fpnet_fold0.pt` の所在から探す(Codex 124 の指摘)→ 小さな配布物に変える時はこの依存を外す |
| 5 | `casmi` パッケージのコード(chem・FPNet 定義・特徴化) | casmi26-v3-models/code(attributed assets 経由、元は ahmedberatozer) | 推論コード | 公開コード(ライセンスファイル無し、規則 6.b の扱いは未回答)。v3 の**重みは使っていない** | 使っている関数を特定し、必要なら自前で再実装 |
| 6 | PubChem tier `pc_mass / pc_off / pc_smiles`(105,875,489 行、質量順) | ahmedberatozer/casmi26-pubchem-tier(attributed assets にも複製) | PubChem 候補の窓 | **生成コードは見つからない** | 必要になれば PubChem の CID-SMILES から自前で作る(元の絞り込み条件は不明 → 別の資産として評価し直す) |
| 7 | pool `pool_meta.parquet`(710,701 行 = train ∪ COCONUT) | ahmedberatozer/casmi26-v2-pool(attributed assets) | 主の候補窓 | **生成コードは見つからない** | train.parquet + COCONUT から自前で作れる(key・pid の順序・src の定義を仕様にする) |
| 8 | 人気度の 6 列 `pc_/pool_{lsid, lpmid, lsynonyms, np, src_mask, lotus_refs}` | dmitriigluzdov/casmi26-pubchem-popularity-prior | 文献の事前分布・NP 所属 | **生成スクリプトが同梱**(build_pop.py、build_annot.py、build_sources.py、download_sources.py、build_delta.py、make_source_groups.py;TECHNICAL_NOTES に手順) | 小さな固定標本で、スクリプトの出力が配列と一致するかを確かめる(行の対応・代表 CID・float16 化を含む) |
| 9 | `pubchemlite_annotations.parquet` | 同上 | PubChemLite の注記 | 同上(PubChemLite は Zenodo) | 8 と同じ |
| 10 | COCONUT 候補 `coco_mass.npy / coco_meta.pkl` | prvsiyan/coconut-casmi26-candidates(CC BY-NC-SA の表示) | COCONUT の候補 | **生成コードは見つからない** | 運営は「元データから作り直した同等物は可」と回答(10/14、kowero への 3 点目)→ COCONUT の取得から自前で作る |
| 11 | GLACIER / ICEBERG の重みと runner | casmi26-glacier / casmi26-iceberg(attributed assets)、重みは ms-pred の MSG 版 | forward model | 重みの学習コードは ms-pred で公開(MSG のみで学習、運営が名指しで許可)。runner は公開 notebook 由来 + 自前の GB10 用修正 | 重みの hash・学習コード・学習データへの経路を記録 |
| 12 | RDKit などの wheel | attributed assets | 実行環境 | 公開パッケージ | 問題なし |
| 13 | knowledge table / panel benchmark | dmitriigluzdov の 2 データセット | **v8w7a は読んでいない**(pipeline と wrapper に参照なし) | — | 次に kernel を作る時に添付から外せる |

## 手順(Codex 124)
1. この台帳(済み)。2. 既存コードの充足確認: 8・9 のスクリプトで小さな標本を再生成して一致を確かめる。4 の bit 選択の生成コードの所在。3. 不足分(6・7・10、必要なら 4・5)の小規模な再生成の試作。
- 111 / 115 の計算資源は削らない。運営の回答(753662)で要件が明確になった部分から本格化する。新しい snapshot で出力が変われば「再現」ではなく別の資産として評価する。
