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
