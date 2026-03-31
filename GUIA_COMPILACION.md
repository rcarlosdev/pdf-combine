# Guia de compilacion de PDFCombine

## 1. Abrir PowerShell en la carpeta del proyecto

```powershell
cd C:\Users\Admin\Documents\DEV\PY\pdf-combine
```

## 2. Verificar que exista el entorno virtual

Debe existir esta ruta:

```text
env\Scripts\python.exe
```

Si no existe, primero crea o restaura el entorno virtual del proyecto.

## 3. Instalar dependencias de la aplicacion

```powershell
.\env\Scripts\pip.exe install -r .\requirements.txt
```

## 4. Instalar dependencias de compilacion

```powershell
.\env\Scripts\pip.exe install -r .\requirements-build.txt
```

## 5. Generar solo el ejecutable

Este paso crea el archivo `.exe` de la aplicacion.

```powershell
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```

Resultado esperado:

```text
dist\PDFCombine.exe
```

## 6. Generar el instalador completo

Este script compila primero el ejecutable y luego crea el instalador.

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

Resultado esperado:

```text
installer-output\PDFCombine-Setup.exe
```

## 7. Compartir la aplicacion

El archivo que debes compartir es:

```text
installer-output\PDFCombine-Setup.exe
```

No es necesario compartir la carpeta `dist` si ya vas a entregar el instalador.

## 8. Desinstalacion

El instalador generado incluye desinstalador.

Se puede quitar desde:

- Configuracion de Windows > Aplicaciones
- Panel de control > Programas
- El desinstalador instalado junto con la aplicacion

Ademas, al desinstalar, el instalador tambien intenta limpiar carpetas de datos de usuario de `PDFCombine`.

## 9. Problemas comunes

### PowerShell bloquea la ejecucion del script

Ejecuta exactamente:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

### No se encuentra Inno Setup

Instala Inno Setup 6 o define la variable `INNO_SETUP_COMPILER` apuntando a `ISCC.exe`.

Ejemplo:

```powershell
$env:INNO_SETUP_COMPILER="C:\Users\Admin\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

### No se encuentra `pypdf`, `pyinstaller` o `pillow`

Reinstala dependencias:

```powershell
.\env\Scripts\pip.exe install -r .\requirements.txt
.\env\Scripts\pip.exe install -r .\requirements-build.txt
```

## 10. Resumen rapido

Generar instalador en un solo paso:

```powershell
cd C:\Users\Admin\Documents\DEV\PY\pdf-combine
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```
