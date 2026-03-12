#!/usr/bin/env python3
"""
SETUP_PUBLISHER.PY - Instalador de dependencias para AutoTok Publisher
Versión: 1.0
Fecha: 2026-02-25

Instala:
  1. playwright (control del navegador)
  2. Descarga Chromium para Playwright
  3. Verifica Chrome instalado en el sistema
  4. Verifica config_publisher.json

USO:
  python scripts/setup_publisher.py
"""

import subprocess
import sys
import os
import json
import shutil


def run_cmd(cmd, description):
    """Ejecuta un comando y muestra resultado."""
    print(f"\n{'─'*50}")
    print(f"  {description}")
    print(f"{'─'*50}")
    print(f"  $ {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           encoding='utf-8', errors='replace')

    if result.returncode == 0:
        print(f"  ✅ OK")
        if result.stdout.strip():
            for line in result.stdout.strip().split('\n')[:10]:
                print(f"    {line}")
    else:
        print(f"  ❌ ERROR (código {result.returncode})")
        if result.stderr.strip():
            for line in result.stderr.strip().split('\n')[:10]:
                print(f"    {line}")

    return result.returncode == 0


def check_python():
    """Verifica versión de Python."""
    version = sys.version_info
    print(f"\n  Python: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ❌ Se requiere Python 3.8+")
        return False

    print("  ✅ Python OK")
    return True


def check_chrome():
    """Verifica que Chrome está instalado."""
    # Rutas comunes de Chrome en Windows
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]

    for path in chrome_paths:
        if os.path.exists(path):
            print(f"\n  Chrome encontrado: {path}")
            print("  ✅ Chrome OK")
            return path

    # Intentar buscar con where/which
    chrome = shutil.which("chrome") or shutil.which("google-chrome")
    if chrome:
        print(f"\n  Chrome encontrado: {chrome}")
        print("  ✅ Chrome OK")
        return chrome

    print("\n  ❌ Chrome no encontrado")
    print("  Instala Google Chrome desde: https://www.google.com/chrome/")
    return None


def install_playwright():
    """Instala playwright y descarga navegadores."""
    # Instalar paquete
    ok = run_cmd(
        f"{sys.executable} -m pip install playwright",
        "Instalando Playwright..."
    )

    if not ok:
        print("\n  ❌ Error instalando playwright")
        print("  Intenta manualmente: pip install playwright")
        return False

    # No necesitamos descargar Chromium bundled porque usamos channel="chrome"
    # (el Chrome instalado en el sistema). Pero instalamos por si acaso.
    run_cmd(
        f"{sys.executable} -m playwright install chromium",
        "Descargando Chromium para Playwright (backup)..."
    )

    return True


def check_config():
    """Verifica config_publisher.json."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config_publisher.json')

    if not os.path.exists(config_path):
        print(f"\n  ❌ config_publisher.json no encontrado")
        print(f"  Crea el archivo en: {config_path}")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"\n  ❌ Error en config_publisher.json: {e}")
        return False

    cuentas = config.get('cuentas', {})
    if not cuentas:
        print(f"\n  ⚠️  No hay cuentas configuradas en config_publisher.json")
        return False

    print(f"\n  Cuentas configuradas: {len(cuentas)}")
    for nombre, cfg in cuentas.items():
        operadora = cfg.get('operadora', '?')
        print(f"    - {nombre} ({operadora})")

    print("  ✅ Config OK")
    return True


def verify_import():
    """Verifica que playwright se puede importar."""
    try:
        from playwright.sync_api import sync_playwright
        print("\n  ✅ Playwright importa correctamente")
        return True
    except ImportError as e:
        print(f"\n  ❌ Error importando playwright: {e}")
        return False


def main():
    print("=" * 60)
    print("  AutoTok Publisher — Setup")
    print("=" * 60)

    all_ok = True

    # 1. Python
    print("\n[1/5] Verificando Python...")
    if not check_python():
        all_ok = False

    # 2. Chrome
    print("\n[2/5] Verificando Chrome...")
    chrome = check_chrome()
    if not chrome:
        all_ok = False

    # 3. Playwright
    print("\n[3/5] Instalando Playwright...")
    if not install_playwright():
        all_ok = False

    # 4. Verificar import
    print("\n[4/5] Verificando importación...")
    if not verify_import():
        all_ok = False

    # 5. Config
    print("\n[5/5] Verificando configuración...")
    check_config()

    # Resumen
    print(f"\n{'='*60}")
    if all_ok:
        print("  ✅ Setup completado correctamente")
        print(f"\n  Próximos pasos:")
        print(f"    1. Editar config_publisher.json con los datos de cada cuenta")
        print(f"    2. Asegurarse de que Chrome está cerrado antes de publicar")
        print(f"    3. Probar con: python tiktok_publisher.py --listar")
        print(f"    4. Dry run:   python tiktok_publisher.py --cuenta X --fecha Y --dry-run")
    else:
        print("  ⚠️  Setup incompleto — revisa los errores arriba")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
