# 10/30 の提出計画(2) — 145 / 144 v2: F = P(v8w7a)+ E2 の identity RRF(K 10、α 0.5)(2026-10-30 11:07 JST = git 42da166、Claude Code)

## 位置づけ
- 144 の登録 v2 の判定(144_result.md、8777e2c)
  - F のローカル関門: 不合格(主指標 +0.0035)。
  - H: 不合格。出さない。
  - Public の診断経路: 条件を満たした。
- 登録どおり、F を「ローカル不合格の診断提出」として一度出す。
  - F は、最終提出にもなり得る完成した候補であり、プローブではない。
  - P(0.394)の置き換えは、Public を見る前に決めない。
- 132(E-lite)とは別の凍結候補である。132 の順位を F の対照に置き換えない。

## 提出する実体(全て凍結してから出す)
- **カーネル**: hayatetaf/casmi26-b1-e2f version 1(11:06:30 に push)。
  - 埋め込み: b1_pipeline.py 72a1a991…(make_e2k v2、LF)、e2_engine.py 85a429b6…、e2_common.py 3b34d05f…、ranker = v8w7a の stripped。
  - 引数: v8w7a の引数に、`--e2_model e2_lgb.txt --e2_model_sha fba8e860… --e2_hedge 0` を加えたもの。
- **データセット**: private の hayatetaf/casmi26-e2-model。
  - e2_lgb.txt(fba8e860…)
  - e2_ik14_to_scorer.parquet(2f025d15…、E2 専用の、開発と同じ索引)
  - manifest
- **P の不変**: GL / ICE の予算は、E2 の時間を除いて計算する。P の索引と analog store は、従来のまま凍結する。

## 提出の条件(全て満たした場合だけ)
1. Spark のパネル C1 の一致確認 v2(e2k_parity_check v2)が PASS すること。
   - 分子の全数、NaN を区別した列の一致、E2 の順位、オフラインの F、参照の P との順序付きの一致、e2_failed = 0。
2. Kaggle のコミット実行の点検(check_e2k_commit.py F)が PASS すること。
   - P が v8w7a の参照のコミット実行と byte 一致すること、引数、埋め込み、manifest の E2 の部分、E2_RECORD / E2_RDKIT。
3. 評価器 v3(Codex 145 の訂正: 名簿・順序の検査・固定の所属表)の再採点で、診断経路の条件が保たれること。
   - E 源の正解の C2 で、F − P が両 fold で正。
   - 新たに 1 位になった identity が 10 以上。
4. C2 の正解の別表記の監査(x145_alias_audit)で、楽観が判定を左右する規模でないこと。結果は記録する。

## 提出の命令(条件を満たした後に一回)
```
kaggle competitions submit enveda-CASMI26-molecule-id-mass-spectra -k hayatetaf/casmi26-b1-e2f -v 1 -f submission.csv -m "145 F = v8w7a + E2 identity RRF (K 10, alpha 0.5); 144 v2 local gate not passed -> registered Public diagnostic path; parity v2 + commit check PASS"
```

## 読み(登録 144 v2 §4'。Public を見た後で α / K / 窓を動かさない)
- 0.409 以上: 明瞭な正。新しい土台の候補とし、P を置き換える。
- 0.380〜0.408: 保留。開発の構成とのずれ(E 源の外の費用、人気度)を分析する。
- 0.379 以下: 負。F を主系に入れず、窓への到達・条件付きの救済・E 源の外の費用から、不足した場所を判定する。
