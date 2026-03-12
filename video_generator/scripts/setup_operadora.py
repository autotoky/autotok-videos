#!/usr/bin/env python3
"""
SETUP_OPERADORA.PY — Configuración automática del PC de la operadora (QUA-43)

Detecta automáticamente:
  - Ruta de chrome.exe
  - Ruta de Google Drive

Configura:
  - config_publisher.json con chrome_path del PC
  - config_operadora.json en %LOCALAPPDATA%/AutoTok/ (fuera de Synology, QUA-184)
  - Perfil limpio de Chrome para AutoTok (en LOCALAPPDATA/AutoTok_Chrome/{cuenta})
  - Login en TikTok (una sola vez, la sesión persiste)
"""

import os
import sys
import json
import subprocess
import time


# Ruta al config_publisher.json (relativa al script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_PATH = os.path.join(PROJECT_DIR, 'config_publisher.json')
CONFIG_OPERADORA_LEGACY_PATH = os.path.join(PROJECT_DIR, 'config_operadora.json')


def get_config_operadora_path():
    """Returns the path for config_operadora.json (QUA-184).

    Priority:
      1. %LOCALAPPDATA%/AutoTok/config_operadora.json (per-PC, outside Synology)
      2. kevin/config_operadora.json (legacy, shared via Synology — fallback)
    """
    localappdata = os.environ.get('LOCALAPPDATA', '')
    if localappdata:
        local_path = os.path.join(localappdata, 'AutoTok', 'config_operadora.json')
        if os.path.exists(local_path):
            return local_path
    # Fallback to legacy (kevin/)
    if os.path.exists(CONFIG_OPERADORA_LEGACY_PATH):
        return CONFIG_OPERADORA_LEGACY_PATH
    # Default: return LOCALAPPDATA path (for creation during setup)
    if localappdata:
        return os.path.join(localappdata, 'AutoTok', 'config_operadora.json')
    return CONFIG_OPERADORA_LEGACY_PATH


def detectar_chrome_exe():
    """Detecta la ruta de chrome.exe en el PC."""
    candidatos = [
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
    ]

    for ruta in candidatos:
        if ruta and os.path.isfile(ruta):
            return ruta

    return None


def detectar_drive_path():
    """Intenta detectar automáticamente la ruta de Synology Drive (o Google Drive como fallback)."""
    candidatos = []

    # Synology Drive (prioridad)
    home = os.path.expanduser('~')
    candidatos.append(os.path.join(home, 'SynologyDrive'))
    candidatos.append(os.path.join(home, 'SynologyDrive', 'AUTOTOK'))
    for letra in ['C', 'D', 'E', 'S']:
        candidatos.append(f'{letra}:\\SynologyDrive')
        candidatos.append(f'{letra}:\\SynologyDrive\\AUTOTOK')
        candidatos.append(f'{letra}:\\autotok')

    # Variable de entorno (si está configurada)
    env_path = os.environ.get('AUTOTOK_DRIVE_SYNC')
    if env_path:
        candidatos.insert(0, env_path)

    # Google Drive (fallback)
    candidatos.append('G:\\Mi unidad\\material_programar')
    candidatos.append('G:\\My Drive\\material_programar')

    for ruta in candidatos:
        if os.path.exists(ruta):
            return ruta

    return None


def abrir_chrome_para_login(chrome_exe, cuenta):
    """Abre Chrome con el perfil limpio de AutoTok para que la operadora haga login en TikTok.

    El perfil se crea en LOCALAPPDATA/AutoTok_Chrome/{cuenta}.
    La primera vez estará vacío — la operadora debe hacer login.
    La sesión queda guardada para futuras ejecuciones.

    Returns:
        bool: True si la operadora confirmó que hizo login
    """
    localappdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    autotok_data = os.path.join(localappdata, 'AutoTok_Chrome', cuenta)
    os.makedirs(autotok_data, exist_ok=True)

    print("  ─────────────────────────────────────────────")
    print()
    print("  Ahora vamos a abrir Chrome para que hagas login en TikTok.")
    print("  Se abrirá una ventana de Chrome especial para AutoTok.")
    print()
    print("  Pasos:")
    print("    1. Se abrirá Chrome con TikTok")
    print("    2. Inicia sesión con tu cuenta de TikTok")
    print("    3. Cuando estés logueada, CIERRA Chrome")
    print("    4. Vuelve aquí y pulsa ENTER")
    print()
    input("  Pulsa ENTER para abrir Chrome...")

    # Abrir Chrome con perfil limpio de AutoTok apuntando a TikTok Studio
    chrome_cmd = [
        chrome_exe,
        f'--user-data-dir={autotok_data}',
        '--profile-directory=Default',
        '--no-first-run',
        '--no-default-browser-check',
        'https://www.tiktok.com/',
    ]

    try:
        process = subprocess.Popen(
            chrome_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        print()
        print("  Chrome abierto. Haz login en TikTok.")
        print("  Cuando hayas terminado, CIERRA Chrome y vuelve aquí.")
        print()
        input("  Pulsa ENTER cuando hayas cerrado Chrome...")

        # Esperar a que Chrome se cierre (si no lo hizo ya)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass

        # Verificar que hay datos de perfil guardados
        default_path = os.path.join(autotok_data, 'Default')
        if os.path.exists(default_path):
            print("  [OK] Sesión de Chrome guardada correctamente")
            return True
        else:
            print("  [OK] Perfil de Chrome creado")
            return True

    except FileNotFoundError:
        print(f"  [!] No se pudo abrir Chrome: {chrome_exe}")
        return False
    except Exception as e:
        print(f"  [!] Error al abrir Chrome: {e}")
        return False


def main():
    print()
    print("  ============================================")
    print("         AUTOTOK — Configurar PC operadora")
    print("  ============================================")
    print()

    # ── 1. Cargar config actual ──
    if not os.path.exists(CONFIG_PATH):
        print(f"  [!] No se encontró config_publisher.json")
        print(f"  [!] Ruta esperada: {CONFIG_PATH}")
        input("\n  Pulsa ENTER para salir...")
        return 1

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)

    cuentas = config.get('cuentas', {})
    if not cuentas:
        print("  [!] No hay cuentas configuradas en config_publisher.json")
        input("\n  Pulsa ENTER para salir...")
        return 1

    # ── 2. Seleccionar cuenta ──
    nombres_cuenta = list(cuentas.keys())
    print(f"  Cuentas disponibles:")
    print()
    for i, nombre in enumerate(nombres_cuenta, 1):
        operadora = cuentas[nombre].get('operadora', '?')
        print(f"    {i}. {nombre} ({operadora})")
    print()

    while True:
        raw = input("  ¿Qué cuenta vas a usar? (número): ").strip()
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(nombres_cuenta):
                cuenta = nombres_cuenta[idx]
                break
        except ValueError:
            pass
        print("  Número no válido.")

    print(f"\n  [OK] Cuenta seleccionada: {cuenta}")
    print()

    # ── 3. Detectar chrome.exe ──
    chrome_exe = detectar_chrome_exe()
    if chrome_exe:
        print(f"  [OK] Chrome encontrado: {chrome_exe}")
    else:
        print("  [!] No se encontró chrome.exe automáticamente.")
        chrome_exe = input("  Pega la ruta completa a chrome.exe: ").strip().strip('"')
        if not os.path.isfile(chrome_exe):
            print(f"  [!] No se encontró: {chrome_exe}")
            input("\n  Pulsa ENTER para salir...")
            return 1

    print()

    # ── 4. Detectar carpeta sincronizada (Synology Drive / Google Drive) ──
    drive_path = detectar_drive_path()
    if drive_path:
        print(f"  [OK] Carpeta sincronizada detectada: {drive_path}")
        respuesta = input("  ¿Es correcto? (S/N): ").strip().upper()
        if respuesta not in ('S', 'SI', 'SÍ', 'Y', 'YES', ''):
            drive_path = None

    if not drive_path:
        drive_path = input("  Ruta a la carpeta sincronizada (ej: C:\\Users\\TU_USUARIO\\SynologyDrive): ").strip()
        drive_path = drive_path.strip('"')

    print()

    # ── 5. Verificar cuenta en config_publisher.json ──
    # QUA-184: NO escribir chrome_path aquí — config_publisher.json es compartido
    # via Synology. chrome_path va en config_operadora.json (per-PC).
    if cuenta in cuentas:
        print(f"  [OK] Cuenta '{cuenta}' encontrada en config_publisher.json")
    else:
        print(f"  [!] La cuenta '{cuenta}' no existe en config_publisher.json")
        print(f"  [!] Pide a Sara que la añada.")

    # ── 6. Crear config_operadora.json en LOCALAPPDATA (QUA-184) ──
    config_op = {
        'cuenta': cuenta,
        'chrome_path': chrome_exe,
        'drive_path': drive_path,
        'api_url': 'https://autotok-api-git-main-autotoky-6890s-projects.vercel.app',
        'api_key': 'ud4sHrM42urTVE7mH6s6WZTSqKxpTrLygR_oyEYogDw',
    }

    # Guardar en LOCALAPPDATA (fuera de Synology, per-PC)
    localappdata = os.environ.get('LOCALAPPDATA', '')
    if localappdata:
        local_config_dir = os.path.join(localappdata, 'AutoTok')
        os.makedirs(local_config_dir, exist_ok=True)
        local_config_path = os.path.join(local_config_dir, 'config_operadora.json')
        with open(local_config_path, 'w', encoding='utf-8') as f:
            json.dump(config_op, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print(f"  [OK] config_operadora.json creado en {local_config_dir}")
    else:
        # Fallback: guardar en kevin/ (legacy, Linux/Mac)
        with open(CONFIG_OPERADORA_LEGACY_PATH, 'w', encoding='utf-8') as f:
            json.dump(config_op, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print(f"  [OK] config_operadora.json creado (legacy)")

    # QUA-184: NO escribir en kevin/ — cada PC usa su LOCALAPPDATA.
    # El legacy kevin/config_operadora.json se ignora si existe LOCALAPPDATA.

    # ── 7. Verificar carpeta de cuenta en Drive ──
    cuenta_dir = os.path.join(drive_path, cuenta)
    if os.path.exists(cuenta_dir):
        print(f"  [OK] Carpeta de cuenta encontrada")
    else:
        print(f"  [!] No se encontró {cuenta_dir}")
        print(f"  [!] Asegúrate de que Synology Drive está sincronizado")

    print()

    # ── 8. Login en TikTok ──
    login_ok = abrir_chrome_para_login(chrome_exe, cuenta)

    print()
    print("  ============================================")
    if login_ok:
        print("         Configuración completada!")
    else:
        print("    Configuración completada (sin login)")
        print("    Ejecuta INSTALAR.bat de nuevo si")
        print("    necesitas hacer login en TikTok.")
    print("  ============================================")
    print()
    print("  Para publicar videos, haz doble-click en PUBLICAR.bat")
    print()
    input("  Pulsa ENTER para salir...")
    return 0


if __name__ == '__main__':
    sys.exit(main())
