# South Plus 每日任务

仅处理用户授权的每日签到/每日任务，不接入其他帖子或付费功能。

已确认入口 `https://south-plus.net/plugin.php?H_name-tasks.html`，未登录会提示无权限并显示含验证码的登录表单。

当前 `task.draft.json` 仅用于打开登录窗口，调度暂停，无提交步骤。登录识别为待验证候选；具体每日任务、领奖与完成标记必须登录后确认。

独立账号命名空间 `south-plus`，私有数据位于 `.data/accounts/south-plus/`。真实页面证据仅放 `.data/evidence/south-plus/`，不提交 Git。不得复制其他站点登录态。
