# Public method map(2026-10-30 19:40 JST、Librarian = Claude Code)

## 皆がやっていること
- 検索 + 複数の証拠の順位付け: train + COCONUT(約 71 万)の pool、PubChem / ChEBI / PubChemLite の経路(±10 ppm)、FPNet の指紋、LightGBM の ranker、人気の事前分布、RRF の融合。Public 0.46〜0.50。改善は CV で検証されていない。

## 上位公開Notebookだけがやっていること
- E0(v18 系譜、Public 0.464): 上位 25 の中の同じ分子式の組を ICEBERG / GLACIER で並べ替え(枠を保つ)、PubChem だけの経路を決まった枠に差し込み、条件で 1 位に昇格、analog からの生成(親 6、変換 46)、MetFrag-lite、二つのエンジンの RRF(fuse2)。
- 最上位(10/23 で 0.504)の手法は非公開。

## 誰もやっていないこと(未観測を不在の証拠にしない)
- バッチの単位でクラスを隠した世界(W135)での検証と、そこで学習した最終の採点器(生成物を含む固定の候補の宇宙)。
- バッチの中の家族の整合(NAP 型の伝播)を順位に使うこと(公開では未観測)。
- C3 で LB を大きく動かした例(751300: 手元の検証は動くが LB は動かないという報告が複数、小さな +0.003〜0.004 の報告が 1 件。753400: 正味 +0.004〜0.010 の見込みで不採用)。

## 自分たちがやっていること
- P(v8w7a、Public 0.394)、独立のエンジン E2(MetFrag-lite + analog + LightGBM)、F = P + E2 の RRF(Public 0.414、暫定の作業基準)。
- W135 の世界(d / c / e、π3 0 / 0.3 / 0.6)、FH v0(NO)、v2 = FH-PEB(U2 = P25 ∪ E25 ∪ B、主対照 F-world、G0 待ち)。
