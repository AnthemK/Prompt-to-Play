# BBC、新华社等权威媒体接入状态

本页基于 [2026-10-01 专项实测报告](../../diagnostics/2026/10/01/authoritative-live-2026-10-01.json)。`ok` 表示本轮在原站取得 72 小时内的报道；BBC 和新华社还核对了标题、页面发布时间与可提取正文。时间均为 UTC，后续运行可能产生新标题和时间。

| 媒体入口 | 发现方式 | 技术验收 | 时间解释 |
| --- | --- | --- | --- |
| [BBC World RSS](https://feeds.bbci.co.uk/news/world/rss.xml) | BBC 官方 RSS | `ok`；抽取 3 篇原文，标题一致，正文 5,427–6,608 字符 | 分别保存首发、文章修改、RSS 条目时间 |
| [BBC Headlines RSS](https://feeds.bbci.co.uk/news/rss.xml) | BBC 官方 RSS | `ok`；抽取 3 篇原文，标题一致，正文 3,950–7,273 字符 | 同上；栏目之间可能出现同一篇文章 |
| [新华社英文 Latest news](https://english.news.cn/list/latestnews.htm) | 原站最新列表 | `ok`；抽取 3 篇 `Source: Xinhua` 文章，标题一致，正文 198–1,544 字符 | 页面时间按 UTC+08:00 转为 UTC |
| [新华网中文“最新播报”](https://www.news.cn/) | 原站首页 | `ok`；抽取 3 篇正文前段有“新华社”署名的文章，标题一致，正文 281–436 字符 | 文章页时间按 UTC+08:00 转为 UTC |
| [中国新闻网即时 RSS](https://www.chinanews.com.cn/rss/scroll-news.xml) | [官方 RSS 目录](https://www.chinanews.com.cn/rss/) | `ok`；取得 3 条近期元数据 | RSS 已含 `+0800` 时区 |
| [中国新闻网国际 RSS](https://www.chinanews.com.cn/rss/world.xml) | 官方 RSS | `ok`；取得 3 条近期元数据，报告中与即时栏目重复稿去重 | 同上 |

BBC/新华社样本正文从原站 HTML 提取，报告只存字符数、段落数和正文 SHA-256；“取得正文”不自动等于全文完整性已被独立证明。中国新闻网此轮只做 feed 层验收。运行者可按 [复现手册](../workflows/source-verification.md)重新采集并执行检查；每一步的发现、淘汰与更正见 [执行记录](../../diagnostics/2026/10/01/execution-log.md)。

## 尚未记为实时接入的权威来源

| 来源 | 当前技术结论 |
| --- | --- |
| [Reuters](https://reutersagency.com/content-delivery-platforms/reuters-connect/) | 正式实时内容通过 Reuters Connect/API；无可用于本轮验证的公开直连 feed。 |
| [AP](https://api.ap.org/media/v/swagger/) | AP Media API 列出 feed/RSS，但返回内容与账号可用套餐相关；本轮无授权接口可测。 |
| [AFP](https://www.afp.com/en/our-offer/afp-api) | 官方 AFP API 支持实时文档及 ATOM/RSS feed，需注册获取接入。 |
| 人民网、中国日报的旧 RSS | 被测入口分别停更或 404，详见[候选审计报告](../../diagnostics/2026/10/01/candidate-audit-2026-10-01.json)。 |
