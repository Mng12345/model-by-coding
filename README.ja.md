> 本文は README.md の日本語訳です。相違がある場合は英語版を優先します。

# model-by-coding

実物の写真から決定論的な three.js モデルを再構築し、そのモデルを分解デモ動画と GIF にするまでの Agent Skill。3D モデリングソフトは開かない。

このリポジトリはスキルそのものだ。Agent が従える手順、再利用可能なスクリプト、長文のリファレンスノート、そして完全な実例を 1 つ収めている。実例は白い USB デスクファンをコードで再構築し、13 個のパーツ、1920×1080、30 fps、43.5 秒の動画としてレンダリングしたものだ。

- [これは何か](#これは何か)
- [何を解決するか](#何を解決するか)
- [4 ステップのパイプライン](#4-ステップのパイプライン)
- [クイックスタート](#クイックスタート)
- [リポジトリ構成](#リポジトリ構成)
- [スクリプト](#スクリプト)
- [既知の制限](#既知の制限)
- [ライセンス](#ライセンス)
- [謝辞とリンク](#謝辞とリンク)

## これは何か

Agent Skill とは、Agent が読み込めるディレクトリのことだ。`SKILL.md` の入口に、タスクに必要なノートとスクリプトが加わる。このリポジトリは 4 つの部分からできている。

| 部分 | 内容 |
| --- | --- |
| `SKILL.md` | 入口。スキルが適用される場面、パイプラインそのもの、省略できないルールを書いている。 |
| `references/` | スキルファイルに収まらない詳細をまとめた 6 本の長文ノート。モデリング、レンダリング、検証、GIF 書き出し、公開、落とし穴の一覧。 |
| `scripts/` | 再利用可能なツール。単一フレームのビューア、写真とレンダーの比較シート、check 出力の読み取り、GIF の操作カード。 |
| `examples/fan/` | 実例。写真、モデルのソース、HyperFrames プロジェクト、検証用レンダー、成果物をまとめている。 |

この実例はモックではない。写真は作者自身が撮ったもので、モデルは JavaScript で手書きし、動画はそのモデルからレンダリングし、6 角度の比較シートもリポジトリに含めている。手順どおりに最後まで進めた結果が何になるかを、これらが示している。数字は [examples/fan/README.md](examples/fan/README.md) にあり、修正しなかった偏差も含まれている。

まず `SKILL.md` を読む。リファレンスは、より多くの紙幅を必要とする部分だ。

| ファイル | 内容 |
| --- | --- |
| `references/01-modeling.md` | 座標系、測定した比率、回転体プロファイル、グリルと羽根のパラメータ、パーツごとのアンカー。 |
| `references/02-render.md` | HyperFrames のレンダリング契約、ショット表、音声同期点。 |
| `references/03-verify.md` | ヘッドレス撮影、バウンディングボックス比較、角度ごとのレビュー、失敗した重ね合わせ実験。 |
| `references/04-gif.md` | gif-master の手順カード、クレジットの制限、ffmpeg の代替手順。 |
| `references/05-publish.md` | 公開チェックリストと、出力の主な公開先ごとの実務的な条件。 |
| `references/06-gotchas.md` | ほかにも、トーンマッピングと露出、ライトの減衰、シャドウのバンディング、丸管ではなく平らな帯にする必要があるグリルのリブ、最小文字サイズ、同梱した `.min.js` などがある。 |

## 何を解決するか

「この物体の 3D モデルを作って」と頼まれた Agent は、たいてい 2 つのどちらかを出す。確認できないきれいなレンダー 1 枚か、比率がいい加減で動画にもつながらないメッシュだ。どちらもレビューが難しい。レンダーのカメラ位置は普通わからないので写真の隣に置けず、変更後に資産を導出し直すこともできない。

このスキルは、各ステップに証拠を残すループで置き換える。

1. **比率は測るもので、推測しない。** モデル内の各定数は、写真上の測定にたどれるか、推定として明示されている。引き継がれるのは絶対サイズではなく比率だ。
2. **同じフレームを再現できる。** モデルが公開するのは素の状態だけである。カメラ位置、分解量、羽根の回転角。時計も乱数もネットワークもない。同じ入力なら同じフレームになり、レビューは正確なカメラ位置を指せる。
3. **比較は同じ条件で行う。** 各レンダーは参照写真と同じカメラ位置で撮影し、両側をそれぞれのシルエットのバウンディングボックスで切り、同じタイルに拡大縮小する。構図と距離が比率の誤差を隠せなくなる。
4. **1 つのモデルがすべての成果物を支える。** 同じ bundle が検証用スチル、インタラクティブページ、動画を動かす。モデルを直せばすべてに反映される。
5. **結果は git でレビューできる。** モデルはコードと名前付き定数である。変更は diff になり、バイナリ資産にはならない。

これは次のものではない。

- フォトグラメトリや 3D スキャナではない。ジオメトリを自動で再構築することはない。
- CAD ではない。寸法は写真にたどれる比率であり、実物の測定値ではない。
- Blender の代替でも汎用モデリングツールでもない。
- ホスト型サービスではなく、モデルの重みも同梱しない。

## 4 ステップのパイプライン

各ステップは、次のステップが使う成果物を生む。以下の順序では計測をステップ 1 に含めている。`SKILL.md` は計測を独立したステップとして扱っており、実例ではモデル段階の早い時期から検証を始め、動画の制作中も繰り返しチェックを再実行した。

### ステップ 1: 写真からコードでモデリングする

入力は正面写真 1 枚に、使える追加角度があれば加える。実例では 6 枚を使った。正面 3/4 ビュー 1 枚と、角度写真 5 枚（side-left、back、back three-quarter、bottom、top）である。

Agent が行うこと:

- 写真を測る。実例では、外縁の動径スキャンでヘッドの円と中心を決め、固定半径での角度方向の周期からグリルのリブ本数を出し、比率からヘッドの厚み、中心キャップ径、ベース径、ノブ径を求めた。
- ワールドスケールを 1 つ決め、仮定として明示する。実例はヘッド径 190 mm を採り、ほかの寸法はすべてそれに対する比率にする。
- three.js のプリミティブと回転体プロファイルでジオメトリを組む。リング、支柱、羽根、モーターの円柱、グリルのリブ、ベースのパーツ。パーツは独立した名前付きオブジェクトにする。動画で個別に動かすためだ。
- 各パーツに分解オフセットと、引き出し線ラベルのためのスクリーン空間アンカーを与える。
- API から時間を取り除く。`setView()`、`setExplode()`、`setSpin()`、`render()`、`getAnchors()`。`Date.now()` も `requestAnimationFrame` もネットワーク要求も使わない。
- esbuild でシーンと three.js を 1 つの IIFE にまとめる。ページ、ビューア、動画が同一のコードを読み込む。
- ブランドを取り除く。モデルのラベル面は空白にし、参照写真のブランド名と型番も同じ理由でぼかしてある。

出力: `examples/fan/src/fan-scene.js` と、ビルドされた `examples/fan/video/assets/vendor/fan.bundle.min.js`。

### ステップ 2: HyperFrames で分解動画をレンダリングする

[HyperFrames](https://github.com/heygen-com/hyperframes) は、一時停止したタイムラインを進めながらフレームを撮影することで、HTML ページを動画にする。

- `examples/fan/video/index.html` がコンポジションのルートである。`data-duration="43.5"`、1920×1080。
- 一時停止した GSAP タイムラインを `window.__timelines.main` に登録する。ページは `hf-seek` を待ち受け、`event.detail.time` から canvas を描き直す。何も自力で進まないので、任意のフレームを撮影できる。
- 43.5 秒の実例は 10 ショット。タイトル、オービット、グリル接写、後方 3/4、ハブ接写、ワイド、分解、13 本の引き出し線ラベル付きホールド、組み戻し、エンドカード。
- 分解はパーツごとに 1 つの進捗値で表す。分離は 21.15 s から 0.30 s 間隔でずらし、組み戻しは 35.18 s から 0.25 s 間隔で進み、最後のパーツは 38.45 s に収まる。各引き出し線ラベルは、対応するパーツが動き始めてから 0.30 s 後にフェードインを開始する（フェード自体は 0.45 s）。
- サウンドトラックも同じタイミング契約で切る。実例のミックスは 43.5 s、48 kHz、16-bit ステレオ、統合ラウドネス −16.0 LUFS、トゥルーピーク −2.0 dBTP。`examples/fan/video/assets/audio/sources.md` に素材の出所と処理チェーンを書いている。
- `check` がゲートである。ゼロ問題を報告するまでレンダリングしない。`snapshot --at <秒>` は確認用に 1 フレームを撮る。実例のポスターは 27.6 s のフレームだ。

出力: `examples/fan/video/renders/` に MP4。既定の名前は `video_<YYYY-MM-DD>_<HH-MM-SS>.mp4`。

### ステップ 3: 写真と照合して検証する

この確認は同一カメラでの比較であり、印象ではない。

1. ヘッドレス Chrome で、参照写真と同じカメラ位置からモデルを撮影する。`scripts/view.html` は URL クエリ（`yaw`、`pitch`、`dist`、`tx`、`ty`、`tz`、`fov`）からカメラ位置を読み、1920×1080 で 1 フレームをレンダリングする。アニメーションループはなく、自身ではネットワーク要求をしない。
2. 写真は手で読んだボックスに、レンダーは自身のバウンディングボックスに切り出す。実例では、写真のボックスはグリッドオーバーレイから読み、レンダーのボックスはヘッドの縁とベースの縁から解析的に投影した。`scripts/verify_sheet.py` は背景色からレンダーのボックスを自動検出することもできる。
3. 両方の切り出しを同じタイルに拡大縮小して並べる。構図と距離が正規化されるので、ヘッドの厚み、中心キャップ径、リブ本数、ベース幅を直接比べられる。
4. すべての角度をレビューし、不一致を書き出し、測定した定数を調整し、再レンダリングして繰り返す。

実例のシートは 6 行ある。記録された結果は近い一致で、既知の偏差が 7 つある。ヘッド中心の高さ（モデル 1.02 D、写真 1.04–1.10 D）、やや広い後部グリルの外周、数パーセント大きいコントロールボックスなどだ。これらは隠さず実例のノートに列挙している。

この手法には記録された否定的な結果もある。初期案は同一カメラでの 50/50 重ね合わせで、ヘッドの円をフィッティングして正規化するものだった。最初は 5 枚の写真で円フィッティングを行い、そのうち 4 枚では最も強い曲線エッジが背景に属していたため、正規化した半径は信用できなかった。正面の写真だけが、物体が均一な壁を背景に画面を満たしており、使える半径スキャンを与えた。重ね合わせはやめ、バウンディングボックス比較に切り替えた。理由は `references/03-verify.md` に残している。

このステップは明示的なボックスによる目視レビューであり、数値的な証明書ではない。

### ステップ 4: GIF を書き出す

最後のステップはブラウザで動くため手動である。

1. ツールを開く。[動画→GIF（英語）](https://gif-master.com/en/tools/video-to-gif) または [動画→GIF（中国語）](https://gif-master.com/zh/tools/video-to-gif)。
2. レンダリングした MP4 を入れる。ファイルはブラウザ内で処理され、アップロードされない。
3. 1 つの動作に絞る。43.5 秒の動画全体ではなく、分解か接写の一部を選び、フレームレートとサイズを設定してプレビューする。
4. 書き出す。編集は無料、ダウンロードにはログインが必要で、無料枠は 1 日 3 クレジット。

`references/04-gif.md` に同じ手順をチェックリストとしてまとめ、ローカル変換用の ffmpeg 代替手順も記録している。

### 成果物の順序

```
examples/fan/
├─ reference/fan.jpg, reference/angles/*.jpg    input: six photographs
├─ src/fan-scene.js                             step 1: model, materials, camera, anchors
├─ video/assets/vendor/fan.bundle.min.js        step 1: the bundle every consumer loads
├─ video/index.html, video/assets/director.js   step 2: composition and timeline
├─ video/assets/audio/mix.wav                   step 2: Release asset, not in git
├─ video/renders/*.mp4                          step 2: output, git-ignored
├─ out/verify2/*-render.png                     step 3: same-camera stills
├─ out/review-sheet.png                         step 3: six photo-versus-model pairs
├─ out/poster.png                               deliverable: 1920×1080 teardown still
└─ out/contact-sheet.png                        deliverable: 4×3 contact sheet
```

## クイックスタート

### 必要なもの

| 要件 | 用途 |
| --- | --- |
| Node.js 22（22.19.0 で動作確認） | `npx` で HyperFrames CLI と esbuild を実行する。 |
| Python 3.11 と Pillow | `scripts/verify_sheet.py`（numpy は任意）、`examples/fan/tools/review_sheet.py` は numpy が必要、実例の音声再構築スクリプトは numpy と scipy を使う。 |
| ffmpeg | HyperFrames のレンダリングと、実例の音声作業。 |
| Chrome または Chromium | ヘッドレス撮影と HyperFrames のフレーム取り込み。 |
| HyperFrames CLI 0.9.36 | `npx --yes hyperframes@0.9.36` が取得する。グローバルインストールは不要。 |
| git | スキルと実例のクローン。 |

`scripts/hf_read_check.py` は Python 標準ライブラリだけを使う。`scripts/view.html` はブラウザとビルド済みのモデル bundle だけを必要とする。

### スキルをインストールする

リポジトリをスキルディレクトリにクローンする。プロジェクト内に入れると、そのプロジェクトだけがスキルを使える。ユーザー単位で入れると、すべてのプロジェクトから使える。

```bash
# project-local
git clone https://github.com/Mng12345/model-by-coding.git .agents/skills/model-by-coding

# or user-wide
git clone https://github.com/Mng12345/model-by-coding.git ~/.agents/skills/model-by-coding
```

DeepSeek Harness や Claude Code といった Agent は、プロジェクトの `.agents/skills/` か、ユーザーの `~/.agents/skills/` からスキルを読む。

skills CLI がある環境なら、同じインストールは 1 コマンドで済む。

```bash
npx skills add Mng12345/model-by-coding
```

そのあと新しい Agent セッションを開き、リクエストでスキル名（`model-by-coding`）を指定する。実際の呼び出し方法はクライアントによって異なる。

### 実例の動画をレンダリングする

リポジトリにバイナリ音声は入っていない。[最新の Release](https://github.com/Mng12345/model-by-coding/releases/latest) から `mix.wav` をダウンロードし、check の前に元の場所へ戻す。

```bash
# 1. put the mixed track back (asset name: mix.wav)
curl -L -o examples/fan/video/assets/audio/mix.wav \
  https://github.com/Mng12345/model-by-coding/releases/latest/download/mix.wav

# 2. check the HyperFrames project, then render
cd examples/fan/video
npx --yes hyperframes@0.9.36 check
npx --yes hyperframes@0.9.36 render --quality delivery
```

`check` がゼロ問題を報告してからレンダリングする。結果は `examples/fan/video/renders/video_<YYYY-MM-DD>_<HH-MM-SS>.mp4` に書き出される。CLI はプロジェクトディレクトリ名とレンダリング時刻でファイルを命名する。ブラウザでローカルプレビューが必要なら、レンダリングの前に `preview` を実行する。

```bash
npx --yes hyperframes@0.9.36 preview
```

動画全体ではなく 1 つの瞬間を見たい場合:

```bash
npx --yes hyperframes@0.9.36 snapshot --at 27.6
```

スナップショットはプロジェクトの `.hyperframes/artifacts/snapshots/` ディレクトリに書き出される。

`examples/fan/out/` に含まれる静止画（ポスター、4×3 コンタクトシート、6 角度の比較シート、6 枚の角度別レンダー）はリポジトリに入っているので、何もレンダリングせずに確認できる。

## リポジトリ構成

```
model-by-coding/
├─ SKILL.md                          skill entry point
├─ README.md                         this file
├─ README.zh-CN.md                   Simplified Chinese translation
├─ README.zh-TW.md                   Traditional Chinese translation
├─ README.ja.md                      Japanese translation
├─ README.de.md                      German translation
├─ README-LICENSES.md                license scope, attribution format, third-party assets
├─ LICENSE                           MIT, with the media exception noted at the end
├─ references/
│  ├─ 01-modeling.md
│  ├─ 02-render.md
│  ├─ 03-verify.md
│  ├─ 04-gif.md
│  ├─ 05-publish.md
│  └─ 06-gotchas.md
├─ scripts/
│  ├─ view.html                      single-frame viewer driven by URL query
│  ├─ verify_sheet.py                photo-versus-render comparison sheet
│  ├─ hf_read_check.py               reads the JSON form of a HyperFrames check
│  └─ make_gif.md                    gif-master operation card (documentation)
└─ examples/
   └─ fan/                           worked example; see examples/fan/README.md
      ├─ README.md                   the example's own notes, measurements and deviations
      ├─ src/
      │  ├─ fan-scene.js             geometry, materials, lighting, anchors
      │  ├─ director.js              camera moves and timeline for the film
      │  └─ fan-ui.js                inspection UI for the standalone HTML build
      ├─ video/
      │  ├─ index.html               composition root, 43.5 s
      │  ├─ hyperframes.json         HyperFrames project configuration
      │  ├─ meta.json                project id and name
      │  ├─ package.json             npx shortcuts for preview (dev), check, snapshot, render
      │  └─ assets/
      │     ├─ director.js           the director compiled for the film
      │     ├─ fonts/                Inter and Inter Tight woff2, with OFL license texts
      │     ├─ vendor/               fan.bundle.min.js and gsap.min.js
      │     └─ audio/
      │        ├─ sources.md         soundtrack sources, processing chain, measured levels
      │        └─ work/              synthesis, mixing, mastering and verification scripts
      ├─ reference/
      │  ├─ fan.jpg                  front three-quarter photograph
      │  └─ angles/                  five additional angles (side-left, back, back 3/4, bottom, top)
      ├─ tools/
      │  ├─ review_sheet.py          builds out/review-sheet.png; runs as-is
      │  ├─ grid6.py                 historical one-off measurement script
      │  ├─ measure-photo.py         historical one-off measurement script
      │  └─ expo_check.py            historical one-off measurement script
      └─ out/
         ├─ poster.png               1920×1080 teardown still
         ├─ contact-sheet.png        4×3 contact sheet of the film
         ├─ review-sheet.png         six photo-versus-model pairs
         └─ verify2/                 six per-angle renders, 1920×1080 each
```

## スクリプト

| パス | 種類 | 内容 |
| --- | --- | --- |
| `scripts/view.html` | ブラウザページ | URL で与えたカメラ位置から、コードで作ったモデルの 1 フレームをレンダリングする。パラメータ: `bundle`、`global`、`yaw`、`pitch`、`dist`、`tx`、`ty`、`tz`、`fov`、`explode`、`spin`、`tilt`、`lift`、`w`、`h`、`dpr`、`bg`。パーツ単位のデバッグフラグ `noshadow`、`hide`、`only` は bundle にそのまま渡される。 |
| `scripts/verify_sheet.py` | Python | 写真とレンダーをそれぞれのバウンディングボックスで切り、同じタイルに拡大縮小して、並べた比較画像を 1 枚書き出す。`--photo`、`--render`、`--out`、手で読んだ `--bbox x0,y0,x1,y1` が必須。任意で `--render-bbox`（既定では背景色から自動検出）、`--bg`、`--threshold`、`--pad`（既定 `0.04`）、`--tile`（既定 `520x620`）、`--gap`、`--label-height`、`--label-photo`、`--label-render`。Pillow が必須で、numpy は背景マスクの高速化にだけ使う。 |
| `scripts/hf_read_check.py` | Python | HyperFrames の check レポートを読む。`check --json` が出力する JSON でも、HyperFrames が `.hyperframes/artifacts/checks/` に保存する artifact でもよい。`ok` とセクション別の指摘件数（lint、runtime、layout、motion、contrast、craft、audio）を表示する。`--max` は表示する指摘の数、`--json` は要約を JSON で出力、`--fail-on-error` はレポート失敗時に非ゼロで終了する。標準ライブラリのみ。UTF-8 と UTF-16 のレポートを受け付ける。 |
| `scripts/make_gif.md` | ドキュメント | gif-master の操作カード。手順、制限、ローカル ffmpeg の代替手順。実行ファイルではない。 |

ビューアはクエリで指定した bundle を読み込む。同梱の実例 bundle は素の IIFE なので、カメラを直接設定できる。

```
file:///<path-to-repo>/scripts/view.html?bundle=../examples/fan/video/assets/vendor/fan.bundle.min.js&yaw=-10&pitch=12&dist=0.85&ty=0.185&fov=30
```

同じサイズのヘッドレス Chrome で撮影する。

```bash
chrome --headless=new --hide-scrollbars --window-size=1920,1080 \
  --screenshot=front.png \
  "file:///<path-to-repo>/scripts/view.html?bundle=../examples/fan/video/assets/vendor/fan.bundle.min.js&yaw=-10&pitch=12&dist=0.85&ty=0.185&fov=30"
```

実例に含まれるレンダーから比較シートを作る。

```bash
python scripts/verify_sheet.py \
  --photo examples/fan/reference/fan.jpg \
  --render examples/fan/out/verify2/front-render.png \
  --bbox 130,245,1195,1455 \
  --out front-pair.png
```

保存した check レポートを読む。HyperFrames は自分のコピーを `.hyperframes/artifacts/checks/<uuid>.json` に保存する。スクリプトは stdout から取り込んだレポートも受け付ける。

```bash
cd examples/fan/video
npx --yes hyperframes@0.9.36 check --json > check.json
python ../../../scripts/hf_read_check.py check.json

# or point it at the report the CLI saved itself
python ../../../scripts/hf_read_check.py .hyperframes/artifacts/checks/<uuid>.json
```

`scripts/` のツールはパラメータ化されている。オブジェクト名も、ファン専用のパスも、絶対パスもない。`examples/fan/tools/` の 4 本はケーススタディで実際に使ったスクリプトだ。`review_sheet.py` は相対パスで書かれていてリポジトリ内でそのまま動く。`grid6.py`、`measure-photo.py`、`expo_check.py` は経緯を残すために置いてあり、入力がこのリポジトリに含まれないためそのままでは動かないとファイル先頭に書いてある。

## 既知の制限

- **比率であり、認証された寸法ではない。** 実例は写真にスケールがないため、ヘッド径 190 mm を宣言した絶対スケールの仮定として置いている。ほかの寸法はそこから導かれる比率だ。モデルは測定器ではない。
- **見えない面は推定である。** 後部グリルの細部、モーター内部、クリップフック機構、ベースの一部は写真では見えきっていない。ノートでは推定として示しており、実製品の事実として読むべきではない。
- **検証は目視である。** バウンディングボックスの整列で構図の差は消えるが、写真のボックスは手で読み、数値の合格しきい値もない。シートが近く見えても、シルエットの外にある細部が間違っていることはある。
- **実例の結論は実例のもの。** 13 個のパーツ、10 ショット、このタイミング、これらの偏差はファンのケーススタディに属し、ほかの物体の既定値ではない。
- **音声は git に入っていない。** 動画は `examples/fan/video/assets/audio/mix.wav` を参照し、このファイルは Release アセットとして配布される。ないとプロジェクトは不完全なので、`check` や `render` の前に戻す。
- **バージョンを固定している。** コマンドは `hyperframes@0.9.36` を固定する。実例をビルドしたバージョンだ。ほかのバージョンでは挙動が変わりうる。互換性リストは主張しない。
- **実例のツール 4 本のうち 3 本はそのまま動かない。** 作者の元の作業環境を指す歴史的な測定スクリプトだ。パラメータ化した版は `scripts/` にある。
- **GIF の工程は手動。** gif-master はブラウザで動き、ダウンロードにはログインが必要で、無料ダウンロードは 1 日 3 回。リポジトリはこの工程を自動化していない。
- **レンダリングには実ブラウザと ffmpeg が要る。** HyperFrames は Chrome 経由でフレームを取り込むため、ブラウザが動かないマシンでは動画をレンダリングできない。

## ライセンス

- **コード** — MIT。全文は [`LICENSE`](LICENSE) にある。
- **写真とレンダリング媒体** — `examples/fan/reference/` の参照写真 6 枚、`examples/fan/out/` の静止画、動画 `fan-teardown-43s.mp4` は [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) でライセンスされる。クレジット: **Mng12345/model-by-coding**、リンクは [github.com/Mng12345/model-by-coding](https://github.com/Mng12345/model-by-coding)。
- **第三者ライブラリと素材** — それぞれのライセンスを保つ。同梱の three.js、GSAP、HyperFrames、Inter/Inter Tight フォントは [`README-LICENSES.md`](README-LICENSES.md) に列挙している。

どちらのライセンスでもカバーされない使い方をする場合は、素材を再利用する前にリポジトリで issue を開いてほしい。

## 謝辞とリンク

- [three.js](https://threejs.org) — MIT。モデルのジオメトリ、マテリアル、レンダラーは three.js。
- [GSAP](https://gsap.com) 3.13.0 — [GSAP 標準ライセンス](https://gsap.com/standard-license)で使用。同梱のコピーはライセンスのヘッダーを保持している。
- [HyperFrames](https://github.com/heygen-com/hyperframes) 0.9.36 — 動画のレンダリングに使った HTML→動画ツール。プロジェクトサイト: https://hyperframes.heygen.com
- [gif-master.com](https://gif-master.com) — ステップ 4 で使うブラウザベースの動画→GIF ツール。
- Inter と Inter Tight — SIL Open Font License 1.1 の Web フォント。ライセンス文は `examples/fan/video/assets/fonts/` にフォントファイルと一緒に置いてある。
- 参照写真は作者が撮影した。ブランド名と型番は公開前にぼかしてある。モデルにブランドはない。これは形状の研究であり、メーカー公認の複製ではない。
- リポジトリ: https://github.com/Mng12345/model-by-coding
- Releases: https://github.com/Mng12345/model-by-coding/releases/latest
- Issues: https://github.com/Mng12345/model-by-coding/issues

ファンの実例は 1 つの物体と 1 本の動画にすぎない。再利用する価値があるのは、測定ノート、同一カメラでの確認、モデルをコードに落とす方法であり、ファン固有の数字ではない。
