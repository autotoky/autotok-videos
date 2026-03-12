@echo off
title AutoTok - Instalacion
cd /d "%~dp0"

echo.
echo   ============================================
echo          AUTOTOK - Instalacion inicial
echo   ============================================
echo.

:: Usar Python embebido local
set PYTHON=%~dp0python\python.exe

:: Descargar Python embebido si no existe
if not exist "%PYTHON%" (
    echo   Python no encontrado. Descargando Python embebido...
    echo.
    mkdir python 2>nul
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip' -OutFile 'python\python_embed.zip'"
    if not exist "python\python_embed.zip" (
        echo   [!] Error descargando Python. Verifica tu conexion a internet.
        pause
        exit /b 1
    )
    powershell -Command "Expand-Archive -Path 'python\python_embed.zip' -DestinationPath 'python' -Force"
    del "python\python_embed.zip"
    echo   [OK] Python descargado y extraido
    echo.
    echo   Descargando get-pip.py...
    powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'python\get-pip.py'"
    echo   [OK] get-pip.py descargado
    echo.
)

:: Verificar que existe el Python embebido
if not exist "%PYTHON%" (
    echo   [!] No se encontro Python tras la descarga.
    echo   [!] Algo ha fallado. Contacta con Sara.
    echo.
    pause
    exit /b 1
)

echo   [OK] Python encontrado
echo.

:: Habilitar import site para que pip funcione
:: Buscar el archivo ._pth y descomentar "import site"
for %%f in (python\python3*._pth) do (
    findstr /v /b "#" "%%f" > nul 2>&1
    echo   Habilitando pip en Python embebido...
    powershell -Command "(Get-Content '%%f') -replace '^#import site','import site' | Set-Content '%%f'"
    echo   [OK] Python configurado
)
echo.

:: Instalar pip si no existe
if not exist "python\Scripts\pip.exe" (
    if exist "python\get-pip.py" (
        echo   Instalando pip...
        "%PYTHON%" python\get-pip.py --no-warn-script-location
        echo   [OK] pip instalado
    ) else (
        echo   [!] No se encontro get-pip.py en la carpeta python\
        echo   [!] Descargalo de https://bootstrap.pypa.io/get-pip.py
        pause
        exit /b 1
    )
) else (
    echo   [OK] pip ya instalado
)
echo.

:: Instalar dependencias
echo   Instalando dependencias...
"%PYTHON%" -m pip install playwright --no-warn-script-location --quiet
echo   [OK] Playwright instalado
echo.

:: Instalar navegador Chromium para Playwright
echo   Instalando navegador (puede tardar un minuto)...
"%PYTHON%" -m playwright install chromium
echo   [OK] Navegador instalado
echo.

:: Configurar PC de la operadora (Chrome, Drive, cuenta)
echo   Ahora vamos a configurar tu PC...
echo.
"%PYTHON%" scripts\setup_operadora.py
