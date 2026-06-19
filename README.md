# hackathon-demo-video

[![skills.sh](https://skills.sh/b/0xfig-labs/hackathon-demo-video)](https://skills.sh/0xfig-labs/hackathon-demo-video)

黑客松项目演示视频自动生成。录制浏览器操作 + AI 旁白 + 字幕烧录，一站式从项目 URL 产出 MP4。

## 安装

```bash
npx skills add 0xfig-labs/hackathon-demo-video
```

## 快速使用

```bash
# 系统依赖
brew install uv ffmpeg

# 录制演示视频
uv run <skill_dir>/scripts/record-demo.py \
  "https://your-project.workers.dev" \
  "你的旁白文字。每条句子自动对应一段字幕。"
```

更多用法见 [SKILL.md](SKILL.md)。

## 工作流

```
预热缓存 → 浏览器录制操作步骤 → edge-tts 旁白+字幕
→ Pillow 字幕渲染 → ffmpeg 合成 → MP4
```

## 功能

- 支持 landscape / portrait / square 三种画幅
- 支持 desktop / mobile / tablet 录制视口
- 自定义操作步骤：click、fill、link、wait_text、scroll
- 中文/英文 TTS 旁白，可调速
- 多 layout 模式：native / fit / crop / framed
- 并行运行，互不干扰
- 非严格模式用于探索阶段

## License

MIT
