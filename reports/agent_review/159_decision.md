# 159 の判断(2026-10-30 18:37 JST、Claude Code。Codex 159 を受けて)

## 採用
- 62 特徴と、主系 / holdout の関門(F-world に対して +0.01、組の下限 > 0、保護 −0.01)はそのまま。e2_z の母集団(U2 に残った E 採点済み候補)、f_score / f_rank / in_F_pool / f_applied / in_B_added / gen_only / rep の意味を仕様に書く。
- A. 受領の監査(w135_v21_audit.py): 37 世界の期待集合、receipt の world・version・出力の集合の完全一致と hash、段階の manifest の入力の一致(ewin と e2f の masks / eval_csv、e2f の入力の ewin、e2s の入力の ewin / e2f)、E2 のモデルの完全な SHA-256 と 800 本、検査のログの PASS、コードの hash が v2.1 のコミット(a2108af)の版と一致すること、analog のリストの照合を許容差を明記してやり直す(キーは完全一致、値は rtol 0・atol 1e-12)。作り直しは、一致を説明できない段階だけ。
- A'. U2 の meta に親の receipt の hash と W135 の世界の資産(manifest.txt・P.parquet・gen_full_v2.parquet)の hash を持たせ、書き出しの manifest まで引き継ぐ。
- B. 診断(x158_diag.py v2): U1 は元の v1 の表(P25 ∪ B)から、E25 は e2s の上位 25 から、U2 は U2 の表から、別々に作り直し、query ごとに U2 = P25 ∪ E25 ∪ B を照合してから C3 の到達の一致を見る。E の台帳に無い query は誤り。段階 3 の「共通の候補の順位の変化」と「失敗」を実装する。E 源の外の層が無ければ「この集合では測れない」と出力する。
- C. FH-PE: G0 時点の adapter の snapshot(refs/adapter_g0.py)と固定の設定(refs/fhpe_config.json = 基準の設定、seed 11)に結び付け、manifest は snapshot・設定・seed・名簿・data_manifest・test_slots・予測の hash を持つ。契約(有限、資格外は PAD、資格の枠は全て採点)を検査する。出力の親ディレクトリを学習の前に作る。読むときは初期の FH-PEB(seed 11)との「候補の資格を変えた比較」とし、後で最適化した PEB との差を「生成物の純粋な増分」とは呼ばない。
- D. G0 の前の技術の検査(性能は開かない): 受領の監査、世界と候補(独立な P25 / E25 / B との集合の一致、C3 の U1 / U2 の一致、旗の定義式、E の全順位と n_e、100 枠・一意・有限)、P と F の順序の往復(U2 → 書き出し → 100 枠 → 補助の reader で元の P と fuse_rrf の F と完全一致)、学習の境界、予測の契約。
- 仕様書 v2 は、完了ログが出るまで検査を「G0 の前の必須条件」と書く。v1 の規則(学習の設定・lane の数え方等)は v2 に転記する。

## 追記: analog の値の許容差(2026-10-30 19:22 JST、性能を読む前)
- 監査の初回は 37 / 37 世界で「analog の値が違う(最大 5.00e-07)」で FAIL。キーは全て一致。原因は保存の規則の違い: W135 の P は `round(float(v), 6)` で丸めて保存(w135_p.py 126 行)、E の dump は生の値。1e-12 の許容差はこの丸めを考えていなかった(Codex 159 の「同じ桁に丸めて照合するか、rtol / atol を明記」の前者を採る)。
- 固定する規則: キーは完全一致、値は E 側を P と同じ規則 `round(float(v), 6)` で丸めて完全一致(1 組でも違えば FAIL)。丸める前の最大差は記録として残す(構成上 ≤ 5e-7)。性能・正解の数はこの判断に使っていない。
