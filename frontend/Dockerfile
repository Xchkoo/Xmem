# 多阶段构建：第一阶段 - 构建前端
FROM node:20.18.0-alpine AS builder

# 锁定 npm 版本（Node.js 20.18.0 自带 npm 10.8.2，如需更新可单独安装）
# RUN npm install -g npm@10.8.2

WORKDIR /app

# 复制 package 文件
COPY package.json package-lock.json ./

# 安装依赖（使用 npm ci 确保使用 package-lock.json 中的精确版本）
RUN npm ci --only=production=false

# 复制源代码
COPY . .

# 构建前端（根据环境变量选择构建模式）
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# 第二阶段 - 使用 Nginx 服务构建好的文件
FROM nginx:1.27-alpine

# 从构建阶段复制构建好的文件
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置文件模板（启动时会替换占位符）
COPY ./nginx.conf /etc/nginx/conf.d/nginx.conf.template

# 复制启动脚本
COPY ./docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 创建 certbot 验证目录（证书会通过 volume 挂载）
RUN mkdir -p /var/www/certbot

EXPOSE 80 443

# 使用自定义启动脚本
ENTRYPOINT ["/docker-entrypoint.sh"]

