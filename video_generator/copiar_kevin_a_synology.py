"""
Copia los archivos de Kevin (publisher) a la carpeta Synology Drive.

IMPORTANTE: Ejecutar SIEMPRE que se modifique cualquier archivo de esta lista.
Claude debe ejecutar este script automáticamente tras hacer cambios en código
que afecte al publisher o la instalación de operadoras.

Arquitectura:
  - PROYECTO:  C:\\Users\\gasco\\Documents\\PROYECTOS_WEB\\autotok-videos\\video_generator
  - KEVIN:     C:\\Users\\gasco\\SynologyDrive\\kevin  (subset para operadoras)
  - VIDEOS:    C:\\Users\\gasco\\SynologyDrive\\{cuenta}\\{video_id}.mp4

Kevin NO es una copia del proyecto — es un subset curado con lo mínimo
necesario para que las operadoras ejecuten INSTALAR.bat y PUBLICAR.bat.
"""
import os
import shutil

# ── Configuración ──
ORIGEN = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(os.path.expanduser('~'), 'SynologyDrive', 'kevin')

# Archivos que necesita Kevin (el publisher) en el PC de la operadora
ARCHIVOS = [
    'publicar_facil.py',
    'tiktok_publisher.py',
    'api_client.py',
    'config.py',
    'config_publisher.json',
    'config_operadora.json',
    'VERSION',
    'INSTALAR.bat',
    'PUBLICAR.bat',
    'logger.py',
]

CARPETAS = [
    'scripts/setup_operadora.py',
    'scripts/email_notifier.py',
    'scripts/lote_manager.py',
    'scripts/db_config.py',
]

# ── Copiar ──
os.makedirs(DESTINO, exist_ok=True)
os.makedirs(os.path.join(DESTINO, 'scripts'), exist_ok=True)

copiados = 0
for f in ARCHIVOS + CARPETAS:
    src = os.path.join(ORIGEN, f)
    dst = os.path.join(DESTINO, f)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        copiados += 1
        print(f"  OK: {f}")
    else:
        print(f"  SKIP: {f} (no existe)")

# Copiar carpeta python/ (Python embebido) si existe
python_src = os.path.join(ORIGEN, 'python')
python_dst = os.path.join(DESTINO, 'python')
if os.path.exists(python_src) and not os.path.exists(python_dst):
    print(f"  Copiando python/ embebido (puede tardar)...")
    shutil.copytree(python_src, python_dst)
    print(f"  OK: python/ (embebido)")
elif os.path.exists(python_dst):
    print(f"  SKIP: python/ (ya existe)")
else:
    print(f"  [!] python/ no encontrado — la operadora necesitará Python instalado")

# Crear subcarpetas de cuentas (QUA-151: almacenamiento plano, sin calendario/)
for cuenta in ['ofertastrendy20', 'lotopdevicky', 'totokydeals']:
    synology_root = os.path.dirname(DESTINO)
    cuenta_dir = os.path.join(synology_root, cuenta)
    os.makedirs(cuenta_dir, exist_ok=True)
    print(f"  OK: {cuenta}/")

print(f"\n--- Resumen ---")
print(f"Archivos copiados: {copiados}")
print(f"Destino: {DESTINO}")
print(f"\nSynology Drive sincronizará esto al NAS automáticamente.")
