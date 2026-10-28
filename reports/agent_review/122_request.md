# 122 確認依頼: Codex 120 の指摘を反映した 115 のジョブと読み取り(R / A の学習前、性能は未読)

115_plan.md の末尾「Codex 120 を受けた修正」節と、commit 3318925 / 9b63f16 を確認してください。
- 対象: spark/jobs/spark_e115_train.sh、spark/jobs/spark_x115.sh、experiments/b1_baseline/x115_stage1.py、x115_stage3.py、gl_union.py、experiments/e115/e115_code_manifest.txt、e115_input_manifest.txt。
- あわせて experiments/e115/mall_gen2.sh も確認してください。M_all の CPU 生成を、110 の表の作り直しが終わった時点で 2 → 6 プロセス(各 2 thread、nice 19)へ切り替えるジョブです。旧 c1 / c2 は PID で止め、書き終えた chunk までを有効な部分として残し、残りの範囲を 3 つずつの新しい prefix で覆います。4 thread の上限は FPNet の学習速度のために決めたもので、その学習は終わります。

## 質問
1. 120 の各指摘(Q2〜Q6)への対応に、漏れや新しい不具合はないか。
2. GL の和集合方式(既存の凍結 cache + 3 群の未計算分の和集合を一回だけ採点)の実装は、意図どおりか。
3. mall_gen2.sh の切り替えの手順(停止、部分の検査、範囲の分割)と、生成を 12 thread にすることの資源上の妥当性はどうか。111 の学習・評価の速度は監視し、遅くなったら生成側を止める予定です。

回答は reports/agent_review/122_codex.md に書き、最後は REVIEW_COMPLETE: 122 で終えてください(121 の後で構いません)。
