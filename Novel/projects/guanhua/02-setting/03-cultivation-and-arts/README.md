# 03 Cultivation And Arts

这个目录处理本项目中的修炼体系、功法体系、斗法体系、百艺体系与法宝体系。

它主要回答的是：在既定天地法则下，修行者如何修、如何承载、如何出手、如何造物，以及如何借助法宝放大自身道路。

## 这个目录解决什么问题

这一层主要处理以下内容：

- 修仙六境为何能成为天下通用的层级尺度
- 正统修仙、炼体、炼魂等主要修途如何成立
- 功法为何是修士根基，以及功法如何塑造道路差异
- 战斗法门与术法如何在功法基础上展开
- 丹、符、阵、器、医护、御兽等百艺如何嵌入修行世界
- 法宝、本命法宝与镇宗重器为何会成为力量与法统的载体

## 边界

本目录负责：

- 修途与境界
- 功法与传承
- 斗法与术法
- 百艺
- 法宝与重器

本目录不负责那些**看起来很像修炼内容、但实际上属于更上层世界论**的部分，例如：

- 天地本体、道的性质、灵气与界域的根本法则
- 气运、因果、天机、生死边界与天劫的底层机制


本目录也不负责那些**看起来会用到修炼体系、但实际上属于更下层世界展开**的部分，例如：

- 宗门、世家、王朝、种族、地域等具体组织结构
- 历史事件、人物经历与正文桥段

## 分层与索引

本目录遵循以下递进结构：

### `01-paths-and-realms/`
**修途与境界**

这一层回答“修什么”。  
它定义修行主干、修仙六境、主要修炼道路，以及破境、瓶颈与修行依附条件。

更细的内容请看：
`01-paths-and-realms/README.md`

### `02-cultivation-methods/`
**功法与传承**

这一层回答“怎么修”。  
它定义功法的地位、结构、相性、冲突、传承、秘传与演化。

更细的内容请看：
`02-cultivation-methods/README.md`

### `03-battle-and-spells/`
**斗法与术法**

这一层回答“怎么打”。  
它定义斗法原则、术法分类、不同修途的战斗展开方式，以及战阵与大战。

更细的内容请看：
`03-battle-and-spells/README.md`

### `04-cultivation-arts/`
**百艺**

这一层回答“怎么做事”。  
它定义丹、符、阵、器、医护、御兽与其他专门技艺如何服务修行、组织与战争。

更细的内容请看：
`04-cultivation-arts/README.md`

### `05-treasures-and-artifacts/`
**法宝与重器**

这一层回答“拿什么承载和放大力量”。  
它定义法宝体系、本命法宝、品阶与相性，以及镇宗重器和战略法宝。

更细的内容请看：
`05-treasures-and-artifacts/README.md`

## 建议阅读顺序

建议按以下顺序阅读：

1. `01-paths-and-realms/`
2. `02-cultivation-methods/`
3. `03-battle-and-spells/`
4. `04-cultivation-arts/`
5. `05-treasures-and-artifacts/`

这个顺序的目的，是先立修行主干，再立功法根基；在此之后，斗法、百艺与法宝才能不彼此混淆。

## 使用原则

本目录只抓主干，不求一次写尽。

当前阶段的目标是先建立清楚、简练、可扩展的骨架，而不是把所有细节一次性定死。  
因此，本目录允许在下一级目录中保留适度接口，用于后续补充具体修途差异、功法演化、偏门百艺与特殊法宝体系。

但所有后续补充，都应服从本目录已经确定的分层与边界，不应在下层目录中反向改写本层结构。


## 完整目录结构 暂定

请直接看源码
03-cultivation-and-arts/
├── README.md
├── 01-paths-and-realms/
│   ├── README.md
│   ├── principles-of-cultivation.md
│   ├── six-realms-of-immortality.md
│   ├── orthodox-cultivation.md
│   ├── body-tempering.md
│   ├── soul-refinement.md
│   ├── dual-and-triple-cultivation.md
│   ├── breakthroughs-and-deviations.md
│   └── resources-and-bottlenecks.md
├── 02-cultivation-methods/
│   ├── README.md
│   ├── method-system.md
│   ├── method-structure.md
│   ├── orthodox-methods/
│   │   ├── README.md
│   │   ├── orthodox-methods.md
│   │   └── 中和经.md
│   ├── body-methods/
│   │   ├── README.md
│   │   └── body-methods.md
│   ├── soul-methods/
│   │   ├── README.md
│   │   └── soul-methods.md
│   └── heterodox-and-forbidden-methods/
│       ├── README.md
│       └── heterodox-and-forbidden-methods.md
├── 03-mystic-arts/
│   ├── README.md
│   ├── art-system.md
│   ├── orthodox-arts/
│   │   ├── README.md
│   │   ├── orthodox-arts.md
│   │   └── 玉宸九霄雷令.md
│   ├── body-arts/
│   │   ├── README.md
│   │   ├── body-arts.md
│   │   └── 裂景拳.md
│   ├── soul-arts/
│   │   └── README.md
│   └── heterodox-and-forbidden-arts/
│       ├── README.md
│       └── heterodox-and-forbidden-arts.md
├── 04-esoteric-crafts/
│   ├── README.md
│   ├── craft-system.md
│   ├── formations.md
│   ├── artifact-forging.md
│   ├── alchemy.md
│   ├── medicine-and-nurture.md
│   └── spirit-beast-arts.md
└── 05-treasures-and-artifacts/
    ├── README.md
    ├── artifact-system.md
    ├── natal-treasures.md
    ├── ordinary-artifacts.md
    ├── strategic-treasures.md
    ├── grades-and-compatibility.md
    └── representative-artifacts.md