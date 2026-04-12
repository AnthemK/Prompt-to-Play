# Character Meta

这一层是角色系统的结构化导航层。

它只处理机械问题，不处理人物文学判断。它的用途是：

1. 快速定位某个角色对应的权威 Markdown 文件
2. 区分角色是独立立传还是合并收录
3. 为卷级写作提供最小的角色筛选入口
4. 与剧情层建立文件级弱连接

这里不承担：

- 人物弧光分析
- 性格细读
- 情感张力说明
- 大段设定正文

这些内容仍以 `03-characters/` 下各正式 Markdown 文件为唯一出处。

## 本层当前文件

`character-index.json`

角色结构化导航索引。

它只保留最小必要字段，例如：

- 角色名与稳定 ID
- 权威文件路径
- 若为合并文件，应优先阅读的标题锚点
- 基础筛选字段
- 首次出场阶段
- 相关剧情文件

`index-usage-and-maintenance.md`

说明这一层应该如何使用、如何维护，以及在什么情况下必须更新索引。

## 字段边界

这一层尤其强调两个字段：

`canonical_file`

角色当前应阅读的权威 Markdown 文件。

`canonical_anchor`

若角色位于合并文件中，说明应优先跳到哪一节；若角色有独立文件，则为 `null`。

补充约定：

- `file_mode = single` 时，`canonical_anchor` 必须为 `null`
- `file_mode = shared` 时，`canonical_anchor` 必须填写
- `factions` 使用列表，而不是单值。这样即使角色后续发生阵营位移，也不需要推翻字段结构

## 与其他索引层的区别

`01-indexes/`

偏叙事与人工阅读，用来理解角色系统、关系和弧光。

`meta/`

偏导航与检索，用来快速回答“这个角色去哪里看”“和哪些剧情文件直接相关”。

## 下一步去哪里看

如果你要找角色的正式人物内容，请根据 `character-index.json` 中的 `canonical_file` 和 `canonical_anchor`，再进入对应 Markdown 文件。

如果你要理解角色关系与人物推进，请回到：

`../01-indexes/README.md`

如果你要维护这一层，请先读：

`index-usage-and-maintenance.md`
