# 环境变量问题诊断

## 问题分析

### 关键问题：`DATABASE_URL` 缺失

**问题**：你的 `.env` 文件中缺少 `DATABASE_URL` 变量，但 `docker-compose.yml` 第 44 行使用了：
```yaml
- DATABASE_URL=${DATABASE_URL}
```

**影响**：
- 如果 `DATABASE_URL` 不存在，会变成空字符串 `""`
- 后端无法连接数据库，服务启动失败
- 这是导致远程服务器无法运行的主要原因

### 其他可能的问题

1. **VITE_API_URL**：虽然 docker-compose.yml 有默认值 `/api`，但最好明确设置
2. **环境变量格式**：确保 `.env` 文件格式正确（无多余空格、正确换行）

## 解决方案

### 完整的 `.env` 文件模板

在你的远程服务器根目录，确保 `.env` 文件包含以下**所有**变量：

```env
# JWT 配置（必须修改为强密码）
JWT_SECRET=your-secret-key-change-this-in-production

# 数据库配置
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=xmem
POSTGRES_PORT=5432

# ⚠️ 关键：数据库连接 URL（必须配置！）
# 格式：postgresql+asyncpg://用户名:密码@主机:端口/数据库名
# 注意：在 Docker Compose 中，主机名是服务名 "db"
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/xmem

# Redis 配置
REDIS_URL=redis://redis:6379/0
REDIS_PORT=6379

# 前端端口（默认 80）
FRONTEND_PORT=80

# 前端 API URL（构建时使用）
VITE_API_URL=/api

# OCR 配置（默认使用本地 OCR）
OCR_PROVIDER=local
TESSERACT_CMD=/usr/bin/tesseract

# LLM 配置
LLM_PROVIDER=deepseek
LLM_API_URL=https://api.deepseek.com
LLM_API_KEY=sk-884f10eec99647d5b72ed2e0fa9b363b
```

### 快速修复步骤

1. **在远程服务器上编辑 `.env` 文件**：
```bash
nano .env
```

2. **添加缺失的 `DATABASE_URL`**：
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/xmem
```

3. **添加 `VITE_API_URL`**（如果还没有）：
```env
VITE_API_URL=/api
```

4. **验证 `.env` 文件格式**：
```bash
# 检查是否有语法错误
cat .env | grep -v "^#" | grep -v "^$"
```

5. **重新启动服务**：
```bash
docker-compose down
docker-compose up -d --build
```

6. **查看日志确认**：
```bash
docker-compose logs -f backend
```

## 验证环境变量

### 方法 1：检查 Docker Compose 是否读取了环境变量

```bash
# 在项目根目录运行
docker-compose config | grep DATABASE_URL
```

应该看到：
```yaml
- DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/xmem
```

如果看到空值或没有输出，说明 `.env` 文件没有被正确读取。

### 方法 2：检查容器内的环境变量

```bash
# 检查后端容器的环境变量
docker-compose exec backend env | grep DATABASE_URL
```

### 方法 3：查看后端启动日志

```bash
docker-compose logs backend | grep -i "database\|error\|failed"
```

## 常见错误

### 错误 1：`DATABASE_URL` 为空

**症状**：
```
sqlalchemy.exc.ArgumentError: Could not parse rfc1738 URL from string ''
```

**解决**：添加 `DATABASE_URL` 到 `.env` 文件

### 错误 2：数据库连接失败

**症状**：
```
asyncpg.exceptions.InvalidCatalogNameError: database "xmem" does not exist
```

**解决**：检查 `POSTGRES_DB` 和 `DATABASE_URL` 中的数据库名是否一致

### 错误 3：前端无法访问后端 API

**症状**：前端页面加载但 API 请求失败

**解决**：
1. 检查 `VITE_API_URL` 是否正确设置为 `/api`
2. 检查 `nginx.conf` 中的代理配置
3. 确保后端服务正常运行

## 为什么本地能运行但远程不行？

可能的原因：

1. **本地有额外的 `.env` 文件**：
   - `frontend/.env.production`
   - `backend/.env`
   - 这些文件被 `.gitignore` 忽略了，所以没有提交到远程

2. **本地环境变量**：
   - 系统环境变量中可能设置了 `DATABASE_URL`
   - 远程服务器没有这些环境变量

3. **Docker Compose 版本差异**：
   - 不同版本的 docker-compose 对 `.env` 文件的处理可能不同

## 最佳实践

1. **使用 `.env.example` 作为模板**（虽然被 gitignore，但可以手动创建）
2. **在部署文档中明确列出所有必需的环境变量**
3. **使用 `docker-compose config` 验证配置**
4. **在启动前检查所有必需的环境变量**

## 调试命令

```bash
# 1. 检查所有环境变量
docker-compose config

# 2. 检查特定服务的环境变量
docker-compose config | grep -A 20 "backend:"

# 3. 检查容器内的实际环境变量
docker-compose exec backend env

# 4. 查看服务状态
docker-compose ps

# 5. 查看所有服务日志
docker-compose logs

# 6. 查看特定服务日志
docker-compose logs -f backend
```


