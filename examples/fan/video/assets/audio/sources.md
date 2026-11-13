# 音频素材来源与合成说明（v2）

交付目录：`video/assets/audio/`
制作日期：2026-11-12（Asia/Shanghai）
成片规格对应：**43.5 s** / 1920×1080 / 30 fps（`SPEC-v2.md` §4）
本文件为 v2 版：时间轴、音效数量（13+13+1）、成片指标全部按 43.5 s 版本重写。
v1（40.0 s / 9+9 版）成片备份在 `work/v1-mix.wav`（40.000000 s，SHA256 `b784e6eb206e7080ce3cde1aa3ffc53b23a8e58ee7bc4508f23995441b5260e7`）。

---

## 1. 逐条素材来源

### 1.1 音乐 bed —— `music.mp3`

| 项目 | 内容 |
| --- | --- |
| 曲名 | Minimal Technology |
| 作者 | fugu_vibes |
| 来源站 | Pixabay（音乐库） |
| 作品页 | https://pixabay.com/music/ambient-minimal-technology-623485/ |
| 直链（当时实际下载地址） | https://cdn.pixabay.com/download/audio/2026/10/20/audio_692a1a560a.mp3?filename=fugu_vibes-minimal-technology-623485.mp3 |
| 许可 | Pixabay Content License（作品页标注 "Free for use"，可商用、无需署名；条款以 pixabay.com 站点 License 页为准） |
| 获取时间 | 2026-11-12 10:39（本地文件时间） |
| 原始文件（ffprobe 实测） | 102.034281 s，44.1 kHz 立体声，MP3 256 kbps，3,265,097 字节 |
| 是否修改 | **是**，见 §4 处理链 |

作品页上标注的信息（获取时读到的页面内容）：时长 1:42，流派 Ambient / Beats / Electronic，情绪 Chill / Laid Back / Dreamy / Bright / Relaxing，描述提到 "minimal synths and modern tech beats"，适合科技类演示。

> ⚠️ **Content ID 提示**：该作品页标注了 Content ID Registered，作者说明若收到版权主张可与其联系。Pixabay Content License 本身允许商用，但**发布到 YouTube 等平台时仍可能被 Content ID 系统命中**。若成片要公开发布，建议发布前确认，或改用其它曲目。此风险由发布方判断。

### 1.2 音效 —— 27 个塑料机构声

交付文件：`foley-part-release-01..13.wav`（13 个分离声）、`foley-part-close-01..13.wav`（13 个合体声）、`foley-final-seat.wav`（最终落座）。

| 项目 | 内容 |
| --- | --- |
| 来源 | **本地合成生成**（非采样、非下载） |
| 生成脚本 | `work/synth_foley.py`（numpy + scipy） |
| 生成时间 | 2026-11-12 14:08 |
| 生成环境 | Python 3.11.1（`D:\Python\Python311\python.exe`）+ numpy 2.4.6 + scipy 1.16.0 |
| 许可 | 无第三方版权，随本项目使用 |
| 是否修改 | 不适用（本身就是生成物） |

**注明：这批音效是「合成生成」的，不是实录采样。** 合成模型为：极短宽带接触瞬态（1–2 ms 指数衰减噪声）→ 3 个塑料体共振模态（阻尼正弦，主频按音色表在 960–6880 Hz 取值）→ 低频"闷响"（面板共鸣，主频 118–286 Hz）→ 少量出气噪声 → 几毫秒后的二次微接触（仅 clip / shell / seat 三种），整体再叠一个 130 ms 的小房间脉冲响应。主瞬态权重最高（0.90），模态 0.22、低频 0.22、气流 0.08，保证峰值即接触瞬态、便于逐点对齐。

原本计划从 Pixabay 音效库下载实录素材（已找到 5 条候选页，见 §6），但该站音效页的下载按钮被 Cloudflare Turnstile 拦截，多次尝试均未取得文件；按任务约定的降级方案改为本地合成。

- `foley-part-release-*.wav`：0.165–0.240 s，峰值 −6.0 / −6.8 / −7.6 dBFS 三档轮换；7 种音色（shell / pull / seat / clip / knob / thud / snap），每个的共振频率、阻尼、音高、亮度、低频体量都不同（见 `work/sfx/foley_manifest_v2.json`）。
  - 实测特征范围：峰值时刻 0.333–4.312 ms、频谱质心 1902.8–5466.4 Hz、主频 100–350 Hz、时长 0.165–0.240 s —— 13 个两两可区分。
  - `release-07/08` 是棘轮声（knob），由 2–3 次递减咔哒组成（后次 0.45 倍），首次咔哒即全文件峰值。
- `foley-part-close-*.wav`：由上述分离声**整段反向**得到（`close-NN` = `release-(14-NN)` 的反向，映射见 `foley_manifest_v2.json` 的 `close_map`），末尾只做 0.5 ms 收尾，使反向后的接触瞬态（即原分离声的起音）成为文件绝对峰值；混音时把该峰值对齐到合体契约时间。听感是"渐强—触到—收尾"的合拢声。
- `foley-final-seat.wav`：0.300 s，两段式（先轻接触、52.542 ms 后清脆到位声），峰值 −5.0 dBFS。契约时间 38.45 s 对齐的是第二段到位声。

### 1.3 风扇 whirr —— `foley-fan-whirr.wav`

| 项目 | 内容 |
| --- | --- |
| 来源 | **本地合成生成** |
| 生成脚本 | `work/synth_beds.py`（`make_whirr`） |
| 生成时间 | 2026-11-12 10:45（沿用 v1，未改动） |
| 规格 | 22.800 s（1,094,400 帧），48 kHz 立体声，16-bit；左右声道 RMS：L −25.87 / R −26.13 dBFS，峰值 L −11.88 / R −12.89 dBFS |
| 循环 | 首尾做了无缝交叠（`seamless`），可整段 loop |
| 内容 | 62 Hz 叶片通过频率 + 谐波、粉噪气流（带通）、轻微 chuff 调幅、一点高频哨音 |

**同样标注「合成生成」**：不是实录风扇声。

### 1.4 房间底噪 —— `foley-room-tone.wav`

| 项目 | 内容 |
| --- | --- |
| 来源 | **本地合成生成** |
| 生成脚本 | `work/synth_beds.py`（`make_room`） |
| 生成时间 | 2026-11-12 10:45（沿用 v1，未改动） |
| 规格 | 5.000 s，48 kHz 立体声，16-bit；左右声道 RMS −58.14 / −58.03 dBFS，峰值 −45.91 / −45.60 dBFS |
| 用途 | 全片垫底的极轻空气声，避免数字静音的死寂感 |

---

## 2. 成片 `mix.wav`（实测）

| 项目 | 实测值 |
| --- | --- |
| 时长 | **43.500000 s**（2,088,000 帧 @48 kHz） |
| 格式 | WAV / PCM 16-bit / 48,000 Hz / 2 ch（立体声），8,352,044 字节 |
| 响度 | **−16.0 LUFS**（integrated，ffmpeg `ebur128=peak=true`） |
| 真峰值 | **−1.9 dBTP**（≤ −1.5） |
| Loudness Range | **2.7 LU**（≤ 6） |
| 采样峰值 | −3.2 dBFS；0 个满刻度采样 |
| 母带限制器 | 采样级 ceiling −3.2 dBFS、6 ms 前瞻、120 ms release，最大增益衰减 4.0 dB |
| 立体声 | 声道相关 0.6128，L/R 电平差 −0.03 dB，side/mid −6.2 dB（单声道兼容良好） |
| SHA256 | `6cc9faefccf2298f0babaa4df3eafc7ff1c2ce56c190755fa4a98e36ad88b543` |

以上为 `work/verify_mix.py` 对成品的实际测量值，完整报告见 `work/build_report_v2.json`（`checks.all_pass = true`）。

---

## 3. 时间轴（与实际渲染一致）

| 时间 | 内容 | 实现 |
| --- | --- | --- |
| 0.00–0.80 | room tone 起底，无音乐、无 whirr | room tone −58 dBFS，0.05 s 淡入 |
| 0.80–1.60 | whirr 淡入 | 余弦淡入到额定电平（比音乐 bed 低约 30 dB） |
| 2.00–2.30 | 音乐进 | 余弦淡入；2.30 起为稳定 bed |
| 5.00–18.00 | 稳定 bed | 音乐层 RMS −22.5 dBFS（5–18 s），成片该段 full RMS −18.6 dBFS |
| 9.00–12.50 | whirr 抬高给格栅特写 | whirr 层 +3.0 dB（×1.4125），13.40 回到额定 |
| 21.15 … 24.75 | **13 个部件分离**（间隔 0.30 s） | 21.15, 21.45, 21.75, 22.05, 22.35, 22.65, 22.95, 23.25, 23.55, 23.85, 24.15, 24.45, 24.75；峰值对齐契约时间，声像 ±0.18 内分布，电平 −6.0 ~ −8.2 dBFS |
| 26.00–34.00 | "空间"段：低频抽掉 | <120 Hz 分频后 ×0.55（−5.19 dB），26.0→26.8 进、33.2→34.0 出；音乐同时整体 ×0.94；实测该段 20–120 Hz RMS 比 bed 段低 3.34 dB（两窗口音乐原素材低频含量不同，非纯增益测量） |
| 35.18 … 38.18 | **13 个部件合体**（间隔 0.25 s） | 35.18, 35.43, 35.68, 35.93, 36.18, 36.43, 36.68, 36.93, 37.18, 37.43, 37.68, 37.93, 38.18；反向音**按峰值对齐**契约时间（否则反向音的冲击会晚 0.18–0.24 s 才响），电平随序号渐强 −8.6 → −6.1 dBFS |
| 38.45 | 最终落座 | 两段式落座声，峰值对齐 38.45 s，声像居中，峰值 −6.8 dBFS |
| 42.30–43.50 | 整体淡出至静音 | 音乐、whirr、room tone 同步余弦淡出，43.50 为 0 |

补充：whirr 用 22.800 s 无缝 loop 平铺，唯一拼接点在 **22.798 s**（采样 1,094,304），拼接处做 2 ms 线性（等增益）交叉淡化，成片无接缝。

---

## 4. 处理链

**音乐 bed**（`work/build_mix.py`）
1. 取源曲第 8.0 s 起的 43.5 s（跳过前奏；源曲 102.03 s，够用，无需循环）。
2. 压缩：threshold −28 dBFS、ratio 3.5、attack 15 ms、release 220 ms。
3. EQ：3.2 kHz 峰值衰减 −2.6 dB（Q 0.9），给咔哒声让出频段。
4. 低频整理：<120 Hz 零相位分频，低频 ×0.72。
5. 电平自动化：2.00→2.30 s 淡入；26.0→26.8 s 降到 0.94、33.2→34.0 s 回 1.0；42.30→43.50 s 归零。
6. 侧链闪避：每当有音效时音乐下压，最多 4.7 dB（attack 8 ms / release 200 ms），让咔哒清晰"浮"在 bed 上。

**whirr / room tone**（`work/build_mix.py`）
- whirr：22.800 s loop 平铺 + 2 ms 拼接交叉淡化；<120 Hz 段在 26.0–34.0 s 同样 ×0.55；电平自动化 0.80→1.60 s 淡入、8.55→9.00 s 抬到 ×1.4125、12.50→13.40 s 回 1.0、42.30→43.50 s 归零；归一化到 RMS −52.5 dBFS（3–8 s）。
- room tone：5 s loop 平铺，0.05 s 淡入，42.30→43.50 s 归零，RMS −58 dBFS。

**母带**（`work/master.py`）：整体 +4.0 dB，过 6 ms 前瞻、采样级 ceiling −3.2 dBFS 的立体声链接砖墙限制器（120 ms release），迭代到 −16.0 LUFS。ceiling 取 −3.2 dBFS 是因为合成塑料瞬态很尖，4× 过采样下真峰值比采样峰值高约 1.3 dB；实测成品 TP −1.9 dBTP。

**自检**（`work/verify_mix.py`）：读 WAV 头 + PCM 实测帧数/格式，ffprobe 交叉核对，`ffmpeg -filter_complex ebur128=peak=true` 测 LUFS/TP/LRA，逐事件测峰值偏差，测声道相关、满刻度采样、分段频带 RMS 与包络。全部实测值写入 `work/build_report_v2.json`（无估算值）。

---

## 5. 自检结果（本次实际运行）

运行命令（工作目录 `video/assets/audio`）：

```
D:\Python\Python311\python.exe work\verify_mix.py mix.wav work\build_report_v2.json
```

- 时长/帧数/格式：2,088,000 帧 = 43.500000 s，48 kHz / 2 ch / 16-bit —— PASS
- −16 LUFS ±0.5 / 真峰值 ≤ −1.5 dBTP / LRA ≤ 6 LU：−16.0 LUFS、−1.9 dBTP、2.7 LU —— PASS
- 27 个事件峰值偏差（口径：成片单声道 1.5–6 kHz 零相位带通后的峰值，在契约时间 ±30 ms 内搜索；合体音是反向渐强音，其峰值就是"触到"的那一下，按设计对齐）：

| 事件 | 契约时间 (s) | 实测偏差 (ms) | 事件 | 契约时间 (s) | 实测偏差 (ms) |
| --- | --- | --- | --- | --- | --- |
| release-01 | 21.150 | −0.542 | close-01 | 35.180 | −0.625 |
| release-02 | 21.450 | −0.125 | close-02 | 35.430 | −0.125 |
| release-03 | 21.750 | +0.104 | close-03 | 35.680 | 0.000 |
| release-04 | 22.050 | 0.000 | close-04 | 35.930 | +0.167 |
| release-05 | 22.350 | −0.146 | close-05 | 36.180 | +0.083 |
| release-06 | 22.650 | 0.000 | close-06 | 36.430 | −0.854 |
| release-07 | 22.950 | +0.583 | close-07 | 36.680 | −0.604 |
| release-08 | 23.250 | +0.833 | close-08 | 36.930 | 0.000 |
| release-09 | 23.550 | 0.000 | close-09 | 37.180 | +0.146 |
| release-10 | 23.850 | −0.167 | close-10 | 37.430 | 0.000 |
| release-11 | 24.150 | 0.000 | close-11 | 37.680 | −0.125 |
| release-12 | 24.450 | +0.104 | close-12 | 37.930 | +0.125 |
| release-13 | 24.750 | +0.625 | close-13 | 38.180 | 0.000 |
| seat | 38.450 | +0.021 | | | |

  **27/27 全部 ≤ ±5 ms，最大 |偏差| 0.854 ms**（且都是 1 个采样 = 0.021 ms 的整数倍，无亚采样漂移）。每个事件的底噪抬升 lift 最小 18.3 dB，说明测到的就是音效本身而不是 bed。
  - 参考值：若按"宽带采样峰值"口径，大多数事件也在 ±0.7 ms 内；close-04/10/12 的宽带峰值比带通峰值早约 7.3–9.2 ms —— 反向渐强音的包络峰落在"触到"之前，属设计使然，故以 1.5–6 kHz 瞬态峰值作为验收口径（`build_report_v2.json` 同时保留 `broadband_peak_deviation_ms` 参考字段）。
- 声道相关 0.6128、L/R 差 −0.03 dB、side/mid −6.2 dB、满刻度采样 0 个 —— PASS
- 分段电平（full / 20–120 Hz / 300–4k / 1.5–6k dBFS RMS）：bed 段 −18.6 / −20.0 / −27.6 / −39.9；分离段 −17.5 / −19.1 / −26.0 / −29.4；空间段 −21.0 / −23.3 / −27.7 / −39.1；合体段 −17.2 / −19.0 / −25.0 / −28.1；收尾段 −18.0 / −20.8 / −25.2 / −38.1；淡出段 −22.2 / −23.0 / −30.4 / −45.0

---

## 6. 交付清单

```
video/assets/audio/
├── mix.wav                          成片混音 43.500000 s / 48 kHz / 16-bit / stereo
├── music.mp3                        音乐原素材（Pixabay, fugu_vibes）
├── foley-part-release-01..13.wav    13 个部件分离声（合成）
├── foley-part-close-01..13.wav      13 个合体声（上述分离声整段反向）
├── foley-final-seat.wav             最终落座声（合成，两段式）
├── foley-fan-whirr.wav              风扇 whirr 22.8 s 可循环（合成）
├── foley-room-tone.wav              房间底噪 5 s（合成）
├── sources.md                       本文件
└── work/                            中间产物与脚本
    ├── synth_foley.py               27 个音效合成
    ├── synth_beds.py                whirr / room tone 合成（沿用 v1）
    ├── build_mix.py                 43.5 s 混音构建
    ├── master.py                    −16 LUFS / 真峰值母带
    ├── verify_mix.py                成品实测与自检
    ├── build_report_v2.json         自检实测报告（27 事件逐条 + 全部检查项）
    ├── mix_build_v2.json            构建参数与分层电平
    ├── mix_raw.wav                  母带前混音
    ├── v1-mix.wav                   v1（40 s）成片备份
    ├── sfx/                         27 个音效 + foley_manifest_v2.json
    └── beds/                        whirr / room tone 循环素材
```

未改动 `src/`、`video/index.html`、`video/assets/director.js`、`out/`、`tools/`、`SPEC-v2.md`、`README.md` 等任何其它文件。

---

## 7. 附：当初找到但没能下载的实录音效候选（供后续替换）

以下页面在 Pixabay 音效库检索到，标题/时长来自页面列表；因下载按钮被 Cloudflare 人机验证拦截，**未取得文件**：

- `pixabay.com/sound-effects/film-special-effects-lego-piece-pressed-105360/`（Lego Piece Pressed，0:01）
- `pixabay.com/sound-effects/film-special-effects-plastic-ratchet-sound-32736/`
- `pixabay.com/sound-effects/film-special-effects-clicking-dial-on-toy-76265/`
- `pixabay.com/sound-effects/film-special-effects-surge-protector-switch-plastic-click-38167/`
- `pixabay.com/sound-effects/film-special-effects-clip-in-106657/`
- `pixabay.com/sound-effects/film-special-effects-slot-in-47863/`

若日后要换成实录素材，替换 `work/sfx/` 下的同名文件后重跑：

```
D:\Python\Python311\python.exe work\synth_foley.py work\sfx   # 仅当仍用合成音时才需要
D:\Python\Python311\python.exe work\build_mix.py              # -> work/mix_raw.wav
D:\Python\Python311\python.exe work\master.py work\mix_raw.wav mix.wav
D:\Python\Python311\python.exe work\verify_mix.py mix.wav work\build_report_v2.json
```

时间轴不用动（契约时间写在 `build_mix.py` 顶部的 `RELEASE_T` / `CLOSE_T` / `SEAT_T`）。
