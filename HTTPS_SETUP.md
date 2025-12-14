# HTTPS 配置指南

本指南将帮助你为应用配置 HTTPS，使用 Let's Encrypt 免费 SSL 证书。

## 前置条件

1. **域名已解析到服务器**
   - 确保你的域名（如 `example.com`）的 A 记录指向服务器 IP
   - 可以使用 `dig example.com` 或 `nslookup example.com` 检查

2. **服务器端口开放**
   - 确保 80 端口开放（用于 Let's Encrypt 验证）
   - 确保 443 端口开放（用于 HTTPS 访问）
   - 检查防火墙规则：`sudo ufw status` 或 `sudo iptables -L`

3. **环境变量配置**
   - 在项目根目录的 `.env` 文件中设置以下变量：
   ```bash
   CERTBOT_EMAIL=your-email@example.com  # 用于接收证书到期通知
   CERTBOT_DOMAIN=yourdomain.com          # 你的域名（不含 www）
   FRONTEND_HTTPS_PORT=443                 # HTTPS 端口（默认 443）
   ```

## 快速开始

### 1. 配置环境变量

编辑 `.env` 文件：

```bash
# SSL 证书配置
CERTBOT_EMAIL=admin@yourdomain.com
CERTBOT_DOMAIN=yourdomain.com
FRONTEND_HTTPS_PORT=443
```

### 2. 首次获取证书

运行初始化脚本：

```bash
# 给脚本添加执行权限
chmod +x init-cert.sh

# 运行初始化脚本
./init-cert.sh
```

脚本会自动：
- 检查域名解析
- 更新 nginx 配置
- 启动前端服务（用于验证）
- 获取 Let's Encrypt 证书
- 重启服务应用证书

### 3. 启动所有服务

```bash
docker-compose up -d
```

### 4. 验证 HTTPS

访问 `https://yourdomain.com`，应该能看到：
- 浏览器地址栏显示 🔒 锁图标
- 没有安全警告
- 应用正常加载

## 证书自动续期

证书会自动续期，无需手动操作：

- **续期检查**: 每 12 小时自动检查一次
- **续期服务**: `certbot` 容器负责续期
- **续期日志**: `docker-compose logs certbot`

## 手动续期（如果需要）

```bash
docker-compose run --rm certbot certbot renew
docker-compose restart frontend
```

## 故障排查

### 问题 1: 证书获取失败

**错误**: `Failed to verify domains`

**解决方案**:
1. 检查域名是否正确解析到服务器 IP
2. 确保 80 端口开放且未被占用
3. 检查防火墙是否阻止了 Let's Encrypt 的验证请求
4. 确保前端服务正在运行（用于验证）

### 问题 2: 证书路径错误

**错误**: `SSL_CTX_use_certificate_file() failed`

**解决方案**:
1. 检查证书文件是否存在：
   ```bash
   ls -la ssl/certbot/conf/live/yourdomain.com/
   ```
2. 确保 nginx.conf 中的域名与 CERTBOT_DOMAIN 一致
3. 重新运行 `./init-cert.sh`

### 问题 3: 浏览器显示"不安全"

**可能原因**:
1. 证书未正确加载
2. 混合内容（HTTP 和 HTTPS 资源混用）
3. 证书已过期

**解决方案**:
1. 检查证书有效期：`docker-compose exec certbot certbot certificates`
2. 查看 nginx 日志：`docker-compose logs frontend`
3. 检查浏览器控制台的错误信息

### 问题 4: 无法访问 HTTPS

**检查清单**:
- [ ] 443 端口是否开放：`sudo ufw allow 443/tcp`
- [ ] 云服务器安全组是否允许 443 端口
- [ ] 防火墙规则是否正确
- [ ] 服务是否正常运行：`docker-compose ps`

## 证书文件位置

证书文件存储在以下位置：

```
ssl/
└── certbot/
    ├── conf/              # Let's Encrypt 配置和证书
    │   └── live/
    │       └── yourdomain.com/
    │           ├── fullchain.pem  # 完整证书链
    │           └── privkey.pem     # 私钥
    └── www/                # Webroot 验证文件
```

## 安全建议

1. **定期检查证书状态**
   ```bash
   docker-compose exec certbot certbot certificates
   ```

2. **监控证书到期时间**
   - Let's Encrypt 证书有效期为 90 天
   - 自动续期会在到期前 30 天进行

3. **备份证书文件**
   ```bash
   tar -czf ssl-backup-$(date +%Y%m%d).tar.gz ssl/certbot/conf/
   ```

4. **使用强密码保护私钥**
   - 虽然 Let's Encrypt 证书不需要密码，但建议限制文件权限：
   ```bash
   chmod 600 ssl/certbot/conf/live/yourdomain.com/privkey.pem
   ```

## 测试证书

使用以下命令测试 SSL 配置：

```bash
# 检查证书信息
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# 使用 SSL Labs 测试（在线）
# 访问: https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com
```

## 常见问题

### Q: 可以使用自签名证书吗？

A: 可以，但不推荐用于生产环境。自签名证书会导致浏览器显示安全警告。

### Q: 证书续期失败怎么办？

A: 检查日志 `docker-compose logs certbot`，常见原因：
- 域名解析问题
- 80 端口被占用
- Let's Encrypt 速率限制（每小时最多 5 次请求）

### Q: 如何为多个域名配置证书？

A: 修改 `init-cert.sh` 和 `docker-compose.yml`，添加多个 `-d` 参数。

### Q: 证书在哪里存储？

A: 证书存储在 `ssl/certbot/conf/` 目录，通过 Docker volume 挂载到容器中。

## 参考资源

- [Let's Encrypt 官方文档](https://letsencrypt.org/docs/)
- [Certbot 用户指南](https://eff-certbot.readthedocs.io/)
- [Nginx SSL 配置](https://nginx.org/en/docs/http/configuring_https_servers.html)

