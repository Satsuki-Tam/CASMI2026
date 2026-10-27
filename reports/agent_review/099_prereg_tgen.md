# 099 事前登録(探索の開発): test 側の親による生成(transductive generation)— パネル(fold-safe 表)での測定

作成: 2026-10-28 02:32 JST(Claude Code)。Codex 099 の回答前の暫定(回答が結果の前に届けば追記で調整)。家族構造を持つ開発集合がパネルしか無いので**探索の位置付け**(採用の判断は別の登録と確認で)。
- 表: run_panel_f0(パネル 250、fold-safe fpnet_fold0 = パネルに未見、GL、gen dump)。評価器 gen_eval2fd(v7f 主出力、rank_v7a)、views c1 / c2 / c3。
- **A**: 基準 + 各分子の主出力の上位 25 の dump(test 側の親 = c2 view の 1 位)。**B**: test 側の親だけ(他の 249 分子の 1 位、sim 1.0)で生成 → 既存の gt3 規則(最良の新規生成物を、その f·z が主リスト 3 位の f·z 以上なら 3 位に挿入)。**C**: train の analog 親 10(従来の gt3 の構成)。**D**: C + test 側の親。
- 主に見る量: c3 view(正解を DB から除く = クラス 3 の模擬)の gt3 の MRR と「正解が生成された率」を B / C / D で比較;c2 / c1 view の gt3 − main(挿入の費用)。
- 予想(結果前に記録): 真の構造を親にした上限は 30%(tgen_panel.py)。予測した 1 位を親にすると、親の正答率(パネル c2 の 1 位率)分だけ下がる。
