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
    print("  🎥  PREPARAR MATERIAL")
    print("  ─────────────────────────────────────────────")
    print("   1.  🔍  Escanear material de un producto")
    print("   2.  ✅  Validar material disponible")
    print("   3.  🔄  Reimportar BOF (sobreescribir)")
    print()
    print("  🎞️   GENERAR VIDEOS")
    print("  ─────────────────────────────────────────────")
    print("   4.  🎞️   Generar videos para un producto")
    print("   5.  🎞️   Generar videos para MULTIPLES productos")
    print("   6.  🗑️   Descartar videos generados")
    print()
    print("  📅  PROGRAMACIÓN")
    print("  ─────────────────────────────────────────────")
    print("   7.  📆  Programar calendario (auto-sync + simulación)")
    print("   8.  ↩️   Deshacer programacion")
    print("   9.  🔄  Sincronizar desde Sheet (deprecated - QUA-151)")
    print()
    print("  📊  ESTADO Y CONTROL")
    print("  ─────────────────────────────────────────────")
    print("  10.  📈  Dashboard de estado")
    print("  11.  📊  Ver estado de todos los productos")
    print("  12.  🏷️   Gestionar productos (lifecycle)")
    print("  13.  🔄  Sync lifecycle desde Sheet (manual)")
    print("  14.  🔍  Verificar integridad (BD↔Local↔Sheet↔Drive)")
    print()
    print("  🎨  MATERIAL IA")
    print("  ─────────────────────────────────────────────")
    print("  15.  🖼️   Generar fondos con IA (screenshot)")
    print("  16.  👁️   Revisar y aprobar material generado")
    print()
    print("  📤  PUBLICACIÓN TIKTOK")
    print("  ─────────────────────────────────────────────")
    print("  19.  📋  Ver videos pendientes de publicar")
    print("  20.  🚀  Publicar videos en TikTok Studio")
    print()
    print("  🔧  GESTION BOFs")
    print("  ─────────────────────────────────────────────")
    print("  21.  🔧  Gestionar BOFs (activar / desactivar)")
    print()
    print("  💾  SISTEMA")
    print("  ─────────────────────────────────────────────")
    print("  17.  💾  Backup de base de datos")
    print("  18.  🧹  Limpiar Drive (deprecated - QUA-151)")
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
# ═══════════════════════════════════════════════════════════

def escanear_material():
    """Escanea material de un producto"""
    clear_screen()
    print_header()
    print("ESCANEAR MATERIAL")
    print()

    producto = seleccionar_o_crear_producto()
    if not producto:
        return

    print(f"\nEscaneando material para: {producto}")
    print()

    import subprocess
    cmd = f'python scripts/scan_material.py "{producto}" --auto-bof'

    print(f"Ejecutando: {cmd}")
    print("-" * 60)

    result = subprocess.run(cmd, shell=True, encoding='utf-8', errors='replace')

    print("-" * 60)

    if result.returncode == 0:
        print("\n[OK] Escaneo completado")
    else:
        print("\n[ERROR] Error en el escaneo")

    input("\nPresiona Enter para continuar...")


def reimportar_bof():
    """Reimporta un BOF sobreescribiendo el anterior (BOF + variantes overlay)"""
    clear_screen()
    print_header()
    print("REIMPORTAR BOF (SOBREESCRIBIR)")
    print()

    producto = seleccionar_producto()
    if not producto:
        return

    # Obtener BOFs del producto
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM productos WHERE nombre = ?", (producto,))
        row = cursor.fetchone()
        if not row:
            print(f"[!] Producto '{producto}' no encontrado en BD")
            input("\nPresiona Enter para continuar...")
            return
        producto_id = row['id']

        cursor.execute("""
            SELECT pb.id, pb.deal_math, pb.guion_audio,
                   (SELECT COUNT(*) FROM variantes_overlay_seo WHERE bof_id = pb.id) as num_variantes
            FROM producto_bofs pb
            WHERE pb.producto_id = ?
            ORDER BY pb.id
        """, (producto_id,))
        bofs = cursor.fetchall()

    if not bofs:
        print(f"[!] El producto '{producto}' no tiene BOFs en BD")
        print("    Usa la opcion 1 (Escanear material) para importar el primero")
        input("\nPresiona Enter para continuar...")
        return

    # Seleccionar BOF a reemplazar
    if len(bofs) == 1:
        bof_sel = bofs[0]
        print(f"  BOF unico encontrado:")
        print(f"    ID: {bof_sel['id']}")
        print(f"    Deal: {bof_sel['deal_math']}")
        print(f"    Guion: {bof_sel['guion_audio'][:60]}...")
        print(f"    Variantes: {bof_sel['num_variantes']}")
        print()
    else:
        print("  BOFs del producto:")
        print()
        for i, bof in enumerate(bofs, 1):
            print(f"    {i}. [ID:{bof['id']}] {bof['deal_math']} - {bof['guion_audio'][:40]}... ({bof['num_variantes']} variantes)")
        print()
        print("    0. Cancelar")
        print()

        while True:
            try:
                opcion = input("  Selecciona BOF a reemplazar (numero): ").strip()
                if opcion == "0":
                    return
                idx = int(opcion) - 1
                if 0 <= idx < len(bofs):
                    bof_sel = bofs[idx]
                    break
                else:
                    print("  [!] Opcion invalida")
            except ValueError:
                print("  [!] Introduce un numero")

    bof_id_viejo = bof_sel['id']

    # Buscar JSON a importar
    from config import RECURSOS_BASE
    producto_dir = os.path.join(RECURSOS_BASE, producto)
    json_default = os.path.join(producto_dir, "bof_generado.json")

    print(f"  JSON por defecto: {json_default}")
    json_path = input(f"  Ruta al JSON (Enter para usar el de arriba): ").strip()
    if not json_path:
        json_path = json_default

    if not os.path.exists(json_path):
        print(f"\n[ERROR] No existe: {json_path}")
        input("\nPresiona Enter para continuar...")
        return

    # Leer y validar JSON
    import json
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"\n[ERROR] No se pudo leer JSON: {e}")
        input("\nPresiona Enter para continuar...")
        return

    campos_requeridos = ['deal_math', 'guion_audio', 'hashtags', 'url_producto', 'variantes']
    faltantes = [c for c in campos_requeridos if c not in data]
    if faltantes:
        print(f"\n[ERROR] Campos faltantes en JSON: {', '.join(faltantes)}")
        input("\nPresiona Enter para continuar...")
        return

    if len(data.get('variantes', [])) < 5:
        print(f"\n[ERROR] Minimo 5 variantes requeridas, encontradas: {len(data.get('variantes', []))}")
        input("\nPresiona Enter para continuar...")
        return

    # Comprobar si hay videos generados con este BOF
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM videos WHERE bof_id = ?", (bof_id_viejo,))
        num_videos = cursor.fetchone()['count']

    if num_videos > 0:
        print(f"\n  [!] ATENCION: Hay {num_videos} videos generados con este BOF")
        print(f"      Si continuas, los videos quedaran con referencias huerfanas")
        confirma = input(f"      Continuar igualmente? (S/N): ").strip().upper()
        if confirma != "S":
            print("  Cancelado")
            input("\nPresiona Enter para continuar...")
            return

    # Preview de cambios
    print(f"\n  {'='*50}")
    print(f"  CAMBIOS A APLICAR:")
    print(f"  {'='*50}")
    print(f"  Deal: {data['deal_math']}")
    print(f"  Guion: {data['guion_audio'][:60]}...")
    print(f"  Variantes: {len(data['variantes'])}")
    for i, v in enumerate(data['variantes'][:3], 1):
        print(f"    {i}. {v['overlay_line1']} / {v.get('overlay_line2', '-')}")
    if len(data['variantes']) > 3:
        print(f"    ... y {len(data['variantes']) - 3} mas")
    print()

    confirma = input("  Confirmar reimportacion? (S/N): ").strip().upper()
    if confirma != "S":
        print("  Cancelado")
        input("\nPresiona Enter para continuar...")
        return

    # Ejecutar reimportacion
    with get_connection() as conn:
        cursor = conn.cursor()

        try:
            # Desactivar foreign keys temporalmente para poder reordenar operaciones
            cursor.execute("PRAGMA foreign_keys = OFF")

            # 1. Obtener IDs de variantes viejas
            cursor.execute("SELECT id FROM variantes_overlay_seo WHERE bof_id = ?", (bof_id_viejo,))
            variante_ids_viejas = [r['id'] for r in cursor.fetchall()]
            variantes_borradas = len(variante_ids_viejas)

            # 2. Actualizar BOF con nuevos datos
            cursor.execute("""
                UPDATE producto_bofs
                SET deal_math = ?, guion_audio = ?, hashtags = ?, url_producto = ?
                WHERE id = ?
            """, (data['deal_math'], data['guion_audio'], data['hashtags'], data['url_producto'], bof_id_viejo))
            print(f"  [OK] BOF actualizado (ID: {bof_id_viejo})")

            # 3. Insertar nuevas variantes PRIMERO
            nuevas_ids = []
            for variante in data['variantes']:
                cursor.execute("""
                    INSERT INTO variantes_overlay_seo (bof_id, overlay_line1, overlay_line2, seo_text)
                    VALUES (?, ?, ?, ?)
                """, (bof_id_viejo, variante['overlay_line1'], variante.get('overlay_line2', ''), variante['seo_text']))
                nuevas_ids.append(cursor.lastrowid)
            print(f"  [OK] Nuevas variantes insertadas: {len(nuevas_ids)}")

            # 4. Reasignar videos que usaban variantes viejas a la primera variante nueva
            if variante_ids_viejas and nuevas_ids:
                placeholders = ",".join("?" * len(variante_ids_viejas))
                cursor.execute(
                    f"UPDATE videos SET variante_id = ? WHERE variante_id IN ({placeholders})",
                    [nuevas_ids[0]] + variante_ids_viejas
                )
                if cursor.rowcount > 0:
                    print(f"  [OK] {cursor.rowcount} videos reasignados a variante nueva")

            # 5. Borrar tracking de hook_variante de variantes viejas
            if variante_ids_viejas:
                placeholders = ",".join("?" * len(variante_ids_viejas))
                cursor.execute(f"DELETE FROM hook_variante_usado WHERE variante_id IN ({placeholders})", variante_ids_viejas)
                print(f"  [OK] Tracking hook_variante limpiado: {cursor.rowcount}")

                # 6. Borrar variantes viejas
                cursor.execute("DELETE FROM variantes_overlay_seo WHERE id IN ({})".format(placeholders), variante_ids_viejas)

            print(f"  [OK] Variantes viejas borradas: {variantes_borradas}")

            # Reactivar foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")

            conn.commit()

            print(f"\n  {'='*50}")
            print(f"  REIMPORTACION COMPLETADA")
            print(f"  {'='*50}")
            print(f"  Producto: {producto}")
            print(f"  BOF ID: {bof_id_viejo} (mismo ID, datos actualizados)")
            print(f"  Variantes: {variantes_borradas} borradas -> {len(data['variantes'])} nuevas")

        except Exception as e:
            conn.rollback()
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()

    input("\nPresiona Enter para continuar...")


def validar_material():
    """Valida material disponible de un producto"""
    clear_screen()
    print_header()
    print("VALIDAR MATERIAL")
    print()

    producto = seleccionar_producto()
    if not producto:
        return

    print(f"\nValidando material para: {producto}")
    print()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM productos WHERE nombre = ?", (producto,))
        row = cursor.fetchone()

        if not row:
            print("[!] Producto no encontrado")
            input("\nPresiona Enter para continuar...")
            return

        producto_id = row['id']

        cursor.execute("SELECT COUNT(*) as count FROM material WHERE producto_id = ? AND tipo = 'hook'", (producto_id,))
        hooks = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM material WHERE producto_id = ? AND tipo = 'broll'", (producto_id,))
        brolls = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM audios WHERE producto_id = ?", (producto_id,))
        audios = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM producto_bofs WHERE producto_id = ?", (producto_id,))
        bofs = cursor.fetchone()['count']

    print("MATERIAL DISPONIBLE:")
    print()
    print(f"  Hooks:  {hooks:>3} {'[OK]' if hooks >= 10 else '[!] (minimo 10)'}")
    print(f"  Brolls: {brolls:>3} {'[OK]' if brolls >= 20 else '[!] (minimo 20)'}")
    print(f"  Audios: {audios:>3} {'[OK]' if audios >= 3 else '[!] (minimo 3)'}")
    print(f"  BOFs:   {bofs:>3} {'[OK]' if bofs >= 1 else '[!] (minimo 1)'}")
    print()

    if hooks >= 10 and brolls >= 20 and audios >= 3 and bofs >= 1:
        print("[OK] Material COMPLETO - Listo para generar videos")
    else:
        print("[!] Material INCOMPLETO - Necesitas mas material")

    input("\nPresiona Enter para continuar...")


def _run_generation_with_progress(productos_list, cuentas, cantidad, bof_id=None, es_ia=False):
    """Ejecuta generacion con contador de progreso integrado.

    Args:
        productos_list: Lista de dicts con al menos 'nombre'
        cuentas: Lista de nombres de cuenta
        cantidad: Videos por producto por cuenta
        es_ia: Si True, marca los videos como contenido generado por IA
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
                with VideoGenerator(nombre, cuenta=cuenta, bof_id=bof_id, es_ia=es_ia) as generator:
                    results = generator.generate_batch(
                        batch_size=cantidad,
                        progress_callback=tracker.on_video_progress
                    )
            except Exception as e:
                print(f"\n[ERROR] Error generando {nombre} / {cuenta}: {e}")
                # Contar los videos que no se generaron como fallidos
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

    # Preguntar si los videos contienen IA (QUA-39)
    print()
    ia_input = input("Contienen contenido generado por IA? (S/N, default N): ").strip().upper()
    es_ia = ia_input == 'S'

    print()
    bof_msg = f" (BOF forzado: {bof_id})" if bof_id else " (auto)"
    ia_msg = " [IA]" if es_ia else ""
    print(f"Generando {cantidad} videos de {producto}{bof_msg}{ia_msg}")
    print(f"Cuentas: {', '.join(cuentas)}")
    print()

    _run_generation_with_progress([{"nombre": producto}], cuentas, cantidad, bof_id=bof_id, es_ia=es_ia)


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

    # Preguntar si los videos contienen IA (QUA-39)
    ia_input = input("Contienen contenido generado por IA? (S/N, default N): ").strip().upper()
    es_ia = ia_input == 'S'
    if es_ia:
        print("  [IA] Videos se marcarán como contenido generado por IA")
    print()

    confirmacion = input("Continuar? (SI para confirmar): ").strip()

    if confirmacion != "SI":
        print("\n[!] Generacion cancelada")
        input("\nPresiona Enter para continuar...")
        return

    _run_generation_with_progress(productos_seleccionados, cuentas, cantidad, es_ia=es_ia)


def ver_estado_productos():
    """Muestra estado de todos los productos"""
    clear_screen()
    print_header()
    print("ESTADO DE PRODUCTOS")
    print()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.id,
                p.nombre,
                (SELECT COUNT(*) FROM material WHERE producto_id = p.id AND tipo = 'hook') as hooks,
                (SELECT COUNT(*) FROM material WHERE producto_id = p.id AND tipo = 'broll') as brolls,
                (SELECT COUNT(*) FROM audios WHERE producto_id = p.id) as audios,
                (SELECT COUNT(*) FROM producto_bofs WHERE producto_id = p.id) as bofs,
                (SELECT COUNT(*) FROM videos WHERE producto_id = p.id AND estado = 'Generado') as videos_generados
            FROM productos p
            ORDER BY p.nombre
        """)

        productos = cursor.fetchall()

    if not productos:
        print("[!] No hay productos en la base de datos")
        input("\nPresiona Enter para continuar...")
        return

    print(f"{'Producto':<35} {'Hooks':>6} {'Brolls':>7} {'Audios':>7} {'BOFs':>5} {'Videos':>7} {'Estado':>12}")
    print("-" * 95)

    for prod in productos:
        nombre = prod['nombre'][:33]
        hooks = prod['hooks']
        brolls = prod['brolls']
        audios = prod['audios']
        bofs = prod['bofs']
        videos = prod['videos_generados']

        if hooks >= 10 and brolls >= 20 and audios >= 3 and bofs >= 1:
            estado = "[OK] Listo"
        else:
            estado = "[!] Incompl."

        print(f"{nombre:<35} {hooks:>6} {brolls:>7} {audios:>7} {bofs:>5} {videos:>7} {estado:>12}")

    print()
    input("Presiona Enter para continuar...")


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


def programar_calendario():
    """Programa calendario para cuentas"""
    clear_screen()
    print_header()
    print("PROGRAMAR CALENDARIO")
    print()

    cuentas = seleccionar_cuentas()
    if not cuentas:
        return

    print()
    dias = input("Cuantos dias programar? (default: 7): ").strip()
    if not dias:
        dias = "7"

    try:
        dias = int(dias)
    except ValueError:
        print("[!] Numero de dias invalido")
        input("\nPresiona Enter para continuar...")
        return

    print()
    fecha_inicio = input("Fecha de inicio? (YYYY-MM-DD o Enter para manana): ").strip()

    if fecha_inicio:
        try:
            datetime.strptime(fecha_inicio, "%Y-%m-%d")
        except ValueError:
            print("[!] Formato de fecha invalido. Usa YYYY-MM-DD (ej: 2026-02-20)")
            input("\nPresiona Enter para continuar...")
            return

    # Filtro por producto
    print()
    print("  Forzar un producto concreto?")
    print("    Enter = todos los productos (normal)")
    print("    P     = seleccionar producto")
    print()
    filtro = input("  Opcion: ").strip().upper()

    producto_filter = None
    if filtro == "P":
        producto_filter = seleccionar_producto()
        if not producto_filter:
            return

    # Videos por dia override
    print()
    videos_override = input("  Videos por dia? (Enter = usar config de la cuenta): ").strip()
    videos_dia_num = None
    if videos_override:
        try:
            videos_dia_num = int(videos_override)
        except ValueError:
            print("[!] Numero invalido, se usara la config de la cuenta")

    print()
    resumen = f"Programando {dias} dias"
    if fecha_inicio:
        resumen += f" desde {fecha_inicio}"
    else:
        resumen += " desde manana"
    if producto_filter:
        resumen += f" | SOLO: {producto_filter}"
    if videos_dia_num:
        resumen += f" | {videos_dia_num} videos/dia"
    print(resumen)
    print()

    import subprocess

    # ── AUTO-SYNC PRE-PROGRAMACIÓN (Cambio 3.3) ──
    print()
    print("=" * 60)
    print("  AUTO-SYNC PRE-PROGRAMACIÓN")
    print("=" * 60)

    # 1. Sync lifecycle desde Sheet (actualizar estado_comercial de productos)
    print("\n[1/2] Sincronizando lifecycle desde Sheet de Productos...")
    try:
        _auto_sync_lifecycle()
        print("  [OK] Lifecycle sincronizado")
    except Exception as e:
        print(f"  [WARNING] Error en sync lifecycle: {e}")
        print("  Continuando con programación...")

    # 2. Sync calendario desde Sheet (actualizar estados de videos)
    print("\n[2/2] Sincronizando estados desde Sheet de Calendario...")
    for cuenta in cuentas:
        try:
            _auto_sync_calendario(cuenta)
            print(f"  [OK] Calendario sincronizado para {cuenta}")
        except Exception as e:
            print(f"  [WARNING] Error sincronizando {cuenta}: {e}")
            print("  Continuando con programación...")

    # ── SIMULACIÓN / DRY RUN (Cambio 3.1) ──
    print()
    print("=" * 60)
    print("  SIMULACIÓN (dry run)")
    print("=" * 60)

    simulacion_ok = True
    for cuenta in cuentas:
        cmd = f'python programador.py --cuenta {cuenta} --dias {dias} --dry-run'
        if fecha_inicio:
            cmd += f' --fecha-inicio {fecha_inicio}'
        if producto_filter:
            cmd += f' --producto "{producto_filter}"'
        if videos_dia_num:
            cmd += f' --videos-dia {videos_dia_num}'

        result = subprocess.run(cmd, shell=True, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            simulacion_ok = False

    print()
    if not simulacion_ok:
        print("[WARNING] La simulación detectó problemas.")

    print()
    confirmacion = input("  ¿Confirmar programación? (SI para ejecutar, otro para cancelar): ").strip()
    if confirmacion != "SI":
        print("\n[!] Programación cancelada")
        input("\nPresiona Enter para continuar...")
        return

    # ── PROGRAMACIÓN REAL ──
    print()
    print("=" * 60)
    print("  PROGRAMANDO CALENDARIO")
    print("=" * 60)

    for cuenta in cuentas:
        print(f"\n{'='*60}")
        print(f"  Programando: {cuenta}")
        print('='*60)

        cmd = f'python programador.py --cuenta {cuenta} --dias {dias}'
        if fecha_inicio:
            cmd += f' --fecha-inicio {fecha_inicio}'
        if producto_filter:
            cmd += f' --producto "{producto_filter}"'
        if videos_dia_num:
            cmd += f' --videos-dia {videos_dia_num}'

        print(f"Ejecutando: {cmd}")
        print("-" * 60)

        subprocess.run(cmd, shell=True, encoding='utf-8', errors='replace')

        print("-" * 60)

    # ── VERIFICACIÓN POST-PROGRAMACIÓN (Cambio 3.6) ──
    print()
    print("=" * 60)
    print("  VERIFICACIÓN POST-PROGRAMACIÓN")
    print("=" * 60)
    _verificar_post_programacion(cuentas)

    print("\n[OK] Programacion completada")
    input("\nPresiona Enter para continuar...")


# ═══════════════════════════════════════════════════════════
# VERIFICAR INTEGRIDAD
# ═══════════════════════════════════════════════════════════

def verificar_integridad():
    """Ejecuta verificación completa de las 4 capas: BD ↔ Local ↔ Sheet ↔ Drive"""
    clear_screen()
    print_header()
    print("🔍  VERIFICACIÓN DE INTEGRIDAD")
    print()
    print("  Comprueba que BD, archivos locales, Sheet y Drive están sincronizados.")
    print()
    print("  1. Solo verificar (mostrar problemas)")
    print("  2. Verificar y REPARAR automáticamente")
    print("  0. Volver")
    print()

    opcion = input("  Opcion: ").strip()
    if opcion == "0" or not opcion:
        return

    fix_flag = "--fix" if opcion == "2" else ""

    import subprocess
    script_path = os.path.join(os.path.dirname(__file__), "scripts", "verificacion_completa.py")

    cmd = [sys.executable, script_path]
    if fix_flag:
        cmd.append(fix_flag)

    print()
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__),
                           encoding='utf-8', errors='replace')

    print()
    input("Presiona Enter para continuar...")


# ═══════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════

def ver_dashboard():
    """Muestra dashboard completo de estado del sistema"""
    clear_screen()

    now = datetime.now()
    hoy = now.strftime("%Y-%m-%d")
    hace_7_dias = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    en_7_dias = (now + timedelta(days=7)).strftime("%Y-%m-%d")

    with get_connection() as conn:
        cursor = conn.cursor()

        print("=" * 80)
        print(f"  DASHBOARD AUTOTOK                                {now.strftime('%d/%m/%Y %H:%M')}")
        print("=" * 80)

        # ── Stats por cuenta ──
        cuentas = _cargar_cuentas_activas()
        stats = {}

        for cuenta in cuentas:
            s = {}

            # Total generados
            cursor.execute("SELECT COUNT(*) as t FROM videos WHERE cuenta = ?", (cuenta,))
            s['generados'] = cursor.fetchone()['t']

            # Disponibles (Generado)
            cursor.execute("SELECT COUNT(*) as t FROM videos WHERE cuenta = ? AND estado = 'Generado'", (cuenta,))
            s['disponibles'] = cursor.fetchone()['t']

            # En calendario (proximos 7 dias)
            cursor.execute("""
                SELECT COUNT(*) as t FROM videos
                WHERE cuenta = ? AND estado = 'En Calendario'
                AND fecha_programada BETWEEN ? AND ?
            """, (cuenta, hoy, en_7_dias))
            s['en_calendario'] = cursor.fetchone()['t']

            # Programados (subidos a TikTok pendientes de publicar, fecha futura)
            cursor.execute("""
                SELECT COUNT(*) as t FROM videos
                WHERE cuenta = ? AND estado IN ('Programado', 'Borrador')
                AND fecha_programada >= ?
            """, (cuenta, hoy))
            s['programados'] = cursor.fetchone()['t']

            # Publicados (Borrador o Programado con fecha pasada = ya deberian estar publicados)
            cursor.execute("""
                SELECT COUNT(*) as t FROM videos
                WHERE cuenta = ? AND estado IN ('Programado', 'Borrador')
                AND fecha_programada < ?
            """, (cuenta, hoy))
            s['publicados'] = cursor.fetchone()['t']

            # Descartados
            cursor.execute("SELECT COUNT(*) as t FROM videos WHERE cuenta = ? AND estado = 'Descartado'", (cuenta,))
            s['descartados'] = cursor.fetchone()['t']

            # Violations
            cursor.execute("SELECT COUNT(*) as t FROM videos WHERE cuenta = ? AND estado = 'Violation'", (cuenta,))
            s['violations'] = cursor.fetchone()['t']

            # Combinaciones usadas vs total posible
            cursor.execute("""
                SELECT COUNT(*) as t FROM hook_variante_usado hvu
                JOIN videos v ON hvu.video_id = v.id
                WHERE v.cuenta = ?
            """, (cuenta,))
            s['combis_usadas'] = cursor.fetchone()['t']

            cursor.execute("SELECT COUNT(*) as t FROM material WHERE tipo = 'hook'")
            total_hooks = cursor.fetchone()['t']
            cursor.execute("SELECT COUNT(*) as t FROM variantes_overlay_seo")
            total_variantes = cursor.fetchone()['t']
            s['combis_posibles'] = total_hooks * total_variantes if total_hooks and total_variantes else 1
            s['pct_combis'] = s['combis_usadas'] / s['combis_posibles'] * 100 if s['combis_posibles'] > 0 else 0

            # Proximo en calendario
            cursor.execute("""
                SELECT fecha_programada, hora_programada FROM videos
                WHERE cuenta = ? AND estado = 'En Calendario'
                AND fecha_programada >= ?
                ORDER BY fecha_programada ASC, hora_programada ASC
                LIMIT 1
            """, (cuenta, hoy))
            prox = cursor.fetchone()
            s['proximo'] = f"{prox['fecha_programada']} {prox['hora_programada']}" if prox else "Sin programar"

            stats[cuenta] = s

        # Imprimir tres columnas: cuenta1 | cuenta2 | TOTAL
        col_w = 30
        c1, c2 = cuentas[0], cuentas[1]
        s1, s2 = stats[c1], stats[c2]

        print()
        print(f"  {'ofertastrendy20':<{col_w}} {'lotopdevicky':<{col_w}} {'TOTAL':<{col_w}}")
        print(f"  {'-'*28:<{col_w}} {'-'*28:<{col_w}} {'-'*28:<{col_w}}")

        stat_rows = [
            ("Generados",     s1['generados'],     s2['generados']),
            ("Disponibles",   s1['disponibles'],   s2['disponibles']),
            ("En calendario", s1['en_calendario'], s2['en_calendario']),
            ("Programados",   s1['programados'],   s2['programados']),
            ("Publicados",    s1['publicados'],    s2['publicados']),
            ("Descartados",   s1['descartados'],   s2['descartados']),
            ("Violations",    s1['violations'],    s2['violations']),
        ]

        for label, v1, v2 in stat_rows:
            total = v1 + v2
            line1 = f"{label + ':':<18}{v1:>6}"
            line2 = f"{label + ':':<18}{v2:>6}"
            line3 = f"{label + ':':<18}{total:>6}"
            print(f"  {line1:<{col_w}} {line2:<{col_w}} {line3:<{col_w}}")

        # Combinaciones
        c1_str = f"{s1['combis_usadas']}/{s1['combis_posibles']} ({s1['pct_combis']:.0f}%)"
        c2_str = f"{s2['combis_usadas']}/{s2['combis_posibles']} ({s2['pct_combis']:.0f}%)"
        t_combis = s1['combis_usadas'] + s2['combis_usadas']
        t_posibles = s1['combis_posibles'] + s2['combis_posibles']
        t_pct = t_combis / t_posibles * 100 if t_posibles > 0 else 0
        t_str = f"{t_combis}/{t_posibles} ({t_pct:.0f}%)"
        line1 = f"{'Combis:':<18}{c1_str:>10}"
        line2 = f"{'Combis:':<18}{c2_str:>10}"
        line3 = f"{'Combis:':<18}{t_str:>10}"
        print(f"  {line1:<{col_w}} {line2:<{col_w}} {line3:<{col_w}}")

        # Proximo (fecha corta dd/mm HH:MM)
        def fecha_corta(s):
            """Convierte '2026-02-19 08:00' a '19/02 08:00'"""
            if s == "Sin programar":
                return s
            try:
                # QUA-91: Formato explícito YYYY-MM-DD HH:MM → DD/MM HH:MM
                parts = s.split(" ")
                fecha_dt = datetime.strptime(parts[0], "%Y-%m-%d")
                return f"{fecha_dt.strftime('%d/%m')} {parts[1]}"
            except Exception:
                return s

        p1 = fecha_corta(s1['proximo'])
        p2 = fecha_corta(s2['proximo'])
        line1 = f"{'Proximo:':<18}{p1}"
        line2 = f"{'Proximo:':<18}{p2}"
        print(f"  {line1:<{col_w}} {line2:<{col_w}}")

        # ── Tabla productos ──
        print()
        print("  PRODUCTOS")
        print("  " + "-" * 76)
        print(f"  {'':2}{'Producto':<25} {'Disp':>5} {'Cal':>5} {'Prog':>5} {'Pub':>5} {'Desc':>5} {'Viol':>5} {'Test':>8}")
        print(f"  {'':2}{'-'*25} {'-'*5} {'-'*5} {'-'*5} {'-'*5} {'-'*5} {'-'*5} {'-'*8}")

        cursor.execute("""
            SELECT
                p.nombre,
                p.estado_comercial,
                p.max_videos_test,
                SUM(CASE WHEN v.estado = 'Generado' THEN 1 ELSE 0 END) as disponibles,
                SUM(CASE WHEN v.estado = 'En Calendario' THEN 1 ELSE 0 END) as en_calendario,
                SUM(CASE WHEN v.estado IN ('Programado', 'Borrador')
                    AND v.fecha_programada >= ? THEN 1 ELSE 0 END) as programados,
                SUM(CASE WHEN v.estado IN ('Programado', 'Borrador')
                    AND v.fecha_programada < ? THEN 1 ELSE 0 END) as publicados,
                SUM(CASE WHEN v.estado = 'Descartado' THEN 1 ELSE 0 END) as descartados,
                SUM(CASE WHEN v.estado = 'Violation' THEN 1 ELSE 0 END) as violations
            FROM productos p
            LEFT JOIN videos v ON v.producto_id = p.id
            GROUP BY p.id
            ORDER BY
                CASE p.estado_comercial
                    WHEN 'top_seller' THEN 1
                    WHEN 'validated' THEN 2
                    WHEN 'testing' THEN 3
                    WHEN 'dropped' THEN 4
                    ELSE 5
                END,
                disponibles DESC
        """, (hoy, hoy))
        productos = cursor.fetchall()

        # Totales
        t_disp = t_cal = t_prog = t_pub = t_desc = t_viol = 0

        for prod in productos:
            estado = prod['estado_comercial'] or 'testing'
            emoji = {'testing': '🧪', 'validated': '✅', 'top_seller': '🔥', 'dropped': '❌'}.get(estado, '?')
            nombre = prod['nombre'][:24]
            disp = prod['disponibles'] or 0
            cal = prod['en_calendario'] or 0
            prog = prod['programados'] or 0
            pub = prod['publicados'] or 0
            desc = prod['descartados'] or 0
            viol = prod['violations'] or 0

            t_disp += disp; t_cal += cal; t_prog += prog
            t_pub += pub; t_desc += desc; t_viol += viol

            test_str = ""
            if estado == 'testing':
                max_test = prod['max_videos_test'] or 20
                total_post = cal + prog + pub
                test_str = f"{total_post}/{max_test}"
                if total_post >= max_test:
                    test_str += "!"

            print(f"  {emoji} {nombre:<24} {disp:>5} {cal:>5} {prog:>5} {pub:>5} {desc:>5} {viol:>5} {test_str:>8}")

        # Fila de totales
        print(f"  {'':2}{'-'*25} {'-'*5} {'-'*5} {'-'*5} {'-'*5} {'-'*5} {'-'*5}")
        print(f"  {'':2}{'TOTAL':<25} {t_disp:>5} {t_cal:>5} {t_prog:>5} {t_pub:>5} {t_desc:>5} {t_viol:>5}")

        # ── Alertas ──
        print()
        print("  ALERTAS")
        print("  " + "-" * 76)

        alertas_encontradas = False

        for cuenta in cuentas:
            cursor.execute("""
                SELECT COUNT(DISTINCT fecha_programada) as dias FROM videos
                WHERE cuenta = ? AND estado = 'En Calendario'
                AND fecha_programada >= ?
            """, (cuenta, hoy))
            dias_restantes = cursor.fetchone()['dias']

            if dias_restantes <= 3:
                alertas_encontradas = True
                if dias_restantes == 0:
                    print(f"  [!!] {cuenta}: Sin dias en calendario")
                else:
                    print(f"  [!]  {cuenta}: Solo {dias_restantes} dias de calendario restantes")

        # Alerta: productos con pocas combinaciones disponibles
        cursor.execute("""
            SELECT
                p.nombre,
                (SELECT COUNT(*) FROM material m WHERE m.producto_id = p.id AND m.tipo = 'hook') as hooks,
                (SELECT COUNT(*) FROM variantes_overlay_seo vs
                 JOIN producto_bofs pb ON vs.bof_id = pb.id
                 WHERE pb.producto_id = p.id) as variantes,
                (SELECT COUNT(*) FROM hook_variante_usado hvu
                 JOIN videos v ON hvu.video_id = v.id
                 WHERE v.producto_id = p.id) as usadas
            FROM productos p
        """)
        for prod in cursor.fetchall():
            potencial = prod['hooks'] * prod['variantes'] if prod['hooks'] and prod['variantes'] else 0
            restantes = potencial - prod['usadas']
            if potencial > 0 and restantes <= 5:
                alertas_encontradas = True
                print(f"  [!]  {prod['nombre']}: Solo {restantes} combinaciones sin usar")

        # Alerta: productos en testing completados
        cursor.execute("""
            SELECT
                p.nombre,
                p.max_videos_test,
                SUM(CASE WHEN v.estado IN ('En Calendario', 'Programado', 'Borrador') THEN 1 ELSE 0 END) as total_post
            FROM productos p
            LEFT JOIN videos v ON v.producto_id = p.id
            WHERE p.estado_comercial = 'testing'
            GROUP BY p.id
        """)
        for prod in cursor.fetchall():
            max_test = prod['max_videos_test'] or 20
            total = prod['total_post'] or 0
            if total >= max_test:
                alertas_encontradas = True
                print(f"  [🧪] {prod['nombre']}: Test completado ({total}/{max_test}). Decide: validar o descartar")

        if not alertas_encontradas:
            print("  Todo en orden, sin alertas.")

    print()
    print("=" * 80)
    print()
    input("Presiona Enter para continuar...")


# ═══════════════════════════════════════════════════════════
# DESHACER PROGRAMACION
# ═══════════════════════════════════════════════════════════

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


def gestionar_productos():
    """Gestiona el ciclo de vida comercial de los productos"""
    clear_screen()
    print_header()
    print("🏷️  GESTIONAR PRODUCTOS (LIFECYCLE)")
    print()

    from datetime import datetime as dt_local
    hoy_local = dt_local.now().strftime("%Y-%m-%d")

    with get_connection() as conn:
        cursor = conn.cursor()

        # Obtener productos con stats (Prog=futuro, Pub=pasado)
        cursor.execute("""
            SELECT
                p.id,
                p.nombre,
                p.estado_comercial,
                p.max_videos_test,
                SUM(CASE WHEN v.estado = 'Generado' THEN 1 ELSE 0 END) as generados,
                SUM(CASE WHEN v.estado = 'En Calendario' THEN 1 ELSE 0 END) as en_calendario,
                SUM(CASE WHEN v.estado IN ('Programado', 'Borrador')
                    AND v.fecha_programada >= ? THEN 1 ELSE 0 END) as programados,
                SUM(CASE WHEN v.estado IN ('Programado', 'Borrador')
                    AND v.fecha_programada < ? THEN 1 ELSE 0 END) as publicados,
                SUM(CASE WHEN v.estado = 'Descartado' THEN 1 ELSE 0 END) as descartados,
                SUM(CASE WHEN v.estado = 'Violation' THEN 1 ELSE 0 END) as violations,
                COUNT(v.id) as total_videos
            FROM productos p
            LEFT JOIN videos v ON v.producto_id = p.id
            GROUP BY p.id
            ORDER BY p.estado_comercial, p.nombre
        """, (hoy_local, hoy_local))
        productos = [dict(row) for row in cursor.fetchall()]

    if not productos:
        print("[!] No hay productos en la base de datos")
        input("\nPresiona Enter para continuar...")
        return

    # Mostrar tabla
    print(f"  {'#':<4} {'Estado':<15} {'Producto':<28} {'Gen':>4} {'Cal':>4} {'Prog':>5} {'Pub':>4} {'Desc':>5} {'Viol':>5} {'Total':>6}")
    print("  " + "-" * 88)

    t_gen = t_cal = t_prog = t_pub = t_desc = t_viol = t_total = 0

    for i, prod in enumerate(productos, 1):
        estado = prod['estado_comercial'] or 'testing'
        emoji = ESTADO_COMERCIAL_EMOJI.get(estado, '?')
        label = ESTADO_COMERCIAL_LABEL.get(estado, estado)
        nombre = prod['nombre'][:26]

        gen = prod['generados'] or 0
        cal = prod['en_calendario'] or 0
        prog = prod['programados'] or 0
        pub = prod['publicados'] or 0
        desc = prod['descartados'] or 0
        viol = prod['violations'] or 0
        total = prod['total_videos'] or 0

        t_gen += gen; t_cal += cal; t_prog += prog
        t_pub += pub; t_desc += desc; t_viol += viol; t_total += total

        # Para testing, mostrar progreso del test batch
        extra = ""
        if estado == 'testing':
            max_test = prod['max_videos_test'] or 20
            total_post = cal + prog + pub
            extra = f"  ({total_post}/{max_test})"

        print(f"  {i:<4} {emoji} {label:<12} {nombre:<28} {gen:>4} {cal:>4} {prog:>5} {pub:>4} {desc:>5} {viol:>5} {total:>6}{extra}")

    # Totales
    print("  " + "-" * 88)
    print(f"  {'':4} {'':15} {'TOTAL':<28} {t_gen:>4} {t_cal:>4} {t_prog:>5} {t_pub:>4} {t_desc:>5} {t_viol:>5} {t_total:>6}")

    print()
    print("  CAMBIAR ESTADO:")
    print("  Escribe el numero del producto para cambiar su estado")
    print("  0. Volver al menu")
    print()

    opcion = input("  Producto: ").strip()
    if opcion == "0" or not opcion:
        return

    try:
        idx = int(opcion) - 1
        if idx < 0 or idx >= len(productos):
            print("[!] Numero invalido")
            input("\nPresiona Enter para continuar...")
            return
    except ValueError:
        print("[!] Introduce un numero")
        input("\nPresiona Enter para continuar...")
        return

    producto = productos[idx]
    estado_actual = producto['estado_comercial'] or 'testing'

    print()
    print(f"  Producto: {producto['nombre']}")
    print(f"  Estado actual: {ESTADO_COMERCIAL_EMOJI.get(estado_actual, '?')} {ESTADO_COMERCIAL_LABEL.get(estado_actual, estado_actual)}")
    print()
    print("  Nuevo estado:")
    print("   1. 🧪 Testing     (producto nuevo, fase de prueba)")
    print("   2. ✅ Validated   (tiene ventas, programar mas)")
    print("   3. 🔥 Top Seller  (top ventas, ir con todo)")
    print("   4. ❌ Dropped     (sin ventas, dejar de programar)")
    print("   0. Cancelar")
    print()

    nuevo = input("  Nuevo estado: ").strip()

    estados_map = {"1": "testing", "2": "validated", "3": "top_seller", "4": "dropped"}

    if nuevo not in estados_map:
        return

    nuevo_estado = estados_map[nuevo]

    if nuevo_estado == estado_actual:
        print(f"\n  Ya esta en {ESTADO_COMERCIAL_LABEL[nuevo_estado]}")
        input("\nPresiona Enter para continuar...")
        return

    # Actualizar
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE productos SET estado_comercial = ? WHERE id = ?
        """, (nuevo_estado, producto['id']))
        conn.commit()

    print(f"\n  [OK] {producto['nombre']}: {ESTADO_COMERCIAL_EMOJI[estado_actual]} {ESTADO_COMERCIAL_LABEL[estado_actual]} → {ESTADO_COMERCIAL_EMOJI[nuevo_estado]} {ESTADO_COMERCIAL_LABEL[nuevo_estado]}")
    input("\nPresiona Enter para continuar...")


# ═══════════════════════════════════════════════════════════
# SINCRONIZAR DESDE SHEET
# ═══════════════════════════════════════════════════════════

def sincronizar_sheet():
    """DEPRECATED (QUA-151): Ya no se sincronizan estados desde Sheet."""
    clear_screen()
    print_header()
    print("SINCRONIZAR DESDE GOOGLE SHEET")
    print()
    print("  [INFO] Esta opción ya no es necesaria (QUA-151).")
    print("  Los estados se gestionan desde el dashboard de Vercel (Turso).")
    print("  Los archivos ya no se mueven entre carpetas.")
    print()
    input("Presiona Enter para continuar...")


# ═══════════════════════════════════════════════════════════
# SYNC LIFECYCLE DESDE SHEET
# ═══════════════════════════════════════════════════════════

def sync_lifecycle_sheet():
    """Sincroniza estado_comercial de productos desde la hoja PRODUCTOS.

    Lee la Google Sheet de productos y usa:
      Columna A: nombre del producto (debe coincidir con BD)
      Columna E: estado_comercial (testing / validated / top_seller / dropped)
    """
    clear_screen()
    print_header()
    print("🔄  SYNC LIFECYCLE DESDE GOOGLE SHEET")
    print()
    print("Lee la hoja de Productos y actualiza el estado_comercial")
    print("de cada producto en la base de datos.")
    print()
    print("  Columna B: nombre del producto")
    print("  Columna E: estado (testing / validated / top_seller / dropped)")
    print()

    ESTADOS_VALIDOS = {'testing', 'validated', 'top_seller', 'dropped'}

    SHEET_URL_PRODUCTOS = 'https://docs.google.com/spreadsheets/d/18b5aQZUby4JHYpnrlZPyisC-aW21z44VKxFJk_3dviQ/'

    # Conectar a Sheet
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials

        SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPES)
        client = gspread.authorize(creds)

        spreadsheet = client.open_by_url(SHEET_URL_PRODUCTOS)

        # Buscar pestaña "PRODUCTOS"
        try:
            worksheet = spreadsheet.worksheet("PRODUCTOS")
        except gspread.exceptions.WorksheetNotFound:
            # Intentar sin mayusculas por si acaso
            try:
                worksheet = spreadsheet.worksheet("Productos")
            except gspread.exceptions.WorksheetNotFound:
                # Usar la primera hoja si no se encuentra por nombre
                worksheet = spreadsheet.sheet1

        print("[OK] Conectado a Google Sheet - Hoja de Productos")
        print()

    except Exception as e:
        print(f"[ERROR] No se pudo conectar a Sheets: {e}")
        input("\nPresiona Enter para continuar...")
        return

    # Leer datos del Sheet
    rows = worksheet.get_all_values()

    if len(rows) <= 1:
        print("[!] La hoja de Productos esta vacia (o solo tiene encabezado)")
        input("\nPresiona Enter para continuar...")
        return

    # Saltar encabezado (fila 1)
    data_rows = rows[1:]

    # Obtener productos actuales de BD
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, estado_comercial FROM productos")
        productos_bd = {row['nombre'].lower(): dict(row) for row in cursor.fetchall()}

    # Comparar y mostrar cambios
    cambios = []
    errores = []
    sin_cambio = 0

    for i, row in enumerate(data_rows, 2):  # Fila 2 en adelante
        # Columna B = indice 1 (0-based)
        if len(row) < 2 or not row[1].strip():
            continue

        nombre_sheet = row[1].strip()

        # Columna E = indice 4 (0-based)
        if len(row) < 5 or not row[4].strip():
            continue  # Sin estado en columna E, saltar

        estado_sheet = row[4].strip().lower()

        # Buscar en BD (case-insensitive)
        producto_bd = productos_bd.get(nombre_sheet.lower())

        if not producto_bd:
            errores.append(f"Fila {i}: '{nombre_sheet}' no encontrado en BD")
            continue

        if estado_sheet not in ESTADOS_VALIDOS:
            errores.append(f"Fila {i}: '{estado_sheet}' no es un estado valido para '{nombre_sheet}'")
            continue

        estado_actual = producto_bd['estado_comercial'] or 'testing'

        if estado_sheet == estado_actual:
            sin_cambio += 1
        else:
            cambios.append({
                'id': producto_bd['id'],
                'nombre': producto_bd['nombre'],
                'anterior': estado_actual,
                'nuevo': estado_sheet,
            })

    # Mostrar resumen
    print(f"Productos leidos del Sheet: {len(data_rows)}")
    print(f"Sin cambios: {sin_cambio}")
    print(f"Cambios detectados: {len(cambios)}")
    print()

    if errores:
        print("AVISOS:")
        for err in errores:
            print(f"  [!] {err}")
        print()

    if not cambios:
        print("[OK] Todo sincronizado, no hay cambios")
        input("\nPresiona Enter para continuar...")
        return

    print("CAMBIOS A APLICAR:")
    for c in cambios:
        emoji_ant = ESTADO_COMERCIAL_EMOJI.get(c['anterior'], '?')
        emoji_new = ESTADO_COMERCIAL_EMOJI.get(c['nuevo'], '?')
        label_ant = ESTADO_COMERCIAL_LABEL.get(c['anterior'], c['anterior'])
        label_new = ESTADO_COMERCIAL_LABEL.get(c['nuevo'], c['nuevo'])
        print(f"  {c['nombre']:<35} {emoji_ant} {label_ant} → {emoji_new} {label_new}")
    print()

    confirmacion = input("Aplicar cambios? (SI para confirmar): ").strip()
    if confirmacion != "SI":
        print("\n[!] Sync cancelado")
        input("\nPresiona Enter para continuar...")
        return

    # Aplicar cambios
    with get_connection() as conn:
        cursor = conn.cursor()
        for c in cambios:
            cursor.execute(
                "UPDATE productos SET estado_comercial = ? WHERE id = ?",
                (c['nuevo'], c['id'])
            )
        conn.commit()

    print(f"\n[OK] {len(cambios)} productos actualizados")
    input("\nPresiona Enter para continuar...")


# ═══════════════════════════════════════════════════════════
# BACKUP DE BASE DE DATOS
# ═══════════════════════════════════════════════════════════

def backup_base_datos():
    """Crea un backup de la base de datos con timestamp"""
    clear_screen()
    print_header()
    print("BACKUP DE BASE DE DATOS")
    print()

    from scripts.db_config import DB_PATH
    import shutil

    if not os.path.exists(DB_PATH):
        print(f"[!] No se encuentra la base de datos: {DB_PATH}")
        input("\nPresiona Enter para continuar...")
        return

    # Directorio de backups
    backup_dir = os.path.join(os.path.dirname(DB_PATH), "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Info del archivo actual
    db_size = os.path.getsize(DB_PATH)
    db_size_mb = db_size / (1024 * 1024)

    print(f"  Base de datos:  {DB_PATH}")
    print(f"  Tamano:         {db_size_mb:.2f} MB")
    print(f"  Destino:        {backup_dir}/")
    print()

    # Listar backups existentes
    backups_existentes = sorted(
        [f for f in os.listdir(backup_dir) if f.startswith("autotok") and f.endswith(".db")],
        reverse=True
    ) if os.path.exists(backup_dir) else []

    if backups_existentes:
        print(f"  Backups existentes: {len(backups_existentes)}")
        for b in backups_existentes[:5]:
            b_path = os.path.join(backup_dir, b)
            b_size = os.path.getsize(b_path) / (1024 * 1024)
            print(f"    {b}  ({b_size:.2f} MB)")
        if len(backups_existentes) > 5:
            print(f"    ... y {len(backups_existentes) - 5} mas")
        print()

    confirmacion = input("Crear backup? (Enter para confirmar, 0 para cancelar): ").strip()
    if confirmacion == "0":
        return

    # Crear backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"autotok_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        print()
        print("Creando backup...")
        shutil.copy2(DB_PATH, backup_path)

        # Verificar
        if os.path.exists(backup_path):
            backup_size = os.path.getsize(backup_path)
            if backup_size == db_size:
                print(f"[OK] Backup creado: {backup_filename}")
                print(f"     Tamano: {backup_size / (1024 * 1024):.2f} MB")
            else:
                print(f"[!] Backup creado pero tamano diferente ({backup_size} vs {db_size})")
        else:
            print("[!] Error: el archivo de backup no se creo")
    except Exception as e:
        print(f"[ERROR] Error creando backup: {e}")

    input("\nPresiona Enter para continuar...")


# ═══════════════════════════════════════════════════════════
# GENERACIÓN DE MATERIAL CON IA
# ═══════════════════════════════════════════════════════════

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
# ═══════════════════════════════════════════════════════════

def gestionar_bofs():
    """Gestiona BOFs de un producto: ver estado, activar/desactivar."""
    clear_screen()
    print_header()
    print("GESTIONAR BOFs (Activar / Desactivar)")
    print()

    producto = seleccionar_producto()
    if not producto:
        return

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM productos WHERE nombre = ?", (producto,))
        row = cursor.fetchone()
        if not row:
            print(f"[!] Producto '{producto}' no encontrado en BD")
            input("\nPresiona Enter para continuar...")
            return
        producto_id = row['id']

        cursor.execute("""
            SELECT pb.id, pb.deal_math, pb.activo, pb.veces_usado,
                   (SELECT COUNT(*) FROM audios WHERE bof_id = pb.id) as num_audios,
                   (SELECT COUNT(*) FROM variantes_overlay_seo WHERE bof_id = pb.id) as num_variantes,
                   (SELECT COUNT(*) FROM videos WHERE bof_id = pb.id) as num_videos,
                   (SELECT COUNT(*) FROM videos WHERE bof_id = pb.id AND estado = 'Generado') as videos_generados,
                   (SELECT COUNT(*) FROM videos WHERE bof_id = pb.id AND estado = 'En Calendario') as videos_calendario
            FROM producto_bofs pb
            WHERE pb.producto_id = ?
            ORDER BY pb.id
        """, (producto_id,))
        bofs = [dict(r) for r in cursor.fetchall()]

    if not bofs:
        print(f"[!] No hay BOFs para '{producto}'")
        input("\nPresiona Enter para continuar...")
        return

    print(f"  BOFs de {producto}:")
    print()
    for i, bof in enumerate(bofs, 1):
        estado = "ACTIVO" if bof['activo'] else "INACTIVO"
        icono = "  " if bof['activo'] else "  "
        print(f"  {icono} {i}. [ID:{bof['id']}] {bof['deal_math']}")
        print(f"       Estado: {estado} | Audios: {bof['num_audios']} | Variantes: {bof['num_variantes']}")
        print(f"       Videos totales: {bof['num_videos']} | Generados: {bof['videos_generados']} | En Calendario: {bof['videos_calendario']}")
        print()

    print("  Opciones:")
    print("    D. Desactivar un BOF")
    print("    A. Activar un BOF")
    print("    0. Volver")
    print()

    opcion = input("  Opcion: ").strip().upper()

    if opcion == "0":
        return

    if opcion not in ("D", "A"):
        print("  [!] Opcion invalida")
        input("\nPresiona Enter para continuar...")
        return

    accion = "desactivar" if opcion == "D" else "activar"
    nuevo_valor = 0 if opcion == "D" else 1

    sel = input(f"  Numero del BOF a {accion}: ").strip()
    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(bofs):
            raise ValueError
        bof_sel = bofs[idx]
    except (ValueError, IndexError):
        print("  [!] Seleccion invalida")
        input("\nPresiona Enter para continuar...")
        return

    if bof_sel['activo'] == nuevo_valor:
        print(f"\n  [!] El BOF {bof_sel['id']} ya esta {'activo' if nuevo_valor else 'inactivo'}")
        input("\nPresiona Enter para continuar...")
        return

    # Avisos de seguridad al desactivar
    if opcion == "D":
        avisos = []
        if bof_sel['videos_generados'] > 0:
            avisos.append(f"Hay {bof_sel['videos_generados']} videos en estado 'Generado' con este BOF")
        if bof_sel['videos_calendario'] > 0:
            avisos.append(f"Hay {bof_sel['videos_calendario']} videos 'En Calendario' con este BOF")

        if avisos:
            print()
            print("  ATENCION:")
            for aviso in avisos:
                print(f"    [!] {aviso}")
            print()
            print("  Desactivar el BOF evita que se generen NUEVOS videos con el,")
            print("  pero los videos existentes no se tocan. Si quieres descartarlos,")
            print("  usa la opcion 6 (Descartar videos) despues.")
            print()

    confirma = input(f"  Confirmar {accion} BOF {bof_sel['id']} ({bof_sel['deal_math']})? (S/N): ").strip().upper()
    if confirma != "S":
        print("  Cancelado")
        input("\nPresiona Enter para continuar...")
        return

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE producto_bofs SET activo = ? WHERE id = ?", (nuevo_valor, bof_sel['id']))
        conn.commit()

    estado_str = "ACTIVO" if nuevo_valor else "INACTIVO"
    print(f"\n  [OK] BOF {bof_sel['id']} ahora esta {estado_str}")

    if opcion == "D" and bof_sel['videos_generados'] > 0:
        print(f"\n  RECUERDA: Usa opcion 6 para descartar los {bof_sel['videos_generados']} videos 'Generado' de este BOF")

    input("\nPresiona Enter para continuar...")


# ═══════════════════════════════════════════════════════════
# DESCARTAR VIDEOS GENERADOS (Cambio 3.4)
# ═══════════════════════════════════════════════════════════

def descartar_videos():
    """Descarta videos generados (por producto, hook, overlay o individual).

    Cambia el estado a 'Descartado' en BD y mueve el archivo a la carpeta descartados/.
    Permite filtrar por: producto, hook, overlay, o selección individual.
    Solo afecta a videos con estado 'Generado' (pre-calendario).
    """
    clear_screen()
    print_header()
    print("🗑️  DESCARTAR VIDEOS GENERADOS")
    print()
    print("  Descarta videos con estado 'Generado' (antes de entrar en calendario).")
    print("  Los archivos se mueven a la carpeta descartados/ de la cuenta.")
    print()

    cuentas = seleccionar_cuentas()
    if not cuentas:
        return

    # Para simplificar, trabajamos con una cuenta a la vez
    cuenta = cuentas[0] if len(cuentas) == 1 else None
    if not cuenta:
        print("Selecciona una sola cuenta:")
        print("  1. ofertastrendy20")
        print("  2. lotopdevicky")
        print("  0. Cancelar")
        opcion = input("Cuenta: ").strip()
        if opcion == "1":
            cuenta = "ofertastrendy20"
        elif opcion == "2":
            cuenta = "lotopdevicky"
        else:
            return

    with get_connection() as conn:
        cursor = conn.cursor()

        # Obtener videos generados con info de producto, hook y overlay
        cursor.execute("""
            SELECT
                v.id, v.video_id, v.filepath,
                p.nombre as producto, p.id as producto_id,
                h.filename as hook, h.id as hook_id,
                var.overlay_line1, var.id as variante_id
            FROM videos v
            JOIN productos p ON v.producto_id = p.id
            JOIN material h ON v.hook_id = h.id
            JOIN variantes_overlay_seo var ON v.variante_id = var.id
            WHERE v.cuenta = ? AND v.estado = 'Generado'
            ORDER BY p.nombre, h.filename
        """, (cuenta,))
        videos = [dict(row) for row in cursor.fetchall()]

    if not videos:
        print(f"\n[!] No hay videos con estado 'Generado' para {cuenta}")
        input("\nPresiona Enter para continuar...")
        return

    # Resumen
    productos = {}
    hooks = {}
    overlays = {}
    for v in videos:
        productos[v['producto']] = productos.get(v['producto'], 0) + 1
        hooks[v['hook']] = hooks.get(v['hook'], 0) + 1
        overlays[v['overlay_line1']] = overlays.get(v['overlay_line1'], 0) + 1

    print(f"\n  Videos generados para {cuenta}: {len(videos)}")
    print(f"  Productos: {len(productos)}")
    print()

    print("  ¿Cómo quieres filtrar los videos a descartar?")
    print()
    print("  1. Por PRODUCTO (todos los videos de un producto)")
    print("  2. Por HOOK (todos los que usan un hook concreto)")
    print("  3. Por OVERLAY (todos los que usan un overlay concreto)")
    print("  4. Selección INDIVIDUAL (elegir videos uno a uno)")
    print("  5. TODOS los videos generados de esta cuenta")
    print("  0. Cancelar")
    print()

    opcion = input("  Opción: ").strip()

    if opcion == "0":
        return

    videos_a_descartar = []

    if opcion == "1":
        # Filtrar por producto
        print("\n  Productos con videos generados:")
        prods_sorted = sorted(productos.items(), key=lambda x: x[1], reverse=True)
        for i, (prod, count) in enumerate(prods_sorted, 1):
            print(f"    {i}. {prod} ({count} videos)")
        print()
        sel = input("  Producto a descartar (numero): ").strip()
        try:
            idx = int(sel) - 1
            prod_nombre = prods_sorted[idx][0]
            videos_a_descartar = [v for v in videos if v['producto'] == prod_nombre]
        except (ValueError, IndexError):
            print("[!] Selección inválida")
            input("\nPresiona Enter para continuar...")
            return

    elif opcion == "2":
        # Filtrar por hook
        print("\n  Hooks usados en videos generados:")
        hooks_sorted = sorted(hooks.items(), key=lambda x: x[1], reverse=True)
        for i, (hook, count) in enumerate(hooks_sorted, 1):
            hook_short = hook[:50]
            print(f"    {i}. {hook_short} ({count} videos)")
        print()
        sel = input("  Hook a descartar (numero): ").strip()
        try:
            idx = int(sel) - 1
            hook_nombre = hooks_sorted[idx][0]
            videos_a_descartar = [v for v in videos if v['hook'] == hook_nombre]
        except (ValueError, IndexError):
            print("[!] Selección inválida")
            input("\nPresiona Enter para continuar...")
            return

    elif opcion == "3":
        # Filtrar por overlay
        print("\n  Overlays usados en videos generados:")
        overlays_sorted = sorted(overlays.items(), key=lambda x: x[1], reverse=True)
        for i, (overlay, count) in enumerate(overlays_sorted, 1):
            overlay_short = overlay[:50]
            print(f"    {i}. {overlay_short} ({count} videos)")
        print()
        sel = input("  Overlay a descartar (numero): ").strip()
        try:
            idx = int(sel) - 1
            overlay_nombre = overlays_sorted[idx][0]
            videos_a_descartar = [v for v in videos if v['overlay_line1'] == overlay_nombre]
        except (ValueError, IndexError):
            print("[!] Selección inválida")
            input("\nPresiona Enter para continuar...")
            return

    elif opcion == "4":
        # Selección individual
        print("\n  Videos generados (máx 50 primeros):")
        for i, v in enumerate(videos[:50], 1):
            print(f"    {i}. {v['producto'][:15]} | {v['hook'][:20]} | {v['overlay_line1'][:20]}")
        if len(videos) > 50:
            print(f"    ... y {len(videos) - 50} más (usa filtro por producto/hook para ver todos)")
        print()
        print("  Introduce los números separados por coma (ej: 1,3,5,7)")
        sel = input("  Videos: ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in sel.split(",")]
            videos_a_descartar = [videos[i] for i in indices if 0 <= i < len(videos)]
        except (ValueError, IndexError):
            print("[!] Selección inválida")
            input("\nPresiona Enter para continuar...")
            return

    elif opcion == "5":
        videos_a_descartar = videos

    else:
        print("[!] Opción inválida")
        input("\nPresiona Enter para continuar...")
        return

    if not videos_a_descartar:
        print("\n[!] No hay videos que descartar con ese filtro")
        input("\nPresiona Enter para continuar...")
        return

    # Confirmar
    print(f"\n  Se van a descartar {len(videos_a_descartar)} videos:")
    # Agrupar por producto para el resumen
    por_prod = {}
    for v in videos_a_descartar:
        por_prod[v['producto']] = por_prod.get(v['producto'], 0) + 1
    for prod, count in sorted(por_prod.items()):
        print(f"    {prod}: {count} videos")
    print()

    confirmacion = input("  Confirmar descarte? (SI para ejecutar): ").strip()
    if confirmacion != "SI":
        print("\n[!] Descarte cancelado")
        input("\nPresiona Enter para continuar...")
        return

    # Ejecutar descarte
    from config import OUTPUT_DIR
    import shutil

    descartados_dir = os.path.join(OUTPUT_DIR, cuenta, 'descartados')
    os.makedirs(descartados_dir, exist_ok=True)

    descartados_ok = 0
    errores = 0

    with get_connection() as conn:
        cursor = conn.cursor()

        for v in videos_a_descartar:
            try:
                # Actualizar estado en BD
                cursor.execute("""
                    UPDATE videos SET estado = 'Descartado' WHERE id = ?
                """, (v['id'],))

                # Mover archivo a carpeta descartados
                if v['filepath'] and os.path.exists(v['filepath']):
                    destino = os.path.join(descartados_dir, os.path.basename(v['filepath']))
                    os.rename(v['filepath'], destino)
                    cursor.execute("UPDATE videos SET filepath = ? WHERE id = ?",
                                 (destino, v['id']))

                descartados_ok += 1
            except Exception as e:
                errores += 1
                print(f"  [ERROR] {v['video_id']}: {e}")

        conn.commit()

    print(f"\n  [OK] {descartados_ok} videos descartados")
    if errores:
        print(f"  [WARNING] {errores} errores")
    print(f"  Archivos movidos a: {descartados_dir}")

    # Registrar en historial
    try:
        from scripts.db_config import registrar_historial
        prods_str = ", ".join(f"{p}:{c}" for p, c in sorted(por_prod.items()))
        registrar_historial(
            accion='descartar',
            cuenta=cuenta,
            num_videos=descartados_ok,
            detalles=f"filtro={opcion} productos=[{prods_str}]"
        )
    except Exception as e:
        print(f"  [WARNING] No se pudo registrar en historial: {e}")

    input("\nPresiona Enter para continuar...")


# ═══════════════════════════════════════════════════════════
# LIMPIAR DRIVE
# ═══════════════════════════════════════════════════════════

def limpiar_drive():
    """DEPRECATED (QUA-151): Ya no hay Drive separado. Videos están en Synology."""
    clear_screen()
    print_header()
    print("🧹  LIMPIAR DRIVE")
    print()
    print("  [INFO] Esta opción ya no es necesaria (QUA-151).")
    print("  Los videos se generan directamente en Synology Drive.")
    print("  No hay copia separada que limpiar.")
    print()
    input("Presiona Enter para continuar...")


# ═══════════════════════════════════════════════════════════
# PUBLICACIÓN TIKTOK
# ═══════════════════════════════════════════════════════════

def ver_pendientes_publicar():
    """Opción 19: Muestra videos pendientes de publicar en TikTok."""
    print(f"\n{'='*60}")
    print(f"  📋 VIDEOS PENDIENTES DE PUBLICAR")
    print(f"{'='*60}\n")

    try:
        from tiktok_publisher import listar_pendientes
    except ImportError as e:
        print(f"[ERROR] No se puede importar tiktok_publisher: {e}")
        print(f"[TIP] Ejecuta: python scripts/setup_publisher.py")
        input("\nPresiona Enter para continuar...")
        return

    cuenta = input("  Cuenta (vacío = todas): ").strip() or None
    dias = input("  Días hacia adelante [7]: ").strip()
    dias = int(dias) if dias else 7

    listar_pendientes(cuenta, dias)
    input("\nPresiona Enter para continuar...")


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

        # PREPARAR MATERIAL
        if opcion == "1":
            escanear_material()
        elif opcion == "2":
            validar_material()
        elif opcion == "3":
            reimportar_bof()
        # GENERAR VIDEOS
        elif opcion == "4":
            generar_videos()
        elif opcion == "5":
            generar_videos_multiples()
        elif opcion == "6":
            descartar_videos()
        # PROGRAMACIÓN
        elif opcion == "7":
            programar_calendario()
        elif opcion == "8":
            deshacer_programacion()
        elif opcion == "9":
            sincronizar_sheet()
        # ESTADO Y CONTROL
        elif opcion == "10":
            ver_dashboard()
        elif opcion == "11":
            ver_estado_productos()
        elif opcion == "12":
            gestionar_productos()
        elif opcion == "13":
            sync_lifecycle_sheet()
        elif opcion == "14":
            verificar_integridad()
        # MATERIAL IA
        elif opcion == "15":
            generar_fondos_ia()
        elif opcion == "16":
            revisar_material_ia()
        # SISTEMA
        elif opcion == "17":
            backup_base_datos()
        elif opcion == "18":
            limpiar_drive()
        # PUBLICACIÓN TIKTOK
        elif opcion == "19":
            ver_pendientes_publicar()
        elif opcion == "20":
            publicar_tiktok()
        # GESTION BOFs
        elif opcion == "21":
            gestionar_bofs()
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
