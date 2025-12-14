FROM postgres:16-alpine

# 复制自定义初始化脚本（可选）
# COPY init-scripts/ /docker-entrypoint-initdb.d/

# 设置工作目录
WORKDIR /var/lib/postgresql

# PostgreSQL 的默认配置已经足够，如果需要自定义配置可以添加
# COPY postgresql.conf /etc/postgresql/postgresql.conf

# 暴露端口
EXPOSE 5432

# 使用默认的 postgres 启动命令
# CMD 已经在基础镜像中定义，无需重复

