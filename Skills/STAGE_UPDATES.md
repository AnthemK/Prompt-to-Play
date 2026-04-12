# Stage Updates（阶段经验更新日志）

## 2026-04-10 | V2.0 发布收尾：Demo 语义校准 + 显式技能测试

### 本阶段做了什么

- 重新核对了 `V2.0` 已有能力和 `Demo` 的覆盖关系
- 修正了一个关键的遭遇语义问题：
  - 敌方体力归零后，之前只是静默解锁 `defeat`
  - 现在引擎会在出口首次解锁时明确写出结果反馈和日志
- 收紧了 `Demo` 的 softer finish 条件：
  - `negotiate`
  - `delay`
  现在都要求敌方仍然存活
- 补上了 `Demo` 的显式技能测试段：
  - `洞察 + 警觉`
  - `敏捷 + 潜行`
  - `意志 + 坚忍`
  - `力量 + 压制`
- `demo_acceptance.py` 同步扩展并校准：
  - 新增 `skill_trials`
  - 修正 `delay_load` 路线，不再依赖自相矛盾的旧出口条件

### 这次得到的经验

1. 真实玩家存档比静态读代码更容易暴露“语义不一致”

- 用户上传的存档直接暴露了两个问题：
  - 敌方已死但缺少明确反馈
  - softer finish 在 hard victory 状态下仍同时出现
- 这种问题往往测试能过、代码也不报错，但玩家体验已经不对了

2. 要先判断问题属于“系统层”还是“故事层”

- 这次分成了两类处理：
  - 系统层修正：
    - 遭遇出口首次解锁时统一发反馈
    - 敌方 HP 归零后不再执行敌方行为
  - 故事层修正：
    - `Demo` 的 `negotiate/delay` 显式加 `requires`
- 这比把所有问题都塞进系统层更干净

3. Demo 覆盖不应只靠“间接出现”

- 虽然 `V2.0` 早就支持 `attribute + skill`
- 但如果只埋在现有行动里，玩家和 reviewer 都不容易立刻看出来
- 所以最后补一个显式的 `skill_trials` 节点是值得的

4. 发布前检查要分两层

- 第一层：自动检查
  - `story_cli validate`
  - `unittest`
  - `demo_acceptance`
  - `review_guard`
- 第二层：语义检查
  - 是否有互相冲突的出口
  - 是否有状态变化但无反馈
  - 是否存在“测试通过但玩家仍会困惑”的点

### 后续复用建议

- 以后每次封一个稳定版本前，都检查：
  - `Demo` 是否真的显式展示本阶段新增机制
  - 新出口/新状态是否有首次解锁反馈
  - 某个故事的出口条件是否需要显式 `requires`
  - 自动验收是否还在依赖过时语义

## 2026-04-09 | 阶段收尾：Demo 覆盖补全 + 交付清单

### 本阶段做了什么

- Demo story 增加两个显式失败验收动作：
  - `fatal_test_death`（生命归零）
  - `fatal_test_corruption`（腐化超限）
- `backend/tools/demo_acceptance.py` 扩展到 6 条路线：
  - `escape / negotiate / delay_load / mechanics_mix / fatal_death / fatal_corrupt`
- `backend/tests/test_demo_acceptance.py` 同步扩展失败结局断言
- 新增阶段交付文档：`docs/STAGE_DELIVERY.md`

### 经验沉淀

- 验收样本必须覆盖“成功路径 + 失败路径”，否则关键致命规则会长期缺乏自动回归。
- 阶段结束时应有“可执行清单”而非口头说明。  
  把验收命令固定在文档里，能显著降低跨 agent 协作误差。

### 给后续 agent 的建议

- 每个阶段收尾前都检查 Demo 是否覆盖了本阶段新增机制
- 新增失败规则时，优先加“显式触发动作”用于回归，不要只依赖随机过程触发
- 阶段验收命令应保持稳定，避免频繁更换入口导致协作成本上升

## 2026-04-09 | 命名规范收口：runtime/template/state/view 边界清晰化

### 本阶段做了什么

- `adventure.py` 新增 `_encounter_runtime_and_template`，统一拿取遭遇运行态与模板态
- 关键遭遇流程变量改名：
  - `encounter_runtime`
  - `encounter_template`
  - `active_encounter_runtime`
- `engine.py` 的视图投影命名收敛为：
  - `runtime_state`
  - `scene_view`
- `docs/ENGINEERING.md` 补充命名推荐与禁止模式

### 经验沉淀

- 运行态和模板态混名是最隐蔽的技术债之一。  
  代码短期能跑，但长期会显著提高 review 成本和 bug 率。
- 对故事驱动引擎来说，命名就是接口的一部分。  
  一旦命名不稳定，文档和测试会被拖着漂移。
- “先重命名再扩功能”比“边扩边混改”更稳，尤其在多 agent 协作场景。

### 给后续 agent 的建议

- 新增遭遇能力时，优先沿用 `encounter_runtime / encounter_template` 命名，不要回退成单一 `encounter`
- 若函数同时处理状态与视图，优先拆分成“state 变更”和“view 投影”两步，减少副作用
- 每次命名收口后都跑一轮完整测试，确认只改可读性不改语义

## 2026-04-09 | 故事 DSL 契约统一：story_contract 真值表

### 本阶段做了什么

- 新增 `backend/game/story_contract.py` 作为 DSL 契约单一来源
  - `ACTION_KINDS` / `ACTION_KIND_CONFIG_KEYS`
  - `EFFECT_OPS` / `IMPACT_EFFECT_OPS`
  - `ENCOUNTER_EXIT_MODES`
- `adventure.py` 改为读取契约常量分发动作与 effect，而不是散落硬编码集合
- `story_validation.py` 改为读取契约常量校验
  - 新增 `EFFECT_OP_INVALID` / `EFFECT_OP_MISSING` 校验
- 新增回归：`backend/tests/test_story_validation.py::test_validation_reports_unknown_effect_op`

### 经验沉淀

- 机制扩展如果没有“统一词表”，会快速出现“运行时认识 A，校验器认识 B，文档写 C”的漂移。  
  把词表收敛到一个模块，是控制技术债的高收益动作。
- 对 story 驱动系统来说，“拒绝未知 DSL”比“静默忽略未知字段”更安全。  
  前者会尽早暴露错误，后者会把问题延后到游玩期。
- 当目标是多题材无缝接入时，要把“可配置能力”与“叙事内容”在代码层分离：
  - 能力词表在系统层
  - 文本与分支在 story 包

### 给后续 agent 的建议

- 每次新增 action kind / effect op 时，必须同步改：
  - `story_contract.py`
  - `story_validation.py` 回归
  - `backend/stories/README.md` 与 `STORY_INTERFACE.md`
- 在实现新机制前先问：这是不是通用能力词汇？  
  如果不是，优先留在 story 文本层，不要进入系统 DSL
- 保持 Demo 验收脚本常绿，确保 DSL 变更不会破坏关键流程

## 2026-04-09 | Demo 验收自动化：多出口 + 存读档回归

### 本阶段做了什么

- 新增 `backend/tools/demo_acceptance.py`
  - 自动跑通 `escape / negotiate / delay_load / mechanics_mix` 四条路线
  - 覆盖新开局、行动推进、至少 3 种结局出口、遭遇中存档/读档往返、debug trace 可拉取
- 新增回归测试 `backend/tests/test_demo_acceptance.py`
- 同步更新 `README.md`、`MEMORY.md`、`backend/stories/demo/README.md` 与 `TODO.md`

### 经验沉淀

- Demo story 不只是“示例内容”，更应该是“机制验收基线”。  
  当机制改动频繁时，先稳住 Demo 自动验收，比继续扩新故事更能降低回归风险。
- 验收脚本要尽量覆盖“引擎闭环”而非单点函数：  
  `new -> act -> save -> load -> act -> ending -> debug` 这一整条链路最能暴露系统耦合问题。
- 对 `lite-trpg` 项目，选择“少而硬”的验收路线比“全覆盖但脆弱”更实用。  
  先保证 3 条稳定出口与关键结算链路，再逐步扩展覆盖深度。

### 给后续 agent 的建议

- 每新增一个系统能力（尤其是 resolution / encounter / effect 生命周期）都要评估是否补进 `mechanics_mix`
- 若 Demo 验收失败，优先从 `debug_trace` 反查 action -> resolution -> effect 的断点
- 把验收脚本当成阶段门禁来维护，避免 TODO 与实际可运行状态脱节

## 2026-04-09 | Lite TRPG Simulator 命名重构阶段

### 本阶段做了什么

- 项目目录从 `Grimweave` 重命名为 `lite-trpg-sim`
- 系统层命名统一为“轻量级跑团模拟器”
- 保留 `grimweave` 作为故事包 ID（内容层）
- 同步更新启动器、前后端标识、文档与本地存档键

### 经验沉淀

- 产品名与故事包名应分层管理：  
  系统中立命名 + 内容题材命名，避免后续扩展被历史题材绑死。
- 重命名必须“代码 + 文档 + 本地存储键”一并处理，  
  否则容易出现运行正常但存档行为异常的隐患。
- 重命名后至少做两类验证：
  - 启动器 smoke test
  - 机制单元测试

### 给后续 agent 的建议

- 如果再次重命名，先全局检索再批量替换，避免遗漏路径硬编码
- 对“必须保留的旧标识”（例如故事包 ID）要提前列白名单
- 阶段结束后，把可复用方法写回 `CREATIVE_PLAYBOOK.md`

## 2026-04-09 | 统一结算扩展：易伤/护盾/治疗/吸取

### 本阶段做了什么

- 在规则层新增伤害结算顺序：抗性减伤 -> 易伤增幅 -> 护盾吸收
- 新增统一结算类型：`healing` 与 `drain`
- 将 `player.shield` 与 `encounter.enemy.shield` 接入运行态与前端展示
- 更新故事接口文档与作者指南，支持 `damage_vulnerabilities` 与 `drain` 配置

### 经验沉淀

- 机制扩展必须沿用统一结算结构，而不是新增独立输出通道。  
  这样前端和日志层改动最小，review 成本也最低。
- 新机制落地时要同步更新三层文档：  
  `README`（用户视角）+ `Memory`（开发记忆）+ `stories/README`（作者视角）。
- 对 `lite-trpg` 项目，优先“少机制高反馈”：  
  护盾吸收、易伤增幅这类一步可见的反馈，性价比高于复杂子系统。

### 给后续 agent 的建议

- 新增机制前先确认是否能被至少两个故事包复用
- 新增字段要先补 `repair_loaded_state`，避免旧存档崩溃
- 每次机制扩展都补最小回归测试，优先覆盖边界顺序问题

## 2026-04-09 | 对抗模板化：主动方/平局策略/失败代价

### 本阶段做了什么

- `contest` 新增 `active_side` 与 `tie_policy`
- `contest` 新增 `failure_cost`（支持资源扣减或伤害模式）
- 统一结算增加对抗元数据：`active_side/passive_side/tie/tie_policy/margin`
- 前端结果面板补充主动方与平局策略展示

### 经验沉淀

- 设计“模板化对抗”时，`success` 语义必须保持稳定（这里保持为“玩家成功”），否则旧故事分支会失效。
- 新机制最好先做“最小可解释版”：
  - 先有可配置字段
  - 再有可视化反馈
  - 最后扩复杂策略（如多轮重投）
- `failure_cost` 作为轻量“失败摩擦”比新增整套子系统更适合 `lite-trpg`。

### 给后续 agent 的建议

- 扩展 `tie_policy` 时优先保证后向兼容，不要改默认语义
- 若新增更复杂对抗规则（例如多对一），先在 `resolution` 中补字段再改前端
- 持续用回归测试覆盖“平局边界”和“失败代价叠加”场景

## 2026-04-09 | 遭遇框架扩展：行动经济与敌方行为模板

### 本阶段做了什么

- 遭遇新增行动经济：`action_economy`（budget/default_cost/max_actions）
- 遭遇动作新增：`cost` 与 `turn_flow`（`continue|end`）
- 系统自动提供“结束回合”动作
- 新增敌方行为模板：`enemy_behaviors`（全局 + phase）
- 前端新增展示：行动预算、动作消耗提示、敌方最近行为

### 经验沉淀

- 行动经济要“能解释、能中断、能手动结束回合”，否则用户会感觉卡住。
- 轻量框架优先“单回合可感知差异”：
  - 一次副动作继续
  - 一次主动作收束
  - 一次敌方回合反馈
- 自动生成 `end_turn` 能显著减少 UI/规则死角。

### 给后续 agent 的建议

- 扩展敌方行为时优先保持“顺序匹配第一条”的简单心智模型
- 若新增行为优先级系统，先保证旧行为表默认行为不变
- 在继续扩遭遇出口策略前，先保持现有 action economy 与分支测试稳定

## 2026-04-09 | 遭遇退出策略落地：defeat/escape/negotiate/delay

### 本阶段做了什么

- 在引擎层新增 `exit_strategies` 解释能力，系统自动生成退出动作
- 新增默认可用性判定：`defeat/delay/negotiate/escape`
- 新增退出执行链：策略 effects -> 写入全局 flag -> 结束遭遇 -> 输出统一 resolution
- 为退出动作补充回归测试（展示条件 + 执行结算）
- 同步更新故事接口文档与作者指南

### 经验沉淀

- “退出策略”应作为遭遇模板的一等能力，而不是每个故事手写 escape action。  
  这样可以保持故事写作简单，也能统一结算语义。
- 退出策略天然是“故事后果桥接点”：  
  推荐统一写 `set_flag`，让后续节点根据退出方式分流。
- 这类系统化动作一定要做“显示条件 + 执行结果”双测试，  
  只测其一会在重构时留下回归盲区。

### 给后续 agent 的建议

- 下一步优先做 encounter 环境对象（光照/掩体/危险区），并复用同一 resolution 管线
- 退出策略若扩展新 mode，先补默认可用性规则和 STORY_INTERFACE 文档
- 若要引入更复杂撤离（追逐判定、多步撤退），建议做成独立 encounter mode，不要把 `escape` 变成特判集合

## 2026-04-09 | 环境对象 + 后端调试追踪

### 本阶段做了什么

- 遭遇新增环境对象最小版：`environment + environment_meta`
- effect DSL 新增：`adjust_environment`
- phase 规则可直接读取环境字段（例：`encounter.environment.light`）
- 后端新增统一调试追踪：`state.debug_trace`
- 新增调试接口：`GET /api/game/{session_id}/debug?limit=...`
- 新增回归测试：环境变化、debug trace 生成、engine debug 读取

### 经验沉淀

- “环境”要先做成轻量规则对象，再谈复杂元素连锁；  
  否则会直接滑向故事特判堆叠。
- 调试信息要“结构化 + 可截断 + 可拉取”，  
  不能只靠控制台 print，也不能把调试内容强塞给玩家 UI。
- 每次系统扩展都要同步文档，否则作者侧和实现侧会很快漂移。

### 给后续 agent 的建议

- 下阶段优先扩环境语义（cover/light/hazard 对 check/contest 的统一影响）
- 继续细化 enemy behavior 模板，但要保持“可解释”和“lite”边界
- Demo story 在阶段收尾前必须补齐，用于机制验收与回归

## 2026-04-09 | 敌方行为细化 + 环境修正接入检定

### 本阶段做了什么

- 敌方行为新增选择策略：`first_match / priority / weighted`
- 敌方行为新增冷却：`repeat_cooldown`
- 遭遇新增 `environment_rules`，可直接影响 `check/save/contest` 修正
- 行动级新增 `environment_bonus_rules`，用于局部覆盖环境修正
- 补充回归测试：敌方行为优先级与冷却、环境修正生效

### 经验沉淀

- 环境系统要先接入“已有结算管线”，不要另起一套判定体系。  
  把环境当作 modifier source，最容易保持可解释性。
- 敌方行为细化优先做“策略+冷却”，能明显降低重复感，  
  成本远低于完整行为树。
- 每次“行为选择逻辑”改动都必须配回归测试，否则很容易在重构时退化。

### 给后续 agent 的建议

- 下一步可考虑让环境规则扩到 damage/save（例如危险区加伤、掩体减伤）
- 若扩展 weighted 策略，记得保持可复盘（debug trace 记录选中原因）
- Demo story 最终要覆盖 selection/cooldown/environment_rules 三组新能力

## 2026-04-09 | 故事工具链落地：validate + scaffold CLI

### 本阶段做了什么

- 新增 `backend/tools/story_cli.py`
  - `validate`：story schema/load + 引用完整性校验
  - `scaffold`：生成最小可运行故事包模板
- 新增 `backend/tools/review_guard.py --doc-sync`
  - 在核心代码改动时要求同步更新文档
- 新增 `backend/game/story_validation.py`
  - 动作结构校验（kind 与配置对象）
  - 引用死链校验（node/item/status/ending/encounter/phase）
  - `requires.item` 校验与 action id 重复检查
- 新增回归：
  - `backend/tests/test_story_validation.py`
  - 覆盖 CLI 退出码、死链发现、scaffold 后可加载可校验

### 经验沉淀

- “作者规范”必须绑定可执行命令，否则很快过期。  
  把规范写成 `story_cli validate`，比纯文档约束更可靠。
- 校验逻辑要和 server 解耦，放在 `game/` 层更利于复用、测试和未来接 CI。
- scaffold 的价值不在“生成代码”，而在“固定接口习惯”：
  - 默认 `story_interface_version`
  - 默认能力声明
  - 默认可运行最小节点
- “改代码必须改文档”要落到命令，而不是只写在口头规范里。

### 给后续 agent 的建议

- 下一步可把 `story_cli validate --json` 接入 CI，形成提交前硬门禁
- scaffold 后续可补“题材模板参数”（黑暗奇幻/科幻/现代悬疑）
- 如果扩 DSL，先扩 `story_validation.py`，再扩故事包与文档
