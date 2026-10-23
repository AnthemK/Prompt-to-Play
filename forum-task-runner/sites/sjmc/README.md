# SJMC 用户中心

- 网站：https://skin.mc.sjtu.cn/user
- 模板：[task.template.json](task.template.json)，默认暂停。
- 当前账号命名空间：`sjmc`；任务 ID：`sjmc-checkin`。
- 实际运行数据：项目 `.data/accounts/sjmc/`，独立数据库和密钥，禁止提交。
- 当前计划：Asia/Shanghai 每日 09:00，15 小时执行窗口，后台浏览器。

流程：进入用户中心 → 用仪表盘主标题确认登录 → 若禁用按钮显示“后可签到”则跳过 → 否则点击“签到” → 等待同一完成标记。

2026-10-22 验证：人工浏览器签到获得 52 积分；独立后台浏览器复用保存的登录态并返回 already_done，第二次运行被同日去重。尚未验证次日自动点击和长期会话寿命。最初以侧栏个人资料链接识别登录未通过，现使用主标题。

普通用户中心登录已验证；jAccount 跨域登录未适配。本次没有遇到验证码，模板没有验证码专属选择器，不代表能自动处理未来验证。

本地结果截图：`.data/evidence/sjmc/checkin.png`。该截图含账号页面信息，不进 Git。模板与实时配置的区别见 [架构说明](../../docs/ARCHITECTURE.md)。
