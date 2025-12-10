#!/bin/bash
# Xmem 后端启动脚本
# 使用 bash 运行 FastAPI 后端服务

# 颜色定义
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Xmem Backend Server${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 检查是否在正确的目录
scriptPath=$(dirname "$0")
backendPath="$scriptPath/backend"

if [ ! -d "$backendPath" ]; then
    echo -e "${RED}错误: 找不到 backend 目录${NC}"
    echo -e "${YELLOW}请确保在项目根目录运行此脚本${NC}"
    exit 1
fi

# 切换到 backend 目录
cd "$backendPath"
echo -e "${GRAY}工作目录: $(pwd)${NC}"
echo ""

# 检查环境变量文件
envFile="$backendPath/.env"
if [ ! -f "$envFile" ]; then
    echo -e "${YELLOW}警告: 未找到 .env 文件${NC}"
    echo -e "${YELLOW}请确保已设置以下环境变量:${NC}"
    echo -e "${YELLOW}  - DATABASE_URL${NC}"
    echo -e "${YELLOW}  - JWT_SECRET${NC}"
    echo ""
fi

# 检查数据库连接（可选）
echo -e "${GRAY}检查配置...${NC}"
echo ""

# 启动服务器
echo -e "${GREEN}正在启动 FastAPI 服务器...${NC}"
echo -e "${CYAN}API 文档: http://localhost:8000/docs${NC}"
echo -e "${CYAN}健康检查: http://localhost:8000/health${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 设置错误处理
set -e
trap 'echo ""; echo -e "${RED}错误: 启动服务器失败${NC}"; echo ""; echo -e "${YELLOW}请检查:${NC}"; echo -e "${YELLOW}  1. 是否已安装 uv: https://github.com/astral-sh/uv${NC}"; echo -e "${YELLOW}  2. 是否已运行 'uv sync' 安装依赖${NC}"; echo -e "${YELLOW}  3. 环境变量是否正确配置${NC}"; cd "$scriptPath"; exit 1' ERR

# 使用 uv 运行 uvicorn
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 返回原目录（正常情况下不会执行到这里，因为服务器会一直运行）
cd "$scriptPath"

