# 102 依頼: 第二エンジン E-lite の事前登録のレビュー(結果の前)

登録案: reports/agent_review/102_prereg_elite.md。実装: experiments/b1_baseline/e_keys.py(新規)、b1_rankfeats.py(FEATSETS["e1"])、b1_rank_train.py(--restrict E / --ekeys / --pointwise)、gen_eval2fd.py(--emodel / --ekeys / --rrf_k)、rank_params_e1b/rank_results.json。学習と評価は Spark で開始しますが、**登録が確定するまで結果は読みません**(変更が必要なら再計算)。

新しい事実: E0 の engine 2(experiments/e0_offline/cells/08.py に埋め込まれた casmi_engine.py / pv.py)の特徴には人気度・候補源の項が一つも無い(pv.rank_features = ライブラリ類似度・analog・FP logits・MetFrag-lite・交差項・窓の大きさ;追加 block = 質量誤差・lib mean/shift/count・極性別 analog・adduct 別 frag)。

質問:
- Q1: 第一段を「既存の表の行を E 窓に制限し、人気度・候補源の特徴を除いた別 ranker(点ごと主 + lambdarank 対照)を RRF で混ぜる」にする設計で、101 の問い(現基準の誤りを救う第二リストがあるか、候補源の加重と新しい順位を区別できるか)を判別できるか。足りない対照・余計な自由度は。
- Q2: 主指標を 053 NP C2(COCONUT 正解)と f1/f2 NP C2(人気度が隠しに近く PubChem のみの正解が多い)の 2 ブロック平均にし、各ブロックの非劣性を課す案の妥当性。隠しの T / B / Pc の構成が不明な中で、片方だけでの採用を防ぐ意図。
- Q3: K = 10 固定、α ∈ {0.5, 1}、候補 6 つ(rrf_pe を含む)から関門通過の最大を一つ選ぶ規則。選択の自由度が確認で吸収できる範囲か。
- Q4: 確認: np096_conf093(H/N 400、093 用に予約・未開封)の用途変更 + 新しい fold 0 の D 型集合(人気度が隠しに近い側のブロック)+ c1cost098。この構成でよいか、件数の目安。
- Q5: e1 の特徴(fp_rank_window を除く、相対特徴を E 窓内で再計算、GL を含む)について、E0 の engine 2 と違う点で、相補性の判定を歪めるものがあるか。
