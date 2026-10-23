# 上传交接

类型：**维护说明**。整理日期：2026-10-23。

## 范围

仅上传 `news-trace/`。保留规则、程序、配置、测试样例、研究、正式证据、已发送附件与回执，以及 `memory/` 中的短期和长期记忆。`diagnostics/` 和历史复测快照属于复现记录。

临时工作统一放在 `tmp/`；项目 [.gitignore](../../.gitignore) 排除临时目录、缓存、本地环境与编辑器产物。不要强制加入被忽略文件。原始标准和已交付文件保持原样。

## 上传前复核

在仓库根目录运行：

```sh
git ls-files --cached --others --exclude-standard -- news-trace/
git ls-files --cached --ignored --exclude-standard -- news-trace/
git add --dry-run -- news-trace/
```

第一项是候选清单；第二项应为空（忽略规则不会自动排除已跟踪文件）；第三项仅预览。仅暂存本项目，并复核最终暂存范围，避免带入仓库其他项目的改动。

在 `news-trace/` 运行首页列出的离线检查。若通过文件打包上传，按候选清单收录实际存在的文件：普通压缩操作不会自动遵守 `.gitignore`。不要使用只包含已提交内容的归档方式遗漏本轮新增文件。

接续工作先读 [短期记忆](../../memory/working-state.md) 和 [AGENTS.md](../../AGENTS.md)。上传检查只验证文件与结构，不代表重新核实新闻内容或实时信源。
