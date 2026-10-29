# 134 事前登録(草稿、Codex の点検の前): GLACIER の timsTOF 適応 — 段階 2(GL 単独の比較)

作成: 2026-10-29 21:08 JST(Claude Code、date)。105 の段階設計の段階 2。結果(学習・評価)の前。

## 0. ここまで(段階 0 / 1、experiments/glt/STAGE0.md)
- 学習環境 .venv-glt(推論環境の上に本物の LinSATNet / pygmtools と前処理の純 Python 依存)。checkpoint の linsat_tau 15 では LinSATNet の shim と本物の top-k は全件一致(推論は不変)だが値は一致しない → 学習は本物を使う。
- 0b PASS: 公開 checkpoint を学習用 JointModel に strict に読み、MSG の小 batch で損失・勾配が有限、全 259 tensor が更新され、過学習で損失が下がる。
- 段階 1 PASS: C0'(学習環境を通して公式形式で保存)は 264 tensor が bit 一致、gl_runner --ckpt の採点は公開版と同じ入力で 2,320 組すべて差 0。保存 cache とは batch 構成の違いで最大 0.005 ずれる → **比較は C0' と適応版を同じ入力で同時に採点**して行う。
- データ(data/glt/tims_s1、make_glt_data.py): enveda-180(timsTOF)の [M+H]+、identity fold 3 / 4 のみ、全名簿の identity group 18,969 とパネル 250 を除外、固定 hash 順に 2,000 identity・5,135 スペクトル(CE 20 / 40 / 60 eV)、val 202 identity(521 スペクトル)。前処理(ms-pred の MAGMa → 部分式 → 強度)済み。instrument token は推論と同じ QTOF。

## 1. 比較(一変種)
- **A = C0'**(公開の重み)、**B = 適応版 A1**: finetune_glt.py --trainable inten(強度側 inten_encoder / inten_decoder / output_map / collision の埋め込み、660 万 parameter;グラフ encoder・断片 decoder・mapper は凍結 = 提案される断片の集合は変えない)、損失はモデル自身の学習目的(_common_step 'train')、AdamW lr 1e-4・wd 0、warmup 100 step の後は一定、勾配の値で clip 5、**1,500 update 固定**(約 5 epoch)、batch 16、seed 0。val 損失は記録のみ(早期終了・checkpoint 選択なし)。
- 採点: gl_runner.py(推論の runner、--ckpt)で A と B を**同じ runner 入力**で採点: パネル P_np250(Enveda の timsTOF の NP、適応データから除外、ただし base GLACIER は MSG で 226 / 250 を既見)、f1dev G_tims_crosslib(timsTOF、合成化学)、np053f1dev NP_H と f1dev D_np_single(NP、主に timsTOF 以外;費用の確認)。
- 読み取り: gl_only_eval.py(view c2;rr_form = 同じ中性分子式の候補の中での真の GL 単独の順位の逆数、rr_gl = 全候補での GL 単独の RR@25、top1_form、margin_form)。

## 2. 関門(段階 3 = 主出力への接続へ進むか)
- 主: **timsTOF の 2 cell(パネル c2、f1dev G c2)の rr_form の B − A の平均 ≥ +0.01 かつ 95% 下限 > 0**。
- 非劣性(下限 ≥ −0.01): NP_H c2 と D c2 の rr_form、4 cell すべての rr_gl。
- 通らなければ:この一変種の記録として止め、学習の範囲(全 parameter)・対照学習(同式 decoy)は別の登録で検討する(結果を見て学習率等を探索しない)。
- 段階 3(通った場合): v8w7a の候補・出力規則を固定し GL だけ B に替えた比較、および旧 / 新 GL の特徴で ranker を同じ手順で学習する比較(露出を揃えた OOF の GL 特徴)。登録は別に行う。

## 3. 露出と限界
- 適応の identity は fold 3 / 4 で、ranker の学習 pool(f3a / f4a)とも重ならない(全名簿を除外)。段階 3 で ranker を新 GL 特徴で学習する場合は、学習行の GL に適応データの露出が無いことを確認する。
- パネルは base GLACIER の既見 identity が多い(timsTOF への適応の効果は読めるが、未見 identity への効果は G と NP の cell で読む)。

## 4. 段階 0 の追加の検査(Codex 133 Q4、結果の前)
- 学習の勾配経路で実際に動くのは scatter_max(shim)・本物の LinSATNet・本物の pygmtools だけ(DGL の shim は呼ばれない)。scatter_max は学習用の shim(勾配を argmax へ送る torch_scatter の意味)を参照と照合して合格。変種 A でも CE 埋め込みを通じて LinSAT の値が勾配に入るため、本物の LinSATNet を使う。
- データ・損失の契約(5,135 件)は違反 0。
- 段階 2 の run の中で: export → gl_runner での strict な再読込、凍結 tensor の bit 一致、学習対象の変化、同じ 10 分子で適応版の採点が C0' と異なること(重みが使われる)を確認し、満たさなければ評価に進まない。
- 学習は「GLACIER の強度側の追加学習(断片の提案と graph encoder は凍結)」であり、full GLACIER の学習の再現とは呼ばない。

## 5. 確定版 v2(2026-10-29 22:19、Codex 134 を受けて、段階 2 の結果は未読)
- **v1 の A1 は使わない(未読のまま保存)**: (1) collision_embedder_denominators / collision_embed_merged は本家の constructor で requires_grad = False の CE 符号化で、v1 の trainer はこれを学習可能にしていた(CE 表現は断片側にも渡るので、断片の提案集合も変わり得た)。(2) 新しい JointModel は step 0 から始まり、magma_warmup_steps 2,500 の間の学習の損失は「MAGMa 断片上の強度 + 断片」で、end-to-end の強度損失は入っていなかった(1,500 update はすべてこの期間)。A1 の採点(stage2_gl/gl_*_A1.json)も読まない。
- **一候補 A2**(finetune_glt.py v2): 更新するのは **inten_encoder / inten_decoder / output_map だけ**(他は本家の requires_grad も含め固定、CE 符号化も固定 = 断片の提案は不変)、損失は **end-to-end の強度損失を明示的に最適化**(推論時と同じく、モデル自身が予測した断片の上の強度;本家の学習分岐と同じ cosine、Hungarian なし)×inten_weight。AdamW lr 1e-4・wd 0・warmup 100 の後一定・勾配の値で clip 5(clip の前に勾配の有限性を検査、更新後の parameter の有限性も検査)、1,500 update 固定、batch 16、seed 0、早期終了・checkpoint 選択なし、val 損失(モデルの検証損失、Hungarian あり)は記録のみ。sampling はスペクトル一様(identity あたり最大 4 スペクトル)。学習の前に CUDA の代表 batch で forward / backward / 1 update の事前検査(CPU では PASS:学習対象 110 tensor がすべて更新、凍結の変化 0)。学習後に凍結 tensor の bit 一致と export → runner の strict な再読込、10 分子で C0' と得点が異なることを検査。LinSATNet / pygmtools / 学習用 scatter shim / torch のパスと版を記録。
- 学習データの CE は 20 / 30 / 40 / 60 eV(§0 の 20 / 40 / 60 を訂正)。
- **評価器 v2**(gl_only_eval.py): 分母は選択名簿の全件(空の窓・正解未到達は両群 0)、真の GL が欠損なら rr_gl = 0(v1 は候補数を順位にしていた)、rr_form は真の式を使う能力診断(25 位で切らない)で rr_gl@25 と区別、A と B の非 null の (分子, SMILES) の集合と runner の状態・採点分子数の一致を要求(不一致は STOP;B が decoy を採点できずに rr_form が上がる値を利得にしない)、公式 key の重複は STOP、identity 単位の bootstrap、同式の競合 2 件以上・singleton・被覆を併記。
- **関門 v2**(x134_read.py v2): **主 = f1dev G c2(timsTOF、base・適応とも未見)の rr_form の A2 − C0' ≥ +0.01 かつ 95% 下限 > 0**。費用(下限 ≥ −0.01): NP_H と D の rr_form、4 cell 各々の rr_gl(パネルを含む)。**パネルの rr_form は記述**(MSG で既見の NP 側;G の不改善をパネルで埋め合わせない)。+0.01 は小試験から次へ進む実用境界で、Public の +0.01 を意味しない。未見 NP への有効性は段階 3 の NP の主指標で判断する。
- 採点: C0'(保存済み、stage2_gl)と A2 は同じ runner 入力・同じ runner の設定(batch 計画は入力から決まる)で順に採点。
- **段階 3(関門を通った場合、別登録)**: 適応の identity は ranker の学習・開発・確認の identity と独立(Codex 134 が公式 key / global group で照合:重複 0)なので、単一の適応 GL で ranker の学習行を採点してよい。(1) GL だけの交換(同じ候補・query・凍結 ranker R0 に C0' と A2 を同条件で)、(2) ranker を合わせた比較(同じ学習 identity・候補・特徴・重み・params / rounds で C0' 特徴の R_A と A2 特徴の R_B):主 = (A2, R_B) − (C0', R_A)、参考 (A2, R0)。C0' の再採点と保存 cache の差は別に記録。
