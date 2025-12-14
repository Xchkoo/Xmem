# Redis Dockerfile

这个 Dockerfile 基于 `redis:7-alpine` 镜像构建。

## 自定义配置

如果需要自定义 Redis 配置，可以：

1. **创建 redis.conf 文件**：
   - 在 `redis/` 目录下创建 `redis.conf` 文件
   - 取消 Dockerfile 中的注释以使用自定义配置

2. **常用配置示例**：

```conf
# 持久化配置
save 900 1
save 300 10
save 60 10000

# 内存限制（根据需求调整）
maxmemory 256mb
maxmemory-policy allkeys-lru

# 日志级别
loglevel notice

# 绑定地址
bind 0.0.0.0

# 端口
port 6379
```

## 持久化

数据持久化通过 docker-compose.yml 中的 volume 配置实现，数据存储在 `redis_data` volume 中。

