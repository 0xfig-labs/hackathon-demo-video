# 黑客松正式提交结构（4–5 分钟）

评审通常不是只看炫技录屏，而是看"问题 → 产品 → 证据 → 未来"。推荐结构：

| 时间 | 模块 | 画面 | 旁白重点 |
|------|------|------|----------|
| 30–60s | Problem overview | 首页、问题场景、目标用户 | 谁有这个问题、现在怎么做、为什么痛 |
| ~3min | Product demo | 真实产品操作 | 核心流程、关键功能、输入输出、成功结果 |
| 20–40s | User testing / feedback | 反馈截图、改进前后、指标 | 你们验证过什么、根据反馈改了什么 |
| 30–60s | Conclusion + future vision | 总结页、路线图、GitHub | 当前价值、技术亮点、下一步 |

**提交前 checklist：**

- [ ] Demo video completed
- [ ] GitHub repo updated and public
- [ ] Clear presentation/demo flow
- [ ] All project details filled out

## 4–5 分钟旁白骨架

```text
[Problem overview]
We built <project> for <user>. Today, <user> struggles with <pain>.
Existing solutions fail because <reason>. Our goal is to make <outcome> possible.

[Product demo]
Now let me show the product. First, we <action>.
The system <does what>. Here is the key result: <result>.
Next, we <second flow>. This matters because <value>.
Behind the scenes, <technical proof / chain / AI / infra detail>.

[User testing / feedback]
During the hackathon, we tested this with <users/testers>.
The feedback was <feedback>. We improved <change> so the MVP now <better outcome>.

[Conclusion + future]
In summary, <project> helps <user> achieve <outcome>.
The repo is public, the demo is live, and the next step is <future vision>.
```

## 对应 steps 节奏

长视频不要靠一个长 wait 硬撑，应该让画面随旁白推进：

```json
[
  {"type":"wait", "selector":"0", "wait":30000},
  {"type":"click", "selector":"Start", "wait":5000},
  {"type":"wait_text", "selector":"Result", "wait":30000},
  {"type":"scroll", "selector":"600", "wait":20000},
  {"type":"scroll", "selector":"1200", "wait":20000},
  {"type":"scroll", "selector":"1800", "wait":20000},
  {"type":"wait", "selector":"0", "wait":30000}
]
```

`Problem overview` 和 `Conclusion` 可以录产品首页/总结页，不必切 PPT；如果有用户反馈或改进截图，放在产品页面里滚动展示即可。
