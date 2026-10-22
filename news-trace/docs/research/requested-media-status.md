# 用户清单媒体接入验收（2026-10-01，Asia/Shanghai）

依据 [扩充后的逐源探测报告](../../diagnostics/2026/10/01/probe-2026-10-01-expanded.json)：UTC 2026-10-01 03:35（北京时间 11:35）开始检查。表内 20 家均取得了近期标题、发布时间和指向原站的文章链接；“近期”按默认 72 小时判断，周刊/国际版按配置的 240 小时判断。这里只证明**新闻元数据可读取**，不代表正文可读取、内容可重用或定时任务已启动。时间均为 UTC，部分来源仅提供日期。

这是加入 BBC、新华社和中国新闻网之前的用户清单验收快照。新增 6 个入口后的全量状态见 [最终报告](../../diagnostics/2026/10/01/probe-2026-10-01-all.json)及[权威媒体专项状态](authoritative-source-status.md)。

| 类别 | 媒体 | 接入入口与方式 | 最近条目 | 验收与限制 |
| --- | --- | --- | --- | --- |
| 财经 | [Bloomberg](https://www.bloomberg.com/robots.txt) | 官方 news sitemap | 10-01 03:01 | 近期；标题/时间/原文链接 |
| 财经 | [WSJ](https://www.wsj.com/robots.txt) | 官方 news sitemap | 10-01 03:17 | 近期；不推定可读付费正文 |
| 财经 | [FT](https://www.ft.com/rss/home) | 原站 RSS | 09-30 21:32 | 近期 |
| 财经 | [The Economist](https://www.economist.com/the-world-this-week/rss.xml) | 原站周刊 RSS | 09-24 13:22 | 符合周刊更新周期；逐日简报需其他来源补充 |
| 财经 | [Harvard Business Review](https://hbr.org/the-latest) | 官方最新文章页的公开卡片 | 2026-09-30（日期） | 近期；时间精度只有日 |
| 综合 | [NYT](https://rss.nytimes.com/services/xml/rss/nyt/World.xml) | 原站 World RSS | 10-01 02:23 | 近期 |
| 综合 | [Washington Post](https://www.washingtonpost.com/information/2026/05/21/washington-post-rss-feeds/) | 官方 World RSS | 09-30 21:43 | 近期；按 [RSS 条款](https://www.washingtonpost.com/discussions/2021/01/01/rss-terms-service/)仅探测，不写入条目清单 |
| 综合 | [The Atlantic](https://www.theatlantic.com/feed/all/) | 原站 RSS | 09-30 22:04 | 近期 |
| 综合 | [The New Yorker](https://www.newyorker.com/about/feeds) | 官方 News RSS | 09-30 23:30 | 72 小时内有条目；非快讯节奏 |
| 科技 | [WIRED](https://www.wired.com/about/rss-feeds/) | 官方 AI 栏目 RSS | 09-30 20:30 | 近期；目前只覆盖 AI 栏目 |
| 科技 | [MIT Technology Review](https://www.technologyreview.com/feed/) | 原站 RSS | 09-30 12:10 | 近期 |
| 科技 | [New Scientist](https://www.newscientist.com/feed/home/) | 原站 RSS | 09-30 23:01 | 近期 |
| 学术 | [Nature](https://www.nature.com/nature.rss) | 原站 RDF/RSS | 2026-09-30（日期） | 近期；需区分论文、新闻与评论 |
| 学术 | [Scientific American](https://www.scientificamerican.com/robots.txt) | 官方文章 sitemap + 文章公开元数据 | 09-30 17:35 | 近期；仅取标题、时间和链接 |
| 中文 | [南方周末](https://www.infzm.com/) | 原站首页文章链接 + 文章公开元数据 | 10-01 03:00 | 近期；首页可能混有旧推荐，按实际发表时间排序 |
| 中文 | [天下杂志](https://www.cw.com.tw/today) | [Bing News RSS](https://www.bing.com/news/search?q=site%3Acw.com.tw%2Farticle%2F&format=RSS)发现，解析为 `cw.com.tw` 原文链接 | 09-30 04:23 | 近期，但依赖第三方索引；原站 [旧 RSS](https://www.cw.com.tw/RSS/cw_content.xml)停在 2021 年，另列为 `stale` |
| 中文 | [南华早报 SCMP](https://www.scmp.com/rss) | 官方 News RSS | 10-01 03:00 | 近期；该报是香港英文媒体 |
| 地区 | [Le Monde in English](https://www.lemonde.fr/en/about-us/article/2026/03/27/le-monde-rss-feeds_6751860_115.html) | 官方国际 RSS | 10-01 03:34 | 近期；官方限制严格个人、非专业、非集体使用，当前仅探测，不写入条目清单 |
| 地区 | [Der Spiegel International](https://www.spiegel.de/international/index.rss) | 原站国际版 RSS | 09-23 15:28 | 符合该栏目较慢的更新节奏；德国语主站可另行扩充 |
| 地区 | [La Repubblica](https://www.repubblica.it/static/servizi/rss/index.html) | 官方首页 RSS | 10-01 03:00 | 近期；意大利语 |

## 额外来源与质量门槛

除表内媒体，还有 PBS、Sky News、Euronews、Al Jazeera、ProPublica、NPR、ABC News、Africanews、CNA、The Guardian、France 24、DW、CBC、The Hindu、The Japan Times、POLITICO Europe 和《联合早报》返回近期元数据。3 个 VOA 地区 RSS 停在 2025 年 3 月，保留健康检查但不输出为最新新闻。订阅媒体的逐篇可读性及 Reuters、AP、BBC 的接入限制见 [paywall-access.md](paywall-access.md)。

本次共检查 **41 个入口**：**37 个近期、4 个停更**；近期入口中有 **2 个只做探测**，报告保留其状态，不保存其条目；报告存有 **167 条**近期条目，覆盖 **35 家保存了条目的媒体**。多个入口可属同一媒体，不能把入口数当作独立媒体数。《天下杂志》的第三方发现方式、标题截断和索引延迟都需要持续监测；《华盛顿邮报》和 Le Monde 的条款决定其当前仅能做有限探测。若这些条件变化，应更新配置与本表，再考虑自动运行。
