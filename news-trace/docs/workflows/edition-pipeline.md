# 一期简报如何完成

本页适用于每日简报。复杂单议题采用[专题追踪流程](topic-tracking.md)，不套用每日事件配额或自动构建验收。

类型：**规则文件**。[首页](../../README.md) · [字段约定](../contracts/edition-v1.md) · [编辑标准](../standards/NEWS_BRIEFING_STANDARD.md)

流程：**建档 → 采集 → 取舍与证据 → 编辑复核 → 生成交付包 → 授权发送与记忆更新**。

## 1. 建档与采集

以下命令从 `news-trace/` 执行，日期占位符需要替换为实际日期。

```sh
python3 -B scripts/edition.py init editions/YYYY/MM/DD --date YYYY-MM-DD
python3 -B scripts/collect.py --limit 15 --max-age-hours 36 --output editions/YYYY/MM/DD/evidence/input.json
```

初始化只创建空模板，不自动生成新闻或标记为已发布。重复初始化拒绝覆盖。采集器本身仍会覆盖指定输出，所以复测必须另存带时间的文件。

## 2. 取舍与逐条证据

填写三个文件，字段及完整合成样例见[约定](../contracts/edition-v1.md)：

- `edition.json`：当天概述、顺序、标题、事件影响和观察到的报道差异；英文邮件文本与完整版文本分别明确填写。
- `evidence/selection-ledger.json`：重要候选、事件聚类、信息增量、独立的重要性／优先级／注意力／可信度判断，以及发现覆盖情况。
- `evidence/claims.json`：每条关键主张、支持它的来源和原文定位。转载使用同一 `dependency_group`；不知道是否独立时保守合并，并在复核时说明。

```sh
python3 -B scripts/edition.py check editions/YYYY/MM/DD --content-only
```

结构通过只代表记录齐全。`ready` 此时始终是 `false`。现阶段主题／地区统计和相同聚类标识检查帮助发现问题；真实事件语义去重及来源立场判断仍由编辑完成。

## 3. 编辑复核

```sh
python3 -B scripts/edition.py review-template editions/YYYY/MM/DD
```

程序生成 `evidence/review.json`，初始状态为 `pending`。复核者（用户或实际执行核验的 agent）需要逐项检查原文、日期和数字、英文转述、来源独立性、发现覆盖、上期内容、标题与分析；填写身份、时间、已完成检查，并为每个 P1 写英文读者提示。实际完成后才能把 `decision` 设为 `approved`。这不是强制用户审批步骤，也不是自动产生的事实正确性证明。

记录绑定四份输入文件的 SHA-256。任何输入变化都会使复核失效，需要复核变更、更新哈希与日期。不要仅为了通过校验填入“已核验”。未确认或争议内容必须保留归属和不确定性。

## 4. 生成交付包

```sh
python3 -B scripts/edition.py check editions/YYYY/MM/DD
python3 -B scripts/edition.py build editions/YYYY/MM/DD
```

P0 阻止生成；P1 必须逐项说明，提示自动显示在正文。生成：

| 文件 | 用途 |
| --- | --- |
| `brief.md` | 完整简报，按每条主张引用来源 |
| `delivery/email.html` | 可直接用于 Gmail 的英文新闻正文 |
| `delivery/brief-full.md` | 与完整版逐字一致的附件 |
| `delivery/supporting-materials.zip` | 输入、台账、主张证据、复核和校验结果 |
| `delivery/manifest.json` | 标题、正文路径、附件清单与文件哈希；状态为 `prepared_not_sent` |

已有正文或交付目录时拒绝覆盖；需要更正时另建带版本后缀的目录并显式说明更正。文件系统故障可能留下未完成目录，此时核对清单、保存问题后再处理，不能把半成品当作已发送。

## 5. 发送与收尾

按[邮件流程](email-delivery.md)确认已有发送授权，使用清单所列正文与附件发送并保存真实回执。这个命令行框架不直接调用 Gmail，也不自行启动定时任务。

完成一期后更新[事件和故事记忆](../../memory/README.md)、[简报索引](../../editions/README.md)，运行状态校验并清理临时材料。记忆自动写入、发送去重和调度重试列为后续实现，避免在没有真实发布结果时提前记为已报道。

历史简报缺少新式逐条证据时会被阻止重新生成交付包。对旧稿的实际事实复核另存记录；不批量给旧稿补上“已核验”标签。
