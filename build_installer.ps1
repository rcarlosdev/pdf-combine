$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildExeScript = Join-Path $projectRoot "build_exe.ps1"
$installerScript = Join-Path $projectRoot "installer.iss"
$distExe = Join-Path $projectRoot "dist\PDFCombine.exe"
$outputInstaller = Join-Path $projectRoot "installer-output\PDFCombine-Setup.exe"

if (-not (Test-Path $buildExeScript)) {
    throw "No se encontro build_exe.ps1"
}

if (-not (Test-Path $installerScript)) {
    throw "No se encontro installer.iss"
}

Write-Host "Generando ejecutable..." -ForegroundColor Cyan
& powershell -ExecutionPolicy Bypass -File $buildExeScript
if ($LASTEXITCODE -ne 0) {
    throw "No fue posible compilar el ejecutable"
}

if (-not (Test-Path $distExe)) {
    throw "No se encontro dist\\PDFCombine.exe para empaquetar"
}

$innoCandidates = @(
    $env:INNO_SETUP_COMPILER,
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) | Where-Object { $_ }

$iscc = $innoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $iscc) {
    throw "No se encontro Inno Setup. Instala Inno Setup 6 o define la variable INNO_SETUP_COMPILER apuntando a ISCC.exe"
}

Write-Host "Creando instalador..." -ForegroundColor Cyan
& $iscc $installerScript
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup no pudo generar el instalador"
}

if (-not (Test-Path $outputInstaller)) {
    throw "La compilacion termino, pero no se encontro installer-output\\PDFCombine-Setup.exe"
}

Write-Host ""
Write-Host "Listo. Instalador generado en installer-output\\PDFCombine-Setup.exe" -ForegroundColor Green
