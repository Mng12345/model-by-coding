> 本文是 README.md 的简体中文译文，如有出入以英文版为准。

# model-by-coding

一个 Agent Skill：把一件实物从照片重建成确定性的 three.js 模型，再把该模型做成拆解演示影片和 GIF，全程不打开 3D 建模软件。

本仓库就是这个技能本身：Agent 可以遵循的说明、可复用脚本、长篇参考笔记，以及一个完整的示例——一台白色 USB 桌面风扇，以代码重建，并渲染为 13 个零件、1920×1080、30 fps、43.5 秒的影片。

- [这是什么](#这是什么)
- [它解决什么问题](#它解决什么问题)
- [四步流程](#四步流程)
- [快速开始](#快速开始)
- [仓库结构](#仓库结构)
- [脚本](#脚本)
- [已知限制](#已知限制)
- [许可证](#许可证)
- [致谢与链接](#致谢与链接)

## 这是什么

Agent Skill 是一个 Agent 可以加载的目录：`SKILL.md` 入口，加上任务需要的笔记和脚本。本仓库分四部分：

| 部分 | 内容 |
| --- | --- |
| `SKILL.md` | 入口文件：技能何时适用、流程本身，以及不可省略的规则。 |
| `references/` | 六篇长篇笔记，记录不适合放进技能文件的细节：建模、渲染、验证、GIF 导出、发布，以及一组常见陷阱。 |
| `scripts/` | 可复用工具：单帧查看器、照片与渲染的对比图、check 输出读取器，以及 GIF 操作卡片。 |
| `examples/fan/` | 完整示例：照片、模型源码、HyperFrames 工程、验证渲染和产物。 |

示例不是演示稿。照片是作者自己拍的；模型是手写 JavaScript；影片由该模型渲染；六角度对比图已随仓库提供。它们共同展示了按说明从头到尾执行会得到什么。[examples/fan/README.md](examples/fan/README.md) 记录了各项数字，包括没有修正的偏差。

先读 `SKILL.md`。参考笔记是需要更多篇幅的部分：

| 文件 | 主题 |
| --- | --- |
| `references/01-modeling.md` | 坐标系、测量得到的比例、旋转体轮廓、格栅与叶片参数、各零件的锚点。 |
| `references/02-render.md` | HyperFrames 的渲染契约、镜头表、音频同步点。 |
| `references/03-verify.md` | 无头截图、包围盒对比、逐角度审查，以及失败的叠图实验。 |
| `references/04-gif.md` | gif-master 的分步操作卡片、点数限制，以及 ffmpeg 备选方案。 |
| `references/05-publish.md` | 发布清单，以及输出通常去向的各个平台上的实际门槛。 |
| `references/06-gotchas.md` | 其中涉及色调映射与曝光、灯光衰减、阴影色带、必须做成扁平带状而非圆管的格栅条、最小文字尺寸，以及随仓库内置的 `.min.js` 文件。 |

## 它解决什么问题

要一个“这个物体的 3D 模型”时，Agent 通常会给出两种结果之一：一张无法核对的漂亮渲染，或者一个比例随意、也没法继续做影片的网格。两者都难以审查。渲染的相机位置通常未知，无法与照片并排；改动之后，资产也无法重新推导。

本技能用一个每一步都留下证据的流程来替代上述做法。

1. **比例是量出来的，不是猜的。** 模型里的每个常量要么能追溯到照片上的测量，要么被标注为推断。真正被延续下去的是比例，而不是绝对尺寸。
2. **同一帧可以复现。** 模型只暴露普通状态——机位、爆炸展开量、叶片旋转角——没有其他东西。没有时钟、没有随机数、没有网络。同样的输入得到同样的帧，因此审查可以针对一个确切的机位。
3. **对比是同口径的。** 每次渲染都用参考照片的机位截图，两侧各自裁到自己的轮廓包围盒，再缩放到同样的画幅。取景和距离不再能掩盖比例错误。
4. **一个模型供给所有产物。** 同一个 bundle 驱动验证截图、交互页面和影片，模型改一次，所有地方都会变。
5. **结果可以用 git 审查。** 模型是代码和命名常量。改动是 diff，不是二进制资产。

它不是：

- 摄影测量或 3D 扫描仪——不会自动重建几何；
- CAD——尺寸是能追溯到照片的比例，不是对实物的测量；
- Blender 的替代品或通用建模工具；
- 托管服务，也不附带任何模型权重。

## 四步流程

每一步都产出下一步要用的产物。下面的顺序把测量放在第 1 步里；`SKILL.md` 把测量单列为一步，而示例在模型阶段很早就开始验证，并在制作影片期间反复重跑检查。

### 第 1 步：用代码从照片建模

输入：一张正面照片，以及任何可用的补充角度。示例用了六张：一张正面四分之三视角，加五张角度照（side-left、back、back three-quarter、bottom、top）。

Agent 做的事：

- 测量照片。示例中，外缘径向扫描确定头部圆及其圆心；固定半径处的角向周期给出格栅条数；比例给出头部厚度、中心盖直径、底座直径和旋钮直径。
- 选定一个世界尺度并把它声明为假设。示例取 190 mm 头径，其他所有尺寸都以它为比例。
- 用 three.js 的图元和旋转体轮廓建几何：圆环、支柱、叶片、电机圆柱、格栅条、底座零件。零件是独立命名对象，因为影片要分别移动它们。
- 给每个零件一个爆炸偏移，以及引线标签的屏幕空间锚点。
- 让 API 不含时间：`setView()`、`setExplode()`、`setSpin()`、`render()`、`getAnchors()`。不用 `Date.now()`、不用 `requestAnimationFrame`、不发网络请求。
- 用 esbuild 把场景和 three.js 打包成一个 IIFE，页面、查看器和影片加载同一份代码。
- 去品牌。模型上的标签面为空白；参考照片中的品牌和型号标签也出于同样原因做了模糊处理。

输出：`examples/fan/src/fan-scene.js`，以及构建出的 `examples/fan/video/assets/vendor/fan.bundle.min.js`。

### 第 2 步：用 HyperFrames 渲染拆解影片

[HyperFrames](https://github.com/heygen-com/hyperframes) 通过驱动一条暂停的时间轴并逐帧截图，把 HTML 页面变成视频。

- `examples/fan/video/index.html` 是合成根：`data-duration="43.5"`，1920×1080。
- 暂停的 GSAP 时间轴注册在 `window.__timelines.main`。页面监听 `hf-seek`，用 `event.detail.time` 重绘 canvas；没有任何东西自行前进，因此任意一帧都能被截取。
- 43.5 秒的示例有十个镜头：标题、环绕、格栅特写、后侧四分之三、中心轮毂特写、全景、爆炸展开、13 个引线标签的定格、合体、片尾。
- 爆炸展开是每个零件一个进度值。分离从 21.15 s 起以 0.30 s 间隔错开；合体从 35.18 s 起以 0.25 s 间隔进行；最后一个零件在 38.45 s 落座。每个引线标签在对应零件开始移动后 0.30 s 开始淡入（淡入本身持续 0.45 s）。
- 声音按同一契约剪辑。示例混音为 43.5 s、48 kHz、16-bit 立体声，整体响度 −16.0 LUFS，真峰值 −1.9 dBTP。`examples/fan/video/assets/audio/sources.md` 列出素材来源和处理链。
- `check` 是门槛：在它报告零问题之前不要渲染。`snapshot --at <秒>` 截取单帧供检查；示例海报就是 27.6 s 那一帧。

输出：一个 MP4，位于 `examples/fan/video/renders/`，默认命名为 `video_<YYYY-MM-DD>_<HH-MM-SS>.mp4`。

### 第 3 步：对照照片验证

这一步是同机位比较，不是凭印象。

1. 用无头 Chrome 在参考照片的机位截图。`scripts/view.html` 从 URL 查询参数取机位（`yaw`、`pitch`、`dist`、`tx`、`ty`、`tz`、`fov`），渲染一帧 1920×1080。它没有动画循环，自身不发网络请求。
2. 把照片裁到手读的框，把渲染裁到它自己的包围盒。示例中，照片框从网格叠加图上读出，渲染框由头部外缘和底座外缘解析投影得到。`scripts/verify_sheet.py` 也可以按背景色自动找渲染框。
3. 两个裁剪缩放到同样画幅并排。取景和距离被归一化掉，于是头部厚度、中心盖直径、格栅条数、底座宽度可以直接比较。
4. 逐个角度审查，记下不一致，调整测量常量，重新渲染，再重复。

示例对比图有六行。已记录的结果是接近匹配，同时有七处已知偏差，其中包括头心高度（模型 1.02 D，照片 1.04–1.10 D）、后格栅外圈略宽、控制盒大了几个百分点。这些偏差写在示例笔记里，而不是藏起来。

这个做法还记录了一个负面结果。早期方案是 50/50 同机位叠图，并把头部圆拟合、归一化。最初在五张照片上做圆拟合，其中四张里最强的曲线边缘属于背景，归一化半径因此不可信；只有正面那张照片让物体在整面均匀墙前填满画面，才得到可用的径向扫描。叠图被放弃，改用包围盒对比，原因保留在 `references/03-verify.md`。

这一步是以明确包围盒进行的目视审查，不是数值证书。

### 第 4 步：导出 GIF

最后一步是手动的，因为它在浏览器里运行：

1. 打开工具：[视频转 GIF（英文）](https://gif-master.com/en/tools/video-to-gif) 或 [视频转 GIF（中文）](https://gif-master.com/zh/tools/video-to-gif)。
2. 放入渲染好的 MP4。文件在浏览器内处理，不会被上传。
3. 裁到一个动作——一次爆炸展开或一个特写，而不是整个 43.5 秒影片——设置帧率和尺寸，预览。
4. 导出。编辑免费；下载需要登录，免费额度为每天 3 个点数。

`references/04-gif.md` 把同样的步骤写成清单，并记录了一个本地转换的 ffmpeg 备选方案。

### 产物顺序

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

## 快速开始

### 环境要求

| 要求 | 用途 |
| --- | --- |
| Node.js 22（实测 22.19.0） | 通过 `npx` 运行 HyperFrames CLI 和 esbuild。 |
| Python 3.11 与 Pillow | `scripts/verify_sheet.py`（numpy 可选）；`examples/fan/tools/review_sheet.py` 需要 numpy；示例的音频重建脚本还会用到 numpy 和 scipy。 |
| ffmpeg | HyperFrames 渲染，以及示例中的音频工作。 |
| Chrome 或 Chromium | 无头截图，以及 HyperFrames 的逐帧捕获。 |
| HyperFrames CLI 0.9.36 | 由 `npx --yes hyperframes@0.9.36` 获取；无需全局安装。 |
| git | 克隆技能和示例。 |

`scripts/hf_read_check.py` 只用 Python 标准库。`scripts/view.html` 只需要浏览器和构建好的模型 bundle。

### 安装技能

把仓库克隆到技能目录。项目内安装让技能跟随使用它的项目；用户级安装让所有项目都能用。

```bash
# project-local
git clone https://github.com/Mng12345/model-by-coding.git .agents/skills/model-by-coding

# or user-wide
git clone https://github.com/Mng12345/model-by-coding.git ~/.agents/skills/model-by-coding
```

DeepSeek Harness、Claude Code 这类 Agent 会从项目的 `.agents/skills/` 或用户的 `~/.agents/skills/` 读取技能。

如果环境里有 skills CLI，同样的安装只需要一条命令：

```bash
npx skills add Mng12345/model-by-coding
```

之后开一个新的 Agent 会话，在请求里点名技能（`model-by-coding`）。具体如何调用取决于客户端。

### 渲染示例影片

仓库不含二进制音频。从[最新 Release](https://github.com/Mng12345/model-by-coding/releases/latest) 下载 `mix.wav`，在运行 check 之前放回原处。

```bash
# 1. put the mixed track back (asset name: mix.wav)
curl -L -o examples/fan/video/assets/audio/mix.wav \
  https://github.com/Mng12345/model-by-coding/releases/latest/download/mix.wav

# 2. check the HyperFrames project, then render
cd examples/fan/video
npx --yes hyperframes@0.9.36 check
npx --yes hyperframes@0.9.36 render --quality delivery
```

`check` 必须报告零问题才能渲染。结果写入 `examples/fan/video/renders/video_<YYYY-MM-DD>_<HH-MM-SS>.mp4`；CLI 用工程目录名和渲染时间命名文件。如果需要在浏览器里本地预览，在渲染前加 `preview`：

```bash
npx --yes hyperframes@0.9.36 preview
```

要检查单个时刻而不是整部影片：

```bash
npx --yes hyperframes@0.9.36 snapshot --at 27.6
```

快照写入工程的 `.hyperframes/artifacts/snapshots/` 目录。

`examples/fan/out/` 中随仓库提供的静态图——海报、4×3 联系表、六角度对比图和六张单角度渲染——都已入库，不渲染任何东西也能查看。

## 仓库结构

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

## 脚本

| 路径 | 类型 | 作用 |
| --- | --- | --- |
| `scripts/view.html` | 浏览器页面 | 按 URL 给出的机位渲染代码模型的一帧。参数：`bundle`、`global`、`yaw`、`pitch`、`dist`、`tx`、`ty`、`tz`、`fov`、`explode`、`spin`、`tilt`、`lift`、`w`、`h`、`dpr`、`bg`；逐零件调试开关 `noshadow`、`hide`、`only` 会原样传给 bundle。 |
| `scripts/verify_sheet.py` | Python | 把一张照片和一张渲染各自裁到包围盒，缩放到同样画幅，输出一张并排对比图。必填 `--photo`、`--render`、`--out` 和手读的 `--bbox x0,y0,x1,y1`；可选 `--render-bbox`（默认按背景色自动检测）、`--bg`、`--threshold`、`--pad`（默认 `0.04`）、`--tile`（默认 `520x620`）、`--gap`、`--label-height`、`--label-photo`、`--label-render`。必须安装 Pillow；numpy 只用于加速背景掩膜。 |
| `scripts/hf_read_check.py` | Python | 读取 HyperFrames check 报告——`check --json` 打印的 JSON，或 HyperFrames 保存在 `.hyperframes/artifacts/checks/` 下的 artifact——打印 `ok`，并按分区给出问题数（lint、runtime、layout、motion、contrast、craft、audio）。`--max` 限制打印的问题条数，`--json` 把摘要按 JSON 输出，`--fail-on-error` 在报告失败时以非零码退出。只用标准库；接受 UTF-8 与 UTF-16 报告。 |
| `scripts/make_gif.md` | 文档 | gif-master 操作卡片：步骤、限制，以及本地 ffmpeg 备选方案。不是可执行文件。 |

查看器加载查询参数里指定的 bundle。随仓库提供的示例 bundle 是一个普通 IIFE，因此可以直接设定机位：

```
file:///<path-to-repo>/scripts/view.html?bundle=../examples/fan/video/assets/vendor/fan.bundle.min.js&yaw=-10&pitch=12&dist=0.85&ty=0.185&fov=30
```

用同样尺寸的无头 Chrome 截图：

```bash
chrome --headless=new --hide-scrollbars --window-size=1920,1080 \
  --screenshot=front.png \
  "file:///<path-to-repo>/scripts/view.html?bundle=../examples/fan/video/assets/vendor/fan.bundle.min.js&yaw=-10&pitch=12&dist=0.85&ty=0.185&fov=30"
```

用示例中已入库的渲染生成对比图：

```bash
python scripts/verify_sheet.py \
  --photo examples/fan/reference/fan.jpg \
  --render examples/fan/out/verify2/front-render.png \
  --bbox 130,245,1195,1455 \
  --out front-pair.png
```

读取保存下来的 check 报告。HyperFrames 会把自己的副本存到 `.hyperframes/artifacts/checks/<uuid>.json`；脚本也接受从 stdout 捕获的报告：

```bash
cd examples/fan/video
npx --yes hyperframes@0.9.36 check --json > check.json
python ../../../scripts/hf_read_check.py check.json

# or point it at the report the CLI saved itself
python ../../../scripts/hf_read_check.py .hyperframes/artifacts/checks/<uuid>.json
```

`scripts/` 里的工具是参数化的：没有对象名、没有风扇专用路径、没有绝对路径。`examples/fan/tools/` 里的四个脚本是案例研究中实际用过的脚本。`review_sheet.py` 使用相对路径，可以在仓库内直接运行；`grid6.py`、`measure-photo.py`、`expo_check.py` 作为过程记录保留，文件头写明其输入不属于本仓库，因此不能原样运行。

## 已知限制

- **是比例，不是认证尺寸。** 示例把头径 190 mm 作为一个声明的绝对尺度假设，因为照片里没有标尺。其他尺寸都是从它推导的比例。模型不是测量仪器。
- **被遮挡的表面是推断的。** 后格栅细节、电机内部、挂钩机构以及底座的一部分在照片中看不全。它们在笔记里被标注为推断，不应被当作真实产品的确凿事实。
- **验证是目视的。** 包围盒对齐消除了取景差异，但照片框是手读的，也没有数值通过阈值。对比图可能看起来很接近，而轮廓之外的细节仍然错误。
- **示例的结论只属于示例。** 13 个零件、十个镜头、这套时间安排和这些偏差都属于风扇案例，不是其他对象的默认值。
- **音频不在 git 里。** 影片引用 `examples/fan/video/assets/audio/mix.wav`，该文件作为 Release 附件分发。缺少它工程就不完整，因此在 `check` 或 `render` 之前要放回原处。
- **版本锁定。** 命令固定使用 `hyperframes@0.9.36`，即构建示例所用的版本。其他版本可能行为不同；这里不声明兼容列表。
- **示例的四个工具中有三个不能原样运行。** 它们是指向作者原始工作区的历史测量脚本。参数化版本在 `scripts/`。
- **GIF 步骤是手动的。** gif-master 在浏览器里运行，下载需要登录，每天允许 3 次免费下载。仓库不自动化这一步。
- **渲染需要真实的浏览器和 ffmpeg。** HyperFrames 通过 Chrome 捕获帧，因此没有可用浏览器的机器无法渲染影片。

## 许可证

- **代码**——MIT。全文见 [`LICENSE`](LICENSE)。
- **照片与渲染媒体**——`examples/fan/reference/` 下的六张参考照片、`examples/fan/out/` 下的静态图，以及影片 `fan-teardown-43s.mp4`，均按 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 授权。署名：**Mng12345/model-by-coding**，并附链接 [github.com/Mng12345/model-by-coding](https://github.com/Mng12345/model-by-coding)。
- **第三方库与素材**保留各自许可证；随仓库内置的 three.js、GSAP、HyperFrames 以及 Inter/Inter Tight 字体列在 [`README-LICENSES.md`](README-LICENSES.md) 中。

如果某种用法不在上述任一许可范围内，请先在仓库里开 issue 再复用素材。

## 致谢与链接

- [three.js](https://threejs.org)——MIT。模型的几何、材质和渲染器都是 three.js。
- [GSAP](https://gsap.com) 3.13.0——按 [GSAP 标准许可证](https://gsap.com/standard-license)使用。随仓库内置的副本保留了许可证头部。
- [HyperFrames](https://github.com/heygen-com/hyperframes) 0.9.36——用于渲染影片的 HTML 转视频工具。项目站点：https://hyperframes.heygen.com
- [gif-master.com](https://gif-master.com)——第 4 步使用的浏览器端视频转 GIF 工具。
- Inter 与 Inter Tight——SIL Open Font License 1.1 下的 Web 字体；许可证文本随字体文件放在 `examples/fan/video/assets/fonts/`。
- 参考照片由作者拍摄；品牌和型号标签在发布前做了模糊处理。模型不带品牌。这是一次几何研究，不是获得授权的复刻。
- 仓库：https://github.com/Mng12345/model-by-coding
- Releases：https://github.com/Mng12345/model-by-coding/releases/latest
- Issues：https://github.com/Mng12345/model-by-coding/issues

风扇示例只是一个对象、一部影片。值得复用的是测量笔记、同机位检查，以及把模型序列化成代码的做法——而不是风扇的具体数字。
