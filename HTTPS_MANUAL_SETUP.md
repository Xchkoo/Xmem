# HTTPS 手动配置指南

## 前置条件

1. 域名已解析到服务器 IP
2. 服务器开放 80 和 443 端口
3. Docker 和 Docker Compose 已安装

## 步骤 1: 配置环境变量

在项目根目录的 `.env` 文件中设置：

```bash
CERTBOT_EMAIL=your-email@example.com
CERTBOT_DOMAIN=yourdomain.com
FRONTEND_HTTPS_PORT=443
```

## 步骤 2: 创建证书目录

```bash
mkdir -p ssl/certbot/conf
mkdir -p ssl/certbot/www/.well-known/acme-challenge
chmod -R 755 ssl/
```

## 步骤 3: 确保前端服务运行（HTTP-only 模式）

前端服务应该已经在运行（使用简化的 HTTP-only 配置）。

检查服务状态：
```bash
docker compose ps frontend
```

如果未运行，启动它：
```bash
docker compose up -d frontend
```

## 步骤 4: 验证前端配置

进入前端容器检查配置：
```bash
docker compose exec frontend cat /etc/nginx/conf.d/default.conf
```

应该看到包含以下内容的配置：
```nginx
location /.well-known/acme-challenge/ {
    root /var/www/certbot;
    allow all;
    default_type text/plain;
    try_files $uri =404;
}
```

如果没有 `allow all;`，需要重新构建前端镜像：
```bash
docker compose build frontend
docker compose restart frontend
```

## 步骤 5: 测试验证路径

在容器内创建测试文件：
```bash
docker compose exec frontend sh -c "mkdir -p /var/www/certbot/.well-known/acme-challenge && chmod -R 755 /var/www/certbot"
echo "test" > ssl/certbot/www/.well-known/acme-challenge/test
```

测试访问：
```bash
curl http://yourdomain.com/.well-known/acme-challenge/test
```

应该返回 "test" 内容（200 状态码），而不是 403。

## 步骤 6: 获取 SSL 证书

使用 certbot 直接获取证书：

```bash
docker run --rm \
    -v "$(pwd)/ssl/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/ssl/certbot/www:/var/www/certbot" \
    --network xmem_default \
    certbot/certbot:latest \
    certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    -d yourdomain.com \
    --verbose
```

**重要参数说明：**
- `--webroot`: 使用 webroot 验证方式
- `--webroot-path=/var/www/certbot`: 验证文件存放路径
- `--email`: 你的邮箱（用于接收证书到期通知）
- `-d yourdomain.com`: 你的域名
- `--verbose`: 显示详细日志

## 步骤 7: 验证证书

证书获取成功后，检查证书文件：

```bash
ls -la ssl/certbot/conf/live/yourdomain.com/
```

应该看到：
- `fullchain.pem` - 完整证书链
- `privkey.pem` - 私钥

## 步骤 8: 启用 HTTPS

证书获取成功后，重启前端服务以启用 HTTPS：

```bash
docker compose restart frontend
```

前端服务会自动检测到证书存在，使用完整的 HTTPS 配置。

## 步骤 9: 验证 HTTPS

访问你的网站：
```bash
curl -I https://yourdomain.com
```

应该返回 200 状态码，浏览器访问应该显示安全锁图标。

## 故障排查

### 问题 1: 证书获取失败，返回 403

**原因**: 验证路径配置不正确或权限问题

**解决**:
1. 检查 nginx 配置是否包含 `allow all;`
2. 检查目录权限：`docker compose exec frontend ls -la /var/www/certbot`
3. 重新构建前端镜像：`docker compose build frontend`

### 问题 2: 证书获取失败，返回连接错误

**原因**: 域名未正确解析或 80 端口未开放

**解决**:
1. 检查域名解析：`ping yourdomain.com`
2. 检查 80 端口：`curl -I http://yourdomain.com`
3. 检查防火墙：`sudo ufw status`

### 问题 3: 前端服务无法启动（证书不存在）

**原因**: 前端配置要求证书存在才能启动

**解决**: 前端服务已经配置为在证书不存在时使用 HTTP-only 模式，应该可以正常启动。

### 问题 4: 证书续期

证书会自动续期（通过 docker-compose.yml 中的 certbot 服务）。

手动续期：
```bash
docker run --rm \
    -v "$(pwd)/ssl/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/ssl/certbot/www:/var/www/certbot" \
    --network xmem_default \
    certbot/certbot:latest \
    renew
```

续期后重启前端：
```bash
docker compose restart frontend
```

## 配置文件位置

- **Nginx 配置**: `frontend/nginx.conf`
- **启动脚本**: `frontend/docker-entrypoint.sh`
- **证书目录**: `ssl/certbot/conf/live/yourdomain.com/`
- **验证文件目录**: `ssl/certbot/www/.well-known/acme-challenge/`

## 注意事项

1. 证书有效期为 90 天，会自动续期
2. 首次获取证书后，需要重启前端服务
3. 确保 `.env` 文件中的 `CERTBOT_DOMAIN` 与你的域名一致
4. 如果修改了域名，需要重新获取证书

