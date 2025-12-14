#!/bin/bash

# SSL 证书初始化脚本
# 用于首次获取 Let's Encrypt SSL 证书

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  SSL 证书初始化脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 加载 .env 文件中的环境变量
if [ -f .env ]; then
    echo "从 .env 文件加载环境变量..."
    # 使用 set -a 自动导出所有变量，忽略注释和空行
    set -a
    source .env
    set +a
    echo "  ✓ .env 文件已加载"
else
    echo -e "${YELLOW}警告: 未找到 .env 文件${NC}"
    echo "将使用系统环境变量"
fi
echo ""

# 检查环境变量
if [ -z "$CERTBOT_EMAIL" ]; then
    echo -e "${RED}错误: 未设置 CERTBOT_EMAIL 环境变量${NC}"
    echo "请在 .env 文件中设置 CERTBOT_EMAIL=your-email@example.com"
    echo "或者使用: export CERTBOT_EMAIL=your-email@example.com"
    exit 1
fi

if [ -z "$CERTBOT_DOMAIN" ]; then
    echo -e "${RED}错误: 未设置 CERTBOT_DOMAIN 环境变量${NC}"
    echo "请在 .env 文件中设置 CERTBOT_DOMAIN=yourdomain.com"
    echo "或者使用: export CERTBOT_DOMAIN=yourdomain.com"
    exit 1
fi

echo -e "${YELLOW}配置信息:${NC}"
echo "  邮箱: $CERTBOT_EMAIL"
echo "  域名: $CERTBOT_DOMAIN"
echo ""

# 创建必要的目录
echo "创建证书目录..."
mkdir -p ssl/certbot/conf
mkdir -p ssl/certbot/www

# 检查域名是否解析到当前服务器
echo "检查域名解析..."
SERVER_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "unknown")

# 尝试多种方法解析域名（按优先级）
DOMAIN_IP=""
if command -v dig >/dev/null 2>&1; then
    DOMAIN_IP=$(dig +short $CERTBOT_DOMAIN 2>/dev/null | tail -n1)
elif command -v nslookup >/dev/null 2>&1; then
    DOMAIN_IP=$(nslookup $CERTBOT_DOMAIN 2>/dev/null | grep -A 1 "Name:" | tail -n1 | awk '{print $2}')
elif command -v host >/dev/null 2>&1; then
    DOMAIN_IP=$(host $CERTBOT_DOMAIN 2>/dev/null | grep -oP 'has address \K[0-9.]+' | head -n1)
elif command -v getent >/dev/null 2>&1; then
    DOMAIN_IP=$(getent hosts $CERTBOT_DOMAIN 2>/dev/null | awk '{print $1}' | head -n1)
elif command -v ping >/dev/null 2>&1; then
    # 使用 ping 作为最后备选（只获取 IP，不实际发送数据包）
    DOMAIN_IP=$(ping -c 1 -W 1 $CERTBOT_DOMAIN 2>/dev/null | grep PING | awk '{print $3}' | tr -d '()')
fi

if [ -z "$DOMAIN_IP" ]; then
    echo -e "${YELLOW}警告: 无法解析域名 $CERTBOT_DOMAIN${NC}"
    echo "请确保域名已正确解析到服务器 IP: $SERVER_IP"
    echo "提示: 可以使用 'ping $CERTBOT_DOMAIN' 手动检查"
    read -p "是否继续? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "  域名 $CERTBOT_DOMAIN 解析到: $DOMAIN_IP"
    echo "  服务器 IP: $SERVER_IP"
    if [ "$DOMAIN_IP" != "$SERVER_IP" ] && [ "$SERVER_IP" != "unknown" ]; then
        echo -e "${YELLOW}警告: 域名解析的 IP 与服务器 IP 不匹配${NC}"
        echo "Let's Encrypt 验证可能会失败"
        read -p "是否继续? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    elif [ "$DOMAIN_IP" == "$SERVER_IP" ]; then
        echo -e "${GREEN}  ✓ 域名解析正确${NC}"
    fi
fi

# 注意：nginx.conf 会在容器启动时自动更新（通过 docker-entrypoint.sh）
echo "nginx.conf 将在容器启动时自动更新"

# 确保前端服务正在运行（用于验证）
echo ""
echo "检查前端服务..."
if ! docker compose ps frontend | grep -q "Up"; then
    echo "启动前端服务（用于证书验证）..."
    docker compose up -d frontend
    echo "等待服务启动..."
    sleep 5
fi

# 获取证书（仅主域名，不包含 www 子域名）
echo ""
echo -e "${GREEN}开始获取 SSL 证书...${NC}"
echo -e "${YELLOW}注意: 仅获取主域名证书，不包含 www 子域名${NC}"
echo "这可能需要几分钟，请耐心等待..."
echo ""

# 直接使用 certbot 镜像，不依赖 docker-compose 的 certbot 服务
docker run --rm \
    -v "$(pwd)/ssl/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/ssl/certbot/www:/var/www/certbot" \
    --network xmem_default \
    certbot/certbot:latest \
    certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$CERTBOT_EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    -d "$CERTBOT_DOMAIN" \
    --verbose || {
    echo ""
    echo -e "${RED}证书获取失败${NC}"
    echo ""
    echo "请尝试以下排查步骤："
    echo "  1. 检查域名解析: ping $CERTBOT_DOMAIN"
    echo "  2. 检查 HTTP 访问: curl -I http://$CERTBOT_DOMAIN"
    echo "  3. 检查验证路径: curl http://$CERTBOT_DOMAIN/.well-known/acme-challenge/test"
    echo "  4. 查看前端日志: docker compose logs frontend"
    echo ""
    echo "或者使用更简单的脚本: ./get-cert-simple.sh"
    exit 1
}

echo ""
echo -e "${GREEN}✓ 证书获取成功！${NC}"
echo ""
echo "证书位置:"
echo "  - 证书文件: ssl/certbot/conf/live/$CERTBOT_DOMAIN/fullchain.pem"
echo "  - 私钥文件: ssl/certbot/conf/live/$CERTBOT_DOMAIN/privkey.pem"
echo ""
echo "重启服务以应用证书..."
docker compose restart frontend

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  证书初始化完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "现在可以通过 https://$CERTBOT_DOMAIN 访问你的应用了"
echo ""
echo "注意: 证书会自动续期（每 12 小时检查一次）"
