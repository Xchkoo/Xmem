#!/bin/sh
# Nginx 启动脚本 - 自动检测证书并选择配置

set -e

DOMAIN="${CERTBOT_DOMAIN:-xmem.top}"
CERT_PATH="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"

echo "使用域名: ${DOMAIN}"

# 检查证书文件是否存在
if [ ! -f "$CERT_PATH" ]; then
    echo "警告: 证书文件不存在: $CERT_PATH"
    echo "将使用 HTTP-only 模式启动（用于 Let's Encrypt 验证）"
    
    # 创建临时的 HTTP-only 配置
    cat > /etc/nginx/conf.d/default.conf << 'EOF'
# HTTP 服务器 - 用于 Let's Encrypt 验证（证书获取前）
server {
    listen 80;
    server_name _;
    
    # Let's Encrypt 验证路径 - 必须在最前面，优先级最高
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        allow all;
        default_type text/plain;
        try_files $uri =404;
    }
    
    # 增加上传文件大小限制
    client_max_body_size 50M;
    
    # 前端静态文件
    root /usr/share/nginx/html;
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
    echo "✓ 已创建 HTTP-only 配置"
else
    echo "✓ 证书文件存在，使用完整 HTTPS 配置"
    # 证书存在，从模板生成配置文件并替换域名占位符
    # 使用 sed 替换 nginx.conf.template 中的 ${DOMAIN} 占位符
    sed "s|\${DOMAIN}|${DOMAIN}|g" /etc/nginx/conf.d/nginx.conf.template > /etc/nginx/conf.d/default.conf
    echo "✓ 已替换域名占位符为: ${DOMAIN}"
fi

# 启动 nginx
exec nginx -g "daemon off;"

