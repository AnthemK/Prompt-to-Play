# 专题记录约定 v1

类型：规则文件。状态：**人工编辑约定，未实现自动校验器**。

[专题流程](../workflows/topic-tracking.md) · [专题入口](../../topics/README.md)

## 目录与最少记录

```text
topics/<stable-topic-id>/
  README.md                         # 当前入口、版本索引、开放问题
  research-brief.md                 # 范围、研究问题、证据计划
  issues/YYYY-MM-DD-v1/
    report.md                       # 读者正文
    reading-guide.md                # 有价值时独立保存
    evidence.md                     # 证据台账与复核
    delivery/                       # 仅实际准备交付时建立
      email.html
      full-report.md
      supporting-materials.zip
      manifest.json
      receipt.json                  # 仅有真实发送结果时建立
```

只创建有实际内容的文件。历史材料保留原位，索引链接即可；不能用空模板伪装完成核验。正文与附件可有布局差异，但不得悄悄删去限定、归属或更正。

## 研究任务说明

最少字段：专题 ID、目的、起止范围、截止时间口径、语言、关键问题、已知事实基线、竞争解释、发现范围、完成标准、交付授权。研究问题保持 3–6 个主问题，细分内容在其下展开。

## evidence.md：唯一主证据记录

| 记录 | 必填内容 |
| --- | --- |
| 来源 S01… | 标题、媒体／机构、作者（可得时）、URL、文章时间及精度、核查时间、实际访问等级、原始报道依赖组 |
| 主张 C01… | 关键主张、类型、对应 S 编号与原文位置、支持范围；进展附事件时间，措施附已证实阶段 |
| 取舍 | 重要候选为何采用、延后或排除；不记录每个搜索结果 |
| 复核 | 复核人／agent、时间、从关键结论反查原文的结果、遗留问题及处理 |

来源元数据只维护一处；如使用 `sources.json`，此处按 S 编号引用。正文与阅读指南从这份记录取用；当前人工同步，不重复抄录完整台账。

访问等级沿用 [skill 约定](../../skills/news-briefing/references/access-levels.md)。只读到部分正文必须注明范围；作者或精确时间未知就标未知。独立性不清楚时不计为已确认的独立来源。网页全文默认不保存，保留必要定位与短摘录；重要更新另存复核记录，不覆盖早期观察。

## 版本与交付清单

首页索引至少列：版本、截止日期／时间、状态（research / reviewed / delivered / superseded）、信息增量、报告和证据链接。`delivered` 指实际文件交付或邮件发送，须说明渠道；它不等于所有历史主张经过新标准认证。

交付清单记录 product_type=`topic_tracker`、topic_id、版本、标题、收件人（发送时）、正文／附件路径、各文件 SHA-256 与状态。`prepared_not_sent`、`sent`、`unknown` 分开；回执含渠道 ID 和真实返回状态。失败与更正不覆盖前次回执。

## 旧材料接续

旧专题不补造 claim IDs 或审核通过记录。首页注明“legacy/manual review”，新一期使用本约定；若重发旧稿，应重新实际核查，保存独立版本。
