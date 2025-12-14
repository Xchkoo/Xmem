#!/bin/bash

# SSL 证书获取失败诊断脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  SSL 证书获取失败诊断工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 加载环境变量
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

DOMAIN="${CERTBOT_DOMAIN:-}"
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}错误: 未设置 CERTBOT_DOMAIN${NC}"
    exit 1
fi

echo -e "${YELLOW}检查域名: $DOMAIN${NC}"
echo ""

# 1. 检查域名解析
echo -e "${BLUE}[1] 检查域名解析...${NC}"
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "unknown")
DOMAIN_IP=""

if command -v ping >/dev/null 2>&1; then
    DOMAIN_IP=$(ping -c 1 -W 1 $DOMAIN 2>/dev/null | grep PING | awk '{print $3}' | tr -d '()')
fi

if [ -n "$DOMAIN_IP" ]; then
    echo "  域名解析 IP: $DOMAIN_IP"
    echo "  服务器 IP: $SERVER_IP"
    if [ "$DOMAIN_IP" == "$SERVER_IP" ]; then
        echo -e "  ${GREEN}✓ 域名解析正确${NC}"
    else
        echo -e "  ${RED}✗ 域名解析 IP 与服务器 IP 不匹配${NC}"
        echo "  这可能是主要问题！"
    fi
else
    echo -e "  ${RED}✗ 无法解析域名${NC}"
fi
echo ""

# 2. 检查 80 端口
echo -e "${BLUE}[2] 检查 80 端口...${NC}"
if sudo netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    PORT_INFO=$(sudo netstat -tlnp 2>/dev/null | grep ":80 ")
    echo "  80 端口状态: 已监听"
    echo "  详细信息: $PORT_INFO"
    
    # 检查是否是 Docker 容器
    if echo "$PORT_INFO" | grep -q "docker"; then
        echo -e "  ${GREEN}✓ 端口由 Docker 容器监听${NC}"
    else
        echo -e "  ${YELLOW}⚠ 端口被其他进程占用（非 Docker）${NC}"
    fi
else
    echo -e "  ${RED}✗ 80 端口未监听${NC}"
    echo "  这是主要问题！Let's Encrypt 需要通过 80 端口验证域名"
fi
echo ""

# 3. 检查前端服务
echo -e "${BLUE}[3] 检查前端服务...${NC}"
if docker compose ps frontend 2>/dev/null | grep -q "Up"; then
    echo -e "  ${GREEN}✓ 前端服务运行中${NC}"
    FRONTEND_STATUS=$(docker compose ps frontend 2>/dev/null | grep frontend)
    echo "  状态: $FRONTEND_STATUS"
else
    echo -e "  ${RED}✗ 前端服务未运行${NC}"
    echo "  尝试启动前端服务..."
    docker compose up -d frontend 2>/dev/null || echo "  启动失败"
fi
echo ""

# 4. 检查 HTTP 访问
echo -e "${BLUE}[4] 检查 HTTP 访问...${NC}"
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://$DOMAIN" 2>/dev/null || echo "000")
if [ "$HTTP_RESPONSE" == "200" ] || [ "$HTTP_RESPONSE" == "301" ] || [ "$HTTP_RESPONSE" == "302" ]; then
    echo -e "  ${GREEN}✓ HTTP 访问正常 (状态码: $HTTP_RESPONSE)${NC}"
elif [ "$HTTP_RESPONSE" == "000" ]; then
    echo -e "  ${RED}✗ 无法访问 HTTP (连接失败)${NC}"
    echo "  可能原因: 防火墙阻止、服务未运行、端口未开放"
else
    echo -e "  ${YELLOW}⚠ HTTP 访问异常 (状态码: $HTTP_RESPONSE)${NC}"
fi

# 检查 Let's Encrypt 验证路径
ACME_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://$DOMAIN/.well-known/acme-challenge/test" 2>/dev/null || echo "000")
echo "  ACME 验证路径测试: $ACME_RESPONSE (404 是正常的，说明路径可访问)"
echo ""

# 5. 检查防火墙
echo -e "${BLUE}[5] 检查防火墙...${NC}"
if command -v ufw >/dev/null 2>&1; then
    UFW_STATUS=$(sudo ufw status 2>/dev/null | head -n1 || echo "unknown")
    echo "  UFW 状态: $UFW_STATUS"
    if echo "$UFW_STATUS" | grep -qi "active"; then
        if sudo ufw status 2>/dev/null | grep -q "80/tcp"; then
            echo -e "  ${GREEN}✓ 80 端口已在防火墙规则中${NC}"
        else
            echo -e "  ${RED}✗ 80 端口未在防火墙规则中${NC}"
            echo "  需要运行: sudo ufw allow 80/tcp"
        fi
    fi
elif command -v iptables >/dev/null 2>&1; then
    if sudo iptables -L -n 2>/dev/null | grep -q "80"; then
        echo "  防火墙规则中包含 80 端口"
    else
        echo -e "  ${YELLOW}⚠ 未检测到 80 端口防火墙规则${NC}"
    fi
else
    echo "  未检测到常见防火墙工具"
fi
echo ""

# 6. 检查 Docker 网络
echo -e "${BLUE}[6] 检查 Docker 网络...${NC}"
if docker network ls 2>/dev/null | grep -q "xmem"; then
    echo -e "  ${GREEN}✓ Docker 网络存在${NC}"
else
    echo -e "  ${YELLOW}⚠ 未找到 xmem 网络${NC}"
fi

# 检查前端容器网络
FRONTEND_IP=$(docker compose ps -q frontend 2>/dev/null | xargs docker inspect 2>/dev/null | grep -oP '"IPAddress": "\K[^"]+' | head -n1 || echo "")
if [ -n "$FRONTEND_IP" ]; then
    echo "  前端容器 IP: $FRONTEND_IP"
fi
echo ""

# 7. 检查证书目录权限
echo -e "${BLUE}[7] 检查证书目录...${NC}"
if [ -d "ssl/certbot/conf" ]; then
    echo "  证书目录存在"
    if [ -d "ssl/certbot/conf/live/$DOMAIN" ]; then
        echo "  证书目录已存在: ssl/certbot/conf/live/$DOMAIN"
        ls -la "ssl/certbot/conf/live/$DOMAIN/" 2>/dev/null || echo "  无法列出文件（权限问题）"
    else
        echo "  证书目录不存在（首次获取）"
    fi
    
    # 检查权限
    if [ -w "ssl/certbot/conf" ]; then
        echo -e "  ${GREEN}✓ 证书目录可写${NC}"
    else
        echo -e "  ${RED}✗ 证书目录不可写${NC}"
        echo "  需要运行: chmod -R 755 ssl/"
    fi
else
    echo -e "  ${YELLOW}⚠ 证书目录不存在${NC}"
fi
echo ""

# 8. 检查 Let's Encrypt 连接
echo -e "${BLUE}[8] 检查 Let's Encrypt 连接...${NC}"
ACME_TEST=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "https://acme-v02.api.letsencrypt.org/directory" 2>/dev/null || echo "000")
if [ "$ACME_TEST" == "200" ]; then
    echo -e "  ${GREEN}✓ 可以连接到 Let's Encrypt API${NC}"
else
    echo -e "  ${RED}✗ 无法连接到 Let's Encrypt API (状态码: $ACME_TEST)${NC}"
    echo "  可能原因: 网络问题、防火墙阻止 HTTPS 出站"
fi
echo ""

# 9. 检查最近的证书获取日志
echo -e "${BLUE}[9] 检查证书获取日志...${NC}"
if docker compose logs certbot 2>/dev/null | tail -n 20 | grep -q "error\|Error\|ERROR\|failed\|Failed"; then
    echo -e "  ${RED}发现错误日志:${NC}"
    docker compose logs certbot 2>/dev/null | tail -n 20 | grep -i "error\|failed" | head -n 5
else
    echo "  未发现明显错误（查看完整日志: docker compose logs certbot）"
fi
echo ""

# 10. 生成诊断报告
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  诊断总结${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

ISSUES=0

if [ "$DOMAIN_IP" != "$SERVER_IP" ] && [ -n "$DOMAIN_IP" ]; then
    echo -e "${RED}[问题] 域名解析 IP 与服务器 IP 不匹配${NC}"
    echo "  解决: 确保域名 A 记录指向 $SERVER_IP"
    ISSUES=$((ISSUES + 1))
fi

if ! sudo netstat -tlnp 2>/dev/null | grep -q ":80 "; then
    echo -e "${RED}[问题] 80 端口未监听${NC}"
    echo "  解决: 确保前端服务运行 (docker compose up -d frontend)"
    ISSUES=$((ISSUES + 1))
fi

if [ "$HTTP_RESPONSE" == "000" ]; then
    echo -e "${RED}[问题] 无法通过 HTTP 访问域名${NC}"
    echo "  解决: 检查防火墙、服务状态、端口映射"
    ISSUES=$((ISSUES + 1))
fi

if [ "$ACME_TEST" != "200" ]; then
    echo -e "${YELLOW}[警告] 无法连接到 Let's Encrypt API${NC}"
    echo "  可能影响证书获取"
    ISSUES=$((ISSUES + 1))
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}未发现明显问题${NC}"
    echo ""
    echo "建议:"
    echo "  1. 查看详细日志: docker compose logs certbot"
    echo "  2. 手动测试证书获取:"
    echo "     docker compose run --rm certbot certbot certonly --webroot \\"
    echo "       --webroot-path=/var/www/certbot \\"
    echo "       --email $CERTBOT_EMAIL \\"
    echo "       --agree-tos --no-eff-email \\"
    echo "       -d $DOMAIN -d www.$DOMAIN --dry-run"
else
    echo ""
    echo -e "${YELLOW}发现 $ISSUES 个潜在问题，请先解决这些问题${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"

