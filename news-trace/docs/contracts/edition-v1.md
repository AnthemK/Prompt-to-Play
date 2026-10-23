# 简报数据约定 v1

类型：**规则文件**。[执行流程](../workflows/edition-pipeline.md) · [完整合成样例](../../tests/fixtures/edition-v1/)

本约定由 [校验模块](../../scripts/briefing/validate.py)执行，使用标准库。升级结构必须递增版本并明确兼容方式。所有时间带时区；展示日期按北京时间解释。普通文本字段不填写 HTML；英文邮件字段由编辑提供忠实英文转述。

## 文件与对象

| 文件／版本 | 必需内容 |
| --- | --- |
| `edition.json` / 1 | `issue_date`、`cutoff`、`overview`、`overview_en`、`events` |
| `evidence/input.json` / 采集器版本 | 原始快照；`snapshot_as_of` 等于本期 `cutoff` |
| `evidence/selection-ledger.json` / 2 | `issue_date`、`input_snapshot` 固定为 `evidence/input.json`、`coverage_review`、`candidates` |
| `evidence/claims.json` / 1 | `evidence` 和 `claims` 两张表，ID 在各自表内唯一 |
| `evidence/review.json` / 1 | 人工或 agent 实际复核记录，程序只生成待填模板 |

旧台账 v1 使用项目根目录相对路径；新台账 v2 使用本期目录相对路径，不能混用。原有历史文件不批量升级。

## 事件与候选

`events` 每项包含 `id`、`headline`、`headline_en`、`section`、`topic`、`region`、`claim_ids`、`why_it_matters`、`why_it_matters_en`。有必要时增加 `media_framing` 和对应的 `media_framing_en`。正文直接由主张生成，不再维护一份独立、容易漂移的事实摘要。

`candidates` 每项包含 `event_id`、`cluster_key`、`story_id`、`information_gain`、`reason`，以及：

- `decision`：`selected` / `rejected` / `deferred`；入选 ID 必须与正文对象一致。
- `global_significance` 与 `briefing_priority`：分别为 S/A/B/C/D，不能合并。
- `attention` 与 `confidence`：分别为 High/Medium/Low。

同一发展使用同一个 `cluster_key`，同一持续故事使用同一个 `story_id`。已报道事件再次出现需明确更正，或为真正的新发展创建新的事件 ID 并说明信息增量。程序无法仅靠文本相似度认定两个事件相同。

`coverage_review` 每项包含 `area`、`status`、`note`。状态为 `covered`、`no_material_development` 或 `gap`。检查领域、地区与重要来源的发现覆盖，不能用固定栏目配额替代选题判断。

## 主张与证据

`claims` 每项包含：

- `id`、`event_id`、`text`（完整版语言）、`text_en`（英文邮件）、`evidence_ids`。
- `kind`：fact / reporting / analysis / opinion / primary_source。
- `status`：verified / disputed / unconfirmed。这个标签由复核者负责，不由程序自动判真。

`evidence` 每项包含：

- `id`、`source_id`、`publisher`、原站 `url`、`published_at`。
- `level`：primary_document / verified_full_article / official_summary / feed_summary / title_only。
- `locator`：原文段落、章节、表格或锚点；`support`：简短摘录或可检查的支持说明，不保存大段全文。
- `checked_by`、`checked_at`：谁在何时检查。
- `dependency_group`：原始信息链；多家转载同一通讯社稿只算一条链。

引用快照内文章时，来源 ID 和发布时间必须一致；额外找到的一手资料可以使用 `discovery: supplemental`，并填写 `discovery_reason`。同一机构自己的声明证明“它说了什么”，不自动证明其有争议的说法为真。

## 复核与限制

复核记录必须包含 `decision: approved`、`input_sha256`、`reviewed_by`、`reviewed_at`、`checks_completed` 和 `disclosures`。六项检查为：`facts`、`translations`、`source_independence`、`coverage`、`prior_issue`、`headline_and_analysis`。

`disclosures` 将检查结果中的每个 P1 `code` 映射到简洁的英文读者提示。哈希覆盖本期四份输入；它用于发现修改，不是身份签名，也不证明复核者确实看过原文。信源真伪、主张支持关系、译文忠实度和分析分寸仍需实际核验。

8–12 条之外只产生数量提示，不强行补齐。所有非空标准栏目可按 `section` 排列；数量检查只计 Core / Other Notable / Personal Focus / Widely Discussed / Unconfirmed 中的新闻事件。阅读推荐、未来里程碑和更正不计入新闻数量，但仍需证据、明确内容类型与复核。未来可将这些辅助条目拆成专门对象，同时保留统一引用规则。
