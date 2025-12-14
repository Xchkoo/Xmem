#!/bin/sh
# Nginx 启动脚本 - 动态替换证书路径中的域名

set -e

# 如果设置了 CERTBOT_DOMAIN 环境变量，替换 nginx.conf 中的域名
if [ -n "$CERTBOT_DOMAIN" ]; then
    echo "使用域名: $CERTBOT_DOMAIN"
    # 替换 nginx.conf 中的域名占位符
    sed -i "s/yourdomain.com/$CERTBOT_DOMAIN/g" /etc/nginx/conf.d/default.conf
    echo "✓ nginx.conf 已更新"
fi

# 检查证书文件是否存在
CERT_PATH="/etc/letsencrypt/live/${CERTBOT_DOMAIN:-yourdomain.com}/fullchain.pem"
if [ ! -f "$CERT_PATH" ]; then
    echo "警告: 证书文件不存在: $CERT_PATH"
    echo "请先运行 ./init-cert.sh 获取证书"
    echo "或者使用 HTTP 模式（注释掉 HTTPS server 块）"
fi

# 启动 nginx
exec nginx -g "daemon off;"

