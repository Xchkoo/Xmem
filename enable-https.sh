#!/bin/bash

# 启用 HTTPS 脚本 - 证书获取后使用

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  启用 HTTPS${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 加载环境变量
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

DOMAIN="${CERTBOT_DOMAIN:-xmem.xchkoo.top}"
CERT_PATH="ssl/certbot/conf/live/${DOMAIN}/fullchain.pem"

# 检查证书是否存在
if [ ! -f "$CERT_PATH" ]; then
    echo -e "${RED}错误: 证书文件不存在: $CERT_PATH${NC}"
    echo "请先运行 ./init-cert.sh 获取证书"
    exit 1
fi

echo -e "${GREEN}✓ 证书文件存在${NC}"
echo ""

# 恢复原始配置
echo "1. 恢复原始 HTTPS 配置..."
if [ -f frontend/nginx.conf.backup ]; then
    cp frontend/nginx.conf.backup frontend/nginx.conf
    echo "  ✓ 已恢复原始配置"
else
    echo -e "  ${YELLOW}⚠ 未找到备份配置，使用当前配置${NC}"
fi
echo ""

# 恢复原始启动脚本
echo "2. 恢复原始启动脚本..."
# docker-entrypoint.sh 会自动检测证书并启用 HTTPS
if [ -f frontend/docker-entrypoint.sh.backup ]; then
    cp frontend/docker-entrypoint.sh.backup frontend/docker-entrypoint.sh
    echo "  ✓ 已恢复原始启动脚本"
else
    # 创建支持证书检测的启动脚本
    cat > frontend/docker-entrypoint.sh << 'EOF'
#!/bin/sh
# Nginx 启动脚本 - 自动检测证书

set -e

DOMAIN="${CERTBOT_DOMAIN:-xmem.xchkoo.top}"
CERT_PATH="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"

if [ -f "$CERT_PATH" ]; then
    echo "✓ 证书存在，启用 HTTPS"
else
    echo "警告: 证书不存在，将使用 HTTP-only 模式"
    # 如果证书不存在，使用简化配置
    if [ -f /etc/nginx/conf.d/default-simple.conf ]; then
        cp /etc/nginx/conf.d/default-simple.conf /etc/nginx/conf.d/default.conf
    fi
fi

exec nginx -g "daemon off;"
EOF
    chmod +x frontend/docker-entrypoint.sh
    echo "  ✓ 已创建新的启动脚本"
fi
echo ""

# 重新构建前端镜像（如果需要）
echo "3. 重新构建前端镜像..."
docker compose build frontend
echo "  ✓ 镜像构建完成"
echo ""

# 重启前端服务
echo "4. 重启前端服务..."
docker compose up -d frontend
echo "  等待服务启动..."
sleep 5

# 检查服务状态
if docker compose ps frontend | grep -q "Up"; then
    echo -e "  ${GREEN}✓ 前端服务已启动${NC}"
else
    echo -e "  ${RED}✗ 前端服务启动失败${NC}"
    echo "  查看日志: docker compose logs frontend"
    exit 1
fi
echo ""

# 测试 HTTPS 访问
echo "5. 测试 HTTPS 访问..."
HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 -k "https://${DOMAIN}" 2>/dev/null || echo "000")
if [ "$HTTPS_CODE" == "200" ] || [ "$HTTPS_CODE" == "301" ] || [ "$HTTPS_CODE" == "302" ]; then
    echo -e "  ${GREEN}✓ HTTPS 访问正常 (状态码: $HTTPS_CODE)${NC}"
else
    echo -e "  ${YELLOW}⚠ HTTPS 访问异常 (状态码: $HTTPS_CODE)${NC}"
    echo "  查看日志: docker compose logs frontend"
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  HTTPS 已启用！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "现在可以通过 https://${DOMAIN} 访问你的应用了"
echo ""

