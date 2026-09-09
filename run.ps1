# 兼容旧入口：现已升级为 Vue + FastAPI 全栈架构，请使用 run-dev.ps1。
Set-Location $PSScriptRoot
Write-Host "项目已升级为 Vue3 + FastAPI 架构，正在调用 run-dev.ps1 ..." -ForegroundColor Yellow
& (Join-Path $PSScriptRoot "run-dev.ps1")
