# Xmem 后端启动脚本
# 使用 PowerShell 运行 FastAPI 后端服务

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Xmem Backend Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在正确的目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $scriptPath "backend"

if (-not (Test-Path $backendPath)) {
    Write-Host "错误: 找不到 backend 目录" -ForegroundColor Red
    Write-Host "请确保在项目根目录运行此脚本" -ForegroundColor Yellow
    exit 1
}

# 切换到 backend 目录
Set-Location $backendPath
Write-Host "工作目录: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# 检查环境变量文件
$envFile = Join-Path $backendPath ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "警告: 未找到 .env 文件" -ForegroundColor Yellow
    Write-Host "请确保已设置以下环境变量:" -ForegroundColor Yellow
    Write-Host "  - DATABASE_URL" -ForegroundColor Yellow
    Write-Host "  - JWT_SECRET" -ForegroundColor Yellow
    Write-Host ""
}

# 检查数据库连接（可选）
Write-Host "检查配置..." -ForegroundColor Gray
Write-Host ""

# 启动服务器
Write-Host "正在启动 uvicorn 服务器..." -ForegroundColor Green
Write-Host "API 文档: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "健康检查: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    # 使用 uv 运行 uvicorn
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}
catch {
    Write-Host ""
    Write-Host "错误: 启动服务器失败" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查:" -ForegroundColor Yellow
    Write-Host "  1. 是否已安装 uv: https://github.com/astral-sh/uv" -ForegroundColor Yellow
    Write-Host "  2. 是否已运行 'uv sync' 安装依赖" -ForegroundColor Yellow
    Write-Host "  3. 环境变量是否正确配置" -ForegroundColor Yellow
    exit 1
}
finally {
    # 返回原目录
    Set-Location $scriptPath
}

