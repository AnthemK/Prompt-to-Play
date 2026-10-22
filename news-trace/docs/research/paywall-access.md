# 英文媒体的订阅与正文可读性检查（2026-10-01）

此轮依照 [BPC 衍生 skill](https://github.com/Lunatic16/paywall-bypass-skill) 的诊断思路，分开记录**发现文章**、**元数据可读**、**文章页响应**、**完整正文可证实**。`inspect_access.py` 用普通研究用 User-Agent 请求一篇样本文章，只记录 HTTP 状态和付费墙/结构化数据标记，不绕过付费墙，也不保存正文。逐篇原始诊断见 [access-probe-2026-10-01.json](../../diagnostics/2026/10/01/access-probe-2026-10-01.json)。单篇样本只能代表该时点和该文章。

| 媒体 | 最新元数据 | 样本文章页 | 诊断解读 |
| --- | --- | --- | --- |
| Bloomberg | 官方 news sitemap 可读 | 403 | 原文正文未证实；可保留标题、时间和链接 |
| WSJ | 官方 news sitemap 可读 | 401 | 文章页需授权；新闻与社论须分开 |
| FT | 原站 RSS 可读 | 403 | 原文正文未证实 |
| The Economist | 周刊 RSS 可读 | 403 | 原文正文未证实 |
| HBR | 最新文章页卡片可读 | 200 | 有 Piano/TinyPass 类标记、`isAccessibleForFree=false`；出现 `articleBody` 字段也不能证明完整正文可读 |
| NYT | World RSS 可读 | 403 | 原文正文未证实 |
| The Atlantic | 原站 RSS 可读 | 403 | 原文正文未证实 |
| The New Yorker | 官方 RSS 可读 | 200 | 有付费相关字样及 `articleBody` 字段；完整性未证实 |
| Nature | 原站 RDF/RSS 可读 | 200 | 样本无已定义的付费标记；仍未做全文完整性验证 |
| Scientific American | 官方文章 sitemap 可读 | 200 | 有 `isAccessibleForFree=false`；仅取公开标题、时间和链接 |
| WIRED | 官方 AI RSS 可读 | 200 | 有付费相关字样；完整性未证实 |
| MIT Technology Review | 原站 RSS 可读 | 200 | 有 Piano/TinyPass 类标记；完整性未证实 |
| New Scientist | 原站 RSS 可读 | 200 | 有 Piano/TinyPass 类标记和 `articleBody` 字段；完整性未证实 |

403/401 可能来自订阅、地区、反自动请求或其他站点规则，**不能仅凭状态码断定具体付费墙机制**。标记命中也可能是站点共用代码，并非该篇的访问限制。后续如要引用正文，必须在适用的个人订阅或正式授权下逐篇检查可见性、长度、发布时间和更正记录；无正文时仅从 RSS 摘要与其他可访问报道中形成有明确证据的简报，不补写未见到的细节。

## 仍需授权的权威英文来源

- [Reuters](https://www.reuters.com/robots.txt) 的公开 robots 声明禁止未经事先书面同意从 `reuters.com` 自动收集内容；其 [Reuters Connect/API](https://reutersagency.com/content-delivery-platforms/reuters-connect/) 提供订阅路径。当前不列为自动采集源。
- [AP Media API](https://api.ap.org/media/v/swagger/) 提供内容 feed 和 RSS，但可用 RSS 与账号套餐相关。当前未获授权，不能把 API 文档当成已接入。
- [BBC 使用条款第 15 节](https://downloads.bbc.co.uk/usingthebbc/bbc_terms_of_use_31March2022english.pdf) 对 RSS/元数据提取和商业使用设有条件；公开 feed 虽可访问，当前不加入自动提取清单。

这三家的新闻仍可在人工阅读、正式订阅或许可明确的合作接口中作为核对来源。BPC skill 的 Googlebot 冒充、清除计量 cookie、屏蔽付费脚本、归档镜像等技术不作为无人值守采集器的默认路径；它们既不证明内容完整，也不改变来源的访问条件。
