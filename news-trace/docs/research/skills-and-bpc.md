# 现成 Skill 与 BPC 审读（2026-09-30）

## 选择

| 候选 | 在溯闻中的用途 | 当前决定 |
| --- | --- | --- |
| [NousResearch `rss-feeds`](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/research/rss-feeds/SKILL.md) | 发现、读取 RSS/Atom/JSON Feed | 借鉴解析方法；现有 `collect.py` 已能探测元数据 |
| [NousResearch `grounded-citations`](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/grounded-citations/SKILL.md) | 断言与证据链接、检查漏引 | 借鉴证据台账；原 skill 的环境和打包需另行验证（[相关报告](https://github.com/NousResearch/hermes-agent/issues/91542)） |
| [NousResearch `competitor-news-monitor`](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/competitor-news-monitor/SKILL.md) | 监测清单、增量、去重 | 只借鉴流程，重写新闻分类 |
| [cclank `news-aggregator-skill`](https://github.com/cclank/news-aggregator-skill) | 多源和中文简报模板 | 只借鉴版式；聚合结果不充当原始证据 |
| [Lunatic16 `paywall-bypass-skill`](https://github.com/Lunatic16/paywall-bypass-skill) | 识别付费墙技术、判断正文可见性与完整性 | **作为重要的信源接入诊断资料**；按站点重新验证，不直接运行通用绕过脚本 |

## BPC 衍生 skill 的完整审读

已审读仓库 `SKILL.md`、`references/paywall-patterns.md`、`content-extraction.md`、`cookie-rules.md` 以及两个 examples，核对的提交为 [`77a3237`](https://github.com/Lunatic16/paywall-bypass-skill/commit/77a32379b39ddfb56cd646d5563755bc768287fc)。该 skill 是从 [Bypass Paywalls Clean](https://gitflic.ru/project/magnolia1234/bypass-paywalls-chrome-clean) 整理的文字规则和示例，不是媒体 API，也没有逐站实时验证。其“500+ 站点”是项目自述，不能据此认为这些站都已可用。

**可吸收的经验**：

1. 把访问问题拆成“可发现链接、可读摘要、可读正文、是否完整、可否保存/展示”五个独立判断，避免“HTTP 200”就认定拿到全文。
2. 查看页面的结构化数据、AMP 指示、常见付费墙服务和正文容器，能解释某篇文章为何只返回导语，也能为订阅或授权接口选型提供线索。
3. 按媒体集团维护规则，但同集团不同站点、新闻与评论、免费与订阅文章仍需分别测；记录检测日期和样本 URL。
4. 将站点规则视为会失效的假设；每次接入需检查是否取得完整标题、发布日期、正文、署名、更新/更正标识。

**不直接照搬的地方**：

- 文档把 Googlebot 冒充、删计量 cookie、屏蔽付费墙脚本和 archive 镜像列为“提取策略”。这些动作涉及具体站点的访问条件，不能作为无人值守采集的默认路径。对需付费的媒体，优先 RSS/API、个人订阅范围内的阅读或正式授权；正文不可获取时只保留元数据与原文链接。
- 示例中的纽约时报、彭博等站点结论没有逐篇测试记录；`content-extraction.md` 给出的 Google Cache 链接和猜测 AMP URL 等属于待验证候选，不可视为稳定接口。
- `paywall-patterns.md` 把 `js.pelcro.com` 放进 Piano 域名表，而主文件又将 Pelcro 单列；说明模式表有需复核的内部不一致。示例的“发现付费墙脚本”也不能证明正文被挡住。
- JSON-LD/Next.js 中出现 `articleBody` 或 `content`，不等于正文完整或允许重用。第三方归档页还可能过期，须回原站核对时间与更正。

## 在溯闻中的使用门槛

对每家媒体建立一张接入卡：官方入口、条款/授权、实际可用字段、文章样本、技术诊断、最后复核日。BPC skill 用在**技术诊断**步骤，输出“可能的付费墙机制”和“可见内容是否完整”的证据；它不自动改变该媒体的接入权限。任何全文提取策略要先有适用的访问依据，再按单站实现与复测。私人订阅、商业 API、网站开放文章和 RSS 各自记录，不互相推定。

2026-10-01 已用 `inspect_access.py` 对 13 家英文媒体的样本文章页执行只读技术诊断；逐站 HTTP 状态、付费墙信号与误判边界见 [paywall-access.md](paywall-access.md)。这些结果把“已取得最新标题”和“可读取完整正文”明确分开。

2026-10-03 再次检查上游仓库，仍只有一个公开提交。项目已把可复现部分固化到 `inspect_access.py` schema 2：输出固定上游提交、HTTP 状态、观察到的付费墙信号、样本哈希和访问等级。等级分为请求失败、文章页不可用、需要授权或请求被阻止、公开页受限或不确定、公开正文候选、公开页未验证。`public_body_candidate` 仍须逐篇核对标题、署名、时间、结尾与长度后，才可升级为 `verified_full_article`；诊断结果本身不升级证据等级。详细定义保存在项目 Skill 的 `references/access-levels.md`。

项目优先顺序：官方 RSS/API → 开放文章 → 已授权的订阅/API → 仅链接和元数据。无正文时不编造基于正文的摘要；可用多家可访问报道和一手文件核对事实。正文存储与再展示另行按授权判断。

## 后续 skill 化

先让溯闻完成几次人工复核的简报，再用本机 `skill-creator` 将信源接入、BPC 诊断、证据链、横向比较和质检沉淀为项目专用 skill。第三方 skill 不原样拼接成自动流程。
