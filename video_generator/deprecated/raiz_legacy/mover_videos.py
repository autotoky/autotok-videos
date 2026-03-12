#!/usr/bin/env python3
"""
MOVER_VIDEOS.PY - DEPRECATED (QUA-151)

Antes: Sincronizaba videos con Google Sheets y movía archivos entre carpetas.
Ahora: Los estados se gestionan desde el dashboard (Turso). Los archivos no se mueven.

Este archivo se mantiene por si algún import legacy lo necesita, pero no debe usarse.
Versión original: 3.5 - Compatible con DB v3.5
"""

import sys
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import shutil

# Añadir parent al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection
from config import OUTPUT_DIR
from drive_sync import borrar_de_drive, copiar_a_drive, is_drive_configured


# Google Sheets config
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = 'credentials.json'
SHEET_URL_TEST = 'https://docs.google.com/spreadsheets/d/1NeepTinvfUrYDP0t9jIqzUe_d2wjfNYQpuxII22Mej8/'
SHEET_URL_PROD = 'https://docs.google.com/spreadsheets/d/1QCb4xYKoLJPaMrGaBW311VQIyDg2Xa08V5DmsD2H81g/'

# Estados válidos
ESTADOS_VALIDOS = ['En Calendario', 'Borrador', 'Programado', 'Descartado', 'Violation']


class SincronizadorVideos:
    """Sincroniza videos desde Google Sheets"""

    def __init__(self, cuenta, test_mode=False):
        self.cuenta = cuenta
        self.test_mode = test_mode
        self.conn = get_connection()
        self.cursor = self.conn.cursor()

        # Conectar a Sheet
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
        client = gspread.authorize(creds)
        sheet_url = SHEET_URL_TEST if test_mode else SHEET_URL_PROD
        self.sheet = client.open_by_url(sheet_url).sheet1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def close(self):
        """Cierra conexión a la base de datos"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            self.conn = None
    
    def sincronizar(self, producto_filter=None, skip_reemplazo=False):
        """Sincroniza todos los videos de la cuenta desde Sheet

        Args:
            producto_filter: si se especifica, los reemplazos solo usan videos de ese producto
            skip_reemplazo: si True, no busca reemplazos para descartados
        """
        print(f"\n{'='*60}")
        print(f"  SINCRONIZAR - {self.cuenta}")
        print(f"{'='*60}\n")

        # Leer Sheet
        videos_sheet = self._leer_sheet()

        if not videos_sheet:
            print("[INFO] No hay videos en Sheet para esta cuenta")
            return

        print(f"[SHEET] {len(videos_sheet)} videos encontrados\n")

        # Mover archivos
        self._mover_archivos(videos_sheet)

        # Actualizar DB
        self._actualizar_db(videos_sheet, producto_filter=producto_filter, skip_reemplazo=skip_reemplazo)
        
        print(f"\n{'='*60}")
        print(f"  ✅ SINCRONIZACIÓN COMPLETADA")
        print(f"{'='*60}\n")
    
    def _leer_sheet(self):
        """Lee videos de la cuenta desde Sheet"""
        all_rows = self.sheet.get_all_records()
        
        videos = []
        for row in all_rows:
            if row.get('Cuenta') == self.cuenta:
                video_id = row.get('Video', '').strip()
                estado = row.get('Estado', '').strip()
                fecha = row.get('Fecha', '').strip()  # Ahora es DD-MM-YYYY
                
                if video_id and estado:
                    videos.append({
                        'video_id': video_id,
                        'estado': estado,
                        'fecha': fecha
                    })
        
        return videos
    
    def _buscar_video_fisico(self, video_id):
        """
        Busca video en todas las ubicaciones posibles
        
        Returns:
            str: Path al video o None
        """
        cuenta_dir = os.path.join(OUTPUT_DIR, self.cuenta)
        
        # Ubicaciones posibles
        ubicaciones = [
            # Raíz
            os.path.join(cuenta_dir, f"{video_id}.mp4"),
            # Calendario
            os.path.join(cuenta_dir, 'calendario'),
            # Borrador
            os.path.join(cuenta_dir, 'borrador'),
            # Programados
            os.path.join(cuenta_dir, 'programados'),
            # Descartados
            os.path.join(cuenta_dir, 'descartados'),
            # Violations
            os.path.join(cuenta_dir, 'violations')
        ]

        # Buscar en raíz
        if os.path.exists(ubicaciones[0]):
            return ubicaciones[0]

        # Buscar en subdirectorios con fechas
        for base_dir in ubicaciones[1:4]:  # calendario, borrador, programados
            if not os.path.exists(base_dir):
                continue

            # Buscar en todas las subcarpetas de fecha
            for fecha_dir in os.listdir(base_dir):
                path = os.path.join(base_dir, fecha_dir, f"{video_id}.mp4")
                if os.path.exists(path):
                    return path

        # Buscar en descartados y violations (sin fecha)
        for flat_dir in ubicaciones[4:]:
            flat_path = os.path.join(flat_dir, f"{video_id}.mp4")
            if os.path.exists(flat_path):
                return flat_path

        return None
    
    def _calcular_destino(self, estado, fecha):
        """
        Calcula carpeta destino según estado
        
        Args:
            estado: Estado del video
            fecha: Fecha en formato DD/MM/YYYY
        
        Returns:
            str: Path a carpeta destino
        """
        cuenta_dir = os.path.join(OUTPUT_DIR, self.cuenta)
        
        # La fecha ya viene en formato DD-MM-YYYY desde Sheet (sin barras)
        # Convertir solo para DB: DD-MM-YYYY → YYYY-MM-DD
        # QUA-91: Usar strptime para validar formato y evitar errores con fechas ambiguas
        fecha_carpeta = None
        fecha_db = None
        if fecha and '-' in fecha:
            try:
                fecha_dt = datetime.strptime(fecha, "%d-%m-%Y")
                fecha_carpeta = fecha  # DD-MM-YYYY (ya viene así de la Sheet)
                fecha_db = fecha_dt.strftime("%Y-%m-%d")  # YYYY-MM-DD para DB
            except ValueError:
                # Intentar formato YYYY-MM-DD por si viene de BD en vez de Sheet
                try:
                    fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
                    fecha_carpeta = fecha_dt.strftime("%d-%m-%Y")
                    fecha_db = fecha
                except ValueError:
                    print(f"[WARNING] Formato de fecha inválido '{fecha}' — esperado DD-MM-YYYY o YYYY-MM-DD")
                    fecha_carpeta = None
                    fecha_db = None

        if estado == 'En Calendario':
            if not fecha_carpeta:
                print(f"[WARNING] Estado 'En Calendario' sin fecha válida")
                return None
            return os.path.join(cuenta_dir, 'calendario', fecha_carpeta)
        
        elif estado == 'Borrador':
            if not fecha_carpeta:
                print(f"[WARNING] Estado 'Borrador' sin fecha válida")
                return None
            return os.path.join(cuenta_dir, 'borrador', fecha_carpeta)
        
        elif estado == 'Programado':
            if not fecha_carpeta:
                print(f"[WARNING] Estado 'Programado' sin fecha válida")
                return None
            return os.path.join(cuenta_dir, 'programados', fecha_carpeta)
        
        elif estado == 'Descartado':
            return os.path.join(cuenta_dir, 'descartados')

        elif estado == 'Violation':
            return os.path.join(cuenta_dir, 'violations')

        else:
            return None
    
    def _mover_archivos(self, videos_sheet):
        """Mueve archivos físicos según Sheet"""
        print(f"{'='*60}")
        print(f"  📁 MOVIENDO VIDEOS")
        print(f"{'='*60}")
        
        movidos = 0
        no_encontrados = 0
        
        for video in videos_sheet:
            video_id = video['video_id']
            estado = video['estado']
            fecha = video['fecha']
            
            # Validar estado
            if estado not in ESTADOS_VALIDOS:
                print(f"   ⚠️  Estado inválido para {video_id}: '{estado}' (omitido)")
                continue
            
            # Buscar video
            origen = self._buscar_video_fisico(video_id)
            if not origen:
                print(f"   ⚠️  No encontrado: {video_id}")
                no_encontrados += 1
                continue
            
            # Calcular destino
            destino_dir = self._calcular_destino(estado, fecha)
            if not destino_dir:
                print(f"   ⚠️  No se pudo calcular destino para {video_id}")
                continue
            
            destino = os.path.join(destino_dir, f"{video_id}.mp4")
            
            # Si ya está en el destino correcto, skip
            if os.path.normpath(origen) == os.path.normpath(destino):
                continue
            
            # Mover
            try:
                os.makedirs(destino_dir, exist_ok=True)
                shutil.move(origen, destino)
                print(f"   ✅ {video_id} → {estado}")
                movidos += 1
            except Exception as e:
                print(f"   ❌ Error moviendo {video_id}: {e}")
        
        print(f"\n[RESUMEN] Movidos: {movidos}, No encontrados: {no_encontrados}")
    
    def _actualizar_db(self, videos_sheet, producto_filter=None, skip_reemplazo=False):
        """Actualiza estados en DB, detecta descartados/violations para reemplazo"""
        print(f"\n{'='*60}")
        print(f"  💾 ACTUALIZANDO BASE DE DATOS")
        print(f"{'='*60}")

        actualizados = 0
        videos_a_reemplazar = []  # Videos que salen de calendario y necesitan reemplazo

        for video in videos_sheet:
            video_id = video['video_id']
            estado = video['estado']
            fecha = video['fecha']

            # Validar estado
            if estado not in ESTADOS_VALIDOS:
                continue

            # Convertir fecha DD-MM-YYYY → YYYY-MM-DD para DB
            # QUA-91: Usar strptime para validar formato y evitar errores con fechas ambiguas
            fecha_db = None
            if fecha and '-' in fecha:
                try:
                    fecha_dt = datetime.strptime(fecha, "%d-%m-%Y")
                    fecha_db = fecha_dt.strftime("%Y-%m-%d")
                except ValueError:
                    try:
                        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
                        fecha_db = fecha  # Ya es YYYY-MM-DD
                    except ValueError:
                        print(f"[WARNING] Formato de fecha inválido '{fecha}' para {video_id} — esperado DD-MM-YYYY")

            # Buscar video en DB
            self.cursor.execute("""
                SELECT id, estado, filepath, fecha_programada, hora_programada
                FROM videos
                WHERE video_id = ? AND cuenta = ?
            """, (video_id, self.cuenta))

            row = self.cursor.fetchone()
            if not row:
                continue

            db_id = row['id']
            estado_actual = row['estado']

            # Si estado cambió, actualizar
            if estado != estado_actual:
                # Detectar si sale de calendario → Descartado/Violation
                if estado_actual in ('En Calendario', 'Programado', 'Borrador') and estado in ('Descartado', 'Violation'):
                    videos_a_reemplazar.append({
                        'video_id': video_id,
                        'fecha': row['fecha_programada'],
                        'hora': row['hora_programada'],
                    })

                    # Borrar del Drive (aplica a cualquier estado que tuviera copia en Drive)
                    if is_drive_configured() and row['fecha_programada']:
                        if borrar_de_drive(video_id, self.cuenta, row['fecha_programada']):
                            print(f"   🗑️  Drive: {video_id} borrado")

                # Actualizar filepath también
                nuevo_filepath = self._buscar_video_fisico(video_id)

                if nuevo_filepath:
                    self.cursor.execute("""
                        UPDATE videos
                        SET estado = ?, filepath = ?, fecha_programada = ?
                        WHERE id = ?
                    """, (estado, nuevo_filepath, fecha_db, db_id))
                    actualizados += 1

        self.conn.commit()
        print(f"\n[OK] {actualizados} videos actualizados en DB")

        # FIX #009: Además de transiciones detectadas, buscar huecos sin cubrir
        # (videos Descartado/Violation con fecha futura que no tienen reemplazo en ese slot)
        if not skip_reemplazo:
            huecos_existentes = self._buscar_huecos_sin_cubrir()
            slots_ya_detectados = {(v['fecha'], v['hora']) for v in videos_a_reemplazar}
            nuevos = 0
            for hueco in huecos_existentes:
                slot = (hueco['fecha'], hueco['hora'])
                if slot not in slots_ya_detectados:
                    videos_a_reemplazar.append(hueco)
                    slots_ya_detectados.add(slot)
                    nuevos += 1

            if nuevos > 0:
                print(f"  [FIX#009] {nuevos} huecos adicionales detectados (ya estaban descartados)")

        # Reemplazar videos descartados/violations
        if videos_a_reemplazar and not skip_reemplazo:
            self._reemplazar_videos(videos_a_reemplazar, producto_filter=producto_filter)
        elif videos_a_reemplazar and skip_reemplazo:
            print(f"\n  [INFO] {len(videos_a_reemplazar)} huecos detectados (reemplazo desactivado)")

    def _buscar_huecos_sin_cubrir(self):
        """FIX #009: Busca slots con video Descartado/Violation que no tienen reemplazo.

        Un 'hueco' es un slot (fecha+hora) donde hay un video Descartado/Violation
        pero no hay otro video En Calendario/Programado en el mismo slot.

        Returns:
            list[dict]: Huecos con video_id, fecha, hora
        """
        ahora = datetime.now().strftime("%Y-%m-%d")

        self.cursor.execute("""
            SELECT v.video_id, v.fecha_programada as fecha, v.hora_programada as hora
            FROM videos v
            WHERE v.cuenta = ?
            AND v.estado IN ('Descartado', 'Violation')
            AND v.fecha_programada >= ?
            AND v.fecha_programada IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM videos v2
                WHERE v2.cuenta = v.cuenta
                AND v2.fecha_programada = v.fecha_programada
                AND v2.hora_programada = v.hora_programada
                AND v2.estado IN ('En Calendario', 'Programado', 'Borrador')
            )
            ORDER BY v.fecha_programada, v.hora_programada
        """, (self.cuenta, ahora))

        return [dict(row) for row in self.cursor.fetchall()]

    def _reemplazar_videos(self, videos_a_reemplazar, producto_filter=None):
        """Busca reemplazos para videos descartados/violations y los programa.

        Para cada video que sale de calendario, busca un video 'Generado' de la
        misma cuenta (respetando lifecycle) y lo programa en el mismo slot (fecha+hora).

        Args:
            videos_a_reemplazar: lista de dicts con video_id, fecha, hora
            producto_filter: si se especifica, solo usa videos de ese producto
        """
        print(f"\n{'='*60}")
        if producto_filter:
            print(f"  🔄 REEMPLAZO ({len(videos_a_reemplazar)} huecos) — SOLO: {producto_filter}")
        else:
            print(f"  🔄 REEMPLAZO AUTOMÁTICO ({len(videos_a_reemplazar)} huecos)")
        print(f"{'='*60}")

        # Obtener videos disponibles (Generado) con lifecycle
        query = """
            SELECT
                v.id, v.video_id, v.filepath,
                p.nombre as producto, p.id as producto_id,
                p.estado_comercial, p.max_videos_test,
                h.filename as hook, h.id as hook_id,
                b.deal_math, var.seo_text, b.hashtags, b.url_producto
            FROM videos v
            JOIN productos p ON v.producto_id = p.id
            JOIN material h ON v.hook_id = h.id
            JOIN producto_bofs b ON v.bof_id = b.id
            JOIN variantes_overlay_seo var ON v.variante_id = var.id
            WHERE v.cuenta = ? AND v.estado = 'Generado'
            AND p.estado_comercial != 'dropped'
        """
        params = [self.cuenta]

        if producto_filter:
            query += " AND p.nombre = ?"
            params.append(producto_filter)

        query += """
            ORDER BY
                CASE p.estado_comercial
                    WHEN 'top_seller' THEN 1
                    WHEN 'validated' THEN 2
                    WHEN 'testing' THEN 3
                END,
                v.created_at ASC
        """
        self.cursor.execute(query, params)

        disponibles = [dict(row) for row in self.cursor.fetchall()]

        if not disponibles:
            if producto_filter:
                print(f"  [!] No hay videos disponibles de '{producto_filter}' para reemplazo")
            else:
                print("  [!] No hay videos disponibles para reemplazo")
            return

        # Anti-duplicados: leer video_ids ya en Sheet
        try:
            col_videos = self.sheet.col_values(5)  # Columna E = Video
            videos_en_sheet = set(col_videos[1:])
        except Exception:
            videos_en_sheet = set()

        # Filtrar los que ya están en Sheet
        disponibles = [v for v in disponibles if v['video_id'] not in videos_en_sheet]

        if not disponibles:
            print("  [!] No hay videos disponibles (todos ya en Sheet)")
            return

        # Contar testing acumulados (para respetar límite)
        self.cursor.execute("""
            SELECT v.producto_id, COUNT(*) as total
            FROM videos v
            JOIN productos p ON v.producto_id = p.id
            WHERE v.cuenta = ? AND p.estado_comercial = 'testing'
            AND v.estado IN ('En Calendario', 'Borrador', 'Programado')
            GROUP BY v.producto_id
        """, (self.cuenta,))
        testing_acumulados = {row['producto_id']: row['total'] for row in self.cursor.fetchall()}

        reemplazados = 0
        rows_to_append = []  # Filas nuevas para Sheet

        ahora = datetime.now()

        for hueco in videos_a_reemplazar:
            fecha = hueco['fecha']
            hora = hueco['hora']

            # No reemplazar slots en el pasado (fecha + hora)
            if fecha and hora:
                try:
                    slot_datetime = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
                    if slot_datetime <= ahora:
                        print(f"  [⏭️] {fecha} {hora} — slot en el pasado, no se reemplaza")
                        continue
                except ValueError:
                    pass
            elif fecha and fecha < ahora.strftime("%Y-%m-%d"):
                print(f"  [⏭️] {fecha} {hora} — fecha pasada, no se reemplaza")
                continue

            # Buscar el mejor reemplazo
            reemplazo = None
            for video in disponibles:
                estado_comercial = video['estado_comercial'] or 'testing'

                # Respetar límite de testing
                if estado_comercial == 'testing':
                    max_test = video['max_videos_test'] or 20
                    ya = testing_acumulados.get(video['producto_id'], 0)
                    if ya >= max_test:
                        continue

                reemplazo = video
                disponibles.remove(video)  # No reutilizar

                # Actualizar contador testing si aplica
                if estado_comercial == 'testing':
                    testing_acumulados[video['producto_id']] = \
                        testing_acumulados.get(video['producto_id'], 0) + 1
                break

            if not reemplazo:
                print(f"  [!] Sin reemplazo para hueco {fecha} {hora}")
                continue

            # Programar reemplazo en el mismo slot
            # 1. Actualizar DB
            self.cursor.execute("""
                UPDATE videos
                SET estado = 'En Calendario',
                    fecha_programada = ?,
                    hora_programada = ?
                WHERE id = ?
            """, (fecha, hora, reemplazo['id']))

            # 2. Mover archivo físico
            en_carpeta = False
            origen = reemplazo['filepath']
            if origen and os.path.exists(origen):
                fecha_carpeta = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d-%m-%Y")
                cuenta_dir = os.path.join(OUTPUT_DIR, self.cuenta)
                destino_dir = os.path.join(cuenta_dir, 'calendario', fecha_carpeta)
                os.makedirs(destino_dir, exist_ok=True)
                destino = os.path.join(destino_dir, os.path.basename(origen))

                try:
                    os.rename(origen, destino)
                    self.cursor.execute("UPDATE videos SET filepath = ? WHERE id = ?",
                                        (destino, reemplazo['id']))

                    # 3. Copiar a Drive
                    drive_result = copiar_a_drive(destino, self.cuenta, fecha)
                    en_carpeta = drive_result is not None
                except Exception as e:
                    print(f"  [!] Error moviendo reemplazo {reemplazo['video_id']}: {e}")

            # 4. Preparar fila para Sheet
            fecha_sheet = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d-%m-%Y")
            rows_to_append.append([
                self.cuenta,
                reemplazo['producto'],
                fecha_sheet,
                hora,
                reemplazo['video_id'],
                reemplazo['hook'],
                reemplazo['deal_math'],
                reemplazo['seo_text'],
                reemplazo['hashtags'],
                reemplazo['url_producto'],
                'En Calendario',
                en_carpeta
            ])

            estado_emoji = {'top_seller': '🔥', 'validated': '✅', 'testing': '🧪'}.get(
                reemplazo.get('estado_comercial', 'testing'), '?')
            print(f"  {estado_emoji} {fecha} {hora} ← {reemplazo['producto'][:25]} ({reemplazo['video_id'][:20]}...)")
            reemplazados += 1

        self.conn.commit()

        # Añadir filas a Sheet
        if rows_to_append:
            try:
                self.sheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
                print(f"\n  [OK] {len(rows_to_append)} reemplazos añadidos a Sheet")
            except Exception as e:
                print(f"\n  [!] Error actualizando Sheet con reemplazos: {e}")

        print(f"\n[REEMPLAZO] {reemplazados}/{len(videos_a_reemplazar)} huecos cubiertos")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Sincronizar videos con Google Sheets')
    parser.add_argument('--cuenta', help='Cuenta específica (opcional)')
    parser.add_argument('--sync', action='store_true', help='Sincronizar desde Sheet')
    parser.add_argument('--test', action='store_true', help='Usar Sheet TEST')
    
    args = parser.parse_args()
    
    if not args.sync:
        print("Uso: python mover_videos.py --sync [--cuenta CUENTA] [--test]")
        return 1
    
    # Cargar cuentas
    import json
    with open('config_cuentas.json', 'r', encoding='utf-8') as f:
        cuentas = json.load(f)
    
    # Determinar qué cuentas procesar
    if args.cuenta:
        if args.cuenta not in cuentas:
            print(f"❌ Cuenta '{args.cuenta}' no encontrada")
            return 1
        cuentas_a_procesar = [args.cuenta]
    else:
        cuentas_a_procesar = list(cuentas.keys())
    
    # Procesar cada cuenta
    for cuenta in cuentas_a_procesar:
        try:
            with SincronizadorVideos(cuenta, test_mode=args.test) as sincronizador:
                sincronizador.sincronizar()
        except Exception as e:
            print(f"\n❌ ERROR en {cuenta}: {e}")
            import traceback
            traceback.print_exc()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
