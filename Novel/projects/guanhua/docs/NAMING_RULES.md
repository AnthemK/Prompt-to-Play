# Naming Rules

## 用途

这份文档定义《观化》项目的命名规则。

目标只有三个：

1. 路径可预测
2. 搜索可稳定命中
3. 后续索引与脚本可低成本复用

它不定义内容写法，只定义文件与目录如何命名。

## 一、总原则

项目内文件命名优先满足：

- 可判读
- 可检索
- 可扩展

避免：

- 模糊命名
- 临时命名长期保留
- 同层目录里中英混杂且无规律

## 二、Markdown 文件

Markdown 文件统一使用：

- 英文小写
- 单词之间用 `-` 连接
- 不使用空格

例如：

- `protagonist-profile.md`
- `chapter-outline.md`
- `volume-01-outline.md`

避免：

- `new draft.md`
- `final-version.md`
- `角色设定1.md`

## 三、JSON 文件

JSON 文件应显式表达其索引或元数据性质。

推荐格式：

- `*-index.json`
- `*-meta.json`

例如：

- `character-index.json`

## 四、卷级与章节级文件

卷级文件统一使用：

- `volume-01-*`
- `volume-02-*`

章节范围文件统一使用：

- `chapter-001-010-*`
- `chapter-011-020-*`

章节编号统一补零，保持排序稳定。

## 五、角色文件

角色独立立传文件统一使用稳定英文转写或约定英文名。

要求：

- 不随临时称呼改动频繁换名
- 一旦稳定，应长期保持

例如：

- `zhou-jibai.md`
- `gu-qingxu.md`

## 六、目录名

目录名优先使用：

- 英文小写
- 层级编号 + 含义名

例如：

- `01-foundation/`
- `03-characters/`
- `04-casts/`

若目录承担临时运行职能，也应在名字上直接表达，例如：

- `08-experimental-writing/`
- `09-cache/`

## 七、禁止项

避免在正式层长期保留这些命名：

- `temp`
- `new`
- `misc`
- `final-final`
- `untitled`

若某文件仍处于临时状态，应放入运行层，而不是靠文件名提醒自己它是临时的。
