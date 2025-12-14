#!/bin/bash

# 重置 HTTPS 配置脚本 - 从头开始

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  重置 HTTPS 配置${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 1. 停止所有服务
echo "1. 停止所有服务..."
docker compose down
echo "  ✓ 服务已停止"
echo ""

# 2. 创建简化的 HTTP-only nginx 配置
echo "2. 创建简化的 HTTP-only 配置..."
cat > frontend/nginx-simple.conf << 'EOF'
# 简化的 HTTP-only 配置（用于证书获取）
server {
    listen 80;
    server_name _;
    
    root /usr/share/nginx/html;
    
    # Let's Encrypt 验证路径
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # 前端静态文件
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # 后端 API 代理
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_http_version 1.1;
    }
}
EOF
echo "  ✓ 已创建简化配置"
echo ""

# 3. 临时替换 nginx.conf
echo "3. 备份原配置并应用简化配置..."
if [ -f frontend/nginx.conf ]; then
    cp frontend/nginx.conf frontend/nginx.conf.backup
    echo "  ✓ 已备份原配置到 nginx.conf.backup"
fi
cp frontend/nginx-simple.conf frontend/nginx.conf
echo "  ✓ 已应用简化配置"
echo ""

# 4. 修改 docker-entrypoint.sh 使其不检查证书
echo "4. 修改启动脚本（跳过证书检查）..."
cat > frontend/docker-entrypoint-simple.sh << 'EOF'
#!/bin/sh
# 简化的启动脚本 - 不检查证书

set -e

echo "使用简化的 HTTP-only 配置启动 Nginx"
exec nginx -g "daemon off;"
EOF
chmod +x frontend/docker-entrypoint-simple.sh
cp frontend/docker-entrypoint-simple.sh frontend/docker-entrypoint.sh
echo "  ✓ 已修改启动脚本"
echo ""

# 5. 启动前端服务
echo "5. 启动前端服务（HTTP-only 模式）..."
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

# 6. 测试 HTTP 访问
echo "6. 测试 HTTP 访问..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://localhost" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "301" ] || [ "$HTTP_CODE" == "302" ]; then
    echo -e "  ${GREEN}✓ HTTP 访问正常 (状态码: $HTTP_CODE)${NC}"
else
    echo -e "  ${YELLOW}⚠ HTTP 访问异常 (状态码: $HTTP_CODE)${NC}"
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  重置完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "下一步："
echo "  1. 运行证书获取脚本: ./init-cert.sh"
echo "  2. 证书获取成功后，运行: ./enable-https.sh"
echo ""

