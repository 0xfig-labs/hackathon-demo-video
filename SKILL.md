---
name: hackathon-demo-video
description: >
  黑客松项目演示视频自动生成。录制浏览器操作 + AI 中文旁白 + 字幕烧录。一站式从项目 URL 产出横屏、竖屏或方形 MP4。当用户提到"录演示视频"、"制作 demo"、"生成黑客松视频"、"录制项目演示"、"录制浏览器操作"、"给项目做个视频"、"demo recording"、"hackathon video"、"录屏演示"、"录个视频"时，必须使用此 skill，即便只是随口一提也要触发。特别适用于 Sui Overflow、ETHGlobal 等黑客松场景。输入项目已部署 URL 和旁白脚本即可。
compatibility:
  - uv (推荐运行方式，读取脚本内 PEP 723 依赖)
  - playwright / edge-tts / Pillow (由 uv run 自动缓存安装)
  - ffmpeg (brew install ffmpeg)
---

# Hackathon Demo Video — 黑客松演示视频生成

## 录制前项目理解（必须）

不要拿到 URL 就盲目录制。每次使用本 skill，先完成轻量 discovery，再写出演示流程，最后才运行脚本。

### 1. 读取项目指令

在项目根目录内优先读取：

```text
AGENTS.md
README.md
doc/DEMO.md
doc/USAGE.md
doc/JUDGE_QA.md
doc/HACKATHON_README.md
package.json
```

如果用户指定了文档，以用户指定文档为准；如果存在项目局部 `AGENTS.md`，其规则覆盖全局规则。

### 2. 理解项目，不要脱离产品

至少确认这些信息：

- 项目一句话 pitch
- 目标用户和痛点
- 评委/用户推荐操作路径
- 是否已有部署 URL，优先用部署 URL，不要擅自跑本地服务
- demo 交易、账号、测试数据、示例输入
- 成功状态、失败状态、加载状态、已知限制
- GitHub / Walrus / chain explorer / API 等可验证证据

如果文档不够，再读最小相关代码：入口页面、demo 数据、i18n 文案、API route。不要全仓库乱翻。

### 3. 先创建演示流程

录制前先写出这个结构，并用它生成旁白和 steps：

```text
Demo Flow
1. Problem overview: <痛点和场景>
2. Product demo: <逐步操作路径>
3. Evidence / validation: <链上证据、Walrus、JSON、测试反馈>
4. Conclusion / future: <价值总结和下一步>

Recording Plan
- URL: <部署 URL 或用户指定 URL>
- Capture: <desktop/mobile/tablet>
- Output: <landscape/portrait/square>
- Steps: <click/fill/wait_text/scroll 列表>
- Expected visible result: <录制中必须出现的页面文本>
```

### 4. 先做轻量浏览器预检

正式录制前，用 Playwright 打开 URL，确认：

- 页面能访问
- 关键按钮/input 存在
- 示例输入能触发结果
- `wait_text` 文本真实会出现

预检失败时先修 steps 或换流程，不要直接录空视频。

### 5. 录制后质量检查

生成 MP4 后至少检查：

- ffprobe 能读出视频、音轨、时长
- 抽 1–2 帧确认不是黑屏/空页面
- 字幕没有超出画布
- 关键结果页确实出现在视频中
- 旁白没有被截断

如果发现画面错误，先修 flow/steps/字幕，再重新录制。

---

## 快速使用

```bash
cd <project-root>

uv run <skill_dir>/scripts/record-demo.py \
  "https://your-project.workers.dev" \
  "旁白文字。每条句子自动对应一段字幕。"
# 输出: ./demo/{project}-demo-subtitled.mp4
```

竖屏移动端网页：

```bash
uv run <skill_dir>/scripts/record-demo.py \
  "https://your-project.workers.dev" \
  "This is the mobile demo." \
  --format portrait \
  --capture mobile \
  --voice en-US-GuyNeural
```

首次使用需安装依赖（见后文 `前置安装`）。

---

## 通用画幅与视口

把三个概念分开，避免把"竖屏"误认为"桌面网页缩放"：

| 参数 | 作用 | 默认 |
|------|------|------|
| `--capture desktop|mobile|tablet` | 浏览器录制视口 | 横屏默认 desktop，竖屏默认 mobile |
| `--format landscape|portrait|square` | 最终视频画布 | landscape |
| `--layout native|fit|crop|framed` | 录屏如何放进画布 | native |
| `--viewport WIDTHxHEIGHT` | 自定义录制视口 | 无 |
| `--output-size WIDTHxHEIGHT` | 自定义输出尺寸 | 无 |

常用组合：

```bash
# 黑客松评审：桌面横屏
--capture desktop --format landscape --layout native

# 移动端网页：原生竖屏，不缩放桌面版
--capture mobile --format portrait --layout native

# 桌面网页发短视频：桌面录制，竖屏画布居中留边
--capture desktop --format portrait --layout framed

# 社媒方图
--capture desktop --format square --layout fit
```

`portrait` 默认使用移动端录制。如果网页移动端体验不好，显式改成：

```bash
--capture desktop --format portrait --layout framed
```

---

## 稳定性开关

有些网页长期轮询或开 WebSocket，`networkidle` 会慢甚至卡。默认使用更稳的：

```bash
--wait-until domcontentloaded
```

如果页面确实要等完整资源：

```bash
--wait-until load
--wait-until networkidle
```

操作步骤默认严格执行，找不到按钮就失败，避免生成错误演示。探索阶段可放宽：

```bash
--no-strict-steps
```

放宽后失败的步骤会打印 `SKIP_STEP:...` 并继续录制。

---

## 性能与并行运行

每次运行都会写入独立的 `.work-<pid>-<id>/` 临时目录，录屏、音频、字幕和合成临时文件互不影响。最终 MP4 先在临时目录生成，成功后再移动到输出路径。

并行跑同一个项目时，给每个任务指定不同 `--output`，避免最后一个覆盖前一个：

```bash
--output demo/project-landscape-zh.mp4
--output demo/project-portrait-en.mp4
```

编码速度可调：

```bash
--preset veryfast --crf 23   # 快速预览
--preset medium --crf 20     # 默认，速度和质量平衡
--preset slow --crf 18       # 更高质量，更慢
```

---

## 中英文配音与字幕

脚本不猜语言，旁白是什么语言，`edge-tts` 就生成对应音频和字幕。

```bash
# 中文男声
--voice zh-CN-YunyangNeural --rate=+0%

# 英文男声
--voice en-US-GuyNeural --rate=+0%

# 英文女声
--voice en-US-JennyNeural --rate=+0%

# 负值语速用等号语法
--voice zh-CN-YunyangNeural --rate=-5%
```

> **注意**：`--rate` 值为负数时（如 `-5%`），必须用 `=` 等号语法 (`--rate=-5%`)，否则 argparse 会将其误判为命令行选项。

更多语音和语速参考 → `references/narration-guide.md`

双语字幕暂时用最稳的方式：用户提供已经排好的双语旁白文本。自动翻译、双音轨、多版本批量导出先不塞进录制脚本，避免不稳定。

---

## 完整工作流

```
预热（无录制） → 加载页面 → 关闭
         ↓
录制 context → 导航（已缓存，无白屏）
         ↓    → 操作步骤（点击/等待/滚动）
         ↓    → context.close() → WebM
         ↓
edge-tts → narration.mp3 + subtitles.vtt
         ↓
Pillow → 字幕 PNG 烧录帧（STHeiti 中文字体）
         ↓
ffmpeg → 深色开场 + 录像 + 旁白 + 字幕 → MP4
```

---

## 自定义操作步骤（`--steps`）

默认步骤是"点击 Fill example → Explain outcome → 滚动页面"。对于不同项目需要用 `--steps` 自定义。

### 支持的操作类型

| type | selector 含义 | 说明 |
|------|--------------|------|
| `click` | button/link 文本 | 点击按钮，`wait` 为点击后等待毫秒 |
| `fill` | CSS selector | 填写输入框，额外字段 `value` 是要填入的文本 |
| `link` | 链接文本 | 点击 `<a>` 元素 |
| `wait_text` | 等待页面出现此文本 | 最长等 `max(wait, 10000)`ms，出现后再等 2s |
| `scroll` | Y 坐标 | 滚动到该位置，`wait` 为滚动后停留毫秒 |
| `wait` | 无用 | 纯粹等待 `wait` 毫秒，用于填充时长 |

### 示例：60s 视频

```bash
--steps '[
  {"type": "fill",     "selector": "input[placeholder=\"Paste digest\"]", "value": "DpM...", "wait": 1000},
  {"type": "click",    "selector": "Connect Wallet",  "wait": 3000},
  {"type": "click",    "selector": "Create Position", "wait": 2000},
  {"type": "wait_text","selector": "Position Created","wait": 30000},
  {"type": "wait",     "selector": "0",              "wait": 10000},
  {"type": "scroll",   "selector": "400",            "wait": 8000},
  {"type": "scroll",   "selector": "800",            "wait": 8000}
]'
```

**关键经验**：视频必须比旁白长，不够用 `"wait"` 步骤填充。旁白 70s → 视频至少 75s。

---

## 输出

```
{project}/demo/
└── {project}-demo-subtitled.mp4    # H.264, AAC 旁白, 字幕烧录；尺寸由 --format/--output-size 决定
```

---

## 前置安装（一次性）

推荐用 `uv run`，脚本内置 PEP 723 依赖声明：`playwright`、`Pillow`、`edge-tts` 会进入 uv 缓存，不需要每个项目重复安装，也不污染系统 Python。

```bash
# 只需要系统工具
brew install uv ffmpeg

# 可选：安装 Playwright 自带 Chromium。未安装时脚本会 fallback 到系统 Chrome / Edge / Chromium。
uv run --with playwright python -m playwright install chromium
```

验证：

```bash
uv run <skill_dir>/scripts/record-demo.py --help
ffmpeg -version | head -1
```

---

## 参考文档

以下参考文档在需要时阅读：

- `references/narration-guide.md` — 旁白写作指南、节奏模板、语音列表
- `references/hackathon-flow.md` — 黑客松 4–5 分钟提交结构、旁白骨架
- `references/examples.md` — 完整命令行示例（TradeTrace、竖屏、短视频）
- `references/troubleshooting.md` — 常见问题（字幕、安装、白屏等）
