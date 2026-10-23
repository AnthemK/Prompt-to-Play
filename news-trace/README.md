# 溯闻 · NewsTrace

从多家媒体发现新闻，按事件核验、比较并生成可追溯简报。当前为手动运行：约 10 个独立事件，每源采集上限 15 条；已配置 47 个入口，尚未启用定时任务。历史接入成功不代表今日仍可用。

**上传交接：** [上传范围与检查](docs/maintenance/upload-handoff.md) · [当前工作状态](memory/working-state.md)

**先选产品：** [每日简报流程](docs/workflows/edition-pipeline.md) · [专题追踪流程](docs/workflows/topic-tracking.md) · [编辑纲领](docs/standards/editorial-charter.md)

**专题阅读：** [专题目录](topics/README.md) · [法国学校抗议研究首页](topics/france-school-protests/README.md)。专题按研究问题展开，不使用每日简报的条数和标题。

**阅读入口：** [简报目录](editions/README.md) · [最近保存的一期：2026-10-03](editions/2026/10/03/brief.md) · [执行流程](docs/workflows/daily-brief.md) · [待办](memory/TODO.md)

| 目录 | 放什么 | 何时打开 |
| --- | --- | --- |
| [docs/](docs/README.md) | 原始标准、流程、研究与设计 | 了解规则或扩展项目 |
| [skills/news-briefing/](skills/news-briefing/SKILL.md) | agent 的简报执行 skill | 开始编写或修订简报 |
| [config/](config/README.md) | 生效信源与待核查入口 | 增加或调整媒体 |
| [scripts/](scripts/README.md) · [tests/](tests/) | 采集、访问检查、校验及测试 | 运行与维护程序 |
| [memory/](memory/README.md) | 跨期故事、事件历史、偏好与待办 | 接续上一次工作 |
| [editions/](editions/README.md) | 按日期集中保存的简报、证据和交付文件 | 阅读、复核或重发一期 |
| [topics/](topics/README.md) | 专题任务、版本索引、报告与开放问题 | 持续追踪复杂议题 |
| [diagnostics/](diagnostics/README.md) | 不依附某一期的信源专项检查 | 排查接入问题 |
| `tmp/` | 可删除的试跑输出和缓存 | 执行结束后清理 |

从本目录执行离线检查：

```sh
python3 -B -m unittest discover -s tests -q
python3 -B scripts/validate_state.py
python3 -B scripts/check_layout.py
```

完整采集命令见[运行手册](scripts/README.md)。新 agent 先读 [AGENTS.md](AGENTS.md)；新文件按[生命周期规则](docs/maintenance/file-lifecycle.md)归类。2026-10-22 的旧路径可通过[迁移索引](docs/maintenance/migrations/2026-10-22-layout.json)查找。
