# 项目维护约定

- 通用代码放 src/；站点专属模板与说明放 sites/<site>/，不要在执行器内硬编码站点。
- 新站点/新账号使用唯一 account，任务 id 全局唯一；不同站点不共用账号命名空间。
- .data、.test-output、Cookie、密钥、管理访问令牌不进 Git，不输出凭据正文。
- 修改存储前先测试迁移，迁移真实数据前停止服务，保留可恢复旧数据；不要在运行中创建第二个 Store 实例读取正式库（构造函数会进行恢复操作）。只读检查使用 SQLite readOnly。
- 模板默认禁用调度；实际配置以数据库为准。不得将本地演示或已签到检查写成真实跨日成功。
- 核心与迁移修改运行 npm test；文档移动检查相对链接。记录保持简短，当前能力以 README 和 docs 为准。

## 必须遵守的隐私规则

- 所有真实账号登录态、密钥、配置导出、诊断正文和截图只放 `.data/`：账号数据放 accounts/，截图放 evidence/<site>/，备份放 backups/。不放 sites/、docs/、examples/。
- sites/ 只保留无凭据模板和概括性说明；文档不得写个人账号标识、邮箱、密码、Cookie、认证头或管理链接令牌。
- 提交前运行 `python3 scripts/privacy-check.py`；推送前运行 `python3 scripts/privacy-check.py --history`。检查失败先移出暂存区并处理，禁止绕过钩子或强制加入私有文件。
- .gitignore 不保护已跟踪文件。新增私有数据类型时同时更新忽略规则、隐私检查器和 docs/PRIVACY.md，并检查 git ls-files。
- 不上传或分享整个项目目录/压缩包，不将私有内容发送给模型、外部 API、错误上报或其他人。网站认证仅按任务授权发送给目标站点。
