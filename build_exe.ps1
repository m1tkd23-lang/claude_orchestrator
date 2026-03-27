# build_exe.ps1
param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Virtual environment not found: .venv\Scripts\python.exe"
}

$pythonExe = Resolve-Path ".venv\Scripts\python.exe"

if ($Clean) {
    if (Test-Path "build") {
        Remove-Item -Recurse -Force "build"
    }
    if (Test-Path "dist") {
        Remove-Item -Recurse -Force "dist"
    }
}

& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install pyinstaller

& $pythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    "claude_orchestrator_gui.spec"

$distDir = Join-Path $repoRoot "dist\claude_orchestrator"
if (-not (Test-Path $distDir)) {
    throw "Build output not found: $distDir"
}

Copy-Item "README.md" $distDir -Force

Write-Host ""
Write-Host "Build completed."
Write-Host "Output: $distDir"
Write-Host ""
Write-Host "Run:"
Write-Host "  dist\claude_orchestrator\claude_orchestrator.exe"