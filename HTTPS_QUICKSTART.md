# HTTPS 快速开始指南

## 📋 前置条件

1. ✅ 域名已解析到服务器 IP
2. ✅ 服务器开放 80 和 443 端口
3. ✅ 已安装 Docker 和 Docker Compose

## 🚀 三步完成 HTTPS 配置

### 步骤 1: 配置环境变量

在项目根目录的 `.env` 文件中添加：

```bash
CERTBOT_EMAIL=admin@yourdomain.com
CERTBOT_DOMAIN=yourdomain.com
FRONTEND_HTTPS_PORT=443
```

### 步骤 2: 获取 SSL 证书

在服务器上运行：

```bash
chmod +x init-cert.sh
./init-cert.sh
```

脚本会自动：
- ✅ 检查域名解析
- ✅ 获取 Let's Encrypt 证书
- ✅ 配置 Nginx

### 步骤 3: 启动服务

```bash
docker-compose up -d
```

## ✅ 验证

访问 `https://yourdomain.com`，应该看到：
- 🔒 浏览器显示安全锁图标
- ✅ 没有安全警告
- ✅ 应用正常加载

## 🔄 证书自动续期

证书会自动续期，无需手动操作：
- 每 12 小时自动检查一次
- 到期前 30 天自动续期
- 查看日志：`docker-compose logs certbot`

## ❓ 常见问题

### 证书获取失败？

1. 检查域名解析：`dig yourdomain.com`
2. 检查 80 端口：`sudo netstat -tlnp | grep :80`
3. 检查防火墙：`sudo ufw status`

### 浏览器显示"不安全"？

1. 检查证书是否存在：
   ```bash
   ls -la ssl/certbot/conf/live/yourdomain.com/
   ```
2. 查看 Nginx 日志：`docker-compose logs frontend`
3. 重启服务：`docker-compose restart frontend`

### 需要帮助？

查看详细文档：`HTTPS_SETUP.md`

