# 长期记忆

类型：**长期记忆**。[首页](../README.md)

| 文件 | 保存什么 |
| --- | --- |
| [preferences.json](preferences.json) | 用户明确偏好、核心媒体和排除来源 |
| [event_history.jsonl](event_history.jsonl) | 已报道事件，供下一期判断信息增量 |
| [story_state.json](story_state.json) | 持续故事的状态、关注程度和待核实问题 |
| [feedback_log.jsonl](feedback_log.jsonl) | 用户反馈原文及解释 |
| [decisions.md](decisions.md) | 跨期工作约定及其来源 |
| [TODO.md](TODO.md) | 按 P0/P1/P2 分级的未完成工作 |

每次制作简报前读取，完成后只更新有依据的状态。历史事实和上次修改时间分别记录。不要把运行输出、缓存或全文抓取放在这里。
