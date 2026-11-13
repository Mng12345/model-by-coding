> 本文是 README.md 的繁體中文譯文，如有出入以英文版為準。

# model-by-coding

一個 Agent Skill：把一件實物從照片重建成確定性的 three.js 模型，再把該模型做成拆解演示影片和 GIF，全程不打開 3D 建模軟體。

本儲存庫就是這個技能本身：Agent 可以遵循的說明、可重複使用的腳本、長篇參考筆記，以及一個完整的範例——一台白色 USB 桌上型風扇，以程式碼重建，並算圖為 13 個零件、1920×1080、30 fps、43.5 秒的影片。

- [這是什麼](#這是什麼)
- [它解決什麼問題](#它解決什麼問題)
- [四步流程](#四步流程)
- [快速開始](#快速開始)
- [儲存庫結構](#儲存庫結構)
- [腳本](#腳本)
- [已知限制](#已知限制)
- [授權條款](#授權條款)
- [誌謝與連結](#誌謝與連結)

## 這是什麼

Agent Skill 是一個 Agent 可以載入的目錄：`SKILL.md` 入口，加上任務需要的筆記和腳本。本儲存庫分四部分：

| 部分 | 內容 |
| --- | --- |
| `SKILL.md` | 入口檔案：技能何時適用、流程本身，以及不可省略的規則。 |
| `references/` | 六篇長篇筆記，記錄不適合放進技能檔案的細節：建模、算圖、驗證、GIF 匯出、發布，以及一組常見陷阱。 |
| `scripts/` | 可重複使用的工具：單幀檢視器、照片與算圖的對比圖、check 輸出讀取器，以及 GIF 操作卡片。 |
| `examples/fan/` | 完整範例：照片、模型原始碼、HyperFrames 專案、驗證算圖和產物。 |

範例不是演示稿。照片是作者自己拍的；模型是手寫 JavaScript；影片由該模型算圖；六角度對比圖已隨儲存庫提供。它們共同展示了按說明從頭到尾執行會得到什麼。[examples/fan/README.md](examples/fan/README.md) 記錄了各項數字，包括沒有修正的偏差。

先讀 `SKILL.md`。參考筆記是需要更多篇幅的部分：

| 檔案 | 主題 |
| --- | --- |
| `references/01-modeling.md` | 座標系、量測得到的比例、旋轉體輪廓、格柵與葉片參數、各零件的錨點。 |
| `references/02-render.md` | HyperFrames 的算圖契約、鏡頭表、音訊同步點。 |
| `references/03-verify.md` | 無頭截圖、包圍盒對比、逐角度審查，以及失敗的疊圖實驗。 |
| `references/04-gif.md` | gif-master 的分步操作卡片、點數限制，以及 ffmpeg 備選方案。 |
| `references/05-publish.md` | 發布清單，以及輸出通常去向的各平台上實際的門檻。 |
| `references/06-gotchas.md` | 其中涉及色調映射與曝光、燈光衰減、陰影色帶、必須做成扁平帶狀而非圓管的格柵條、最小文字尺寸，以及隨儲存庫內建的 `.min.js` 檔案。 |

## 它解決什麼問題

要一個「這個物體的 3D 模型」時，Agent 通常會給出兩種結果之一：一張無法核對的漂亮算圖，或者一個比例隨意、也沒法繼續做影片的網格。兩者都難以審查。算圖的相機位置通常未知，無法與照片並排；改動之後，資產也無法重新推導。

本技能用一個每一步都留下證據的流程來替代上述做法。

1. **比例是量出來的，不是猜的。** 模型裡的每個常數要嘛能追溯到照片上的量測，要嘛被標註為推斷。真正被延續下去的是比例，而不是絕對尺寸。
2. **同一幀可以重現。** 模型只暴露普通狀態——機位、爆炸展開量、葉片旋轉角——沒有其他東西。沒有時鐘、沒有隨機數、沒有網路。同樣的輸入得到同樣的幀，因此審查可以針對一個確切的機位。
3. **對比是同口徑的。** 每次算圖都用參考照片的機位截圖，兩側各自裁到自己的輪廓包圍盒，再縮放到同樣的畫幅。取景和距離不再能掩蓋比例錯誤。
4. **一個模型供給所有產物。** 同一個 bundle 驅動驗證截圖、互動頁面和影片，模型改一次，所有地方都會變。
5. **結果可以用 git 審查。** 模型是程式碼和具名常數。改動是 diff，不是二進位資產。

它不是：

- 攝影測量或 3D 掃描儀——不會自動重建幾何；
- CAD——尺寸是能追溯到照片的比例，不是對實物的量測；
- Blender 的替代品或通用建模工具；
- 託管服務，也不附帶任何模型權重。

## 四步流程

每一步都產出下一步要用的產物。下面的順序把測量放在第 1 步裡；`SKILL.md` 把測量單獨列為一步，而範例在模型階段很早就開始驗證，並在製作影片期間反覆重跑檢查。

### 第 1 步：用程式碼從照片建模

輸入：一張正面照片，以及任何可用的補充角度。範例用了六張：一張正面四分之三視角，加五張角度照（side-left、back、back three-quarter、bottom、top）。

Agent 做的事：

- 量測照片。範例中，外緣徑向掃描確定頭部圓及其圓心；固定半徑處的角向週期給出格柵條數；比例給出頭部厚度、中心蓋直徑、底座直徑和旋鈕直徑。
- 選定一個世界尺度並把它宣告為假設。範例取 190 mm 頭徑，其他所有尺寸都以它為比例。
- 用 three.js 的圖元和旋轉體輪廓建幾何：圓環、支柱、葉片、馬達圓柱、格柵條、底座零件。零件是獨立具名物件，因為影片要分別移動它們。
- 給每個零件一個爆炸偏移，以及引線標籤的螢幕空間錨點。
- 讓 API 不含時間：`setView()`、`setExplode()`、`setSpin()`、`render()`、`getAnchors()`。不用 `Date.now()`、不用 `requestAnimationFrame`、不發網路請求。
- 用 esbuild 把場景和 three.js 打包成一個 IIFE，頁面、檢視器和影片載入同一份程式碼。
- 去品牌。模型上的標籤面為空白；參考照片中的品牌和型號標籤也出於同樣原因做了模糊處理。

輸出：`examples/fan/src/fan-scene.js`，以及建置出的 `examples/fan/video/assets/vendor/fan.bundle.min.js`。

### 第 2 步：用 HyperFrames 算圖拆解影片

[HyperFrames](https://github.com/heygen-com/hyperframes) 透過驅動一條暫停的時間軸並逐幀截圖，把 HTML 頁面變成影片。

- `examples/fan/video/index.html` 是合成根：`data-duration="43.5"`，1920×1080。
- 暫停的 GSAP 時間軸註冊在 `window.__timelines.main`。頁面監聽 `hf-seek`，用 `event.detail.time` 重繪 canvas；沒有任何東西自行前進，因此任意一幀都能被截取。
- 43.5 秒的範例有十個鏡頭：標題、環繞、格柵特寫、後側四分之三、中心輪轂特寫、全景、爆炸展開、13 個引線標籤的定格、合體、片尾。
- 爆炸展開是每個零件一個進度值。分離從 21.15 s 起以 0.30 s 間隔錯開；合體從 35.18 s 起以 0.25 s 間隔進行；最後一個零件在 38.45 s 落座。每個引線標籤在對應零件開始移動後 0.30 s 開始淡入（淡入本身持續 0.45 s）。
- 聲音按同一契約剪輯。範例混音為 43.5 s、48 kHz、16-bit 立體聲，整體響度 −16.0 LUFS，真峰值 −2.0 dBTP。`examples/fan/video/assets/audio/sources.md` 列出素材來源和處理鏈。
- `check` 是門檻：在它報告零問題之前不要算圖。`snapshot --at <秒>` 截取單幀供檢查；範例海報就是 27.6 s 那一幀。

輸出：一個 MP4，位於 `examples/fan/video/renders/`，預設命名為 `video_<YYYY-MM-DD>_<HH-MM-SS>.mp4`。

### 第 3 步：對照照片驗證

這一步是同機位比較，不是憑印象。

1. 用無頭 Chrome 在參考照片的機位截圖。`scripts/view.html` 從 URL 查詢參數取機位（`yaw`、`pitch`、`dist`、`tx`、`ty`、`tz`、`fov`），算圖一幀 1920×1080。它沒有動畫迴圈，自身不發網路請求。
2. 把照片裁到手讀的框，把算圖裁到它自己的包圍盒。範例中，照片框從網格疊加圖上讀出，算圖框由頭部外緣和底座外緣解析投影得到。`scripts/verify_sheet.py` 也可以按背景色自動找算圖框。
3. 兩個裁剪縮放到同樣畫幅並排。取景和距離被正規化掉，於是頭部厚度、中心蓋直徑、格柵條數、底座寬度可以直接比較。
4. 逐個角度審查，記下不一致，調整量測常數，重新算圖，再重複。

範例對比圖有六列。已記錄的結果是接近匹配，同時有七處已知偏差，其中包括頭心高度（模型 1.02 D，照片 1.04–1.10 D）、後格柵外圈略寬、控制盒大了幾個百分點。這些偏差寫在範例筆記裡，而不是藏起來。

這個做法還記錄了一個負面結果。早期方案是 50/50 同機位疊圖，並把頭部圓擬合、正規化。最初在五張照片上做圓擬合，其中四張裡最強的曲線邊緣屬於背景，正規化半徑因此不可信；只有正面那張照片讓物體在整面均勻牆前填滿畫面，才得到可用的徑向掃描。疊圖被放棄，改用包圍盒對比，原因保留在 `references/03-verify.md`。

這一步是以明確包圍盒進行的目視審查，不是數值證書。

### 第 4 步：匯出 GIF

最後一步是手動的，因為它在瀏覽器裡執行：

1. 打開工具：[影片轉 GIF（英文）](https://gif-master.com/en/tools/video-to-gif) 或 [影片轉 GIF（中文）](https://gif-master.com/zh/tools/video-to-gif)。
2. 放入算圖好的 MP4。檔案在瀏覽器內處理，不會被上傳。
3. 裁到一個動作——一次爆炸展開或一個特寫，而不是整個 43.5 秒影片——設定幀率和尺寸，預覽。
4. 匯出。編輯免費；下載需要登入，免費額度為每天 3 個點數。

`references/04-gif.md` 把同樣的步驟寫成清單，並記錄了一個本機轉換的 ffmpeg 備選方案。

### 產物順序

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

## 快速開始

### 環境需求

| 需求 | 用途 |
| --- | --- |
| Node.js 22（實測 22.19.0） | 透過 `npx` 執行 HyperFrames CLI 和 esbuild。 |
| Python 3.11 與 Pillow | `scripts/verify_sheet.py`（numpy 選用）；`examples/fan/tools/review_sheet.py` 需要 numpy；範例的音訊重建腳本還會用到 numpy 和 scipy。 |
| ffmpeg | HyperFrames 算圖，以及範例中的音訊工作。 |
| Chrome 或 Chromium | 無頭截圖，以及 HyperFrames 的逐幀擷取。 |
| HyperFrames CLI 0.9.36 | 由 `npx --yes hyperframes@0.9.36` 取得；無需全域安裝。 |
| git | 複製技能和範例。 |

`scripts/hf_read_check.py` 只用 Python 標準庫。`scripts/view.html` 只需要瀏覽器和建置好的模型 bundle。

### 安裝技能

把儲存庫複製到技能目錄。專案內安裝讓技能跟隨使用它的專案；使用者層級安裝讓所有專案都能用。

```bash
# project-local
git clone https://github.com/Mng12345/model-by-coding.git .agents/skills/model-by-coding

# or user-wide
git clone https://github.com/Mng12345/model-by-coding.git ~/.agents/skills/model-by-coding
```

DeepSeek Harness、Claude Code 這類 Agent 會從專案的 `.agents/skills/` 或使用者的 `~/.agents/skills/` 讀取技能。

如果環境裡有 skills CLI，同樣的安裝只需要一條指令：

```bash
npx skills add Mng12345/model-by-coding
```

之後開一個新的 Agent 工作階段，在請求裡點名技能（`model-by-coding`）。具體如何呼叫取決於用戶端。

### 算圖範例影片

儲存庫不含二進位音訊。從[最新 Release](https://github.com/Mng12345/model-by-coding/releases/latest) 下載 `mix.wav`，在執行 check 之前放回原處。

```bash
# 1. put the mixed track back (asset name: mix.wav)
curl -L -o examples/fan/video/assets/audio/mix.wav \
  https://github.com/Mng12345/model-by-coding/releases/latest/download/mix.wav

# 2. check the HyperFrames project, then render
cd examples/fan/video
npx --yes hyperframes@0.9.36 check
npx --yes hyperframes@0.9.36 render --quality delivery
```

`check` 必須報告零問題才能算圖。結果寫入 `examples/fan/video/renders/video_<YYYY-MM-DD>_<HH-MM-SS>.mp4`；CLI 用專案目錄名和算圖時間命名檔案。如果需要在瀏覽器裡本機預覽，在算圖前加 `preview`：

```bash
npx --yes hyperframes@0.9.36 preview
```

要檢查單個時刻而不是整部影片：

```bash
npx --yes hyperframes@0.9.36 snapshot --at 27.6
```

快照寫入專案的 `.hyperframes/artifacts/snapshots/` 目錄。

`examples/fan/out/` 中隨儲存庫提供的靜態圖——海報、4×3 聯絡表、六角度對比圖和六張單角度算圖——都已入庫，不算圖任何東西也能檢視。

## 儲存庫結構

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

## 腳本

| 路徑 | 類型 | 作用 |
| --- | --- | --- |
| `scripts/view.html` | 瀏覽器頁面 | 按 URL 給出的機位算圖程式碼模型的一幀。參數：`bundle`、`global`、`yaw`、`pitch`、`dist`、`tx`、`ty`、`tz`、`fov`、`explode`、`spin`、`tilt`、`lift`、`w`、`h`、`dpr`、`bg`；逐零件除錯開關 `noshadow`、`hide`、`only` 會原樣傳給 bundle。 |
| `scripts/verify_sheet.py` | Python | 把一張照片和一張算圖各自裁到包圍盒，縮放到同樣畫幅，輸出一張並排對比圖。必填 `--photo`、`--render`、`--out` 和手讀的 `--bbox x0,y0,x1,y1`；選用 `--render-bbox`（預設按背景色自動偵測）、`--bg`、`--threshold`、`--pad`（預設 `0.04`）、`--tile`（預設 `520x620`）、`--gap`、`--label-height`、`--label-photo`、`--label-render`。必須安裝 Pillow；numpy 只用於加速背景遮罩。 |
| `scripts/hf_read_check.py` | Python | 讀取 HyperFrames check 報告——`check --json` 列印的 JSON，或 HyperFrames 儲存在 `.hyperframes/artifacts/checks/` 下的 artifact——列印 `ok`，並按分區給出問題數（lint、runtime、layout、motion、contrast、craft、audio）。`--max` 限制列印的問題條數，`--json` 把摘要按 JSON 輸出，`--fail-on-error` 在報告失敗時以非零碼結束。只用標準庫；接受 UTF-8 與 UTF-16 報告。 |
| `scripts/make_gif.md` | 文件 | gif-master 操作卡片：步驟、限制，以及本機 ffmpeg 備選方案。不是可執行檔案。 |

檢視器載入查詢參數裡指定的 bundle。隨儲存庫提供的範例 bundle 是一個普通 IIFE，因此可以直接設定機位：

```
file:///<path-to-repo>/scripts/view.html?bundle=../examples/fan/video/assets/vendor/fan.bundle.min.js&yaw=-10&pitch=12&dist=0.85&ty=0.185&fov=30
```

用同樣尺寸的無頭 Chrome 截圖：

```bash
chrome --headless=new --hide-scrollbars --window-size=1920,1080 \
  --screenshot=front.png \
  "file:///<path-to-repo>/scripts/view.html?bundle=../examples/fan/video/assets/vendor/fan.bundle.min.js&yaw=-10&pitch=12&dist=0.85&ty=0.185&fov=30"
```

用範例中已入庫的算圖產生對比圖：

```bash
python scripts/verify_sheet.py \
  --photo examples/fan/reference/fan.jpg \
  --render examples/fan/out/verify2/front-render.png \
  --bbox 130,245,1195,1455 \
  --out front-pair.png
```

讀取儲存下來的 check 報告。HyperFrames 會把自己的副本存到 `.hyperframes/artifacts/checks/<uuid>.json`；腳本也接受從 stdout 擷取的報告：

```bash
cd examples/fan/video
npx --yes hyperframes@0.9.36 check --json > check.json
python ../../../scripts/hf_read_check.py check.json

# or point it at the report the CLI saved itself
python ../../../scripts/hf_read_check.py .hyperframes/artifacts/checks/<uuid>.json
```

`scripts/` 裡的工具是參數化的：沒有物件名稱、沒有風扇專用路徑、沒有絕對路徑。`examples/fan/tools/` 裡的四個腳本是案例研究中實際用過的腳本。`review_sheet.py` 使用相對路徑，可以在儲存庫內直接執行；`grid6.py`、`measure-photo.py`、`expo_check.py` 作為過程紀錄保留，檔案開頭寫明其輸入不屬於本儲存庫，因此不能原樣執行。

## 已知限制

- **是比例，不是認證尺寸。** 範例把頭徑 190 mm 作為一個宣告的絕對尺度假設，因為照片裡沒有標尺。其他尺寸都是從它推導的比例。模型不是量測儀器。
- **被遮擋的表面是推斷的。** 後格柵細節、馬達內部、掛鉤機構以及底座的一部分在照片中看不全。它們在筆記裡被標註為推斷，不應被當作真實產品的確鑿事實。
- **驗證是目視的。** 包圍盒對齊消除了取景差異，但照片框是手讀的，也沒有數值通過閾值。對比圖可能看起來很接近，而輪廓之外的細節仍然錯誤。
- **範例的結論只屬於範例。** 13 個零件、十個鏡頭、這套時間安排和這些偏差都屬於風扇案例，不是其他物件的預設值。
- **音訊不在 git 裡。** 影片引用 `examples/fan/video/assets/audio/mix.wav`，該檔案作為 Release 附件分發。缺少它專案就不完整，因此在 `check` 或 `render` 之前要放回原處。
- **版本鎖定。** 指令固定使用 `hyperframes@0.9.36`，即建置範例所用的版本。其他版本可能行為不同；這裡不宣告相容清單。
- **範例的四個工具中有三個不能原樣執行。** 它們是指向作者原始工作區的歷史量測腳本。參數化版本在 `scripts/`。
- **GIF 步驟是手動的。** gif-master 在瀏覽器裡執行，下載需要登入，每天允許 3 次免費下載。儲存庫不自動化這一步。
- **算圖需要真實的瀏覽器和 ffmpeg。** HyperFrames 透過 Chrome 擷取幀，因此沒有可用瀏覽器的機器無法算圖影片。

## 授權條款

- **程式碼**——MIT。全文見 [`LICENSE`](LICENSE)。
- **照片與算圖媒體**——`examples/fan/reference/` 下的六張參考照片、`examples/fan/out/` 下的靜態圖，以及影片 `fan-teardown-43s.mp4`，均按 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 授權。署名：**Mng12345/model-by-coding**，並附連結 [github.com/Mng12345/model-by-coding](https://github.com/Mng12345/model-by-coding)。
- **第三方函式庫與素材**保留各自授權條款；隨儲存庫內建的 three.js、GSAP、HyperFrames 以及 Inter/Inter Tight 字型列在 [`README-LICENSES.md`](README-LICENSES.md) 中。

如果某種用法不在上述任一授權範圍內，請先在儲存庫裡開 issue 再重複使用素材。

## 誌謝與連結

- [three.js](https://threejs.org)——MIT。模型的幾何、材質和算圖都是 three.js。
- [GSAP](https://gsap.com) 3.13.0——按 [GSAP 標準授權條款](https://gsap.com/standard-license)使用。隨儲存庫內建的副本保留了授權標頭。
- [HyperFrames](https://github.com/heygen-com/hyperframes) 0.9.36——用於算圖影片的 HTML 轉影片工具。專案網站：https://hyperframes.heygen.com
- [gif-master.com](https://gif-master.com)——第 4 步使用的瀏覽器端影片轉 GIF 工具。
- Inter 與 Inter Tight——SIL Open Font License 1.1 下的 Web 字型；授權條款文字隨字型檔案放在 `examples/fan/video/assets/fonts/`。
- 參考照片由作者拍攝；品牌和型號標籤在發布前做了模糊處理。模型不帶品牌。這是一次幾何研究，不是獲得授權的復刻。
- 儲存庫：https://github.com/Mng12345/model-by-coding
- Releases：https://github.com/Mng12345/model-by-coding/releases/latest
- Issues：https://github.com/Mng12345/model-by-coding/issues

風扇範例只是一個物件、一部影片。值得重複使用的是量測筆記、同機位檢查，以及把模型序列化成程式碼的做法——而不是風扇的具體數字。
