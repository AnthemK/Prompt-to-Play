# xsijishe 每日签到

范围仅为每日签到，固定入口 `https://xsijishe.com/k_misign-sign.html`，不访问帖子或执行补签、充值等操作。

- 模板：`task.template.json`，默认暂停；实际任务启用每日 Asia/Shanghai 09:10，14 小时运行窗口。
- 账号命名空间：`xsijishe`；任务：`xsijishe-checkin`。
- 私有数据：`.data/accounts/xsijishe/`，独立数据库和密钥。
- 私有证据：`.data/evidence/xsijishe/checkin.png`，禁止提交。

流程：打开签到页，未登录的 `#JD_sign` 指向登录页；已登录未签到时指向本站签到操作。只点击 `#JD_sign[href*="operation=qiandao"]`，让网页生成当次 formhash；不将 token 写入模板。个人“您的签到排名：”为完成标记，避免把全站“今日已签到人数”误判为本人完成。

2026-10-22：用户自行登录后保存会话，重新打开独立浏览器成功复用；点击签到后页面显示今日已签到、积分奖励 223。随后后台 Runner 使用保存会话返回 already_done，第二次调用被同日去重。每日计划已启用。

已签到后原提交链接消失，因此登录识别包含未签到入口与已签到个人排名两种状态。尚未验证下一自然日后台自动点击和长期会话寿命；本次未出现验证码，未来遇到验证仍可能需要人工介入。
