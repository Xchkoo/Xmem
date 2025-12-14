#!/bin/bash

# 一键修复并获取证书脚本

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  修复配置并获取证书${NC}"
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

echo "1. 重新构建前端镜像（应用新配置）..."
docker compose build frontend
echo "  ✓ 镜像构建完成"
echo ""

echo "2. 重启前端服务..."
docker compose up -d frontend
echo "  等待服务启动..."
sleep 5
echo "  ✓ 服务已启动"
echo ""

echo "3. 创建验证目录..."
docker compose exec -T frontend sh << 'EOF'
mkdir -p /var/www/certbot/.well-known/acme-challenge
chmod -R 755 /var/www/certbot
EOF
echo "  ✓ 目录已创建"
echo ""

echo "4. 验证配置..."
CONFIG_CHECK=$(docker compose exec -T frontend cat /etc/nginx/conf.d/default.conf | grep -A 3 "acme-challenge" | grep -c "allow all" || echo "0")
if [ "$CONFIG_CHECK" -gt 0 ]; then
    echo -e "  ${GREEN}✓ 配置已更新（包含 allow all）${NC}"
else
    echo -e "  ${YELLOW}⚠ 配置可能未更新，但继续尝试...${NC}"
fi
echo ""

echo "5. 测试验证路径..."
echo "test-content-$(date +%s)" > ssl/certbot/www/.well-known/acme-challenge/test
sleep 2

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${DOMAIN}/.well-known/acme-challenge/test" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" == "200" ]; then
    echo -e "  ${GREEN}✓ 验证路径可访问 (状态码: $HTTP_CODE)${NC}"
    rm -f ssl/certbot/www/.well-known/acme-challenge/test
elif [ "$HTTP_CODE" == "404" ]; then
    echo -e "  ${YELLOW}⚠ 返回 404（可能是文件不存在，但路径可访问）${NC}"
else
    echo -e "  ${RED}✗ 验证路径访问异常 (状态码: $HTTP_CODE)${NC}"
    echo "  可能需要检查 nginx 配置和权限"
fi
echo ""

echo "6. 获取证书..."
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
    echo "请检查："
    echo "  1. 验证路径配置: docker compose exec frontend cat /etc/nginx/conf.d/default.conf | grep -A 5 acme"
    echo "  2. 目录权限: docker compose exec frontend ls -la /var/www/certbot"
    echo "  3. 测试访问: curl http://${DOMAIN}/.well-known/acme-challenge/test"
    echo ""
    exit 1
}

echo ""
echo -e "${GREEN}✓ 证书获取成功！${NC}"
echo ""
echo "证书位置: ssl/certbot/conf/live/$DOMAIN/"
echo ""
echo "现在运行以下命令启用 HTTPS:"
echo "  ./enable-https.sh"
echo ""

