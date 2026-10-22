> 历史复核记录：命令与参数反映当时执行过程；当前复现入口见[运行手册](../../../../scripts/README.md)。本地证据链接已随目录整理更新。

# 2026-10-02 简报复核记录

**原简报截至：** 2026-10-02 22:05（UTC+08:00）。**本次复核：** 同日约 22:30 至 23:00。原始[全量快照](evidence/input.json)保留不覆盖；[中文入口复测](../../../../diagnostics/2026/10/02/chinese-recheck-2026-10-02.json)和 [BBC/新华社四入口复测](../../../../diagnostics/2026/10/02/authoritative-recheck-2026-10-02.json)是后续独立运行，不能冒充原简报截至时的输入。

## 发现与处理

1. 原快照的五个中文站点错误来自当前环境的本地代理所呈现的自签证书。直连这些域名的 HTTPS 证书可验证；`collect.py` 现在只对指定域名使用直连并逐个尝试 CDN 地址，任何节点都必须通过正常证书校验。中文复测五个入口均为 `ok`，各返回 3 条近期条目。没有关闭证书校验。
2. 首次四入口复测发现 BBC World 和新华中文各有一篇列表标题与文章页标题不一致。采集器现在排除不一致的样本，再寻找其他可核验条目。重新运行 `verify_authoritative.py` 得到 `PASS: 4 BBC/Xinhua entrances`，四个入口各 3 条。
3. 美国劳工统计局的 [当前版就业报告](https://www.bls.gov/news.release/empsit.nr0.htm)会被下一期替换。本期引用的是 **USDL-26-1549，2026-10-02 发布的 2026 年 9 月数据**：非农就业增加 29,000、失业率 4.2%；统计局对两项的描述均为“变化不大”。这份记录保存了当时版本号和关键数值；如以后需要永久原站链接，应核查 [BLS 历史报告目录](https://www.bls.gov/bls/news-release/empsit.htm)并补入该期档案地址，不要沿用当时的“当前版”链接来声称已经核验未来版本。
4. 柴油报道中不同数量来自不同媒体描述的提议，不能直接视为同一方案的相互矛盾数据。成稿已改为“讨论中的方案范围尚未统一或确认”。
5. 最终版采集器将**入口活跃度**与**每日入选窗口**分开判定，并将所有媒体的窗口固定在同一 `snapshot_as_of`。少数周刊可以保持 `ok`，但其旧文章不进入每日候选集。中间的[首次 47 入口复测](evidence/rechecks/daily-input-2026-10-02-recheck.json)为 43 个 `ok`、3 个 `stale`、1 个临时连接错误；`voa-europe` [单独重试](../../../../diagnostics/2026/10/02/voa-europe-recheck-2026-10-02.json)为 `stale`。采用统一截止时间的[最终全量复测](evidence/rechecks/daily-input-2026-10-02-final-check.json)为 **43 个 `ok`、4 个 `stale`、0 个 `error`**，输出 343 条全部位于同一 36 小时窗口内；`verify_authoritative.py` 在这份最终报告上为 `PASS`，BBC/新华社四入口各 10 条。复测在原简报截止后进行，不把新候选稿倒填到原简报中。

## 逐事件证据边界

| # | 事件 | 已核查的核心依据 | 边界 |
| --- | --- | --- | --- |
| 1 | 美国就业 | BLS 原站正文、PBS 报道、FT 官方公开摘要 | BLS 当前版 URL 会滚动；以本记录的发布编号定位 |
| 2 | 法国学生抗议 | Guardian 原站正文，BBC 原站文章元数据与正文提取，Euronews 公开报道 | 约 400 校为当时预计或媒体报道数字 |
| 3 | 柴油争议 | Politico、France 24、FT 的原站链接与公开摘要 | 储备释放仍属讨论，数字不可混为已决定数量 |
| 4 | 基辅桥梁 | AP 原站索引摘要、DW 官方摘要 | 伤亡、损毁可能更新；未引具体未核数字 |
| 5 | 埃塞俄比亚与厄立特里亚 | BBC 原站文章核验、DW 分析 | 各方责任说法保持归属，不当作定论 |
| 6 | 刚果埃博拉 | AP 原站索引、Sky News 官方摘要、WHO 背景页 | WHO 背景页不是本日 4,000 人数据来源 |
| 7 | 埃及记者 | AP 报道、CPJ 原站声明 | 当局的指控不是已裁定事实 |
| 8 | OpenAI 解雇 | BBC 原站文章核验、Axios 公开报道 | 离职员工个人行为未独立查证 |
| 9 | Venom 主唱 | Guardian 原站新闻及单独的评论文章 | 去世事实与文化影响评价区分 |
| 10 | 中国外商股权性质直接投资 | 新华社原站正文，援引外汇局半年报 | 638 亿美元、55% 均为该项统计口径 |

同一事件中的多条链接只算一个事件；转载 AP 的媒体不算独立通讯社核实。任何只取得标题或官方摘要的来源，不用来支持不可见的正文细节。

## 复现命令与不变量

从 `news-trace/` 目录执行。实时报道会变化，因此重新运行不应期待与历史快照相同的标题和条数；应检查结构、时效和核验规则。

```sh
python3 -m unittest discover -s tests -q
python3 collect.py --limit 10 --max-age-hours 36 --output reports/daily-input-YYYY-MM-DD.json
python3 verify_authoritative.py reports/daily-input-YYYY-MM-DD.json
```

最终报告的 `schema_version` 为 4，`snapshot_as_of` 是全体媒体共同的 UTC 截止时间；每个顶层 `items` 条目的 `published_at` 必须位于此前 36 小时内。报告还保存 Python 版本、配置与核心代码的 SHA-256、开始和完成时间、逐入口结果。本轮原始 `NEWS_BRIEFING_STANDARD.md` 的 SHA-256 为 `6c3ecd5281726add949f461d105c94435edc5d6106ed6d23f9239fdddd283e34`，复核前后相同。
