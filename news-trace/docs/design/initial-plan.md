> 历史规划存档：这是整理前的项目首页，内含当时状态与旧命令。当前入口见[首页](../../README.md)，执行方式见[运行手册](../../scripts/README.md)。

# 溯闻（NewsTrace）

文件用途与清理约定见 [FILE_LIFECYCLE.md](../maintenance/file-lifecycle.md)：临时输出放 `tmp/`，跨期记忆放 `state/`，规则集中在标准、skill 和流程文件中；已交付简报及可追溯证据单独保留。

面向全球新闻的定时简报项目：定期收集主流媒体与可信网站的公开报道，把同一事件的报道归在一起，生成可快速浏览、逐层展开、逐条追溯来源的双语简报。英文媒体用英文，中文媒体用中文。

> 当前阶段：已固定首选六家信源，并按新标准生成[10 个不同事件的 2026-10-02 手动简报](../../editions/2026/10/02/brief.md)。全部候选共配置 47 个入口；历史最终复测为 43 个健康入口、4 个过旧入口。新版报告分别记录入口健康、是否实际贡献候选稿，以及是否触及每源 15 条采集上限。BBC/新华社四入口已通过专项核验。尚未启动定时任务。

现成技能与 BPC 的完整审读见 [research/skills-and-bpc.md](../research/skills-and-bpc.md)；用户清单中的 20 家媒体及逐家验收见 [research/requested-media-status.md](../research/requested-media-status.md)；[首选六家媒体及依据](../research/core-six-selection.md)；BBC、新华社等权威媒体的[复现手册](../workflows/source-verification.md)；订阅媒体的实测见 [research/paywall-access.md](../research/paywall-access.md)。入口按类别保存在 [sources/](../../config/sources) 和 [sources.json](../../config/sources.json)。`collect.py` 分别报告入口健康和候选贡献；`inspect_access.py` 依固定版本的 BPC 衍生规则输出访问等级；`validate_snapshot.py` 用 P0/P1/P2 检查快照。运行示例：`python3 collect.py --limit 15 --max-age-hours 36 --output /tmp/news-trace-probe.json`。

每日简报以用户提供的[原始标准](../standards/NEWS_BRIEFING_STANDARD.md)为编辑依据，项目内的 [news-briefing skill](../../skills/news-briefing/SKILL.md)将其整理为可执行流程；[写作流程](../workflows/daily-brief.md)、输入快照及逐事件复核记录可用于复现。原始标准未作修改。持久状态包括[事件历史](../../memory/event_history.jsonl)、[故事状态](../../memory/story_state.json)、[明确偏好](../../memory/preferences.json)和[反馈原文及解释](../../memory/feedback_log.jsonl)，可用 `python3 validate_state.py` 检查。新 agent 的入口说明见 [AGENTS.md](../../AGENTS.md)。

## 目标

- **快速浏览**：先看到当天值得关注的事件、更新时间和一句话摘要。
- **逐层展开**：每个事件可以展开背景、时间线、不同媒体的报道重点及尚待确认的问题。
- **逐条追溯**：每个关键事实都指向原始报道，保留媒体、标题、原文链接、发布时间、抓取时间和引用位置。
- **持续更新**：新报道进入既有事件；更正、撤稿和事实变化以版本记录呈现，不静默覆盖旧结论。

## 初版流程

1. **维护信源清单**：按地区、语言、所有权与编辑使命选择媒体；逐个记录官方 RSS/API/网站入口、使用条款、更新频率及可获取字段。优先使用官方 RSS 或 API。按 BPC 衍生 skill 的识别方法检查付费墙与正文完整性，但只在有适用访问依据的范围内读取内容。没有适合自动获取的入口时，保留候选卡与原文链接。
2. **定时采集**：按固定间隔拉取标题、摘要、链接、发布时间和来源标识。记录每次运行时间、成功/失败及增量游标；重试与限速按各信源规则设置。
3. **标准化与去重**：统一时间为 UTC 存储、界面按用户时区显示；规范链接，按原始 ID/URL 去重，并把讨论同一事件的不同报道聚合。
4. **提取与核对**：从可合法访问的内容中提取候选事实；区分“媒体报道”“当事方说法”和“已核实事实”。重要或有争议的断言尽量寻找独立来源；无法交叉核对时标明“单一来源”。
5. **横向比较并生成简报**：先选出重要事件，再比较共同事实、报道用词、受访者选择、不同地区的影响及尚有争议的断言；写短摘要和可展开的背景、时间线、来源差异、未解问题。每个事实点绑定证据；生成前检查链接可访问性、时间范围与重复内容。
6. **保存与展示**：保存结构化事件/证据/版本记录，同时输出便于阅读的简报。第一版先用静态页面或 Markdown 验证信息结构，再决定是否开发交互界面。
7. **复核与反馈**：对首批简报人工抽查；记录漏报、误归类、无来源断言和过期链接，修订信源与摘要规则。

建议先手动跑通一次完整流程，再启用定时运行。初版可考虑每 6 小时采集一次、每天 09:00（Asia/Shanghai）生成一次简报；这是待确认的默认方案，不是已经启用的计划。

## 简报的展开层级

| 层级 | 展示内容 |
| --- | --- |
| 总览 | 日期、覆盖范围、重点事件、一句话摘要 |
| 事件 | 发生了什么、为什么重要、最新进展、时间线 |
| 证据 | 每条关键事实对应的报道、发布时间、引用位置、原文链接 |
| 追踪 | 更正/撤稿、相互矛盾的说法、历史版本与未解问题 |

最小数据关系：`简报 → 事件 → 断言 → 证据（原始报道）`。摘要和背景属于生成内容，必须能回溯到证据；观点与推断要明确标注。

## Skill 与工具选择

- 已有项目专用的 [news-briefing skill](../../skills/news-briefing/SKILL.md)，负责事件聚类、核验、排序、成稿与复核；实时新闻仍来自源站。
- 已有的 **OpenAI Docs** skill 可用于核对 Codex 定时任务、技能和相关配置的当前用法。
- 使用 **skill-creator** 将用户提供的完整标准整理为项目内 skill，后续流程调整先更新 skill 和另存的新标准版本，不直接修改原始标准。
- 定时执行可选 Codex Scheduled tasks 或仓库级调度。前者可结合 skill、在本地项目中运行，但需要运行任务的电脑和桌面应用保持开启；如需不依赖本机在线，再比较云端调度方案。

参考：[OpenAI Skills 说明](https://developers.openai.com/plugins/concepts/skills)、[Scheduled tasks 说明](https://learn.chatgpt.com/docs/automations?surface=app)、[GitHub Actions 定时工作流](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onschedule)。

## 信源接入原则

首批已找到多个英文媒体的官方或媒体域名下的 RSS 入口，另有 [The Guardian Open Platform](https://open-platform.theguardian.com/documentation/) 可在申请 key 后评估。具体状态见接入清单；不得把一个通讯社稿件被多家转载误算成多个独立来源。

项目默认保存元数据、短摘录、证据定位与原文链接；是否保存全文或对外展示媒体内容，须按具体来源的授权条件决定。

## 下一阶段的实施顺序与验收

1. **接入卡**：为首批媒体补官方入口、条款、所有权/资金背景、可用字段与更新状态；同一集团与通讯社转载关系能识别。截至 2026-10-01 的[最新全量手动探测](../../diagnostics/2026/10/01/probe-2026-10-01-final.json)：47 个入口中 43 个返回近期条目，4 个停更。用户清单的 20 家媒体均能取得近期元数据，但《天下杂志》使用第三方索引；《华盛顿邮报》和 Le Monde 当前只做有限探测，具体见[验收表](../research/requested-media-status.md)。
2. **事件与证据模型**：建立 `报道 → 事件 → 断言 → 证据/版本` 的结构化记录。验收时每条简报事实都能打开原文，缺证据或仅有单一来源的地方有明确标记。
3. **真实样例**：已完成一个 24 小时窗口的[双语简报样稿](../../editions/2026/10/01/brief.md)与同一事件的多媒体比较；下一步是人工检查共同事实、差异、转载谱系、付费墙导致的证据空缺和更正。
4. **定时化与展示**：样例通过后再固定生成频率和输出位置，制作溯闻专用 skill、自动运行及可展开的阅读界面；监测 feed 停更、链接失效和源站条款变化。
