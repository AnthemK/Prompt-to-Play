# 运行手册

类型：**程序入口**。[首页](../README.md) · [每日流程](../docs/workflows/daily-brief.md)

使用 Python 3.10+，当前程序仅依赖标准库。以下命令从 `news-trace/` 执行。程序通过自身位置查找配置和记忆；显式输入、输出路径按当前工作目录解释。

| 程序 | 用途 |
| --- | --- |
| [collect.py](collect.py) | 合并信源配置，采集并输出带时间和哈希的候选快照 |
| [article_probe.py](article_probe.py) | 文章解析辅助模块，供采集器调用 |
| [inspect_access.py](inspect_access.py) | 对明确指定的快照检查访问等级；`--report` 必填 |
| [audit_candidates.py](audit_candidates.py) | 审计未纳入日常采集的候选入口 |
| [validate_snapshot.py](validate_snapshot.py) | 检查快照时间、结构及 P0/P1/P2 问题 |
| [verify_authoritative.py](verify_authoritative.py) | BBC／新华社文章核验；已知时间窗口限制见待办 |
| [validate_state.py](validate_state.py) | 检查跨期记忆 |
| [check_layout.py](check_layout.py) | 检查文档本地链接、台账输入路径及受保护原稿哈希 |
| [paths.py](paths.py) | 统一定位项目、程序、配置和记忆目录 |

试跑（输出可删除）：

```sh
python3 -B scripts/collect.py --limit 15 --max-age-hours 36 --output tmp/discovery.json
python3 -B scripts/validate_snapshot.py tmp/discovery.json
python3 -B scripts/inspect_access.py --report tmp/discovery.json --source-id wsj-news --output tmp/access-check.json
```

`--source-id` 使用配置中的真实 ID；可用其他 ID 替换示例。生成正式一期时，将日期替换为实际日期：

```sh
python3 -B scripts/collect.py --limit 15 --max-age-hours 36 --output editions/YYYY/MM/DD/evidence/input.json
python3 -B scripts/validate_snapshot.py editions/YYYY/MM/DD/evidence/input.json
python3 -B scripts/verify_authoritative.py editions/YYYY/MM/DD/evidence/input.json
python3 -B scripts/validate_state.py
```

同一期复测写入 `evidence/rechecks/` 下带时间的新文件，避免覆盖首轮输入。正式路径存在时先检查内容；采集器的 `--output` 会覆盖已有文件。编写摘要前仍需逐项核验原文。
