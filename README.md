# Xmem

一个现代化的个人记账和待办事项管理应用，支持笔记记录、智能记账和任务管理。

## ✨ 功能特性

- 📝 **笔记管理** - 快速记录和管理个人笔记
- 💰 **智能记账** - 支持自然语言输入，AI 自动识别金额、分类和商户信息
- ✅ **待办事项** - 简洁的任务管理功能
- 🔐 **用户认证** - 安全的用户注册和登录系统
- 🖥️ **多端支持** - Web 应用和 Electron 桌面应用
- 🐳 **容器化部署** - 使用 Docker Compose 一键部署

## 🛠️ 技术栈

### 后端
- **FastAPI** - 现代化的 Python Web 框架
- **PostgreSQL** - 关系型数据库
- **SQLAlchemy** - ORM 框架
- **Alembic** - 数据库迁移工具
- **JWT** - 用户认证
- **Pydantic** - 数据验证

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全的 JavaScript
- **Vite** - 快速的前端构建工具
- **Tailwind CSS** - 实用优先的 CSS 框架
- **Pinia** - Vue 状态管理
- **Axios** - HTTP 客户端

### 桌面应用
- **Electron** - 跨平台桌面应用框架

### 部署
- **Docker** - 容器化
- **Docker Compose** - 多容器编排
- **Nginx** - Web 服务器（前端）

## 📁 项目结构

```
Xmem/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── routers/      # API 路由
│   │   │   ├── auth.py   # 认证路由
│   │   │   ├── notes.py  # 笔记路由
│   │   │   ├── ledger.py # 记账路由
│   │   │   └── todos.py  # 待办路由
│   │   ├── services/     # 业务逻辑
│   │   │   └── ledger_ai.py  # AI 分析服务
│   │   ├── models.py     # 数据库模型
│   │   ├── schemas.py    # Pydantic 模式
│   │   ├── db.py         # 数据库配置
│   │   ├── auth.py       # 认证工具
│   │   └── main.py       # FastAPI 应用入口
│   ├── Dockerfile
│   └── pyproject.toml    # Python 项目配置
├── frontend/             # 前端应用
│   ├── src/
│   │   ├── components/   # Vue 组件
│   │   ├── stores/       # Pinia 状态管理
│   │   ├── api/          # API 客户端
│   │   └── utils/        # 工具函数
│   ├── Dockerfile
│   └── package.json
├── electron/             # Electron 桌面应用
│   ├── main.js
│   ├── preload.js
│   └── package.json
└── docker-compose.yml    # Docker Compose 配置
```

## 🚀 快速开始

### 前置要求

- Docker 和 Docker Compose
- 或本地安装：
  - Python 3.10+
  - Node.js 18+
  - PostgreSQL 16+

### 使用 Docker Compose（推荐）

1. 克隆仓库
```bash
git clone <repository-url>
cd Xmem
```

2. 启动所有服务
```bash
docker-compose up -d
```

3. 访问应用
- 前端：http://localhost:8080
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 本地开发

#### 后端开发

1. 安装依赖（使用 uv）
```bash
cd backend
uv sync
```

2. 配置环境变量
创建 `.env` 文件：
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/xmem
SECRET_KEY=your-secret-key-here
```

3. 启动数据库
```bash
docker-compose up -d db
```

4. 运行后端服务
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发

1. 安装依赖
```bash
cd frontend
npm install
```

2. 配置环境变量
创建 `.env` 文件：
```env
VITE_API_URL=http://localhost:8000
```

3. 启动开发服务器
```bash
npm run dev
```

#### Electron 桌面应用

1. 安装依赖
```bash
cd electron
npm install
```

2. 开发模式运行
```bash
npm run dev
```

3. 生产模式运行
```bash
npm start
```

## 📖 API 文档

启动后端服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要 API 端点

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息
- `GET /api/notes` - 获取笔记列表
- `POST /api/notes` - 创建笔记
- `GET /api/ledger` - 获取记账记录
- `POST /api/ledger` - 创建记账记录
- `GET /api/todos` - 获取待办事项
- `POST /api/todos` - 创建待办事项
- `PUT /api/todos/{id}/toggle` - 切换待办状态
- `DELETE /api/todos/{id}` - 删除待办事项

## 🔧 配置说明

### 数据库配置

默认配置（docker-compose.yml）：
- 数据库：PostgreSQL 16
- 用户名：postgres
- 密码：postgres
- 数据库名：xmem
- 端口：5432

### 环境变量

#### 后端
- `DATABASE_URL` - 数据库连接字符串
- `SECRET_KEY` - JWT 密钥（用于生成 token）

#### 前端
- `VITE_API_URL` - 后端 API 地址

## 🧪 开发指南

### 数据库迁移

使用 Alembic 进行数据库迁移：

```bash
cd backend
uv run alembic revision --autogenerate -m "描述"
uv run alembic upgrade head
```

### 代码规范

- 后端：遵循 PEP 8 Python 代码规范
- 前端：使用 TypeScript 严格模式，遵循 Vue 3 最佳实践

## 🚢 部署

### 生产环境部署

1. 修改 `docker-compose.yml` 中的环境变量
2. 构建并启动服务：
```bash
docker-compose up -d --build
```

3. 查看日志：
```bash
docker-compose logs -f
```

### 前端构建

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist` 目录。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 👤 作者

Copyright (c) 2025 Xchkoo

---

如有问题或建议，欢迎提交 Issue。

