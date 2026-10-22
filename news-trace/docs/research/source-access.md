# 首轮信源接入清单（2026-09-30）

这里记录第一轮英文媒体调研。用户指定的 20 家媒体与最新逐源验收已移至 [requested-media-status.md](requested-media-status.md)；完整配置由 `sources.json` 和 `sources/` 共同组成。这里的“可读取”表示手动探测取得了近期标题、时间和原文链接，**不等于已启动定时任务或取得内容再利用许可**。

| 媒体 | 地区/类型 | 找到的入口 | 当前判断 |
| --- | --- | --- | --- |
| [PBS News](https://www.pbs.org/newshour/about/pbs-news-rss-feeds) | 美国公共媒体 | 官方 Headlines、World、Politics RSS | Headlines 可读取近期条目；仍需核对使用条款 |
| [Sky News](https://news.sky.com/info/rss) | 英国商业广播 | 官方 World 等 RSS | World 可读取近期条目 |
| [Euronews](https://www.euronews.com/widgets) | 欧洲跨国媒体 | 官方 World News MRSS | 可读取近期条目；页面明确要求遵守使用条款 |
| [VOA](https://www.voanews.com/rssfeeds) | 美国国际广播 | 官方区域 RSS（非洲、中东、欧洲等） | 三个区域 feed 可解析但最新条目停在 2025-03；采集器标为 `stale` 并排除 |
| [Al Jazeera](https://www.aljazeera.com/xml/rss/all.xml) | 卡塔尔国际媒体 | 媒体域名下的 RSS | 可读取近期条目；需核对具体条款 |
| [ProPublica](https://www.propublica.org/feeds/propublica/main) | 美国非营利调查媒体 | 媒体域名下的 XML feed | 可读取近期条目；更新频率不同于快讯媒体 |
| [The Guardian](https://open-platform.theguardian.com/documentation/) | 英国报纸 | 官方 Content API | 需申请 key，并按[访问级别和限额](https://open-platform.theguardian.com/access/)使用 |
| [NPR](https://feeds.npr.org/1004/rss.xml) | 美国公共广播 | 媒体域名下的 World RSS | 可读取近期条目；需补充官方目录/条款依据 |
| [ABC News（美国）](https://abcnews.go.com/Site/page?id=3520115) | 美国商业广播 | 官方 International Headlines RSS | 可读取近期条目；与澳大利亚 ABC 是不同机构 |
| [Africanews](https://www.africanews.com/page/widgets/) | 非洲跨国媒体 | 官方英文 RSS | 可读取近期条目 |
| [CNA（新加坡）](https://www.channelnewsasia.com/rss) | 新加坡英文亚洲媒体 | 官方 Asia RSS | 可读取近期条目；页面明确限个人非商业用途 |
| [The Guardian](https://www.theguardian.com/help/feeds) | 英国报纸 | 官方 World RSS | 可读取近期条目；官方说明限个人非商业使用，其他用途需另查条款/API |
| [BBC News](https://support.bbc.co.uk/platform/feeds/NewsFeeds.htm) | 英国公共广播 | 官方 World 与 Headlines RSS | 已完成近期条目和样本文章页核对；首发、修改、RSS 时间分别保存。访问条件见 [BBC 条款](https://downloads.bbc.co.uk/usingthebbc/bbc_terms_of_use_31March2022english.pdf)，此轮为手动技术测试 |
| [The New York Times](https://rss.nytimes.com/services/xml/rss/nyt/World.xml) | 美国报纸 | World RSS 已实测；Times Newswire API 是另一条需 key 的路径 | World RSS 有近期条目；正文权限另计 |
| [AP](https://developer.ap.org/ap-media-api/) | 国际通讯社 | 官方 Media API，含 feed/search | 仅对[已授权内容](https://api.ap.org/media/v/docs/Getting_Started_API.htm)开放，需订阅/合同 |
| [Reuters](https://www.thomsonreuters.com/en/products-services/news-media) | 国际通讯社 | Reuters Connect / API & Feeds | 需商用接入或授权；BPC 站点清单不能代替此接口 |
| [DW](https://rss.dw.com/rdf/rss-en-all) | 德国国际广播 | 公开英文 RDF/RSS 已实测；另有合作伙伴定制 RSS | 近期标题、时间和原文链接可读；定制内容仍需向 DW 咨询授权 |
| [ABC News Australia](https://help.abc.net.au/hc/en-us/articles/6147104938383-Why-are-RSS-feeds-no-longer-being-updated) | 澳大利亚公共广播 | 旧公共 RSS | 官方说明已停止更新；[新闻分发](https://www.abc.net.au/newssyndication)走合作渠道，暂不自动接入 |
| [SCMP](https://www.scmp.com/rss) | 香港英文媒体 | 官方 News RSS 已实测 | 有近期条目；详见[逐源验收](requested-media-status.md) |
| [Le Monde in English](https://www.lemonde.fr/en/about-us/article/2026/03/27/le-monde-rss-feeds_6751860_115.html) | 法国媒体英文版 | 官方国际 RSS 已实测 | 有近期条目；官方限制严格个人、非专业和非集体使用，当前仅探测而不保存条目 |

第二轮扩充还实测了 [France 24 English](https://www.france24.com/en/rss)、[CBC News World](https://www.cbc.ca/cmlink/rss-world)、[The Hindu International](https://www.thehindu.com/news/international/feeder/default.rss)、[The Japan Times](https://www.japantimes.co.jp/feed/) 和 [POLITICO Europe](https://www.politico.eu/feed/) 的公开 feed，已加入 `sources/english-additions.json`。南非 Daily Maverick 的常见 `/feed/` 地址返回 403，尚未计入接入；NHK World 的候选地址返回 404。Reuters、AP、BBC 的当前访问条件与订阅媒体逐篇诊断见 [paywall-access.md](paywall-access.md)。

第三轮新增 [新华社英文 Latest news](https://english.news.cn/list/latestnews.htm)、[新华网中文首页](https://www.news.cn/)中的新华社署名稿，以及[中国新闻网官方 RSS](https://www.chinanews.com.cn/rss/)。新华社官网列出的旧 RSS 停更，不能代替现行页面；逐项证据和重跑步骤见[权威信源状态](authoritative-source-status.md)与[复现手册](../workflows/source-verification.md)。

## 覆盖规则

- 媒体数量按**独立新闻机构和所有权集团**分别计，不按 feed 数计；同一通讯社转载稿也不增加独立证据数。Euronews 将 Africanews 列为姊妹频道，横向比较必须显示这层关系。
- 先广泛发现标题和原文链接，再按可用权限决定是否读取正文。摘要只陈述已取得证据支持的事实，无法确认的细节保持未确认。
- GDELT 可作为[跨语言新闻发现索引](https://gdeltproject.org/data.html)，但简报的最终证据应回到原始媒体或一手文件；不能把索引结果算作另一家媒体的报道。
- 每个接入项记录：媒体、地区、语言、来源类型、入口、条款链接、可用字段、抓取频率、最后成功时间与失败原因。

## 首次实测

2026-09-30 首次手动运行 `collect.py --limit 2`：11 个 feed 地址中，8 个取到 72 小时内的条目，覆盖 8 家媒体；VOA 的 3 个区域 feed 为停更状态。原型仅采集 feed 元数据，并按时间窗口排除旧闻。实测成功不表示可以抓取文章全文或对外再发布摘要。

随后增加 CNA Asia 与 Guardian World 并用 `--limit 1` 重测：13 个 feed 中 10 个取到近期条目，对应 10 个媒体品牌；VOA 3 个仍为 `stale`。这是首轮历史记录；最新 41 个入口的结果见[逐源验收](requested-media-status.md)。Euronews 与 Africanews 同属一个集团，不能宣称已取得 10 个互相独立的所有权视角。媒体背景、视角检查与横向比较格式见 [media-perspectives.md](media-perspectives.md)。
