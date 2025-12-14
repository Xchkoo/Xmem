FROM nginx:1.27-alpine

# 复制已构建的前端文件
COPY ./dist /usr/share/nginx/html

# 复制 nginx 配置文件
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

