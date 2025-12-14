#!/bin/bash

# 修复 certbot 验证路径的脚本

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}修复 certbot 验证路径...${NC}"
echo ""

# 1. 确保目录存在并设置正确权限
echo "1. 创建并设置验证目录权限..."
mkdir -p ssl/certbot/www/.well-known/acme-challenge
chmod -R 755 ssl/certbot/www
echo "  ✓ 目录已创建"
echo ""

# 2. 在前端容器内创建目录
echo "2. 在前端容器内创建目录..."
docker compose exec -T frontend sh << 'EOF'
mkdir -p /var/www/certbot/.well-known/acme-challenge
chmod -R 755 /var/www/certbot
ls -la /var/www/certbot
EOF
echo "  ✓ 容器内目录已创建"
echo ""

# 3. 重新加载 nginx 配置
echo "3. 重新加载 nginx 配置..."
docker compose exec frontend nginx -s reload 2>/dev/null || {
    echo "  重新加载失败，重启容器..."
    docker compose restart frontend
    sleep 3
}
echo "  ✓ Nginx 配置已重新加载"
echo ""

# 4. 测试验证路径
echo "4. 测试验证路径..."
TEST_FILE="ssl/certbot/www/.well-known/acme-challenge/test"
echo "test-content" > "$TEST_FILE"
sleep 2

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://xmem.xchkoo.top/.well-known/acme-challenge/test" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" == "200" ]; then
    echo -e "  ${GREEN}✓ 验证路径可访问 (状态码: $HTTP_CODE)${NC}"
    rm -f "$TEST_FILE"
else
    echo -e "  ${YELLOW}⚠ 验证路径访问异常 (状态码: $HTTP_CODE)${NC}"
    echo "  可能需要检查 nginx 配置"
fi
echo ""

echo -e "${GREEN}修复完成！${NC}"
echo ""
echo "现在可以重新运行证书获取脚本:"
echo "  ./get-cert-simple.sh"
echo ""

