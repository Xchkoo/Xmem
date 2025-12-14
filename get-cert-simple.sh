#!/bin/bash

# 最简单的证书获取脚本 - 直接运行，不依赖复杂配置

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  简单证书获取脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 加载环境变量
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

EMAIL="${CERTBOT_EMAIL:-}"
DOMAIN="${CERTBOT_DOMAIN:-xmem.xchkoo.top}"

if [ -z "$EMAIL" ]; then
    echo -e "${RED}错误: 未设置 CERTBOT_EMAIL${NC}"
    exit 1
fi

echo "邮箱: $EMAIL"
echo "域名: $DOMAIN"
echo ""

# 创建证书目录
mkdir -p ssl/certbot/conf
mkdir -p ssl/certbot/www

# 确保前端服务运行
echo "检查前端服务..."
if ! docker compose ps frontend | grep -q "Up"; then
    echo "启动前端服务..."
    docker compose up -d frontend
    sleep 5
fi
echo "  ✓ 前端服务运行中"
echo ""

# 测试 HTTP 访问
echo "测试 HTTP 访问..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://${DOMAIN}" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" == "200" ]; then
    echo -e "  ${GREEN}✓ HTTP 访问正常${NC}"
else
    echo -e "  ${YELLOW}⚠ HTTP 访问异常 (状态码: $HTTP_CODE)${NC}"
fi
echo ""

# 直接使用 certbot 镜像运行，不依赖 docker-compose 的 certbot 服务
echo -e "${GREEN}开始获取证书...${NC}"
echo "这可能需要几分钟，请耐心等待..."
echo ""

docker run --rm \
    -v "$(pwd)/ssl/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/ssl/certbot/www:/var/www/certbot" \
    --network xmem_default \
    certbot/certbot:latest \
    certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    -d "$DOMAIN" \
    --verbose || {
    echo ""
    echo -e "${RED}证书获取失败${NC}"
    echo ""
    echo "常见问题排查："
    echo "  1. 检查域名解析: ping $DOMAIN"
    echo "  2. 检查 HTTP 访问: curl -I http://$DOMAIN"
    echo "  3. 检查验证路径: curl http://$DOMAIN/.well-known/acme-challenge/test"
    echo "  4. 查看详细日志: docker logs <certbot-container-id>"
    echo ""
    exit 1
}

echo ""
echo -e "${GREEN}✓ 证书获取成功！${NC}"
echo ""
echo "证书位置:"
echo "  ssl/certbot/conf/live/$DOMAIN/"
echo ""
echo "现在运行以下命令启用 HTTPS:"
echo "  ./enable-https.sh"
echo ""

