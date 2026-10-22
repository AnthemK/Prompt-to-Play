# BBC、新华社等权威信源的复现手册

## 2026-10-02 复测补充

本机联网环境的本地代理曾给 `news.cn`、`chinanews.com.cn`、`infzm.com` 返回自签证书，使全量采集中的五个中文入口报错。`collect.py` 对这几个指定域名使用直连，逐个尝试 CDN 节点，仍要求正常 TLS 证书校验；其他域名保持默认网络路径。若另一台机器必须经代理访问且直连不可用，入口会如实报错，不应关闭证书校验。修复后[五入口复测](../../diagnostics/2026/10/02/chinese-recheck-2026-10-02.json)均为 `ok`。四个 BBC/新华社入口的[最终复测](../../diagnostics/2026/10/02/authoritative-recheck-2026-10-02.json)运行 `verify_authoritative.py` 得到 `PASS`，各有 3 条标题、时间、正文及署名核验通过的文章。列表和正文标题不一致的候选会被剔除，不能标成已核验。原始全量快照保留在[此前的报告](../../editions/2026/10/02/evidence/input.json)。

采集报告 schema 5 以 `snapshot_as_of` 固定整次运行的统一截止时间，并明确分开 `health_status` 与 `contribution_status`。前者判断入口是否活跃，后者说明该入口是否真正向本期候选集贡献文章；`emit_enabled`、`emitted_items` 与 `retrieval_limit_reached` 用于解释禁用、去重和采集截断。周刊可能健康但在本期窗口内没有候选稿，不能把上周文章写成今日要闻。

[中间复测](../../editions/2026/10/02/evidence/rechecks/daily-input-2026-10-02-recheck.json)曾有 1 个 VOA Europe 临时连接错误；其[单独重试](../../diagnostics/2026/10/02/voa-europe-recheck-2026-10-02.json)确认是 `stale`。采用固定截止时间的[最终 47 入口复测](../../editions/2026/10/02/evidence/rechecks/daily-input-2026-10-02-final-check.json)为 43 个 `ok`、4 个 `stale`、0 个 `error`，343 条输出文章全部在同一 36 小时窗口内。该最终报告直接运行 `verify_authoritative.py` 为 `PASS`，BBC 与新华社四入口各 10 条。保留各次报告，不改写失败的原始记录。

## 验收定义

本轮“接入成功”要求：从媒体自身入口取得 72 小时内条目；打开原站文章页；列表/Feed 标题与文章页标题一致；取得文章首发时间及至少 80 个正文字符；记录正文段落数与 SHA-256，但不把全文写入报告。BBC 另保留 RSS 条目时间与文章 `dateModified`；新华社中文稿须在正文前段出现“新华社”署名，英文稿须显示 `Source: Xinhua`。这些检查证明**当前公开页面的文字可提取**，不等于每篇文章在未来都保持同样结构，也不以字符数冒充完整性证明。

## 环境

- Python **3.10 或更新**，只用标准库；不需要浏览器扩展、账号或 `pip install`。
- 运行机器需能访问 `feeds.bbci.co.uk`、`www.bbc.co.uk`、`english.news.cn`、`www.news.cn`、`www.chinanews.com.cn`。各入口有 15 秒超时；多站点连续测试可能需要数十秒。
- 全部时间按 UTC 保存。新华社列表/文章页的无时区时间按 UTC+08:00 解释；这一固定偏移写在 `collect.py` 中，因此 Windows 机器无需额外时区数据库。
- 网络实时内容会变化。请比较**状态和验收规则**，不要期望后来运行得到与 2026-10-01 完全相同的标题、时间或正文哈希。

## 从项目目录执行

```sh
cd news-trace
python3 --version
python3 -B -m unittest discover -s tests -v
python3 -B scripts/collect.py \
  --source-id bbc-world \
  --source-id bbc-headlines \
  --source-id xinhua-en-latest \
  --source-id xinhua-zh-latest \
  --source-id chinanews-latest \
  --source-id chinanews-world \
  --limit 3 \
  --output tmp/authoritative-live.json
python3 -B scripts/verify_authoritative.py tmp/authoritative-live.json
python3 -B scripts/validate_snapshot.py tmp/authoritative-live.json
python3 -B scripts/audit_candidates.py --output tmp/candidate-audit.json
python3 -B scripts/collect.py --limit 15 --max-age-hours 36 --output tmp/all-sources.json
python3 -B scripts/validate_snapshot.py tmp/all-sources.json
```

Windows 可把 `python3` 换为 `py -3`。若只测某一媒体，保留对应的 `--source-id` 即可；`verify_authoritative.py` 则要求 BBC 与新华社四个核心入口都在同一份报告中。

验收脚本成功时输出 `PASS: 4 BBC/Xinhua entrances`。报告里的 `schema_version`、运行参数、Python 版本、配置 SHA-256、采集器与文章解析器 SHA-256、开始/结束时间，以及每个入口的地址、状态、首发/更新时间，足以识别一次运行所用的版本。`article_body_sha256` 是提取出的标准化段落文本的校验值；报告不含全文。若网页改版，验收失败会直接指出来源 ID 和失败条件。

全量命令应产生 47 个入口的状态；历史报告保留原 schema 和配置哈希，不改写。网络默认采用 `--network-mode auto`：先使用系统代理或系统路由，指定中文域名失败时再尝试保持 TLS 校验的直连。必须使用代理的机器可选 `system`，确认本地代理有证书问题时可选 `direct-affected`；不得关闭证书校验。每个入口在网络错误时只重试一次，仍失败则记为 `error`。

## 入口及解析路径

| 来源 | 发现入口 | 文章核对路径 |
| --- | --- | --- |
| BBC World | [BBC World RSS](https://feeds.bbci.co.uk/news/world/rss.xml)，[BBC 官方 feed 目录](https://support.bbc.co.uk/platform/feeds/NewsFeeds.htm) | RSS 标题/链接 → 原文 HTML `h1`、`datePublished`、`dateModified`、`article` 段落 |
| BBC Headlines | [BBC Headlines RSS](https://feeds.bbci.co.uk/news/rss.xml) | 同上；RSS `pubDate` 独立保存为 `feed_timestamp_at` |
| 新华社英文 | [Xinhua Latest news](https://english.news.cn/list/latestnews.htm) | 列表标题/北京时间 → 文章页 `h1`、`p.time`、`Source: Xinhua`、`#detail` 段落 |
| 新华社中文 | [新华网首页“最新播报”](https://www.news.cn/) | 首页标题/链接 → 文章页标题、时间、`#detailContent` 段落；仅保留前段具有“新华社”署名的稿件 |
| 中国新闻网 | [官方 RSS 目录](https://www.chinanews.com.cn/rss/)的即时与国际 feed | RSS 标题、时间、原文链接；此轮未执行逐篇正文一致性检查 |

## BPC 衍生 skill 的使用点

以已审读的 [BPC 衍生 skill 固定提交](https://github.com/Lunatic16/paywall-bypass-skill/commit/77a32379b39ddfb56cd646d5563755bc768287fc)作为**页面诊断清单**：先确认是否存在公开 RSS/列表，再检查文章页面 HTML、JSON-LD 时间字段、正文容器和可能的付费墙信号。BBC 和新华社的样本文章在普通请求下返回可解析正文，因此本轮不需要清 cookie、伪装爬虫、屏蔽脚本、AMP 或归档站。订阅媒体的独立诊断见 [paywall-access.md](../research/paywall-access.md)。

## 失败与回退规则

- HTTP 错误、XML/HTML 结构变化、无发布时间或正文过短：入口标为 `error`，不把旧结果冒充实时报道。
- 解析成功但最新发表时间超出窗口：标为 `stale`。周刊等其他媒体可在配置中使用独立的 `freshness_hours`；BBC/新华社本轮使用 72 小时。
- BBC 的 RSS 时间可能晚于文章 `dateModified`；两者分别保留，不把 RSS 时间改称首发或修改时间。验证首发 ≤ 修改，RSS 时间不早于首发超过 1 秒。
- 标题或新华社署名不能核对：`verify_authoritative.py` 失败；需人工检查页面改版或报道性质。
- 旧 RSS 的停更/404 证据由 `audit_candidates.py` 复测，候选列表保存在 `candidate-endpoints.json`；它们不进入实时采集配置。

类型：**规则文件**。上述命令输出到临时目录；正式引用的结果移到 `diagnostics/YYYY/MM/DD/`，并更新引用。候选入口实际配置位于 `config/candidate-endpoints.json`。校验器的历史窗口限制仍见[待办](../../memory/TODO.md)。
