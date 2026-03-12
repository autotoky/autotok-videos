#!/usr/bin/env python3
"""
CLI.PY - Interfaz interactiva para tareas comunes de AutoTok
Versión: 2.0 - Con contador de progreso y dashboard
Fecha: 2026-02-16

Uso:
    python cli.py
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# Añadir parent directory al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from scripts.db_config import get_connection
except ImportError:
    print("Error: No se puede importar db_config")
    print("   Asegurate de ejecutar desde la raiz del proyecto")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════
# UTILIDADES
# ═══════════════════════════════════════════════════════════

def clear_screen():
    """Limpia la pantalla"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Imprime encabezado del CLI"""
    print()
    print("  ══════════════════════════════════════════════════════")
    print("        🎬  AUTOTOK - PÍDELE A KEVIN LO QUE QUIERAS")
    print("  ══════════════════════════════════════════════════════")
    print()

def print_menu():
    """Imprime menu principal"""
    print("  🎞️   GENERAR VIDEOS")
    print("  ─────────────────────────────────────────────")
    print("   4.  🎞️   Generar videos para un producto")
    print("   5.  🎞️   Generar videos para MULTIPLES productos")
    print()
    print("  📅  PROGRAMACIÓN")
    print("  ─────────────────────────────────────────────")
    print("   8.  ↩️   Deshacer programacion")
    print()
    print("  🎨  MATERIAL IA")
    print("  ─────────────────────────────────────────────")
    print("  15.  🖼️   Generar fondos con IA (screenshot)")
    print("  16.  👁️   Revisar y aprobar material generado")
    print()
    print("  📤  PUBLICACIÓN TIKTOK")
    print("  ─────────────────────────────────────────────")
    print("  20.  🚀  Publicar videos en TikTok Studio")
    print()
    print("   0.  🚪  Salir")
    print()

def format_time(seconds):
    """Formatea segundos a string legible"""
    if seconds < 60:
        return f"{seconds:.0f} seg"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins} min {secs:02d} seg"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins:02d}min"

def make_progress_bar(current, total, width=30):
    """Genera barra de progreso visual"""
    if total == 0:
        return "[" + " " * width + "]   0%"
    pct = current / total
    filled = int(width * pct)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {pct * 100:5.1f}%"

def get_productos_lista():
    """Obtiene lista de productos de la BD"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM productos ORDER BY nombre")
        return cursor.fetchall()

def seleccionar_producto():
    """Permite al usuario seleccionar un producto"""
    productos = get_productos_lista()

    if not productos:
        print("\n[!] No hay productos en la base de datos")
        input("\nPresiona Enter para continuar...")
        return None

    print("\nPRODUCTOS DISPONIBLES:")
    print()

    for i, prod in enumerate(productos, 1):
        print(f"  {i}. {prod['nombre']}")

    print()
    print("  0. Cancelar")
    print()

    while True:
        try:
            opcion = input("Selecciona un producto (numero): ").strip()

            if opcion == "0":
                return None

            idx = int(opcion) - 1
            if 0 <= idx < len(productos):
                return productos[idx]['nombre']
            else:
                print("[!] Opcion invalida")
        except ValueError:
            print("[!] Introduce un numero valido")

def seleccionar_o_crear_producto():
    """Permite seleccionar un producto existente o crear uno nuevo"""
    productos = get_productos_lista()

    print("\nPRODUCTOS DISPONIBLES:")
    print()

    for i, prod in enumerate(productos, 1):
        print(f"  {i}. {prod['nombre']}")

    print()
    print(f"  N. Crear producto NUEVO")
    print("  0. Cancelar")
    print()

    while True:
        opcion = input("Selecciona un producto (numero o N): ").strip()

        if opcion == "0":
            return None

        if opcion.upper() == "N":
            nombre = input("\nNombre del nuevo producto: ").strip().lower()
            if not nombre:
                print("[!] Nombre vacio")
                continue

            # Comprobar si ya existe
            for prod in productos:
                if prod['nombre'].lower() == nombre:
                    print(f"[!] Ya existe el producto '{prod['nombre']}'")
                    return prod['nombre']

            # Crear en BD
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO productos (nombre) VALUES (?)", (nombre,))
                conn.commit()
                print(f"[OK] Producto creado: {nombre}")

            # Crear carpetas de recursos
            from config import RECURSOS_BASE
            producto_dir = os.path.join(RECURSOS_BASE, nombre)
            for subcarpeta in ["hooks", "brolls", "audios", "screenshots"]:
                os.makedirs(os.path.join(producto_dir, subcarpeta), exist_ok=True)
            print(f"[OK] Carpetas creadas en: {producto_dir}")
            print(f"     Coloca los screenshots en: {os.path.join(producto_dir, 'screenshots')}")

            return nombre

        try:
            idx = int(opcion) - 1
            if 0 <= idx < len(productos):
                return productos[idx]['nombre']
            else:
                print("[!] Opcion invalida")
        except ValueError:
            print("[!] Introduce un numero valido o N")

def _cargar_cuentas_activas():
    """Carga cuentas activas desde config_cuentas.json."""
    config_path = os.path.join(os.path.dirname(__file__), 'config_cuentas.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return [k for k, v in config.items() if v.get('activa', False)]
    except Exception:
        # Fallback hardcodeado por si falla la lectura
        return ["ofertastrendy20", "lotopdevicky"]

def seleccionar_cuentas():
    """Menu comun de seleccion de cuentas. Retorna lista de cuentas o None."""
    cuentas = _cargar_cuentas_activas()

    print()
    print("CUENTAS DISPONIBLES:")
    print()
    for i, cuenta in enumerate(cuentas, 1):
        print(f"  {i}. {cuenta}")
    if len(cuentas) > 1:
        print(f"  {len(cuentas) + 1}. Todas las cuentas")
    print("  0. Cancelar")
    print()

    opcion = input("Selecciona cuenta: ").strip()

    if opcion == "0":
        return None

    try:
        idx = int(opcion)
        if 1 <= idx <= len(cuentas):
            return [cuentas[idx - 1]]
        elif idx == len(cuentas) + 1 and len(cuentas) > 1:
            return cuentas
    except ValueError:
        pass

    print("[!] Opcion invalida")
    return None

# ═══════════════════════════════════════════════════════════
# CONTADOR DE PROGRESO
# ═══════════════════════════════════════════════════════════

class ProgressTracker:
    """Tracker de progreso para generacion de videos con display visual"""

    def __init__(self, total_videos, total_productos, total_cuentas):
        self.total_videos = total_videos
        self.total_productos = total_productos
        self.total_cuentas = total_cuentas
        self.start_time = time.time()
        self.videos_completados = 0
        self.videos_exitosos = 0
        self.videos_fallidos = 0
        self.errores = []  # lista de (video_id, error_msg)
        self.ultimo_video = None
        self.producto_actual = ""
        self.cuenta_actual = ""
        self.producto_num = 0

    def set_context(self, producto, cuenta, producto_num):
        """Actualiza contexto de producto/cuenta actual"""
        self.producto_actual = producto
        self.cuenta_actual = cuenta
        self.producto_num = producto_num

    def on_video_progress(self, info):
        """Callback llamado por VideoGenerator tras cada video"""
        self.videos_completados += 1

        if info.get("success"):
            self.videos_exitosos += 1
            self.ultimo_video = info.get("video_id", "")
        else:
            self.videos_fallidos += 1
            self.errores.append((
                info.get("video_id", "desconocido"),
                info.get("error_msg", "Error desconocido")
            ))

        self._print_progress(info)

    def _print_progress(self, info):
        """Muestra el estado de progreso actual"""
        elapsed = time.time() - self.start_time
        speed = self.videos_completados / elapsed if elapsed > 0 else 0
        remaining = (self.total_videos - self.videos_completados) / speed if speed > 0 else 0

        video_num = info.get("video_num", 0)
        video_total = info.get("total", 0)

        # Limpiar y mostrar progreso
        print()
        print("=" * 60)
        print("  GENERACION EN CURSO")
        print("=" * 60)
        print()
        print(f"  Producto:    {self.producto_num} / {self.total_productos}   {self.producto_actual}")
        print(f"  Cuenta:      {self.cuenta_actual}")
        print(f"  Video:       {video_num} / {video_total}")
        print()
        print("  " + "-" * 56)
        print(f"  Progreso global:  {self.videos_completados} / {self.total_videos}")
        print(f"  {make_progress_bar(self.videos_completados, self.total_videos)}")
        print("  " + "-" * 56)
        print()
        print(f"  Transcurrido:    {format_time(elapsed)}")
        print(f"  Estimado:        {format_time(remaining)} restantes")
        speed_min = speed * 60  # convertir de videos/seg a videos/min
        if speed_min >= 1:
            print(f"  Velocidad:       {speed_min:.1f} videos/min")
        else:
            speed_hour = speed * 3600
            print(f"  Velocidad:       {speed_hour:.1f} videos/hora")
        print()

        if self.ultimo_video:
            # Mostrar solo el nombre del archivo, no la ruta completa
            nombre_corto = self.ultimo_video
            if len(nombre_corto) > 50:
                nombre_corto = "..." + nombre_corto[-47:]
            status = "[OK]" if info.get("success") else "[ERROR]"
            print(f"  {status} {nombre_corto}")

        print("=" * 60)

    def print_summary(self):
        """Muestra resumen final de generacion"""
        elapsed = time.time() - self.start_time
        speed_min = self.videos_completados / elapsed * 60 if elapsed > 0 else 0

        print()
        print("=" * 60)

        if self.videos_fallidos == 0:
            print("  [OK] GENERACION COMPLETADA")
        else:
            print("  [!] GENERACION COMPLETADA CON ERRORES")

        print("=" * 60)
        print()
        print(f"  Total videos:     {self.videos_completados}")

        if self.videos_completados > 0:
            pct_ok = self.videos_exitosos / self.videos_completados * 100
            pct_fail = self.videos_fallidos / self.videos_completados * 100
            print(f"  Exitosos:         {self.videos_exitosos}  ({pct_ok:.1f}%)")
            print(f"  Errores:          {self.videos_fallidos}  ({pct_fail:.1f}%)")

        print(f"  Tiempo total:     {format_time(elapsed)}")
        if speed_min >= 1:
            print(f"  Velocidad media:  {speed_min:.1f} videos/min")
        else:
            print(f"  Velocidad media:  {speed_min * 60:.1f} videos/hora")

        if self.errores:
            print()
            print("  Detalle de errores:")
            for video_id, error_msg in self.errores[:10]:
                nombre_corto = video_id
                if len(nombre_corto) > 40:
                    nombre_corto = "..." + nombre_corto[-37:]
                print(f"     - {nombre_corto}: {error_msg}")
            if len(self.errores) > 10:
                print(f"     ... y {len(self.errores) - 10} errores mas")

        print()
        print("=" * 60)

# ═══════════════════════════════════════════════════════════
# FUNCIONES DE MENU

def _run_generation_with_progress(productos_list, cuentas, cantidad, bof_id=None):
    """Ejecuta generacion con contador de progreso integrado.

    Args:
        productos_list: Lista de dicts con al menos 'nombre'
        cuentas: Lista de nombres de cuenta
        cantidad: Videos por producto por cuenta
        bof_id: ID de BOF específico a usar (None = auto-selección)
    """
    from config import validate_config
    from generator import VideoGenerator

    if not validate_config():
        print("\n[!] Configura config.py antes de continuar")
        input("\nPresiona Enter para continuar...")
        return

    total_productos = len(productos_list)
    total_videos = total_productos * len(cuentas) * cantidad

    tracker = ProgressTracker(total_videos, total_productos, len(cuentas))

    for idx, producto_info in enumerate(productos_list, 1):
        nombre = producto_info['nombre'] if hasattr(producto_info, '__getitem__') and not isinstance(producto_info, str) else producto_info

        for cuenta in cuentas:
            tracker.set_context(nombre, cuenta, idx)

            try:
                with VideoGenerator(nombre, cuenta=cuenta, bof_id=bof_id) as generator:
                    results = generator.generate_batch(
                        batch_size=cantidad,
                        progress_callback=tracker.on_video_progress
                    )
            except Exception as e:
                print(f"\n[ERROR] Error generando {nombre} / {cuenta}: {e}")
                remaining = cantidad - (tracker.videos_completados % cantidad if tracker.videos_completados % cantidad != 0 else 0)
                for _ in range(remaining):
                    tracker.videos_completados += 1
                    tracker.videos_fallidos += 1
                    tracker.errores.append((f"{nombre}_{cuenta}", str(e)))

    tracker.print_summary()
    input("\nPresiona Enter para continuar...")


def generar_videos():
    """Genera videos para un producto"""
    clear_screen()
    print_header()
    print("GENERAR VIDEOS")
    print()

    producto = seleccionar_producto()
    if not producto:
        return

    # Preguntar si quiere forzar un BOF concreto
    bof_id = None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM productos WHERE nombre = ?", (producto,))
        row = cursor.fetchone()
        if row:
            producto_id = row['id']
            cursor.execute("""
                SELECT pb.id, pb.deal_math, pb.activo,
                       (SELECT COUNT(*) FROM audios WHERE bof_id = pb.id) as num_audios
                FROM producto_bofs pb
                WHERE pb.producto_id = ?
                ORDER BY pb.id
            """, (producto_id,))
            bofs = [dict(r) for r in cursor.fetchall()]

            if len(bofs) > 1:
                print("  BOFs disponibles:")
                print()
                for i, bof in enumerate(bofs, 1):
                    estado = "ACTIVO" if bof['activo'] else "INACTIVO"
                    print(f"    {i}. [ID:{bof['id']}] {bof['deal_math']} ({estado}, {bof['num_audios']} audios)")
                print()
                print("    Enter = auto (usa BOFs activos con audios)")
                print()
                sel = input("  Forzar un BOF concreto? (numero o Enter): ").strip()
                if sel:
                    try:
                        idx = int(sel) - 1
                        if 0 <= idx < len(bofs):
                            bof_id = bofs[idx]['id']
                            if not bofs[idx]['activo']:
                                print(f"\n  [!] ATENCION: BOF {bof_id} esta INACTIVO")
                                confirma = input("      Usar igualmente? (S/N): ").strip().upper()
                                if confirma != "S":
                                    bof_id = None
                            if bof_id and bofs[idx]['num_audios'] == 0:
                                print(f"\n  [!] ERROR: BOF {bof_id} no tiene audios, no se pueden generar videos")
                                input("\nPresiona Enter para continuar...")
                                return
                            if bof_id:
                                print(f"\n  Forzando BOF {bof_id}: {bofs[idx]['deal_math']}")
                    except (ValueError, IndexError):
                        print("  [!] Seleccion invalida, usando auto")
                print()

    cuentas = seleccionar_cuentas()
    if not cuentas:
        return

    print()
    cantidad = input("Cuantos videos generar? (default: 20): ").strip()
    if not cantidad:
        cantidad = "20"

    try:
        cantidad = int(cantidad)
    except ValueError:
        print("[!] Cantidad invalida")
        input("\nPresiona Enter para continuar...")
        return

    print()
    bof_msg = f" (BOF forzado: {bof_id})" if bof_id else " (auto)"
    print(f"Generando {cantidad} videos de {producto}{bof_msg}")
    print(f"Cuentas: {', '.join(cuentas)}")
    print("(es_ia se hereda automaticamente del formato)")
    print()

    _run_generation_with_progress([{"nombre": producto}], cuentas, cantidad, bof_id=bof_id)

def generar_videos_multiples():
    """Genera videos para multiples productos en batch"""
    clear_screen()
    print_header()
    print("GENERAR VIDEOS - MULTIPLES PRODUCTOS")
    print()

    # Obtener productos con material completo
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.id,
                p.nombre,
                (SELECT COUNT(*) FROM material WHERE producto_id = p.id AND tipo = 'hook') as hooks,
                (SELECT COUNT(*) FROM material WHERE producto_id = p.id AND tipo = 'broll') as brolls,
                (SELECT COUNT(*) FROM audios WHERE producto_id = p.id) as audios,
                (SELECT COUNT(*) FROM producto_bofs WHERE producto_id = p.id) as bofs
            FROM productos p
            ORDER BY p.nombre
        """)

        productos = cursor.fetchall()

    # Filtrar solo productos con material completo
    productos_listos = [
        p for p in productos
        if p['hooks'] >= 10 and p['brolls'] >= 20 and p['audios'] >= 3 and p['bofs'] >= 1
    ]

    if not productos_listos:
        print("[!] No hay productos con material completo")
        input("\nPresiona Enter para continuar...")
        return

    print("PRODUCTOS CON MATERIAL COMPLETO:")
    print()

    for i, prod in enumerate(productos_listos, 1):
        print(f"  {i}. {prod['nombre']}")

    print()
    print("Selecciona productos (separados por coma, ej: 1,3,5)")
    print("O escribe 'todos' para seleccionar todos")
    print("0. Cancelar")
    print()

    seleccion = input("Productos a generar: ").strip().lower()

    if seleccion == "0":
        return

    # Procesar seleccion
    if seleccion == "todos":
        productos_seleccionados = productos_listos
    else:
        try:
            indices = [int(x.strip()) - 1 for x in seleccion.split(",")]
            productos_seleccionados = [productos_listos[i] for i in indices if 0 <= i < len(productos_listos)]
        except (ValueError, IndexError):
            print("[!] Seleccion invalida")
            input("\nPresiona Enter para continuar...")
            return

    if not productos_seleccionados:
        print("[!] No se selecciono ningun producto valido")
        input("\nPresiona Enter para continuar...")
        return

    cuentas = seleccionar_cuentas()
    if not cuentas:
        return

    print()
    cantidad = input("Cuantos videos generar por producto? (default: 20): ").strip()
    if not cantidad:
        cantidad = "20"

    try:
        cantidad = int(cantidad)
    except ValueError:
        print("[!] Cantidad invalida")
        input("\nPresiona Enter para continuar...")
        return

    # Resumen
    total = len(productos_seleccionados) * len(cuentas) * cantidad
    print()
    print("=" * 60)
    print("  RESUMEN DE GENERACION")
    print("=" * 60)
    print(f"Productos: {len(productos_seleccionados)}")
    for p in productos_seleccionados:
        print(f"  - {p['nombre']}")
    print(f"Cuentas: {', '.join(cuentas)}")
    print(f"Videos por producto por cuenta: {cantidad}")
    print(f"Total videos a generar: {total}")
    print("=" * 60)
    print()

    print("(es_ia se hereda automaticamente del formato)")
    print()

    confirmacion = input("Continuar? (SI para confirmar): ").strip()

    if confirmacion != "SI":
        print("\n[!] Generacion cancelada")
        input("\nPresiona Enter para continuar...")
        return

    _run_generation_with_progress(productos_seleccionados, cuentas, cantidad)

def _auto_sync_lifecycle():
    """Sync lifecycle silencioso: lee Sheet Productos y actualiza estado_comercial en BD."""
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    SHEET_URL_PRODUCTOS = 'https://docs.google.com/spreadsheets/d/18b5aQZUby4JHYpnrlZPyisC-aW21z44VKxFJk_3dviQ/'
    ESTADOS_VALIDOS = {'testing', 'validated', 'top_seller', 'dropped'}

    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(SHEET_URL_PRODUCTOS)

    try:
        worksheet = spreadsheet.worksheet("PRODUCTOS")
    except Exception:
        try:
            worksheet = spreadsheet.worksheet("Productos")
        except Exception:
            worksheet = spreadsheet.sheet1

    rows = worksheet.get_all_values()
    if len(rows) <= 1:
        return

    data_rows = rows[1:]

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, estado_comercial FROM productos")
        productos_bd = {row['nombre'].lower(): dict(row) for row in cursor.fetchall()}

        cambios = 0
        for row in data_rows:
            if len(row) < 5 or not row[1].strip() or not row[4].strip():
                continue
            nombre_sheet = row[1].strip()
            estado_sheet = row[4].strip().lower()
            prod = productos_bd.get(nombre_sheet.lower())
            if not prod or estado_sheet not in ESTADOS_VALIDOS:
                continue
            if estado_sheet != (prod['estado_comercial'] or 'testing'):
                cursor.execute("UPDATE productos SET estado_comercial = ? WHERE id = ?",
                             (estado_sheet, prod['id']))
                cambios += 1

        if cambios:
            conn.commit()
            print(f"  {cambios} productos actualizados desde Sheet")

def _auto_sync_calendario(cuenta):
    """DEPRECATED (QUA-151): Ya no se sincroniza con Sheet/filesystem.
    Los estados se gestionan desde el dashboard (Turso) directamente."""
    pass

def _verificar_post_programacion(cuentas):
    """Verificación post-programación: comprueba consistencia BD ↔ archivos locales."""
    from config import OUTPUT_DIR

    problemas_total = 0

    for cuenta in cuentas:
        print(f"\n  Verificando {cuenta}...")

        with get_connection() as conn:
            cursor = conn.cursor()

            # Videos 'En Calendario' en BD
            cursor.execute("""
                SELECT id, video_id, filepath, fecha_programada, hora_programada
                FROM videos
                WHERE cuenta = ? AND estado = 'En Calendario'
                ORDER BY fecha_programada, hora_programada
            """, (cuenta,))
            videos_cal = cursor.fetchall()

        if not videos_cal:
            print(f"  [OK] Sin videos en calendario")
            continue

        sin_archivo = 0
        sin_hora = 0
        sin_fecha = 0

        for v in videos_cal:
            if not v['filepath'] or not os.path.exists(v['filepath']):
                sin_archivo += 1
            if not v['hora_programada']:
                sin_hora += 1
            if not v['fecha_programada']:
                sin_fecha += 1

        total = len(videos_cal)
        problemas = sin_archivo + sin_hora + sin_fecha

        if problemas == 0:
            print(f"  [OK] {total} videos en calendario - Todo correcto")
        else:
            problemas_total += problemas
            if sin_archivo:
                print(f"  [WARNING] {sin_archivo}/{total} videos sin archivo local")
            if sin_hora:
                print(f"  [WARNING] {sin_hora}/{total} videos sin hora programada")
            if sin_fecha:
                print(f"  [WARNING] {sin_fecha}/{total} videos sin fecha programada")

        # Verificar que no hay horas duplicadas el mismo día
        cursor_dup = get_connection().cursor()
        cursor_dup.execute("""
            SELECT fecha_programada, hora_programada, COUNT(*) as cnt
            FROM videos
            WHERE cuenta = ? AND estado IN ('En Calendario', 'Borrador', 'Programado')
            AND hora_programada IS NOT NULL
            GROUP BY fecha_programada, hora_programada
            HAVING cnt > 1
        """, (cuenta,))
        duplicados = cursor_dup.fetchall()

        if duplicados:
            problemas_total += len(duplicados)
            print(f"  [WARNING] {len(duplicados)} horas duplicadas detectadas:")
            for d in duplicados[:5]:
                print(f"    {d['fecha_programada']} {d['hora_programada']} -> {d['cnt']} videos")

    if problemas_total == 0:
        print(f"\n  [OK] Verificación completada sin problemas")
    else:
        print(f"\n  [!] {problemas_total} problemas detectados. Revisa los warnings.")

def deshacer_programacion():
    """Permite deshacer una programacion de calendario"""
    clear_screen()
    print_header()
    print("DESHACER PROGRAMACION")
    print()

    cuentas = seleccionar_cuentas()
    if not cuentas:
        return

    # Para simplificar, trabajamos con una cuenta a la vez
    cuenta = cuentas[0] if len(cuentas) == 1 else None
    if not cuenta:
        print("Selecciona una sola cuenta para deshacer:")
        print()
        print("  1. ofertastrendy20")
        print("  2. lotopdevicky")
        print("  0. Cancelar")
        print()
        opcion = input("Cuenta: ").strip()
        if opcion == "1":
            cuenta = "ofertastrendy20"
        elif opcion == "2":
            cuenta = "lotopdevicky"
        else:
            return

    # Mostrar programaciones actuales agrupadas por rango de fechas
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                fecha_programada,
                COUNT(*) as total
            FROM videos
            WHERE cuenta = ? AND estado = 'En Calendario'
            GROUP BY fecha_programada
            ORDER BY fecha_programada
        """, (cuenta,))
        fechas = cursor.fetchall()

    if not fechas:
        print(f"[!] No hay videos En Calendario para {cuenta}")
        input("\nPresiona Enter para continuar...")
        return

    total_calendario = sum(f['total'] for f in fechas)
    print(f"Videos En Calendario para {cuenta}: {total_calendario}")
    print()
    print("Fechas programadas:")
    for f in fechas:
        print(f"  {f['fecha_programada']}  ->  {f['total']} videos")
    print()

    print("Que quieres deshacer?")
    print()
    print("  1. Ultima tanda (bloque de fechas mas reciente)")
    print("  2. Desde una fecha especifica")
    print("  3. TODO el calendario de esta cuenta")
    print("  0. Cancelar")
    print()

    opcion = input("Opcion: ").strip()

    if opcion == "0":
        return

    try:
        from rollback_calendario import rollback_calendario, get_videos_en_calendario
    except ImportError:
        print("[!] rollback_calendario eliminado (QUA-148). Usa BD directamente.")
        input("\nPresiona Enter para continuar...")
        return

    if opcion == "1":
        videos = get_videos_en_calendario(cuenta, ultima=True)
    elif opcion == "2":
        print()
        fecha = input("Desde que fecha? (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            print("[!] Formato invalido")
            input("\nPresiona Enter para continuar...")
            return
        videos = get_videos_en_calendario(cuenta, fecha_desde=fecha)
    elif opcion == "3":
        videos = get_videos_en_calendario(cuenta)
    else:
        print("[!] Opcion invalida")
        input("\nPresiona Enter para continuar...")
        return

    if not videos:
        print("[!] No se encontraron videos con esos criterios")
        input("\nPresiona Enter para continuar...")
        return

    # Confirmar
    print()
    print(f"Se van a revertir {len(videos)} videos:")
    fechas_resumen = {}
    for v in videos:
        f = v['fecha_programada'] or 'Sin fecha'
        fechas_resumen[f] = fechas_resumen.get(f, 0) + 1
    for f in sorted(fechas_resumen.keys()):
        print(f"  {f}: {fechas_resumen[f]} videos")
    print()

    confirmacion = input("Continuar? (SI para confirmar): ").strip()
    if confirmacion != "SI":
        print("\n[!] Rollback cancelado")
        input("\nPresiona Enter para continuar...")
        return

    # Preguntar si usar Sheet TEST
    print("Sheet a limpiar:")
    print("  1. PROD (por defecto)")
    print("  2. TEST")
    sheet_opcion = input("Opcion (Enter para PROD): ").strip()
    test_mode = sheet_opcion == "2"

    # Ejecutar rollback
    video_ids = [v['video_id'] for v in videos]

    result = rollback_calendario(
        cuenta,
        video_ids=video_ids,
        test_mode=test_mode,
        skip_files=False,
        skip_sheet=False
    )

    # ── VERIFICACIÓN POST-ROLLBACK (Cambio 3.6) ──
    print()
    print("=" * 60)
    print("  VERIFICACIÓN POST-ROLLBACK")
    print("=" * 60)
    _verificar_post_programacion([cuenta])

    input("\nPresiona Enter para continuar...")

# ═══════════════════════════════════════════════════════════
# GESTIONAR PRODUCTOS (LIFECYCLE)
# ═══════════════════════════════════════════════════════════

ESTADO_COMERCIAL_EMOJI = {
    'testing': '🧪',
    'validated': '✅',
    'top_seller': '🔥',
    'dropped': '❌',
}

ESTADO_COMERCIAL_LABEL = {
    'testing': 'Testing',
    'validated': 'Validado',
    'top_seller': 'Top Seller',
    'dropped': 'Descartado',
}

def generar_fondos_ia():
    """Genera variaciones de fondo para screenshots de producto usando SDXL"""
    clear_screen()
    print_header()
    print("🖼️  GENERAR FONDOS CON IA")
    print()

    # Verificar dependencias
    try:
        import torch
    except ImportError:
        print("[!] PyTorch no esta instalado.")
        print("    Ejecuta: python scripts/setup_ai.py")
        input("\nPresiona Enter para continuar...")
        return

    producto = seleccionar_o_crear_producto()
    if not producto:
        return

    # Comprobar si hay screenshots en la carpeta del producto
    from config import RECURSOS_BASE
    screenshots_dir = os.path.join(RECURSOS_BASE, producto, "screenshots")
    extensiones = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}

    screenshots_producto = []
    if os.path.isdir(screenshots_dir):
        screenshots_producto = [
            os.path.join(screenshots_dir, f)
            for f in sorted(os.listdir(screenshots_dir))
            if os.path.splitext(f)[1].lower() in extensiones
        ]

    print()
    print("ORIGEN DE LOS SCREENSHOTS:")
    print()
    if screenshots_producto:
        print(f"  D. Usar carpeta del producto ({len(screenshots_producto)} imagenes encontradas)")
        print(f"     {screenshots_dir}")
    print("  1. Dar ruta a un screenshot individual")
    print("  2. Dar ruta a otra carpeta")
    print("  0. Cancelar")
    print()

    opcion = input("Opcion: ").strip().upper()

    if opcion == "0":
        return

    if opcion == "D" and screenshots_producto:
        rutas = screenshots_producto
        print(f"\n[OK] Usando {len(rutas)} imagenes de screenshots/")
    elif opcion == "1":
        ruta = input("\nRuta al screenshot (arrastra el archivo aqui): ").strip().strip('"').strip("'")
        if not os.path.isfile(ruta):
            print(f"\n[!] Archivo no encontrado: {ruta}")
            input("\nPresiona Enter para continuar...")
            return
        rutas = [ruta]
    elif opcion == "2":
        ruta = input("\nRuta a la carpeta de screenshots: ").strip().strip('"').strip("'")
        if not os.path.isdir(ruta):
            print(f"\n[!] Carpeta no encontrada: {ruta}")
            input("\nPresiona Enter para continuar...")
            return
        rutas = [
            os.path.join(ruta, f)
            for f in sorted(os.listdir(ruta))
            if os.path.splitext(f)[1].lower() in extensiones
        ]
        if not rutas:
            print(f"\n[!] No se encontraron imagenes en: {ruta}")
            input("\nPresiona Enter para continuar...")
            return
        print(f"\n[OK] Encontradas {len(rutas)} imagenes")
    else:
        print("[!] Opcion invalida")
        input("\nPresiona Enter para continuar...")
        return

    # Configurar variaciones
    print()
    from config import DEFAULT_VARIATIONS
    variaciones_input = input(f"Cuantas variaciones por imagen? (default: {DEFAULT_VARIATIONS}): ").strip()
    if variaciones_input:
        try:
            num_variaciones = int(variaciones_input)
        except ValueError:
            print("[!] Numero invalido, usando default")
            num_variaciones = DEFAULT_VARIATIONS
    else:
        num_variaciones = DEFAULT_VARIATIONS

    # Resumen
    total = len(rutas) * num_variaciones
    print()
    print("=" * 60)
    print("  RESUMEN DE GENERACION")
    print("=" * 60)
    print(f"  Producto:           {producto}")
    print(f"  Screenshots:        {len(rutas)}")
    print(f"  Variaciones/imagen: {num_variaciones}")
    print(f"  Total imagenes:     {total}")
    print()

    # Mostrar prompts que se usarán
    from config import DEFAULT_INPAINTING_PROMPTS
    prompts_a_usar = DEFAULT_INPAINTING_PROMPTS[:num_variaciones]
    print("  Fondos a generar:")
    for i, p in enumerate(prompts_a_usar, 1):
        # Mostrar solo la parte descriptiva corta
        desc = p.split(",")[0].replace("product on a ", "").replace("product on ", "").replace("product held in a ", "").replace("product ", "")
        print(f"    {i}. {desc}")

    print("=" * 60)
    print()

    confirmacion = input("Continuar? (SI para confirmar): ").strip()
    if confirmacion != "SI":
        print("\n[!] Generacion cancelada")
        input("\nPresiona Enter para continuar...")
        return

    # Ejecutar generación
    print()
    print("Cargando modelos de IA (primera vez puede tardar)...")
    print()

    try:
        from generar_material import MaterialGenerator

        generator = MaterialGenerator(producto)

        for i, ruta_img in enumerate(rutas, 1):
            nombre_img = os.path.basename(ruta_img)
            print(f"\n{'='*60}")
            print(f"  [{i}/{len(rutas)}] Procesando: {nombre_img}")
            print('='*60)

            resultado = generator.procesar_screenshot(
                ruta_img,
                num_variaciones=num_variaciones
            )

            if resultado and resultado.get('status') == 'success':
                print(f"  [OK] {resultado['num_generadas']} variaciones generadas")
                print(f"       Guardadas en: staging/{producto}/pendientes/")
            else:
                print(f"  [!] Error procesando {nombre_img}")

        print()
        print("=" * 60)
        print("  [OK] GENERACION COMPLETADA")
        print("=" * 60)
        print()
        print("  Usa la opcion 14 para revisar y aprobar las imagenes generadas.")
        print()

    except Exception as e:
        print(f"\n[ERROR] Error en la generacion: {e}")
        import traceback
        traceback.print_exc()

    input("\nPresiona Enter para continuar...")

def revisar_material_ia():
    """Revisa y aprueba/rechaza material generado por IA"""
    clear_screen()
    print_header()
    print("👁️  REVISAR Y APROBAR MATERIAL GENERADO")
    print()

    producto = seleccionar_producto()
    if not producto:
        return

    try:
        from generar_material import StagingManager
    except ImportError:
        print("[!] Error importando generar_material")
        input("\nPresiona Enter para continuar...")
        return

    staging = StagingManager(producto)
    sesiones = staging.listar_pendientes()

    if not sesiones:
        print(f"\n[!] No hay imagenes pendientes de revision para {producto}")
        input("\nPresiona Enter para continuar...")
        return

    total_imgs = sum(s['num_imagenes'] for s in sesiones)

    print(f"MATERIAL PENDIENTE PARA: {producto}")
    print()
    print(f"  Sesiones:         {len(sesiones)}")
    print(f"  Total imagenes:   {total_imgs}")
    print()

    for i, s in enumerate(sesiones, 1):
        origen_corto = os.path.basename(s['origen'])[:30]
        print(f"  {i}. {s['sesion'][:30]}  ({s['num_imagenes']} imgs) - {origen_corto}")

    print()
    print("OPCIONES:")
    print()
    print("  A. Abrir carpeta de pendientes en Explorer")
    print("  S. Aprobar TODA una sesion (mover a material)")
    print("  R. Rechazar TODA una sesion")
    print("  0. Volver")
    print()

    opcion = input("Opcion: ").strip().upper()

    if opcion == "0":
        return

    if opcion == "A":
        carpeta_pendientes = staging.pendientes_dir
        if os.name == 'nt':
            os.system(f'explorer "{os.path.abspath(carpeta_pendientes)}"')
        else:
            os.system(f'xdg-open "{os.path.abspath(carpeta_pendientes)}"')
        print(f"\n[OK] Carpeta abierta: {carpeta_pendientes}")
        print("     Revisa las imagenes y vuelve para aprobar/rechazar.")
        input("\nPresiona Enter para continuar...")
        return

    if opcion in ("S", "R"):
        print()
        if len(sesiones) == 1:
            idx = 0
        else:
            sel = input(f"Que sesion {'aprobar' if opcion == 'S' else 'rechazar'}? (numero): ").strip()
            try:
                idx = int(sel) - 1
                if idx < 0 or idx >= len(sesiones):
                    print("[!] Numero invalido")
                    input("\nPresiona Enter para continuar...")
                    return
            except ValueError:
                print("[!] Introduce un numero")
                input("\nPresiona Enter para continuar...")
                return

        sesion = sesiones[idx]

        if opcion == "S":
            print()
            print(f"Aprobar {sesion['num_imagenes']} imagenes de {sesion['sesion'][:30]}?")
            print()
            dest = input("Destino (1=hooks, 2=brolls, default=hooks): ").strip()
            tipo_destino = "broll" if dest == "2" else "hook"

            confirmacion = input(f"\nMover {sesion['num_imagenes']} imagenes a {tipo_destino}s/? (SI): ").strip()
            if confirmacion != "SI":
                print("\n[!] Cancelado")
                input("\nPresiona Enter para continuar...")
                return

            aprobadas = staging.aprobar_sesion(sesion['path'], tipo_destino)
            print(f"\n[OK] {len(aprobadas)} imagenes aprobadas y movidas")
            print("     Ejecuta opcion 1 (Escanear material) para registrarlas en BD.")

        else:  # R
            confirmacion = input(f"\nRechazar {sesion['num_imagenes']} imagenes? (SI): ").strip()
            if confirmacion != "SI":
                print("\n[!] Cancelado")
                input("\nPresiona Enter para continuar...")
                return

            staging.rechazar_sesion(sesion['path'])
            print(f"\n[OK] Sesion rechazada")

        input("\nPresiona Enter para continuar...")
        return

    print("[!] Opcion invalida")
    input("\nPresiona Enter para continuar...")

# ═══════════════════════════════════════════════════════════
# GESTIONAR BOFS (Activar/Desactivar)
def publicar_tiktok():
    """Opción 20: Publica videos en TikTok Studio con Playwright."""
    print(f"\n{'='*60}")
    print(f"  🚀 PUBLICAR VIDEOS EN TIKTOK STUDIO")
    print(f"{'='*60}\n")

    try:
        from tiktok_publisher import TikTokPublisher, get_videos_para_publicar
    except ImportError as e:
        print(f"[ERROR] No se puede importar tiktok_publisher: {e}")
        print(f"[TIP] Ejecuta: python scripts/setup_publisher.py")
        input("\nPresiona Enter para continuar...")
        return

    # Seleccionar cuenta
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT nombre FROM cuentas_config WHERE activa = 1 ORDER BY nombre")
    cuentas = [row['nombre'] for row in cursor.fetchall()]
    conn.close()

    if not cuentas:
        print("[ERROR] No hay cuentas activas configuradas")
        input("\nPresiona Enter para continuar...")
        return

    print("  Cuentas disponibles:")
    for i, c in enumerate(cuentas, 1):
        print(f"    {i}. {c}")

    sel = input(f"\n  Selecciona cuenta (1-{len(cuentas)}): ").strip()
    try:
        cuenta = cuentas[int(sel) - 1]
    except (ValueError, IndexError):
        print("[ERROR] Selección inválida")
        input("\nPresiona Enter para continuar...")
        return

    # Seleccionar fecha
    manana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    fecha = input(f"  Fecha a publicar [{manana}]: ").strip() or manana

    # Verificar videos disponibles
    videos = get_videos_para_publicar(cuenta, fecha)
    if not videos:
        print(f"\n  No hay videos programados para {cuenta} en {fecha}")
        input("\nPresiona Enter para continuar...")
        return

    print(f"\n  {len(videos)} videos encontrados para {cuenta} — {fecha}:")
    for v in videos:
        exists = "✓" if os.path.exists(v['filepath']) else "✗"
        print(f"    [{exists}] {v['hora_programada']} - {v['producto'][:25]} - {v['video_id']}")

    # Modo
    print(f"\n  Opciones:")
    print(f"    1. 🧪 Dry run (simular sin publicar)")
    print(f"    2. 🚀 Publicar en TikTok Studio")
    print(f"    0. Cancelar")
    modo = input(f"\n  Selecciona (1/2/0): ").strip()

    if modo == "0" or not modo:
        return

    dry_run = modo == "1"

    # Límite opcional
    limite = input(f"  Límite de videos (vacío = todos): ").strip()
    limite = int(limite) if limite else None

    # Confirmar
    mode_label = "DRY RUN" if dry_run else "PRODUCCIÓN"
    print(f"\n  ⚠️  Se va a {'simular' if dry_run else 'publicar'} en modo {mode_label}")
    print(f"  Cuenta: {cuenta}")
    print(f"  Fecha:  {fecha}")
    print(f"  Videos: {limite or len(videos)}")

    if not dry_run:
        print(f"\n  ⚠️  IMPORTANTE: Chrome debe estar CERRADO antes de continuar")

    confirmar = input(f"\n  Confirmar? (s/n): ").strip().lower()
    if confirmar != 's':
        print("  Cancelado")
        input("\nPresiona Enter para continuar...")
        return

    # Publicar
    publisher = TikTokPublisher(cuenta, dry_run=dry_run)
    stats = publisher.run(fecha, limite)

    input("\nPresiona Enter para continuar...")

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    """Loop principal del CLI"""

    # Migraciones de BD
    try:
        from scripts.db_config import ensure_bof_activo_column
        ensure_bof_activo_column()
    except Exception as e:
        logging.debug(f"Migración BD falló (no bloquea CLI): {e}")

    while True:
        clear_screen()
        print_header()
        print_menu()

        opcion = input("  👉 Selecciona una opcion: ").strip()

        if opcion == "4":
            generar_videos()
        elif opcion == "5":
            generar_videos_multiples()
        elif opcion == "8":
            deshacer_programacion()
        elif opcion == "15":
            generar_fondos_ia()
        elif opcion == "16":
            revisar_material_ia()
        elif opcion == "20":
            publicar_tiktok()
        elif opcion == "0":
            print("\n  👋 Hasta luego!\n")
            break
        else:
            print("\n  ❌ Opcion invalida")
            input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nHasta luego!\n")
        sys.exit(0)
