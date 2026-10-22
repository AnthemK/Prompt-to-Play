# 每日简报流程（按用户标准修订，2026-10-02）

编辑依据是用户提供的[原始标准](../standards/NEWS_BRIEFING_STANDARD.md)；可直接执行的提要见项目内的 [news-briefing skill](../../skills/news-briefing/SKILL.md)。原始标准保持只读。新简报以标准和 skill 为准。

## 当前执行顺序

1. 读取上期简报和事件历史，确定上期与本期的实际截至时间，并识别旧事件的新事实。手动补刊必须标出实际时间。
2. 从全部可用信源广泛发现候选事件，保存带时间和配置哈希的输入快照；复测另存文件，不覆盖首轮。按统一 `snapshot_as_of` 筛选，分别检查入口健康、候选贡献和是否触及采集上限。固定六家是重点输入，其他可靠媒体和一手材料可补充。
3. 运行快照校验。`P0` 必须修复，`P1` 必须解决或披露，`P2` 进入 `memory/TODO.md`。只保留快照、重要候选台账、成稿和持久状态四类记录。
4. 把讨论同一发展过程的报道合为**一个事件**。每日目标约 10 个不同且有实质价值的事件；重要候选台账记录事件 ID、分级、可信度、证据等级、来源独立性、取舍和一句理由。
5. 逐篇核验原文或一手材料，按 Skill 的证据等级和 BPC 访问等级记录；核实时间、数字与引述；明示单一来源、争议说法、付费墙限制，以及新闻与评论的区别。
6. 根据全球影响、信息增量和用户相关性排序。横向比较只写报道中可观察到的差异，不凭媒体政治标签猜测文章立场。
7. 依标准第 14 节成稿，并按第 22 节核稿。英文媒体报道用英文，中文媒体报道用中文。存 `editions/YYYY/MM/DD/brief.md`，更新事件、故事和反馈状态；更正必须可见。

全量发现示例：`python3 -B scripts/collect.py --limit 15 --max-age-hours 36 --output editions/YYYY/MM/DD/evidence/input.json`，随后运行 `python3 -B scripts/validate_snapshot.py editions/YYYY/MM/DD/evidence/input.json`。采集结果只是候选清单，不是正文核验。

本流程类型：**规则文件**。每期输入、台账、必要复测与交付材料同目录保存，结构见[简报索引](../../editions/README.md)。试跑输出放 `tmp/`；结束后按[文件规则](../maintenance/file-lifecycle.md)清理。邮件发送遵循[邮件交付流程](email-delivery.md)。
