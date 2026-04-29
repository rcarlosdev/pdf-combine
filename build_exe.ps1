$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot "env\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "No se encontro el interprete del entorno virtual en env\\Scripts\\python.exe"
}

$basePython = (& $pythonExe -c "import sys; print(sys.base_prefix)").Trim()
$env:TCL_LIBRARY = Join-Path $basePython "tcl\tcl8.6"
$env:TK_LIBRARY = Join-Path $basePython "tcl\tk8.6"

Write-Host "Verificando dependencias de compilacion..." -ForegroundColor Cyan
& $pythonExe -c "import pypdf, PyInstaller, PIL; print('Dependencias OK')"
if ($LASTEXITCODE -ne 0) {
    throw "Faltan dependencias en el entorno virtual. Ejecuta env\\Scripts\\pip.exe install -r requirements.txt y env\\Scripts\\pip.exe install -r requirements-build.txt"
}

Write-Host "Verificando icono..." -ForegroundColor Cyan
& $pythonExe -c "from pathlib import Path; from PIL import Image; source = Path('logo_pdf_app.png'); target = Path('app_icon.ico'); image = Image.open(source); image.save(target, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]); print(target.resolve())"
if ($LASTEXITCODE -ne 0) {
    throw "No fue posible generar app_icon.ico"
}

Write-Host "Compilando ejecutable..." -ForegroundColor Cyan
& $pythonExe -m PyInstaller --noconfirm --clean "$projectRoot\pdf_combine.spec"
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller no pudo generar el ejecutable"
}

$exePath = Join-Path $projectRoot "dist\PDFCombine.exe"
if (-not (Test-Path $exePath)) {
    throw "La compilacion finalizo, pero no se encontro dist\\PDFCombine.exe"
}

Write-Host ""
Write-Host "Listo. Ejecutable generado en dist\\PDFCombine.exe" -ForegroundColor Green
