129への回答（2026-10-29、128 v2評価前）

**v2の並べ替え本体と上限は採用してよい。開始前に直したいのは、adapterの強度の丸め順、C2の合否・分類、入力manifestとの結び付けである。修正後のコードと採点表を固定すれば、fold 1の未読評価を進めてよい。C2合格前に選択readerを実行することは勧めない。**

129_request、128登録v2、評価器・wf_common・MIST scorer/adapter・reader・両job・check_c2を確認した。r128 v1、127の学習曲線、pop0の局所費用、128 v2の性能結果は読んでいない。以下はソースと人工配列の確認であり、実データの再採点やモデル推論は行っていない。

**Q1 — 順位処理は直っている。再設計を追加する必要はない。**

評価器のWFブロックを取り出し、欠測の固定、群外候補の固定、複数の真、異なる式の交互配置を人工例で確認した。小さい例では、許された有限候補の置換を全列挙した上限と `wf_ub_gl` が一致した。26位の真が25位へ動く例でも、main=0、変更後=0.04、上限=0.04となった。

次の変更は意図どおりである。

- neutral_formulaを共有し、Noneを式群へ入れない。
- 有限なXの部分集合で両順位を定義し、その部分集合の位置だけを使う。
- α=0、P自身を第二順位とする対照、候補集合・式位置・動かせない候補の位置の不変を検査する。
- 全ての真について上限を取り、対象外の真は元の位置のRRを保持する。
- 元の候補表とMIST表のouter/one-to-one照合を行い、辞書の未登録をNaNで隠さない。

評価器に残る修正は、主に入力検査と診断である。

**入力値の検査。** 現在はnon-okのcosについて「有限なら停止」なので、+Inf/−Infは欠測として通る。non-okは明示的にNaNかつn_q=0、okは有限cosかつ0≤cos≤1（浮動小数の許容は固定）、n_qは1以上max_spectra以下の整数、としたい。行照合前にkey・statusのnullも拒否する。statusの検査は値の整合を確認するもので、no_formula等の理由が正しいことまで自動的に証明するわけではない。

**P/X順位の診断の母集団。** 現在の `wf_rP_form` は式群全体でのP順位だが、`wf_rX_form_pess` は有限X部分集合での順位である。movable行だけへ絞っても、この違いは残る。人工例では、同式10候補の末尾2件だけにXがあり、両者の順序が全く変わらないのに、表示はP順位10、X順位2となった。実際のPの有限部分集合内順位は2である。

`wf_rP_<x>_form`等を追加し、PとXを**同じ真・同じ有限部分集合**で比較する。式群全体でのP順位は別の診断として残せる。複数の真がある場合も、現在のmove/rankは「Pで最も早い真」に関する値であり、行内のどれかの真が動ける件数とは区別する。

**scorerの完全性。** 選択CSVへ常に限定する修正はよい。ただし、現在はTに存在しない選択分子を全てempty_windowとして数えるため、正当な空窓と候補表の欠落を区別できない。保存された分子ledgerの候補数等と照合し、0である根拠がある場合だけ空窓にする。全選択分子の窓が空の場合も、列名を指定した空のOを作る必要がある。現在の `DataFrame(rows)` だけではstatus列等がなくなる。

もう一点、score jobのコメントは4 threadsだが、scorerは `torch.set_num_threads(8)` で上書きしている。実際の資源割当と設定を揃える。

後述のpacking修正はMIST入力を変えるため、**進行中の採点プロセスのファイルは書き換えず**、修正した版・出力先を分ける。古い採点表へ新しいコードhashを後付けしない。GLや候補特徴を作り直す必要はない。

**Q2 — 保護・確認構成は改善した。manifestと開封条件はまだ実装が説明に届いていない。**

陽イオンC1の保護、fold 2のブロック・保護条件、選択済みpickの照合、正イオンのc1confを使う構成は支持する。主指標と採否閾値をさらに変更する提案はしない。残りは次の点である。

**1. row manifestが読む全ファイルを含むことを検査する。** 現readerはmanifestに書かれた行だけを確認するので、空のmanifestや一部のCSVを省いたmanifestでも、その検査を通る。foldごとの期待ファイル集合を明示し、欠落・余分な項目・重複を拒否してからhashを照合する。job側もglob任せにせず、そのrunで作ったファイルの明示リストを使う。

**2. 評価に使った入力と結び付ける。** MISTのcheckpoint・現在の出力hashの検査は追加されたが、`code`と`mist_commit`は現在printするだけで、登録版との一致は検査していない。eval CSVや特徴表のhashもreaderでは未照合である。また、評価後に採点表とそのmanifestの両方を更新すると、現在の照合だけでは「r128がどの採点表から作られたか」を確定できない。

評価開始時に、実際に使うMIST各manifest/得点表、評価CSV、特徴表、ranker、評価器、wf_common等のhashを入力記録へ固定し、終了時にも変更がないことを確認する。その入力記録をrow manifest・選択JSONと結ぶ。MIST commit、scorer/adapter/wf_commonは検査済みの版か、記録した版として整合していることを確認し、unknownや空のcommitを正常扱いにしない。大きな実データをPCで再読込する作業は不要である。

**3. C2の技術合格を開封条件へ結ぶ。** 現jobはMIST_SCORE_DONE、現readerはcheckpoint/表hashを確認するが、C2の合格は確認していない。採点完了と技術合格は別である。C2の合否・失敗件数・使用したadapter/checkpoint/compactの版を機械可読で保存し、対応するPASSがなければMISTを含む選択readerを止める。

未読の予測・評価の計算を先行すること自体は可能だが、C2で入力が変わった場合は該当する採点・評価を取り直す。GL単独の結果を先に開く場合は、現在の「GL/MIST合同で最大の一候補を選ぶ」登録とは区別し、読む範囲を結果前に固定する。

**4. fold 2の非選択系統の診断がまだ出る。** up/downのSHOWは直ったが、coverage-aware boundのループ、movable truths、reorderable groups、P/X順位のループはFAMS全体のままである。選択されなかった系統の真を使った診断も表示される。fold 2では表示対象familyをpickから決め、選択されたものだけにする。入力の有限性検査は別としてよい。

また、fold 2の表のgate列はfold 1の条件でPASS/noを表示し、最後の進行判断はstabを使っている。実際の進行条件は登録どおりだが、表の列もstabilityとして表示すれば判断を取り違えにくい。selection.jsonには選択名とprimaryだけでなく、選択に使った入力記録・reader/登録の版も残す。

確認C1を陽イオン側へ変更した点はよい。ただし登録v2節にも、**そのC1 usable陽イオン群での差の95%下限≥−0.01を必要条件にする**と明記する。旧本文のc1cost098の条件からの引継ぎを暗黙にしない。名簿366件と実際のusable件数を区別し、件数・被覆確認を性能開封前に済ませる。C2はH/4＋N/4＋D/2のままでよい。

**Q3 — C2の分離設計はよい。ただし、同じtableのpackingにも一つ具体的な差がある。**

**強度は公式と同じfloat32→float16の順にする。** 公式 `PeakFormula.featurize` は強度を一度float32へ変換し、cache builderがそれをfloat16配列へ代入する。現在のadapterは元のPython floatから直接float16へ変換している。この二つは丸めの境界で一致しない。[公式の特徴化](https://raw.githubusercontent.com/coleygroup/MIST/48e339be6535546c87ba4f6b81a0f787c2e4ac40/src/mist/data/featurizers.py)、[公式cache builder](https://raw.githubusercontent.com/coleygroup/MIST/48e339be6535546c87ba4f6b81a0f787c2e4ac40/src/mist/data/build_all_cache.py)

人工値 `0.500244140625 + 1e-9` では、直接float16は0.50048828125、float32を経由したfloat16は0.5になることを確認した。これは今回の実データ不一致の原因を確定したものではないが、同じ割当表でも差が出る実装上の経路である。`tree_to_row`で、強度列をfloat32にしてからfloat16へ代入する。collateでfloat32へ戻す時点では、既に失った丸め情報は戻らない。

**(1)は全件を分母にして厳密に判定する。** 現在は一致数を `N−len(fail1)` で割るため、変換に失敗した行があっても表示上100%になる。また、check_c2は不一致があってもJSONを書いて通常終了する。

PASSは少なくとも `failures==0` かつ `agree_all==N` とし、各フィールドの一致件数/Nを保存する。N、namesの一意性、TSVとの対応、fingerprintの行順・shape、root formula/adduct、CLS位置、paddingも確認する。現在FIELDSからinstrumentsが外れているので、それも照合するか、凍結configでembed_instrument=Falseのため対象外と明記する。

100%にならない場合は、ID・異なるフィールド・値を記録し、入力版、丸め順、同点順序、root、詰め方を調べる。失敗行を除いたり、99.9%へ緩めたり、平均Tanimotoが近いことを合格理由にしない。不一致は技術未完了であり、MISTの性能NOではない。報告は保存しても、合否をexit codeまたは明示statusへ反映し、選択readerが読めるようにする。packingが不一致のまま全件の予測比較を何度も回す必要はない。

**(2)の現在の分類は誤分類できる。** 実コードを人工行へ適用すると、式・ion・長さが同じで**強度だけ変えた例**も、**peak_typeだけ変えた例**も、tie_order_onlyになった。現在のmultisetが式とionだけで、強度・peak_typeを含まないためである。

分類は次の定義に直したい。

- identical：比較対象の全配列が順序込みで同一。
- tie_order_only：長さ、root/CLS、paddingが同じで、fragment側の **(formula vector, ion, peak_type, 格納精度のintensity)** の重複込みmultisetが一致する。さらに移動が同じ強度の位置の間だけであることを確認する。rootをfragmentと一緒に並べ替えて比較しない。
- それ以外：count、root/ion、intensity、formula、schema/packingの差を分ける。複数の差がある行には複数flagを持たせてもよい。変換失敗はIDと例外を残す。

ion配列の位置ごとの不一致だけで先にcount_or_ionへ振り分けると、同じ強度のfragmentがionごと入れ替わっただけの行も誤分類する。まず完全なfragment tupleで順序だけの差を判定する方がよい。分類名だけで原因を確定せず、必要な例は元tableのm/zも対応させて追う。

**IDごとの記録も追加する。** 現在保存されるのはCounterと一部の失敗例だけで、依頼にある「IDごとの分類」は残らない。全IDの分類・変化flag・失敗理由を小さなJSONL/CSVへ保存し、集計がNと一致することを確認する。

**(3)は絶対差に加え、符号付き差を残す。** Tanimotoの符号付き分位点・平均・改善/悪化/不変件数と、絶対差・確率差を併記し、(2)の分類ごとに追えるようにする。最大差のIDも保存する。check Aの閾値が同じcheckpointに対応することを検査し、C2出力にcheckpoint・閾値ファイル・adapter・入力archive/compactの版を結ぶ。

生ピーク経路を今回の固定前処理にする方針は妥当である。同じtableからのpacking一致と、生ピークから再割当した場合の差を分けたまま記録する。後者を見てCASMIの成績に合う割当規則を選ぶことはしない。C2が通ったこともCASMIでの増分の証明ではなく、その後の登録比較で判断する。

点検した評価器SHA256：`c6685f1a63036d070df11787e9324c43ec63618594b67172c25b97326d407ab8`。順位処理の意味は維持し、packing・入力検査・診断/readerの補強を新しい版へ対応させればよい。

REVIEW_COMPLETE: 129
