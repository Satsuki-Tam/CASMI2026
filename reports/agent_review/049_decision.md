# 049 判断(2026-10-27 02:39 JST)— Codex 049 の回答を受けて

## 採用
1. **優先順位**: (i) 正イオン proxy(050 実行中、負イオンは別仮説として扱い平均しない)と ranker の重み対照(056 で実行中: v8w = pool C1 ×1、v8n = pool から G を除く)、(ii) B 群の一対 probe(今日の枠 4・5、055 で読みを固定、kernel push 済み)、(iii) E0 型 pool 経路の分解(到達・shortlist・decoy 数・forward 被覆 → 同じ候補での ranker レシピ比較)、(iv) 露出を揃えた 2 本の FPNet ensemble(自前の fold-1 除外モデルの学習が必要)と MIST の入力試験、(v) テスト間関連の小試験。ggt3t は予定どおり完成させる。
2. **probe の読み**: B 群に絞った方策の MRR(群内で順位が詰まる量)であり、元の全体への寄与や class 比率ではない。E0_B は旧 0.354 の B1_B(0.202)ではなく現行 0.379 の B1_B と一対で比べる。
3. **評価の役割分担**: 主な改善対象 = 未見 NP C2(C/D/E/F 等重みマクロ、同じ分子・checkpoint・候補資産の一対比較);主保護 = 採用時のモデル露出に対応した identity 既見・query 独立の NP C1 と NP C2 各層;stress = identity 未見 C1、G の C1/C2、パネルでの本番と異なる ensemble 混合。−0.03 のような緩和幅は根拠なく決めない(049b の placebo の議論と合わせて次の登録で固定)。
4. **ensemble とパネルの露出**: 公開 fold-safe の 5 本は全 fold でパネルの identity 群を学習から除外している → 自前 full_eval + 公開 5 本では、パネル C1 は「既見 1・未見 5」で本番の通常の train 内 identity(既見 5・未見 1)と混合が違う。ensemble のパネル C1 は stress として読む。
5. **外部スペクトルの訂正**: 782 identity = train 内 672、train 外 110(全部が未見 C2 ではない)。110 は小規模な未見 C2 proxy、672 は監査後に C1 の候補。
6. **proxy の対象**: 実際の query 選択とピーク cut 後に proxy を作れるかで判定(q_proxy_capable フラグでは混在 adduct を取りこぼす)。現実装(forward_proxies)は混在でも NH4 / 水脱離のスペクトルごとに proxy を作るので、fold-1 F の proxy 対象 84/100 は Codex のメタデータ集計(84)と一致。

## 保留 / 利用者の判断が要る点
- **E0 を第二の提出基盤にする選択肢**(Codex の提示): 10/24 に利用者が「公開 notebook への継ぎ足しはやめ、自前の B1 を作る」と決めているため、Claude の判断では採らない。朝のまとめで選択肢として記載し、判断を仰ぐ。

## 自分の追加の観察(052)
- 開発集合の「NP 層」は正解の 2/3 が非 NP の化学で、パネル(隠しに最も近い)は 99.6% が COCONUT の NP。NP の正解では GLACIER が弱く prior が強い → NP 正解の開発集合(053、fold-1/2 の dev 各 320 + 閉じた conf 各 320)と、パネルを fold-safe FPNet で未見にした class-2 ベンチ(054)を作成中。次の Codex 依頼(053)で評価の主対象をこれに移す提案をする。
