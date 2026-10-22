# 首选六家媒体（2026-10-01，1 中文 + 5 英文）

按用户修订，从正式采集配置中移除半岛电视台英文站；在原有新华社、BBC、《卫报》、《华尔街日报》之外，增加明确的保守派观点来源《National Review》和科技专业媒体《MIT Technology Review》。六家均通过[专项实测](../../diagnostics/2026/10/01/core-six-live-2026-10-01.json)：UTC 08:52:03–08:52:17 每个入口均为 `ok`，各取得 3 条近期条目。移除不需要的媒体后，[最终全量回归](../../diagnostics/2026/10/01/probe-2026-10-01-final.json)于 UTC 08:56:33–08:59:40 完成：47 个入口中 43 个 `ok`、4 个 `stale`，无 `error`，且不含半岛电视台入口。

| 媒体与配置 ID | 角色与选择依据 | 本次接入深度 |
| --- | --- | --- |
| [新华社](https://www.news.cn/xinhuashe/jbqk.htm) `xinhua-zh-latest` | 唯一中文席位；该社[自述](https://www.news.cn/xinhuashe/jbqk.htm)为中国国家通讯社，可直接追踪中国官方政策表述。 | 首页“最新播报”→原站文章；抽样核对标题、时间、新华社署名和正文。 |
| [BBC News](https://support.bbc.co.uk/platform/feeds/NewsFeeds.htm) `bbc-world` | 英国公共广播的世界新闻；[皇家宪章](https://downloads.bbc.co.uk/bbctrust/assets/files/pdf/about/how_we_govern/2016/charter.pdf)规定准确与公正要求。 | 官方 World RSS→原站文章；抽样核对标题、首发/修改时间和正文。 |
| [The Guardian](https://www.theguardian.com/the-scott-trust/2015/jul/26/the-scott-trust) `guardian-world` | Scott Trust 保障编辑独立，并明确其自由主义传统；补充权利、气候和公共问责的报道重点。 | 原站 World RSS；近期标题、时间和链接已验。 |
| [The Wall Street Journal](https://www.wsj.com/about-us) `wsj-news` | 权威商业与经济新闻。[报社说明](https://www.wsj.com/about-us)将新闻部与倡导自由市场的意见版分开；两者不能混为一谈。 | 官方新闻 sitemap；近期标题、时间和链接已验，部分正文需订阅。 |
| [National Review](https://www.nationalreview.com/) `national-review-all` | 明确的美国保守主义评论传统；该刊[官方资料](https://www.nationalreview.com/wp-content/uploads/2014/10/NRO_MediaKit_2014-2.pdf)将网站定位为保守派新闻、评论与观点来源。提供《华尔街日报》新闻版不能直接代表的保守派**观点文本**。 | 原站 RSS；近期标题、时间和链接已验。采集时须标明评论/分析，事实断言另行核对。 |
| [MIT Technology Review](https://event.technologyreview.com/offensive-ai/mittr) `mittr-all` | 专门覆盖技术及其社会影响；[机构介绍](https://event.technologyreview.com/offensive-ai/mittr)说明其创办于 MIT，依靠技术领域编辑与记者。作为科技专业来源，避免只靠综合媒体报道技术。 | 原站 RSS；近期标题、时间和链接已验。 |

选择标准是媒体自身入口可返回近期条目、具备明确的编辑使命与专业能力、并在有限席位中增加可比较的视角。六个品牌不是六个预设的政治标签。《National Review》以评论和分析见长，它提供保守派论证，不能代替对事实的独立核实。《华尔街日报》当前采集的是新闻版元数据，不能因为其意见版主张自由市场，就给每篇新闻贴“保守派”标签。科技报道也应区分新闻、评测和观点。

接入层级仍有差别：BBC 和新华社已完成[文章级抽样](../../diagnostics/2026/10/01/authoritative-live-2026-10-01.json)，其余四家目前主要通过 RSS/sitemap 验证近期**元数据**。生成简报中的具体断言前，需逐篇取得可核查内容或原始文件，并保留链接与引用位置。单一中文席位不足以代表所有中文声音；其他已接入媒体继续作为事件级补充来源。

## 候选比较与复现

《每日电讯报》是可考虑的英国保守派主流报纸，但 2026-10-01 在本机测试其两个 RSS 地址和两个 sitemap 地址均返回 HTTP 402，因此没有将其记为“成功接入”。《The Dispatch》的 `/feed/` 可读且有近期稿，但在“广泛认可的长期声誉”这一条件下，本轮选择创刊更久的《National Review》。它们的观点不能按单一左右轴完全互相替代。

```sh
cd news-trace
python3 -B scripts/collect.py \
  --source-id xinhua-zh-latest \
  --source-id bbc-world \
  --source-id guardian-world \
  --source-id wsj-news \
  --source-id national-review-all \
  --source-id mittr-all \
  --limit 3 \
  --output tmp/core-six-live.json
```

运行结果中的 `checked_at`、`completed_at`、源 URL、配置及代码哈希可用于对照；实时标题与时间会随新闻发布变化。
