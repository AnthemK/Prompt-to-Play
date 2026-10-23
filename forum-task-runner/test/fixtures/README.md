TLS 测试证书与密钥由测试通过 OpenSSL 在临时目录动态生成，用后随测试目录删除，不提交证书私钥。运行完整集成测试需要本机提供 openssl 命令。旧的 localhost.key / localhost.crt 仅为历史本地测试文件，不参与测试，不应提交。
