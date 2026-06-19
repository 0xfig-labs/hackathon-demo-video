# 常见问题

**Q: Playwright 报错找不到模块？**
A: 用 `uv run <skill_dir>/scripts/record-demo.py ...`。脚本内置 PEP 723 依赖声明，会自动缓存安装 Python Playwright。

**Q: 旁白比视频长？**
A: 优先在 `--steps` 里加 `{"type":"wait"}` 填充视频时长；赶时间再用 `--rate "+15%"` 加速旁白。

**Q: 视频比旁白长？**
A: `-shortest` 会自动截断，多余视频不保留。

**Q: 字幕没出现？**
A: 已兼容带序号和不带序号的 WebVTT。如果仍没字幕，先检查 `edge-tts` 是否生成了非空 `subtitles.vtt`。

**Q: 字幕重叠？**
A: 检查 VTT 时间轴——edge-tts 会自动处理。只有手动加 intro 字幕才会重叠，**不要手动加额外字幕**。

**Q: 字幕乱码/方框？**
A: 使用 `/System/Library/Fonts/STHeiti Medium.ttc`（macOS 自带）。无此字体则回退到 Helvetica。

**Q: 需要录制音频（麦克风/系统声）？**
A: Playwright headless 不支持录制系统音频。旁白由 edge-tts 生成。

**Q: 页面需要登录？**
A: 需要先在脚本中添加登录步骤（点击 Connect Wallet / 输入密码等）。

**Q: Playwright 自带 Chromium 没安装？**
A: 脚本会先尝试 Playwright Chromium，失败后 fallback 到系统 Chrome / Edge / Chromium。

**Q: 旁白比录屏长会被截断？**
A: 不会。合成时会自动克隆最后一帧补足到旁白时长。

**Q: 页面加载白屏？**
A: 脚本自动预热：先在无录制 context 中加载页面（缓存），再在录制 context 中重加载（瞬开）。

**Q: --rate=-5% 报错 "expected one argument"？**
A: 负值必须以等号语法传入：`--rate=-5%`。`--rate "+0%"` 正数可以用空格或等号。
