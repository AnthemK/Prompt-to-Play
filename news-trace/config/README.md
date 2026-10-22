# 信源配置

类型：**长期配置**。[首页](../README.md) · [媒体选择依据](../docs/research/core-six-selection.md)

采集器合并 [sources.json](sources.json) 和 `sources/` 下全部 JSON 文件。每个入口的 `id` 必须全局唯一；同一媒体可以有多个栏目入口。

| 配置文件 | 内容 |
| --- | --- |
| [sources.json](sources.json) | 基础媒体入口 |
| [authoritative](sources/authoritative.json) · [general](sources/general.json) | BBC、新华社等权威来源及综合新闻 |
| [finance](sources/finance.json) · [technology](sources/technology.json) · [science](sources/science.json) | 财经、科技与科学 |
| [chinese](sources/chinese.json) · [regional](sources/regional.json) | 中文与地区媒体 |
| [conservative](sources/conservative.json) · [english-additions](sources/english-additions.json) | 保守派来源及其他英文媒体 |
| [candidate-endpoints.json](candidate-endpoints.json) | 待核查或旧入口；仅由候选审计程序读取，不进入日常采集 |

新增媒体：先在 `tmp/` 试跑，核对日期、语言、来源与可见正文，再加入合适的配置文件。无需每家媒体建一个文件夹；只有出现专用解析器、测试样例等独立资源时再分目录。
