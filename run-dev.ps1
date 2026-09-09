# 一键启动开发环境：FastAPI 后端(8000) + Vite 前端(5173)
# 用法：在项目根目录执行  .\run-dev.ps1
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

$server = Join-Path $root "server"
$web = Join-Path $root "web"
$py = Join-Path $server ".venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
  Write-Host "未发现后端虚拟环境，正在创建并安装依赖..." -ForegroundColor Yellow
  python -m venv (Join-Path $server ".venv")
  & $py -m pip install --upgrade pip
  & $py -m pip install -r (Join-Path $server "requirements.txt")
}

if (-not (Test-Path (Join-Path $web "node_modules"))) {
  Write-Host "未发现前端依赖，正在 npm install..." -ForegroundColor Yellow
  Push-Location $web; npm install; Pop-Location
}

Write-Host "启动后端 http://localhost:8000 ..." -ForegroundColor Green
Start-Process -FilePath $py -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000" -WorkingDirectory $server

Write-Host "启动前端 http://localhost:5173 ..." -ForegroundColor Green
Push-Location $web
npm run dev
Pop-Location
