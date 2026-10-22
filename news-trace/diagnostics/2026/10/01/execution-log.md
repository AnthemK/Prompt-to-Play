> 历史执行记录：保留当时命令与结果，旧路径可查[迁移索引](../../../../docs/maintenance/migrations/2026-10-22-layout.json)。当前命令见[运行手册](../../../../scripts/README.md)。

# 权威媒体接入执行记录（2026-10-01）

本记录对应用户提出的 BBC、新华社等权威媒体技术测试。执行机器为 macOS，`python3 --version` 返回 **Python 3.9.6**；代码仅使用标准库。所有报告时间为 UTC，页面中的新华社时间按 UTC+08:00 解析。完整重跑命令和验收规则见 [复现手册](../../../../docs/workflows/source-verification.md)。

## 1. 起点和技能核对

开始时 `news-trace` 已配置 41 个入口，但 BBC 与新华社均未列入实时源。检查了 [BPC 衍生 skill 固定提交](https://github.com/Lunatic16/paywall-bypass-skill/commit/77a32379b39ddfb56cd646d5563755bc768287fc)及其正文抽取和付费墙诊断规则。本轮借用其“先查官方入口、再看文章 HTML/JSON-LD/正文容器、最后验证正文完整性信号”的步骤；没有把 skill 的站点清单当作接口有效性证明。

## 2. 发现、淘汰、替换入口

| 步骤 | 官方入口或候选 | 实测结果与决定 |
| --- | --- | --- |
| BBC | [BBC 官方 feed 目录](https://support.bbc.co.uk/platform/feeds/NewsFeeds.htm) → `feeds.bbci.co.uk/news/world/rss.xml` 与 `feeds.bbci.co.uk/news/rss.xml` | 两个 XML 均返回当天条目，进入实测配置。 |
| 新华社英文旧 RSS | [英文站 RSS 目录](https://english.news.cn/rss/) → `xinhuanet.com/english/rss/worldrss.xml`、`chinarss.xml` | HTTP 200 但最新分别为 **2018-01-24、2017-05-07**；弃作实时源。 |
| 新华网中文旧 RSS | [官方 RSS 列表](https://www.news.cn/linktous.htm) → `world/news_world.xml`、`politics/news_politics.xml` | HTTP 200 但最新均为 **2022-12-14**；弃作实时源。 |
| 新华社英文现行列表 | [Latest news](https://english.news.cn/list/latestnews.htm) | 页面含标题、文章链接、秒级时间；文章页另有 `Source: Xinhua`、发布时间和正文，加入配置。 |
| 新华社中文现行列表 | [新华网首页](https://www.news.cn/)“最新播报” | 首页含当日文章链接；只收正文前段标有“新华社”的稿件，加入配置。 |
| 中国新闻网 | [官方 RSS 目录](https://www.chinanews.com.cn/rss/)的即时、国际 feed | 两个 feed 均返回当天条目，加入配置；本轮只验收 RSS 元数据。 |
| 其他候选 | 人民网旧 RSS、中国日报旧 RSS | 人民网最新 **2025-06-05**；中国日报两个旧地址均 **404**，暂不接入。 |

上述旧入口的每个 URL、HTTP 状态、条目数、最大日期及检查时间均保存于 [candidate-audit-2026-10-01.json](candidate-audit-2026-10-01.json)。该审计于 UTC **04:08:58–04:09:00** 执行；重跑命令为 `python3 audit_candidates.py --output reports/candidate-audit.json`。404 和停更源均未加入实时配置。

## 3. 文章级技术核对

对 BBC RSS 和新华社现行列表分别选择最新 3 条，普通 `NewsTrace/0.2` User-Agent 打开原站页面。对照列表/Feed 标题与文章 `h1`，解析首发和更新时间，抽取公开正文容器中的段落，在报告中只保存段落数、字符数及 SHA-256。

- BBC 文章 HTML 中使用 `datePublished`、`dateModified` 和 `<article>`。RSS `pubDate` 单独保存为 `feed_timestamp_at`。一次样本中 RSS 时间为 **2026-10-01 04:01:32 UTC**，文章 `dateModified` 为 **03:46:55.318 UTC**，因此 RSS 时间不能一概当作文章修改时间。
- 新华社英文文章页使用 `p.time`、`p.source` 和 `#detail`；列表与文章时间一致，`2026-10-01 11:32:45` 被明确转为 `03:32:45 UTC`。
- 新华网中文文章页使用标题、`div.info` 时间和 `#detailContent`；即使页面 `source` 元标签写“新华网”，只有正文前段出现“新华社”署名的稿件才被归入“新华社”入口。
- `article_body_sha256` 用于复验同一版本的提取结果，不保存或声称发布了文章全文。字符数只证明提取到可观测文本；后续若要证明全文完整，需和文章页显示的全部段落逐篇人工或授权接口比对。

首次文章级实测于 UTC **04:00:00** 开始；随后加入中国新闻网及运行元数据，六个入口在 UTC **04:04:18–04:04:30** 复测。最终代码下再次运行 `python3 collect.py --source-id bbc-world --source-id bbc-headlines --source-id xinhua-en-latest --source-id xinhua-zh-latest --source-id chinanews-latest --source-id chinanews-world --limit 3 --output reports/authoritative-live-2026-10-01.json`，报告时间为 UTC **04:15:29–04:15:53**。接着执行 `python3 verify_authoritative.py reports/authoritative-live-2026-10-01.json`，输出 `PASS: 4 BBC/Xinhua entrances`。报告见 [authoritative-live-2026-10-01.json](authoritative-live-2026-10-01.json)：6 个入口均为 `ok`；BBC/新华社 4 个入口共核对 12 篇，**12/12 标题相符**，各篇至少提取到 2 个正文段落；中国新闻网 2 个 RSS 源取得 5 条去重后的近期条目。报告保存 BBC 的三个不同时间字段，且同一稿被两个栏目转载时按文章 ID 去重。

## 4. 可复用实现与验收

- [sources/authoritative.json](../../../../config/sources/authoritative.json) 保存 6 个新增入口，按媒体与语言分开。
- [collect.py](../../../../scripts/collect.py) 增加 `bbc_rss`、`xinhua_en`、`xinhua_zh` 解析和 `--source-id` 精确筛选；失败、停更和近期分别记录。
- [article_probe.py](../../../../scripts/article_probe.py) 提取三种文章页面的标题、时间和正文段落；报告只写入长度及哈希。
- [verify_authoritative.py](../../../../scripts/verify_authoritative.py) 校验域名、72 小时时效、标题一致性、正文长度、SHA-256、BBC 时间顺序与新华社署名。
- [tests/test_authoritative.py](../../../../tests/test_authoritative.py) 使用不含媒体原文的合成页面校验解析逻辑；`python3 -m unittest discover -s tests -v` 的 **5 项测试通过**。

## 5. 全量复测与故障处理

第一次全量复测使用 `python3 collect.py --limit 3 --output reports/probe-2026-10-01-all.json`，于 UTC **04:10:11–04:11:43** 完成：47 个入口中 42 个 `ok`、4 个 `stale`、1 个 `error`。错误来自 `politico-eu` 的 `[Errno 54] Connection reset by peer`。随即只对该入口执行 `python3 collect.py --source-id politico-eu --limit 3 --output reports/politico-recheck-2026-10-01.json`，取得 3 条近期报道，说明首次错误是一次暂时性网络故障。为避免将这种故障直接计入入口失效，给入口首次请求增加一次 0.5 秒后重试；两次失败仍记录原始错误。

最终再次执行 `python3 collect.py --limit 3 --output reports/probe-2026-10-01-all.json`，时间为 UTC **04:16:18–04:18:01**。最终[全量报告](probe-2026-10-01-all.json)含 **47 个入口：43 个 `ok`、4 个 `stale`、0 个 `error`、119 条去重后的近期条目**。四个停更入口是 `voa-africa`、`voa-middle-east`、`voa-europe`、`cw-content`；旧新华社/人民网/中国日报候选没有纳入这 47 个配置入口。专项报告和全量报告都记录配置及代码 SHA-256，方便其他机器核对使用的版本。

期间一次可选 `py_compile` 因 macOS 的 Python 默认尝试写入受限用户缓存目录而失败；设置 `PYTHONPYCACHEPREFIX=/private/tmp/news-trace-pycache` 后语法检查通过。网络无关的 5 项单元测试始终通过。

## 6. 此次测试的边界

BBC 和新华社样本文章在普通请求下取得公开 HTML，因此无需使用 BPC 的清 cookie、伪装爬虫、屏蔽脚本、AMP 或归档回退。Reuters、AP、AFP 的正式内容 API/新闻线需要相应访问方式；本次没有凭网站可搜索或 BPC 站点条目将其记为已接入。各来源是否可用于未来对外发布的简报是另一个配置问题，不改变这次“当前机器能否取得并核对报道”的技术实测结论。
