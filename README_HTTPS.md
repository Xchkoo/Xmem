# HTTPS 配置指南

## 证书获取方式

### 方式 1：使用 Let's Encrypt 免费证书（推荐）

Let's Encrypt 提供免费的 SSL 证书，有效期 90 天，会自动续期。

#### 前置条件

1. **域名已解析到服务器 IP**
   ```bash
   # 检查域名解析
   nslookup yourdomain.com
   # 应该返回你的服务器 IP
   ```

2. **80 和 443 端口已开放**
   ```bash
   # 检查端口
   sudo ufw status
   # 或云服务器安全组配置
   ```

3. **设置环境变量**
   
   在项目根目录的 `.env` 文件中添加：
   ```env
   CERTBOT_EMAIL=your-email@example.com
   CERTBOT_DOMAIN=yourdomain.com
   FRONTEND_HTTPS_PORT=443
   ```

#### 首次获取证书

**方法 A：使用初始化脚本（推荐）**

```bash
# 1. 设置环境变量
export CERTBOT_EMAIL=your-email@example.com
export CERTBOT_DOMAIN=yourdomain.com

# 2. 运行初始化脚本
chmod +x init-cert.sh
./init-cert.sh

# 3. 启动服务
docker-compose up -d
```

**方法 B：手动获取证书**

```bash
# 1. 先启动前端服务（用于证书验证）
docker-compose up -d frontend

# 2. 获取证书
docker run --rm \
    -v "$(pwd)/ssl/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/ssl/certbot/www:/var/www/certbot" \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email \
    -d yourdomain.com \
    -d www.yourdomain.com

# 3. 创建证书软链接
mkdir -p ssl/live
ln -sf ssl/certbot/conf/live/yourdomain.com/fullchain.pem ssl/live/fullchain.pem
ln -sf ssl/certbot/conf/live/yourdomain.com/privkey.pem ssl/live/privkey.pem

# 4. 重启服务
docker-compose restart frontend
```

#### 证书自动续期

`docker-compose.yml` 中已配置 `certbot` 服务，会自动：
- 每 12 小时检查一次证书
- 证书到期前 30 天自动续期
- 续期后需要手动重启 nginx（或使用 webhook）

**自动续期并重启 nginx：**

如果需要续期后自动重启 nginx，可以修改 `docker-compose.yml` 中的 certbot 服务：

```yaml
certbot:
  # ... existing code ...
  entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew --webroot --webroot-path=/var/www/certbot --deploy-hook \"docker exec frontend-1 nginx -s reload\" --quiet; sleep 12h & wait $${!}; done;'"
```

### 方式 2：使用自签名证书（仅测试用）

如果暂时没有域名，可以使用自签名证书（浏览器会显示警告）：

```bash
# 生成自签名证书
mkdir -p ssl/live
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/live/privkey.pem \
  -out ssl/live/fullchain.pem \
  -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"

# 启动服务
docker-compose up -d
```

**注意：** 自签名证书浏览器会显示"不安全"警告，仅用于测试。

### 方式 3：使用商业证书

如果你有商业 SSL 证书：

```bash
# 1. 将证书文件放到 ssl/live/ 目录
mkdir -p ssl/live
cp your-certificate.crt ssl/live/fullchain.pem
cp your-private-key.key ssl/live/privkey.pem

# 2. 启动服务
docker-compose up -d
```

## 验证 HTTPS

### 1. 检查证书

```bash
# 检查证书信息
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

### 2. 测试访问

```bash
# 测试 HTTPS
curl https://yourdomain.com/api/health

# 测试 HTTP 重定向
curl -I http://yourdomain.com
# 应该返回 301 重定向到 HTTPS
```

### 3. 浏览器访问

访问 `https://yourdomain.com`，应该看到：
- 地址栏显示锁图标
- 证书信息正确
- 可以正常登录（`crypto.subtle` 可用）

## 故障排查

### 证书获取失败

1. **检查域名解析**
   ```bash
   nslookup yourdomain.com
   ```

2. **检查端口开放**
   ```bash
   # 检查 80 端口是否开放
   sudo netstat -tlnp | grep :80
   ```

3. **检查防火墙**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

4. **查看 certbot 日志**
   ```bash
   docker-compose logs certbot
   ```

### Nginx 无法找到证书

1. **检查证书文件是否存在**
   ```bash
   ls -la ssl/live/
   ```

2. **检查文件权限**
   ```bash
   chmod 644 ssl/live/fullchain.pem
   chmod 600 ssl/live/privkey.pem
   ```

3. **检查 docker-compose 挂载**
   ```bash
   docker-compose exec frontend ls -la /etc/nginx/ssl/live/
   ```

### 证书续期失败

1. **手动测试续期**
   ```bash
   docker-compose exec certbot certbot renew --dry-run
   ```

2. **检查证书有效期**
   ```bash
   openssl x509 -in ssl/live/fullchain.pem -noout -dates
   ```

## 目录结构

```
项目根目录/
├── ssl/
│   ├── certbot/
│   │   ├── conf/          # Let's Encrypt 配置和证书
│   │   └── www/           # Webroot 验证目录
│   └── live/              # Nginx 使用的证书（软链接）
├── init-cert.sh           # 证书初始化脚本
└── docker-compose.yml
```

## 安全建议

1. **定期检查证书有效期**
   ```bash
   openssl x509 -in ssl/live/fullchain.pem -noout -dates
   ```

2. **监控证书续期**
   - 设置邮件通知（CERTBOT_EMAIL）
   - 监控 certbot 容器日志

3. **备份证书**
   ```bash
   tar -czf ssl-backup-$(date +%Y%m%d).tar.gz ssl/
   ```

4. **使用强密码保护私钥**
   - 生产环境建议使用带密码的私钥

## 常见问题

**Q: 证书多久续期一次？**  
A: Let's Encrypt 证书有效期 90 天，certbot 会在到期前 30 天自动续期。

**Q: 续期需要停机吗？**  
A: 不需要，certbot 使用 webroot 方式验证，不需要停止服务。

**Q: 可以同时支持多个域名吗？**  
A: 可以，在 `init-cert.sh` 或 certbot 命令中添加多个 `-d` 参数。

**Q: 本地开发环境怎么办？**  
A: 本地开发可以使用 HTTP（localhost 不受限制），或使用自签名证书。

