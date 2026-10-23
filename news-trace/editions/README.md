# 简报与交付档案

类型：**长期成果与证据**。[首页](../README.md)

| 日期 | 正文 | 原始输入 | 取舍／复核 | 邮件材料 |
| --- | --- | --- | --- | --- |
| 2026-10-03 | [简报](2026/10/03/brief.md) | [输入快照](2026/10/03/evidence/input.json) | [候选台账](2026/10/03/evidence/selection-ledger.json) | [材料包](2026/10/03/delivery/NewsTrace-2026-10-03-supporting-materials.zip) · [清单](2026/10/03/delivery/2026-10-03-supporting-materials-README.txt) |
| 2026-10-02 | [简报](2026/10/02/brief.md) | [输入快照](2026/10/02/evidence/input.json) | [复核说明](2026/10/02/verification.md) · [复测](2026/10/02/evidence/rechecks/) | — |
| 2026-10-01 | [简报](2026/10/01/brief.md) | [输入快照](2026/10/01/evidence/input.json) | 早期样稿，未保存独立候选台账 | — |

后续每期放在 `YYYY/MM/DD/`：

```text
edition.json                  结构化编辑内容
brief.md                      正式正文
evidence/input.json           首轮输入快照
evidence/selection-ledger.json 重要候选的取舍
evidence/claims.json           逐条主张与原文定位
evidence/review.json           绑定输入哈希的编辑复核
evidence/rechecks/            必须保留的后续复测
verification.md               有实质问题时才建立复核说明
delivery/                     邮件正文、完整版附件、资料包与发送回执
```

仅创建实际用到的文件和目录。旧期缺少的材料标明缺口，不补造历史记录；新期完成后在本索引增加一行。旧台账 v1 的 `input_snapshot` 相对 `news-trace/`；新台账 v2 相对本期目录，固定为 `evidence/input.json`。邮件附件中归档的原始文件名保留，不因工作目录迁移重做已发送压缩包。
