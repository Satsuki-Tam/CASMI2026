# 119 相談: 115 v2 の学習コードの点検(学習・性能の前、2026-10-29 02:10 JST)

Codex 118 を受けて作り直した 115 v2 の実装を、学習に使う前に点検してください。性能はまだ何も読んでいません。

- 計画: reports/agent_review/115_plan.md の「v2」節と「v2 の固定値」節(S = 24,000、e = 0.577 の根拠、R / A 共通のレシピ)。
- コード: experiments/e115/make_simplan.py(M_all のカタログ・巡回・必要な job だけの生成リスト;alias 24 行は正規行へ対応付け)、experiments/e115/train_fpaug2.py(公開の規則の負例 + 正例自身の identity 除外、全体で一つの巡回カウンタ、消費した模擬の台帳、生成の完全性検査と複数 prefix の完全被覆、用途別の RNG、模擬の augmentation)、experiments/e115/gl_simulate.py(--start / --stop の大域 index、chunk ごとの meta 更新、原子的な shard 書き込み)、experiments/e115/mall_gen.sh(cat15k の CPU 生成の後に nice 19 で 2 プロセス)。
- 生成物: experiments/e115/mall_plan_manifest.json(catalog 447,245、jobs 894,490、COCONUT 行 462,261、alias の対応 24、構造規則で除外 101)。
- 小試験: CPU で R の 3 更新(loss 有限、対象枠の割合 0.531)。A の小試験は cat15k の生成完了(4:40 頃)後に、cat15k の既存 job に対する計画(make_simplan existing)で行う予定。

## 質問
1. train_fpaug2.py の負例・巡回・台帳・RNG・読み込みの実装に、Codex 118 の意図とずれる点や不具合はあるか(特に: 複数 worker の共有カウンタと prefetch の扱い、正例自身の identity の除外の作り方(pool 行 → identity の対応)、窓 < 8 の扱い、生成の meta の整合検査)。
2. make_simplan.py のカタログ規則(src 2 / 3、alias → 正規行、150〜1,200 Da、構造規則)と巡回(条件の置換・巡回順の hash)は、性能の前の固定として十分か。
3. S = 24,000 の決め方(2 巡、e はメタデータから)と、R を生成の完了前に GPU で先に学習する順序は妥当か。
4. A の小試験で確認すべき項目(台帳・被覆・速度・メモリ)の過不足。

最後は REVIEW_COMPLETE: 119 で終えてください。
