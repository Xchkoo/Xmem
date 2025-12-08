# Xmem 前端启动脚本
# 使用 PowerShell 运行 Vue.js 前端开发服务器

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Xmem Frontend Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在正确的目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendPath = Join-Path $scriptPath "frontend"

if (-not (Test-Path $frontendPath)) {
    Write-Host "错误: 找不到 frontend 目录" -ForegroundColor Red
    Write-Host "请确保在项目根目录运行此脚本" -ForegroundColor Yellow
    exit 1
}

# 切换到 frontend 目录
Set-Location $frontendPath
Write-Host "工作目录: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# 检查 node_modules 是否存在
$nodeModulesPath = Join-Path $frontendPath "node_modules"
if (-not (Test-Path $nodeModulesPath)) {
    Write-Host "警告: 未找到 node_modules 目录" -ForegroundColor Yellow
    Write-Host "正在安装依赖..." -ForegroundColor Yellow
    Write-Host ""
    try {
        npm install
        Write-Host ""
        Write-Host "依赖安装完成!" -ForegroundColor Green
        Write-Host ""
    }
    catch {
        Write-Host "错误: 依赖安装失败" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
}

# 检查环境变量文件
$envFile = Join-Path $frontendPath ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "提示: 未找到 .env 文件" -ForegroundColor Gray
    Write-Host "默认 API 地址: http://localhost:8000" -ForegroundColor Gray
    Write-Host ""
}

# 启动开发服务器
Write-Host "正在启动 Vite 开发服务器..." -ForegroundColor Green
Write-Host "前端地址: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    # 使用 npm run dev 启动
    npm run dev
}
catch {
    Write-Host ""
    Write-Host "错误: 启动服务器失败" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查:" -ForegroundColor Yellow
    Write-Host "  1. 是否已安装 Node.js (https://nodejs.org/)" -ForegroundColor Yellow
    Write-Host "  2. 是否已运行 'npm install' 安装依赖" -ForegroundColor Yellow
    Write-Host "  3. package.json 中是否配置了 'dev' 脚本" -ForegroundColor Yellow
    exit 1
}
finally {
    # 返回原目录
    Set-Location $scriptPath
}

