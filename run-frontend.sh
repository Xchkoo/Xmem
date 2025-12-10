#!/bin/bash
# Xmem 前端启动脚本
# 使用 bash 运行 Vue.js 前端开发服务器

# 颜色定义
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Xmem Frontend Server${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 检查是否在正确的目录
scriptPath=$(dirname "$0")
frontendPath="$scriptPath/frontend"

if [ ! -d "$frontendPath" ]; then
    echo -e "${RED}错误: 找不到 frontend 目录${NC}"
    echo -e "${YELLOW}请确保在项目根目录运行此脚本${NC}"
    exit 1
fi

# 切换到 frontend 目录
cd "$frontendPath"
echo -e "${GRAY}工作目录: $(pwd)${NC}"
echo ""

# 检查 node_modules 是否存在
nodeModulesPath="$frontendPath/node_modules"
if [ ! -d "$nodeModulesPath" ]; then
    echo -e "${YELLOW}警告: 未找到 node_modules 目录${NC}"
    echo -e "${YELLOW}正在安装依赖...${NC}"
    echo ""
    if ! npm install; then
        echo -e "${RED}错误: 依赖安装失败${NC}"
        exit 1
    fi
    echo ""
    echo -e "${GREEN}依赖安装完成!${NC}"
    echo ""
fi

# 检查环境变量文件
envFile="$frontendPath/.env"
if [ ! -f "$envFile" ]; then
    echo -e "${GRAY}提示: 未找到 .env 文件${NC}"
    echo -e "${GRAY}默认 API 地址: http://localhost:8000${NC}"
    echo ""
fi

# 启动开发服务器
echo -e "${GREEN}正在启动 Vite 开发服务器...${NC}"
echo -e "${CYAN}前端地址: http://localhost:5173${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 设置错误处理
set -e
trap 'echo ""; echo -e "${RED}错误: 启动服务器失败${NC}"; echo ""; echo -e "${YELLOW}请检查:${NC}"; echo -e "${YELLOW}  1. 是否已安装 Node.js (https://nodejs.org/)${NC}"; echo -e "${YELLOW}  2. 是否已运行 'npm install' 安装依赖${NC}"; echo -e "${YELLOW}  3. package.json 中是否配置了 'dev' 脚本${NC}"; cd "$scriptPath"; exit 1' ERR

# 使用 npm run dev 启动
npm run dev

# 返回原目录（正常情况下不会执行到这里，因为服务器会一直运行）
cd "$scriptPath"

