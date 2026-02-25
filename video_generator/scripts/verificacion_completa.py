"""
VERIFICACIÓN COMPLETA: cruza las 4 capas del sistema
  1. Google Sheet (calendario)
  2. SQLite BD
  3. Carpetas locales
  4. Google Drive

Detecta inconsistencias entre capas y genera informe.

Ejecutar desde video_generator/:
  python scripts/verificacion_completa.py
  python scripts/verificacion_completa.py --fix   (corrige BD y mueve archivos)
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.db_config import get_connection
from config import OUTPUT_DIR, DRIVE_SYNC_PATH

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════

CUENTAS = ["ofertastrendy20", "lotopdevicky"]
BASE_LOCAL = Path(OUTPUT_DIR)
BASE_DRIVE = Path(DRIVE_SYNC_PATH)

# Mapeo carpeta local → estado esperado en BD
CARPETA_ESTADO_LOCAL = {
    "raiz": "Generado",
    "calendario": "En Calendario",
    "programados": "Programado",
    "descartados": "Descartado",
}

# Estados que deberían tener copia en Drive
ESTADOS_EN_DRIVE = ["En Calendario", "Programado"]


def scan_local(cuenta):
    """Escanea archivos .mp4 en carpetas locales. Returns {video_id: carpeta}"""
    cuenta_path = BASE_LOCAL / cuenta
    archivos = {}

    if not cuenta_path.exists():
        print(f"  [!] Carpeta local no existe: {cuenta_path}")
        return archivos

    # Raíz
    for f in cuenta_path.glob("*.mp4"):
        archivos[f.stem] = {"carpeta": "raiz", "path": str(f)}

    # Subcarpetas
    for sub in ["calendario", "programados", "descartados"]:
        sub_path = cuenta_path / sub
        if sub_path.exists():
            for f in sub_path.rglob("*.mp4"):
                archivos[f.stem] = {"carpeta": sub, "path": str(f)}

    return archivos


def scan_drive(cuenta):
    """Escanea archivos .mp4 en Drive. Returns {video_id: path}"""
    archivos = {}
    drive_cuenta = BASE_DRIVE / cuenta

    if not drive_cuenta.exists():
        print(f"  [!] Carpeta Drive no existe: {drive_cuenta}")
        return archivos

    for f in drive_cuenta.rglob("*.mp4"):
        archivos[f.stem] = str(f)

    return archivos


def read_sheet(cuenta):
    """Lee videos del Sheet para una cuenta. Returns {video_id: {estado, fecha}}"""
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials

        SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        SHEET_URL = 'https://docs.google.com/spreadsheets/d/1QCb4xYKoLJPaMrGaBW311VQIyDg2Xa08V5DmsD2H81g/'

        creds_path = os.path.join(os.path.dirname(__file__), "..", "credentials.json")
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, SCOPES)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(SHEET_URL).sheet1
        all_rows = sheet.get_all_records()

        videos = {}
        for row in all_rows:
            if row.get('Cuenta', '').strip() == cuenta:
                vid = row.get('Video', '').strip()
                estado = row.get('Estado', '').strip()
                fecha = row.get('Fecha', '').strip()
                if vid:
                    videos[vid] = {"estado": estado, "fecha": fecha}
        return videos

    except Exception as e:
        print(f"  [!] Error leyendo Sheet: {e}")
        return None


def read_bd(cuenta):
    """Lee videos de la BD para una cuenta. Returns {video_id: {estado, fecha, hora, filepath, batch}}"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT video_id, estado, fecha_programada, hora_programada, filepath, batch_number
        FROM videos WHERE cuenta = ?
    """, (cuenta,))
    videos = {}
    for r in cursor.fetchall():
        videos[r["video_id"]] = {
            "estado": r["estado"],
            "fecha": r["fecha_programada"],
            "hora": r["hora_programada"],
            "filepath": r["filepath"],
            "batch": r["batch_number"],
        }
    conn.close()
    return videos


def main():
    fix_mode = "--fix" in sys.argv
    ahora = datetime.now()
    hoy = ahora.strftime("%Y-%m-%d")

    print("=" * 80)
    print(f"  VERIFICACIÓN COMPLETA AUTOTOK          {ahora.strftime('%d/%m/%Y %H:%M')}")
    if fix_mode:
        print(f"  MODO: REPARACIÓN AUTOMÁTICA")
    print("=" * 80)

    errores_totales = 0
    total_fixed = 0

    for cuenta in CUENTAS:
        print(f"\n{'='*80}")
        print(f"  CUENTA: {cuenta}")
        print(f"{'='*80}")

        # === Leer las 4 capas ===
        print("\n  Leyendo capas...")
        bd = read_bd(cuenta)
        local = scan_local(cuenta)
        drive = scan_drive(cuenta)
        sheet = read_sheet(cuenta)

        bd_system = {k: v for k, v in bd.items() if v["batch"] != 0}
        bd_imported = {k: v for k, v in bd.items() if v["batch"] == 0}

        print(f"    BD total:      {len(bd):>4} ({len(bd_system)} sistema + {len(bd_imported)} importados)")
        print(f"    Local:         {len(local):>4}")
        print(f"    Drive:         {len(drive):>4}")
        if sheet is not None:
            print(f"    Sheet:         {len(sheet):>4}")
        else:
            print(f"    Sheet:         ERROR (sin acceso)")

        errores = []

        # ═══════════════════════════════════════
        # CHECK 1: Local vs BD (solo sistema)
        # ═══════════════════════════════════════
        print(f"\n  --- CHECK 1: Local ↔ BD ---")

        # 1a. En local pero no en BD
        local_no_bd = {vid: info for vid, info in local.items() if vid not in bd}
        if local_no_bd:
            print(f"  [!] En local pero NO en BD: {len(local_no_bd)}")
            for vid, info in sorted(local_no_bd.items())[:10]:
                print(f"      {vid} (carpeta: {info['carpeta']})")
            if len(local_no_bd) > 10:
                print(f"      ... y {len(local_no_bd) - 10} más")
            errores.append(("LOCAL_SIN_BD", local_no_bd))

        # 1b. En BD (sistema) pero no en local
        bd_no_local = {vid: info for vid, info in bd_system.items() if vid not in local}
        if bd_no_local:
            print(f"  [!] En BD pero NO en local: {len(bd_no_local)}")
            for vid, info in sorted(bd_no_local.items())[:10]:
                print(f"      {vid} (estado BD: {info['estado']})")
            if len(bd_no_local) > 10:
                print(f"      ... y {len(bd_no_local) - 10} más")
            errores.append(("BD_SIN_LOCAL", bd_no_local))

        # 1c. Estado BD no coincide con carpeta local
        estado_mismatch = []
        for vid, info in local.items():
            if vid in bd_system:
                estado_bd = bd_system[vid]["estado"]
                esperado = CARPETA_ESTADO_LOCAL.get(info["carpeta"])
                if esperado and estado_bd != esperado:
                    estado_mismatch.append((vid, info["carpeta"], esperado, estado_bd))

        if estado_mismatch:
            print(f"  [!] Estado BD ≠ carpeta local: {len(estado_mismatch)}")
            for vid, carpeta, esperado, real in sorted(estado_mismatch)[:10]:
                print(f"      {vid}: carpeta={carpeta} → esperado={esperado}, BD={real}")
            errores.append(("ESTADO_MISMATCH_LOCAL", estado_mismatch))

        if not local_no_bd and not bd_no_local and not estado_mismatch:
            print(f"  [OK] Local ↔ BD sincronizados")

        # ═══════════════════════════════════════
        # CHECK 2: BD vs Sheet
        # ═══════════════════════════════════════
        if sheet is not None:
            print(f"\n  --- CHECK 2: BD ↔ Sheet ---")

            # Videos en Sheet pero no en BD
            sheet_no_bd = {vid: info for vid, info in sheet.items() if vid not in bd}
            if sheet_no_bd:
                print(f"  [!] En Sheet pero NO en BD: {len(sheet_no_bd)}")
                for vid, info in sorted(sheet_no_bd.items())[:10]:
                    print(f"      {vid} (estado Sheet: {info['estado']})")
                errores.append(("SHEET_SIN_BD", sheet_no_bd))

            # Videos en BD (con calendario) pero no en Sheet
            bd_calendario = {vid: info for vid, info in bd_system.items()
                            if info["estado"] in ("En Calendario", "Programado", "Descartado")
                            and info["fecha"] is not None}
            bd_cal_no_sheet = {vid: info for vid, info in bd_calendario.items() if vid not in sheet}
            if bd_cal_no_sheet:
                print(f"  [!] En BD (calendario) pero NO en Sheet: {len(bd_cal_no_sheet)}")
                for vid, info in sorted(bd_cal_no_sheet.items())[:10]:
                    print(f"      {vid} (estado BD: {info['estado']}, fecha: {info['fecha']})")
                errores.append(("BD_CAL_SIN_SHEET", bd_cal_no_sheet))

            # Estado Sheet ≠ BD
            estado_mismatch_sheet = []
            for vid, sheet_info in sheet.items():
                if vid in bd:
                    bd_estado = bd[vid]["estado"]
                    sh_estado = sheet_info["estado"]
                    if sh_estado and bd_estado != sh_estado:
                        estado_mismatch_sheet.append((vid, sh_estado, bd_estado))

            if estado_mismatch_sheet:
                print(f"  [!] Estado Sheet ≠ BD: {len(estado_mismatch_sheet)}")
                for vid, sh_est, bd_est in sorted(estado_mismatch_sheet)[:10]:
                    print(f"      {vid}: Sheet={sh_est}, BD={bd_est}")
                errores.append(("ESTADO_MISMATCH_SHEET", estado_mismatch_sheet))

            if not sheet_no_bd and not bd_cal_no_sheet and not estado_mismatch_sheet:
                print(f"  [OK] BD ↔ Sheet sincronizados")

        # ═══════════════════════════════════════
        # CHECK 3: Drive vs BD
        # ═══════════════════════════════════════
        print(f"\n  --- CHECK 3: Drive ↔ BD ---")

        # Videos que deberían estar en Drive (En Calendario o Programado con fecha)
        deberia_drive = {vid: info for vid, info in bd_system.items()
                        if info["estado"] in ESTADOS_EN_DRIVE
                        and info["fecha"] is not None}

        # Faltan en Drive
        faltan_drive = {vid: info for vid, info in deberia_drive.items() if vid not in drive}
        if faltan_drive:
            print(f"  [!] Deberían estar en Drive pero NO están: {len(faltan_drive)}")
            for vid, info in sorted(faltan_drive.items())[:10]:
                print(f"      {vid} (estado: {info['estado']}, fecha: {info['fecha']})")
            if len(faltan_drive) > 10:
                print(f"      ... y {len(faltan_drive) - 10} más")
            errores.append(("FALTA_DRIVE", faltan_drive))

        # En Drive pero no deberían (estado Generado o Descartado)
        drive_sobrante = {}
        for vid, path in drive.items():
            if vid in bd_system:
                if bd_system[vid]["estado"] not in ESTADOS_EN_DRIVE:
                    drive_sobrante[vid] = {"path": path, "estado": bd_system[vid]["estado"]}
            elif vid not in bd:
                drive_sobrante[vid] = {"path": path, "estado": "NO EN BD"}

        if drive_sobrante:
            print(f"  [!] En Drive pero NO deberían: {len(drive_sobrante)}")
            for vid, info in sorted(drive_sobrante.items())[:10]:
                print(f"      {vid} (estado: {info['estado']})")
            errores.append(("DRIVE_SOBRANTE", drive_sobrante))

        if not faltan_drive and not drive_sobrante:
            print(f"  [OK] Drive ↔ BD sincronizados")

        # ═══════════════════════════════════════
        # RESUMEN + FIX
        # ═══════════════════════════════════════
        total_errores = sum(len(e[1]) for e in errores)
        errores_totales += total_errores

        if total_errores == 0:
            print(f"\n  ✅ {cuenta}: TODO CORRECTO")
        else:
            print(f"\n  ⚠️  {cuenta}: {total_errores} inconsistencias detectadas")

            if fix_mode:
                print(f"\n  --- REPARANDO {cuenta} ---")
                fixed = fix_cuenta(cuenta, errores)
                total_fixed += fixed

    # ═══════════════════════════════════════
    # RESUMEN GLOBAL
    # ═══════════════════════════════════════
    print(f"\n{'='*80}")
    if errores_totales == 0:
        print(f"  ✅ VERIFICACIÓN COMPLETA: TODO CORRECTO")
    else:
        print(f"  ⚠️  VERIFICACIÓN COMPLETA: {errores_totales} inconsistencias")
        if fix_mode:
            print(f"  🔧 Reparados: {total_fixed}")
        else:
            print(f"\n  Para corregir automáticamente ejecuta:")
            print(f"    python scripts/verificacion_completa.py --fix")
    print(f"{'='*80}\n")


def fix_cuenta(cuenta, errores):
    """Repara inconsistencias de una cuenta en las 4 capas.

    Reparaciones soportadas:
      - ESTADO_MISMATCH_LOCAL: Mover archivo a carpeta correcta según BD
      - FALTA_DRIVE: Copiar archivo a Drive
      - DRIVE_SOBRANTE: Borrar archivo de Drive
      - LOCAL_SIN_BD: Registrar video en BD como Generado (solo si está en raíz)

    NO repara automáticamente (requiere intervención manual):
      - SHEET_SIN_BD: Video en Sheet que no existe en BD
      - BD_CAL_SIN_SHEET: Video en BD con calendario que no está en Sheet
      - ESTADO_MISMATCH_SHEET: Estado Sheet ≠ BD (usar sync para resolver)
      - BD_SIN_LOCAL: Video en BD cuyo archivo no existe
    """
    from drive_sync import copiar_a_drive, is_drive_configured

    fixed = 0

    for tipo, datos in errores:

        # --- Actualizar BD para que coincida con la carpeta donde está el archivo ---
        if tipo == "ESTADO_MISMATCH_LOCAL":
            conn = get_connection()
            cursor = conn.cursor()
            for vid, carpeta, esperado, estado_bd in datos:
                # 'esperado' es el estado que corresponde a la carpeta donde ESTÁ el archivo
                # 'estado_bd' es el estado actual en BD (incorrecto)
                # → Actualizamos BD al estado de la carpeta (la carpeta manda)

                # Buscar el path real del archivo
                local_info = scan_local(cuenta).get(vid)
                if not local_info:
                    continue
                real_path = local_info["path"]

                # Para Descartado/Violation/Generado: limpiar fecha/hora programada
                clear_fecha = esperado in ("Descartado", "Generado")

                if clear_fecha:
                    cursor.execute(
                        """UPDATE videos
                        SET estado = ?, filepath = ?, fecha_programada = NULL, hora_programada = NULL
                        WHERE video_id = ? AND cuenta = ?""",
                        (esperado, real_path, vid, cuenta),
                    )
                else:
                    cursor.execute(
                        "UPDATE videos SET estado = ?, filepath = ? WHERE video_id = ? AND cuenta = ?",
                        (esperado, real_path, vid, cuenta),
                    )
                print(f"    [FIX] {vid}: BD {estado_bd} → {esperado}")
                fixed += 1

            conn.commit()
            conn.close()

        # --- Copiar a Drive los que faltan ---
        elif tipo == "FALTA_DRIVE" and is_drive_configured():
            for vid, info in datos.items():
                fecha = info.get("fecha")
                filepath = info.get("filepath")
                if filepath and os.path.exists(filepath) and fecha:
                    result = copiar_a_drive(filepath, cuenta, fecha)
                    if result:
                        print(f"    [FIX] {vid}: copiado a Drive")
                        fixed += 1
                    else:
                        print(f"    [!] {vid}: no se pudo copiar a Drive")

        # --- Borrar de Drive los sobrantes ---
        elif tipo == "DRIVE_SOBRANTE":
            for vid, info in datos.items():
                path = info.get("path")
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                        print(f"    [FIX] {vid}: borrado de Drive")
                        fixed += 1
                    except OSError as e:
                        print(f"    [!] Error borrando {vid} de Drive: {e}")

        # --- Registrar en BD archivos locales sin registro (solo raíz = Generado) ---
        elif tipo == "LOCAL_SIN_BD":
            conn = get_connection()
            cursor = conn.cursor()

            # Obtener placeholders por producto
            cursor.execute("SELECT id, nombre FROM productos")
            productos_db = {r["nombre"]: r["id"] for r in cursor.fetchall()}

            placeholders = {}
            for nombre_bd, prod_id in productos_db.items():
                ph = {}
                cursor.execute(
                    "SELECT id FROM producto_bofs WHERE producto_id = ? LIMIT 1",
                    (prod_id,),
                )
                r = cursor.fetchone()
                ph["bof"] = r["id"] if r else None
                if ph["bof"]:
                    cursor.execute(
                        "SELECT id FROM variantes_overlay_seo WHERE bof_id = ? LIMIT 1",
                        (ph["bof"],),
                    )
                    r = cursor.fetchone()
                    ph["var"] = r["id"] if r else None
                    cursor.execute(
                        "SELECT id FROM audios WHERE bof_id = ? LIMIT 1",
                        (ph["bof"],),
                    )
                    r = cursor.fetchone()
                    ph["aud"] = r["id"] if r else None
                else:
                    ph["var"] = None
                    ph["aud"] = None
                cursor.execute(
                    "SELECT id FROM material WHERE producto_id = ? AND tipo = 'hook' LIMIT 1",
                    (prod_id,),
                )
                r = cursor.fetchone()
                ph["hook"] = r["id"] if r else None
                placeholders[nombre_bd] = ph

            for vid, info in datos.items():
                if info["carpeta"] != "raiz":
                    print(f"    [SKIP] {vid}: en carpeta {info['carpeta']}, requiere revisión manual")
                    continue

                # Extraer producto del video_id (formato: producto_cuenta_batchXXX_video_XXX)
                producto_nombre = None
                for pname in sorted(productos_db.keys(), key=len, reverse=True):
                    if vid.startswith(pname + "_"):
                        producto_nombre = pname
                        break

                if not producto_nombre or producto_nombre not in placeholders:
                    print(f"    [SKIP] {vid}: producto no identificado")
                    continue

                ph = placeholders[producto_nombre]
                if not all([ph.get("bof"), ph.get("var"), ph.get("hook"), ph.get("aud")]):
                    print(f"    [SKIP] {vid}: faltan FKs para {producto_nombre}")
                    continue

                prod_id = productos_db[producto_nombre]
                filepath = str(BASE_LOCAL / cuenta / f"{vid}.mp4")

                try:
                    cursor.execute(
                        """INSERT INTO videos
                        (video_id, producto_id, cuenta, bof_id, variante_id, hook_id, audio_id,
                         estado, filepath, batch_number, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'Generado', ?, 1, datetime('now'))""",
                        (vid, prod_id, cuenta, ph["bof"], ph["var"], ph["hook"], ph["aud"], filepath),
                    )
                    print(f"    [FIX] {vid}: registrado en BD como Generado")
                    fixed += 1
                except Exception as e:
                    print(f"    [!] Error registrando {vid}: {e}")

            conn.commit()
            conn.close()

        # --- Casos que NO se reparan automáticamente ---
        elif tipo in ("SHEET_SIN_BD", "BD_CAL_SIN_SHEET", "ESTADO_MISMATCH_SHEET", "BD_SIN_LOCAL"):
            print(f"    [INFO] {tipo}: {len(datos)} — requiere revisión manual o sync (opción 7)")

    return fixed


if __name__ == "__main__":
    main()
