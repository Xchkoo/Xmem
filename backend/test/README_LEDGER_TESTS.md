# Ledger 测试指南

本文档说明如何运行和测试 ledger 相关的所有代码。

## 测试文件结构

```
backend/test/
├── test_ledger_api.py          # API 路由测试
├── test_ledger_tasks.py        # Celery 任务测试
├── test_ledger_integration.py  # 集成测试
└── conftest.py                 # 测试 fixtures
```

## 运行测试

### 1. 运行所有 Ledger 测试

```bash
cd backend
uv run pytest test/test_ledger_*.py -v
```

### 2. 运行特定测试文件

```bash
# 只测试 API
uv run pytest test/test_ledger_api.py -v

# 只测试 Celery 任务
uv run pytest test/test_ledger_tasks.py -v

# 只测试集成测试
uv run pytest test/test_ledger_integration.py -v
```

### 3. 运行特定测试类

```bash
# 测试创建 ledger 的 API
uv run pytest test/test_ledger_api.py::TestCreateLedger -v

# 测试更新 ledger 条目的任务
uv run pytest test/test_ledger_tasks.py::TestUpdateLedgerEntry -v
```

### 4. 运行特定测试函数

```bash
# 测试只提供文本创建 ledger
uv run pytest test/test_ledger_api.py::TestCreateLedger::test_create_ledger_with_text_only -v
```

### 5. 使用标记运行测试

```bash
# 运行所有 ledger 相关测试
uv run pytest -m ledger -v

# 运行所有 API 测试
uv run pytest -m api -v

# 运行所有任务测试
uv run pytest -m tasks -v

# 运行所有集成测试
uv run pytest -m integration -v
```

### 6. 生成覆盖率报告

```bash
# 安装 coverage（如果还没有）
uv add --dev pytest-cov

# 运行测试并生成覆盖率报告
uv run pytest test/test_ledger_*.py \
  --cov=app.routers.ledger \
  --cov=app.tasks.ledger_tasks \
  --cov=app.services.ledger_ai \
  --cov-report=html \
  --cov-report=term

# 查看 HTML 报告
# 打开 htmlcov/index.html
```

## 测试内容

### API 路由测试 (test_ledger_api.py)

- ✅ 创建只有文本的 ledger
- ✅ 创建只有图片的 ledger
- ✅ 创建文本+图片的 ledger
- ✅ 获取所有 ledger
- ✅ 获取单个 ledger
- ✅ 获取摘要
- ✅ 认证和权限验证
- ✅ 错误处理（无效输入、未授权等）

### Celery 任务测试 (test_ledger_tasks.py)

- ✅ 合并文本并分析（有/无原始文本）
- ✅ 包装分析任务
- ✅ 更新数据库条目
- ✅ LLM 分析（成功/失败场景）
- ✅ 错误处理和状态回退
- ✅ 时间格式验证

### 集成测试 (test_ledger_integration.py)

- ✅ 完整流程（文本 → LLM → 更新）
- ✅ 完整流程（图片 → OCR → LLM → 更新）
- ✅ 状态流转（pending → processing → completed）
- ✅ 错误处理和状态回退
- ✅ 多用户数据隔离

## 手动测试步骤

### 1. 启动服务

```bash
# 终端1：启动 FastAPI
cd backend
uv run uvicorn app.main:app --reload

# 终端2：启动 Celery Worker
cd backend
uv run celery -A app.celery_app worker --loglevel=info

# 终端3：启动 Redis（如果还没运行）
redis-server
```

### 2. 测试 API（使用 curl）

```bash
# 1. 登录获取 token
TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "hashed_password"}' \
  | jq -r '.access_token')

# 2. 创建只有文本的 ledger
curl -X POST "http://localhost:8000/ledger" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "今天午餐花费50元"}'

# 3. 创建带图片的 ledger
curl -X POST "http://localhost:8000/ledger" \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@/path/to/image.jpg" \
  -F "text=这是备注"

# 4. 获取所有 ledger
curl -X GET "http://localhost:8000/ledger" \
  -H "Authorization: Bearer $TOKEN"

# 5. 获取单个 ledger（用于轮询）
LEDGER_ID=1
curl -X GET "http://localhost:8000/ledger/$LEDGER_ID" \
  -H "Authorization: Bearer $TOKEN"

# 6. 获取摘要
curl -X GET "http://localhost:8000/ledger/summary" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. 验证流程

1. **创建 ledger** → 检查状态是否为 `pending`
2. **查看 Celery worker 日志** → 确认任务被接收
3. **等待几秒** → 检查状态是否变为 `processing`
4. **等待完成** → 检查状态是否变为 `completed`，数据是否正确

## 测试检查清单

### API 路由测试
- [ ] 创建只有文本的 ledger
- [ ] 创建只有图片的 ledger
- [ ] 创建文本+图片的 ledger
- [ ] 获取所有 ledger
- [ ] 获取单个 ledger
- [ ] 获取摘要
- [ ] 认证和权限验证
- [ ] 错误处理

### Celery 任务测试
- [ ] OCR 文本提取
- [ ] 文本合并逻辑
- [ ] LLM 分析调用
- [ ] 数据库更新
- [ ] 错误处理和状态回退

### 集成测试
- [ ] 完整流程（创建 → OCR → LLM → 更新）
- [ ] BackgroundTasks 执行
- [ ] 状态流转
- [ ] 多用户隔离

### 性能测试
- [ ] 并发创建 ledger
- [ ] 大量数据查询
- [ ] 长时间运行稳定性

## 常见问题

### 1. 测试失败：找不到模块

确保在 `backend` 目录下运行测试，或者设置正确的 Python 路径。

### 2. 测试失败：数据库连接错误

确保测试环境变量正确设置，或者使用测试数据库。

### 3. 测试失败：Celery 任务未执行

集成测试可能需要运行 Celery worker，或者使用 mock 来模拟 Celery 任务。

### 4. 覆盖率报告不准确

确保所有相关模块都被包含在 `--cov` 参数中。

## 持续集成

如果使用 CI/CD，可以在配置文件中添加：

```yaml
# .github/workflows/test.yml 示例
- name: Run Ledger Tests
  run: |
    cd backend
    uv run pytest test/test_ledger_*.py -v --cov=app.routers.ledger --cov=app.tasks.ledger_tasks --cov-report=xml
```

## 贡献

添加新测试时，请确保：
1. 测试名称清晰描述测试内容
2. 使用适当的 fixtures
3. 包含成功和失败场景
4. 添加必要的文档注释

