# 完整示例

## 70s TradeTrace 演示

```bash
uv run <skill_dir>/scripts/record-demo.py \
  "https://tradetrace.ygz0425.workers.dev/" \
  "欢迎使用 TradeTrace。今天我们来验证一笔 DeFi 预测交易。首先把交易编号粘贴到输入框。点击分析按钮，开始查询链上数据。几秒钟后分析结果就清晰呈现出来了。展示了头寸类型是二元期权，方向是看涨。往下滚动可以看到每一条分析结论，每条结论都映射到具体的链上证据。继续往下看，事件时间线记录了所有关键操作。再往下，证据的哈希值已经存储在 Walrus 网络上，任何人都可以独立验证。最后还提供了完整的 JSON 证据包，评审可以直接下载验证。TradeTrace 让 DeFi 预测市场的结果透明可信。基于 Sui 和 Walrus，完全开源项目。感谢观看。" \
  --rate "-5%" \
  --steps '[
    {"type": "click",    "selector": "Fill example transaction", "wait": 2000},
    {"type": "click",    "selector": "Explain outcome",         "wait": 500},
    {"type": "wait_text","selector": "OUTCOME EXPLANATION",     "wait": 50000},
    {"type": "wait",     "selector": "0",                       "wait": 15000},
    {"type": "scroll",   "selector": "400",                     "wait": 12000},
    {"type": "scroll",   "selector": "800",                     "wait": 12000},
    {"type": "scroll",   "selector": "1200",                    "wait": 12000},
    {"type": "scroll",   "selector": "1600",                    "wait": 12000},
    {"type": "wait",     "selector": "0",                       "wait": 8000}
  ]'
```

## 竖屏移动端演示

```bash
uv run <skill_dir>/scripts/record-demo.py \
  "https://your-mobile-app.workers.dev" \
  "This is the mobile demo. First we open the dashboard. Then we check today's analytics." \
  --format portrait \
  --capture mobile \
  --voice en-US-GuyNeural
```

## 桌面网页发短视频（竖屏画布居中留边）

```bash
uv run <skill_dir>/scripts/record-demo.py \
  "https://your-project.workers.dev" \
  "桌面录屏，竖屏输出，四周留黑边。适合发短视频平台。" \
  --capture desktop --format portrait --layout framed
```
