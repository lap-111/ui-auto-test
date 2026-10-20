# MoneyKeeper UI 自动化测试 — 便捷命令脚本（PowerShell）
# 用法示例：
#   .\run.ps1 app      启动被测应用（后台）
#   .\run.ps1 test     运行全部 UI 用例
#   .\run.ps1 all      启动应用 + 跑测试 + 生成 Allure 报告 + 托管报告

param(
    [Parameter(Position = 0)]
    [ValidateSet("app", "test", "all", "report")]
    [string]$Command = "test"
)

$venv = ".venv\Scripts\python.exe"
$appPort = "8000"
$reportPort = "8082"

function Test-App {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$appPort/api/dev/features" -UseBasicParsing -TimeoutSec 3
        return $true
    } catch {
        return $false
    }
}

function Start-App {
    if (Test-App) { Write-Host "应用已在运行 (port $appPort)"; return }
    Start-Process -FilePath $venv -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", $appPort -WindowStyle Hidden
    Start-Sleep -Seconds 3
    if (Test-App) { Write-Host "应用已启动: http://127.0.0.1:$appPort (账号 admin/123456)" }
    else { Write-Host "[警告] 应用启动检测失败，请检查端口 $appPort" }
}

function Run-Tests {
    & $venv -m pytest
}

function Gen-Report {
    if (Test-Path "allure-report") { Remove-Item -Recurse -Force "allure-report" }
    & allure generate allure-results -o allure-report --clean
    Start-Process -FilePath $venv -ArgumentList "-m", "http.server", $reportPort, "--bind", "127.0.0.1", "--directory", (Join-Path $PWD "allure-report") -WindowStyle Hidden
    Write-Host ""
    Write-Host "Allure 报告已生成并托管: http://127.0.0.1:$reportPort/index.html"
}

switch ($Command) {
    "app"    { Start-App }
    "test"   { Run-Tests }
    "report" { Gen-Report }
    "all"    { Start-App; Run-Tests; Gen-Report }
}