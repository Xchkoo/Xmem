# Docker 部署指南

## 环境变量配置

在项目根目录创建 `.env` 文件，配置以下环境变量：

```env
# 数据库配置
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=xmem
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/xmem

# JWT 配置（必须修改为强密码）
JWT_SECRET=your-secret-key-change-this-in-production

# Redis 配置
REDIS_URL=redis://redis:6379/0
REDIS_PORT=6379

# 服务端口配置
# 前端端口（生产环境建议使用 80）
FRONTEND_PORT=80
# 后端端口（生产环境建议不暴露，如需调试可取消 docker-compose.yml 中的注释）
# BACKEND_PORT=8000

# OCR 配置
OCR_PROVIDER=local
# Tesseract 可执行文件路径（Docker 容器内默认为 /usr/bin/tesseract）
TESSERACT_CMD=/usr/bin/tesseract
# 如果使用远程 OCR，配置以下参数
# OCR_API_URL=
# OCR_API_KEY=

# LLM 配置（可选）
# LLM_PROVIDER=
# LLM_API_URL=
# LLM_API_KEY=

# 前端 API URL
VITE_API_URL=/api
```

## 部署步骤

### 1. 确保前端已构建

```bash
cd frontend
npm install
npm run build
cd ..
```

### 2. 启动所有服务

```bash
docker-compose up -d
```

### 3. 查看服务状态

```bash
docker-compose ps
```

### 4. 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f celery
docker-compose logs -f frontend
```

### 5. 停止服务

```bash
docker-compose down
```

### 6. 停止并删除数据卷（谨慎操作）

```bash
docker-compose down -v
```

## 服务说明

- **db**: PostgreSQL 数据库（通过 `database/Dockerfile` 构建）
- **redis**: Redis 服务器（通过 `redis/Dockerfile` 构建，用于 Celery）
- **backend**: FastAPI 后端服务（通过 `backend/Dockerfile` 构建，使用 uvicorn）
- **celery**: Celery Worker（通过 `backend/Dockerfile` 构建，处理异步任务如 OCR）
- **frontend**: Nginx 前端服务（通过 `frontend/Dockerfile` 构建）

## Dockerfile 说明

所有服务都使用自定义 Dockerfile：

- `database/Dockerfile`: 基于 postgres:16-alpine，可添加自定义初始化脚本
- `redis/Dockerfile`: 基于 redis:7-alpine，可添加自定义配置文件
- `backend/Dockerfile`: Python 3.12，包含 Tesseract OCR 和所有依赖
- `frontend/Dockerfile`: 使用已构建的 dist 文件夹，通过 Nginx 提供服务

如需自定义数据库或 Redis 配置，请参考 `database/README.md` 和 `redis/README.md`。

## 访问地址

- 前端: http://localhost:80 (或 http://localhost，默认端口)
- 后端 API: 通过前端 Nginx 代理访问 `/api/` 路径
- API 文档: 如需直接访问，可在 docker-compose.yml 中取消后端端口映射注释，然后访问 http://localhost:8000/docs

## 端口配置说明

### 生产环境推荐配置

- **前端**: 容器内 80 端口，主机映射到 80 端口（对外服务）
- **后端**: 容器内 8000 端口，主机不暴露端口（只通过 Nginx 代理访问，更安全）

### 开发/调试配置

如需直接访问后端 API 进行调试，可以在 `docker-compose.yml` 中取消后端 `ports` 部分的注释，然后通过 `BACKEND_PORT` 环境变量设置端口（默认 8000）。

### 为什么后端不暴露端口？

1. **安全性**: 后端 API 不直接暴露给外部，只能通过 Nginx 代理访问
2. **统一入口**: 所有请求都通过前端 Nginx（80 端口）进入，便于统一管理和配置
3. **简化配置**: 不需要在防火墙中开放多个端口

## 注意事项

1. **JWT_SECRET**: 生产环境必须修改为强密码
2. **数据库密码**: 生产环境必须修改
3. **Tesseract**: Docker 容器内已安装 Tesseract OCR 和中文语言包，默认路径为 `/usr/bin/tesseract`
4. **数据持久化**: 数据库和 Redis 数据存储在 Docker volumes 中
5. **上传文件**: 后端上传的文件存储在 `./backend/uploads` 目录

## 故障排查

### 数据库连接失败

检查 `.env` 文件中的 `DATABASE_URL` 是否正确，确保数据库服务已启动。

### Celery Worker 无法启动

检查 Redis 服务是否正常运行：
```bash
docker-compose exec redis redis-cli ping
```

### OCR 功能不工作

确保 `TESSERACT_CMD` 设置为 `/usr/bin/tesseract`（Docker 容器内的默认路径）。

### 前端无法访问后端 API

检查 `nginx.conf` 中的代理配置是否正确，确保 `proxy_pass` 指向 `http://backend:8000/`。

