# 待办助手一键打包脚本（PowerShell 5.1 兼容）
# 用法：在项目根目录执行 .\scripts\build.ps1
# 前置：Python 依赖已安装（含 pyinstaller）；desktop/ 已 npm install

# 注意：不设 $ErrorActionPreference="Stop"（PS5.1 下 npm/stderr 会误杀脚本），
# 各原生命令后用 $LASTEXITCODE 显式判错

# Electron 二进制与 electron-builder 工具链走国内镜像（GitHub Releases 在当前网络不可达，原型验证结论）
$env:ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"
$env:ELECTRON_BUILDER_BINARIES_MIRROR = "https://npmmirror.com/mirrors/electron-builder-binaries/"

$PY = "D:\developTools\python\python3.14.5\python.exe"
$ROOT = $PSScriptRoot | Split-Path -Parent

Write-Host "== 1/4 构建前端 ==" -ForegroundColor Cyan
Set-Location (Join-Path $ROOT "frontend")
npm run build
if ($LASTEXITCODE -ne 0) { throw "前端构建失败" }

Write-Host "== 2/4 PyInstaller 打包后端 ==" -ForegroundColor Cyan
Set-Location $ROOT
& $PY -m PyInstaller --onedir --name todo_backend --noconsole --clean -y `
    --distpath (Join-Path $ROOT "dist") `
    --workpath (Join-Path $ROOT ".temp\pyinstaller-build") `
    --specpath (Join-Path $ROOT ".temp") `
    (Join-Path $ROOT "backend\start_dev.py")
if ($LASTEXITCODE -ne 0) { throw "后端打包失败" }

Write-Host "== 3/4 前端产物嵌入后端目录 ==" -ForegroundColor Cyan
Copy-Item -Recurse -Force (Join-Path $ROOT "frontend\dist") (Join-Path $ROOT "dist\todo_backend\frontend_dist")

Write-Host "== 4/4 electron-builder 打包 portable EXE ==" -ForegroundColor Cyan
Set-Location (Join-Path $ROOT "desktop")
npm run build
if ($LASTEXITCODE -ne 0) { throw "electron-builder 打包失败" }

Write-Host "`n打包完成：release\ 待办助手.exe (portable)" -ForegroundColor Green
