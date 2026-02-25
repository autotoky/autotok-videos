#!/usr/bin/env python3
"""
PROGRAMADOR.PY - Sistema de programación inteligente de calendario
Versión: 4.0 - Smart Scheduling con lifecycle + distribución por categoría
Fecha: 2026-02-16

Distribución por estado_comercial:
  - top_seller: prioridad máxima, se programa TODO lo disponible
  - validated:  segunda prioridad, se programa TODO lo disponible
  - testing:    prioridad baja, se programa hasta max_videos_test acumulativo
  - dropped:    no se programa nada

Los slots diarios se reparten por porcentajes configurables (pct_top_seller,
pct_validated, pct_testing). Si una categoría no tiene suficientes videos,
sus slots se redistribuyen a las demás.

Reglas adicionales:
  - Anti-consecutivos: evitar 2 videos seguidos del mismo producto
  - Distancia mínima de hooks entre publicaciones
  - Max mismo producto por día
  - Gap mínimo entre publicaciones
"""

import sys
import os
import json
from datetime import datetime, timedelta
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Añadir parent al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import get_connection
from config import OUTPUT_DIR
from drive_sync import copiar_a_drive, is_drive_configured


# Google Sheets config
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = 'credentials.json'
SHEET_URL_TEST = 'https://docs.google.com/spreadsheets/d/1NeepTinvfUrYDP0t9jIqzUe_d2wjfNYQpuxII22Mej8/'
SHEET_URL_PROD = 'https://docs.google.com/spreadsheets/d/1QCb4xYKoLJPaMrGaBW311VQIyDg2Xa08V5DmsD2H81g/'


def load_cuenta_config(cuenta_nombre):
    """Carga configuración de cuenta desde DB, fallback a JSON."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cuentas_config WHERE nombre = ?", (cuenta_nombre,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)

    # Fallback: leer JSON y mapear campos al formato que espera el código
    try:
        with open('config_cuentas.json', 'r', encoding='utf-8') as f:
            cuentas = json.load(f)
    except FileNotFoundError:
        return {}

    raw = cuentas.get(cuenta_nombre, {})
    if not raw:
        return {}

    # Mapear estructura JSON → formato plano que usa el programador
    horarios = raw.get('horarios', {})
    return {
        'nombre': raw.get('nombre', cuenta_nombre),
        'videos_por_dia': raw.get('videos_por_dia', 5),
        'max_mismo_producto_por_dia': raw.get('max_mismo_producto_por_dia', 2),
        'max_mismo_hook_por_dia': raw.get('max_mismo_hook_por_dia', 1),
        'distancia_minima_hook': raw.get('distancia_minima_hook', 12),
        'gap_minimo_horas': raw.get('gap_minimo_horas', 1.0),
        'horario_inicio': horarios.get('inicio', '08:00'),
        'horario_fin': horarios.get('fin', '21:30'),
        'pct_top_seller': raw.get('pct_top_seller', 40),
        'pct_validated': raw.get('pct_validated', 40),
        'pct_testing': raw.get('pct_testing', 20),
    }


def get_videos_disponibles(cuenta, producto_filter=None):
    """Obtiene videos 'Generado' con info de lifecycle del producto.

    Args:
        cuenta: Nombre de la cuenta
        producto_filter: Si se especifica, solo devuelve videos de ese producto

    Returns:
        list[dict]: Videos con estado_comercial y max_videos_test del producto
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            v.id,
            v.video_id,
            v.filepath,
            p.nombre as producto,
            p.id as producto_id,
            p.estado_comercial,
            p.max_videos_test,
            h.filename as hook,
            h.id as hook_id,
            b.deal_math,
            var.seo_text,
            b.hashtags,
            b.url_producto
        FROM videos v
        JOIN productos p ON v.producto_id = p.id
        JOIN material h ON v.hook_id = h.id
        JOIN producto_bofs b ON v.bof_id = b.id
        JOIN variantes_overlay_seo var ON v.variante_id = var.id
        WHERE v.cuenta = ? AND v.estado = 'Generado'
    """
    params = [cuenta]

    if producto_filter:
        query += " AND p.nombre = ?"
        params.append(producto_filter)

    query += " ORDER BY v.created_at ASC"

    cursor.execute(query, params)

    videos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return videos


def get_videos_ya_programados(cuenta):
    """Obtiene videos ya programados (para distancia hook)"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT video_id, fecha_programada, hook_id, producto_id
        FROM videos
        WHERE cuenta = ? AND estado IN ('En Calendario', 'Borrador', 'Programado')
        ORDER BY fecha_programada ASC, hora_programada ASC
    """, (cuenta,))

    programados = []
    for row in cursor.fetchall():
        programados.append({
            'video_id': row['video_id'],
            'fecha': row['fecha_programada'],
            'hook_id': row['hook_id'],
            'producto_id': row['producto_id']
        })

    conn.close()
    return programados


def get_videos_acumulados_testing(cuenta):
    """Cuenta cuántos videos ya se han programado/publicado por producto en testing.

    Para saber cuánto margen queda de max_videos_test.

    Returns:
        dict: {producto_id: count} con videos en cualquier estado post-generado
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT v.producto_id, COUNT(*) as total
        FROM videos v
        JOIN productos p ON v.producto_id = p.id
        WHERE v.cuenta = ?
        AND p.estado_comercial = 'testing'
        AND v.estado IN ('En Calendario', 'Borrador', 'Programado')
        GROUP BY v.producto_id
    """, (cuenta,))

    result = {row['producto_id']: row['total'] for row in cursor.fetchall()}
    conn.close()
    return result


def get_horas_ocupadas(cuenta, fecha):
    """Obtiene las horas ya programadas para un día/cuenta desde BD.

    Returns:
        list[datetime]: Horas ya ocupadas como objetos datetime
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT hora_programada FROM videos
        WHERE cuenta = ? AND fecha_programada = ?
        AND estado IN ('En Calendario', 'Borrador', 'Programado')
        AND hora_programada IS NOT NULL
    """, (cuenta, fecha))
    horas = [row['hora_programada'] for row in cursor.fetchall()]
    conn.close()
    return horas


def redondear_5min(dt):
    """Redondea un datetime al siguiente intervalo de 5 minutos (TikTok only allows 5-min intervals)."""
    minutos = dt.minute
    resto = minutos % 5
    if resto != 0:
        dt += timedelta(minutes=(5 - resto))
    return dt.replace(second=0, microsecond=0)


def generar_horario(config, videos_nuevos, fecha, cuenta=None):
    """Genera horarios para slots vacíos, respetando horas ya ocupadas y usando intervalos de 5 min.

    Args:
        config: Configuración de la cuenta
        videos_nuevos: Cuántos videos NUEVOS hay que programar en este día
        fecha: Fecha en formato YYYY-MM-DD
        cuenta: Nombre de cuenta (para consultar horas ocupadas en BD)

    Returns:
        list[str]: Horarios en formato HH:MM, solo para los slots nuevos
    """
    inicio = config.get('horario_inicio', '08:00')
    fin = config.get('horario_fin', '21:30')
    gap_minimo = config.get('gap_minimo_horas', 1.0)

    inicio_dt = datetime.strptime(f"{fecha} {inicio}", "%Y-%m-%d %H:%M")
    fin_dt = datetime.strptime(f"{fecha} {fin}", "%Y-%m-%d %H:%M")

    gap_minimo_minutos = gap_minimo * 60

    # Consultar horas ya ocupadas en BD para este día
    horas_ocupadas = []
    if cuenta:
        horas_str = get_horas_ocupadas(cuenta, fecha)
        for h in horas_str:
            try:
                horas_ocupadas.append(datetime.strptime(f"{fecha} {h}", "%Y-%m-%d %H:%M"))
            except ValueError:
                continue

    if horas_ocupadas:
        print(f"  [INFO] {len(horas_ocupadas)} horas ya ocupadas: {', '.join(sorted(h.strftime('%H:%M') for h in horas_ocupadas))}")

    if videos_nuevos <= 0:
        return []

    # Construir lista de todos los momentos ocupados (para respetar gap)
    ocupados = sorted(horas_ocupadas)

    # Generar slots nuevos evitando conflictos con los existentes
    horarios_nuevos = []
    current = redondear_5min(inicio_dt)

    intentos_max = 500  # safety limit
    intentos = 0

    while len(horarios_nuevos) < videos_nuevos and intentos < intentos_max:
        intentos += 1

        if current > fin_dt:
            # No queda espacio, intentar rellenar desde el inicio con gaps reducidos
            break

        # Comprobar que no choca con ninguna hora ocupada (respetando gap)
        conflicto = False
        for ocup in ocupados:
            distancia = abs((current - ocup).total_seconds()) / 60
            if distancia < gap_minimo_minutos:
                conflicto = True
                # Saltar al siguiente slot libre después de esta hora ocupada
                current = redondear_5min(ocup + timedelta(minutes=gap_minimo_minutos))
                break

        if conflicto:
            continue

        # Slot válido
        horarios_nuevos.append(current.strftime("%H:%M"))
        ocupados.append(current)
        ocupados.sort()

        # Avanzar al siguiente slot con gap + variación
        variacion = random.choice([-5, 0, 5, 10])  # variación en múltiplos de 5 min
        current = redondear_5min(current + timedelta(minutes=gap_minimo_minutos + variacion))

    if len(horarios_nuevos) < videos_nuevos:
        faltantes = videos_nuevos - len(horarios_nuevos)
        print(f"  [WARNING] Solo se pudieron generar {len(horarios_nuevos)}/{videos_nuevos} horarios (faltan {faltantes})")
        print(f"   Intentando rellenar con gap reducido...")

        # Segunda pasada: reducir gap para meter los que faltan
        todos_ocupados = sorted(ocupados)
        # Buscar huecos entre las horas existentes
        puntos = [inicio_dt] + todos_ocupados + [fin_dt]
        for i in range(len(puntos) - 1):
            if len(horarios_nuevos) >= videos_nuevos:
                break
            hueco_inicio = redondear_5min(puntos[i] + timedelta(minutes=5))
            hueco_fin = puntos[i + 1] - timedelta(minutes=5)
            candidate = hueco_inicio
            while candidate <= hueco_fin and len(horarios_nuevos) < videos_nuevos:
                hora_str = candidate.strftime("%H:%M")
                if hora_str not in horarios_nuevos and candidate not in horas_ocupadas:
                    # Verificar distancia mínima de 5 min con cualquier ocupado
                    ok = all(abs((candidate - o).total_seconds()) >= 300 for o in ocupados)
                    if ok:
                        horarios_nuevos.append(hora_str)
                        ocupados.append(candidate)
                        ocupados.sort()
                candidate = redondear_5min(candidate + timedelta(minutes=5))

    if len(horarios_nuevos) < videos_nuevos:
        print(f"  [WARNING] Solo hay espacio para {len(horarios_nuevos)} videos nuevos de {videos_nuevos} solicitados")

    return sorted(horarios_nuevos)


def cumple_distancia_hook(hook_id, posicion_calendario, videos_programados, distancia_minima):
    """Verifica si hook cumple distancia mínima de publicaciones"""
    ultima_posicion = -999

    for i, video in enumerate(videos_programados):
        if video['hook_id'] == hook_id:
            ultima_posicion = i

    distancia_actual = posicion_calendario - ultima_posicion
    return distancia_actual >= distancia_minima


def cumple_distancia_seo(seo_text, posicion_calendario, videos_programados, distancia_minima):
    """Verifica si SEO text cumple distancia mínima de publicaciones"""
    ultima_posicion = -999

    for i, video in enumerate(videos_programados):
        if video.get('seo_text') == seo_text:
            ultima_posicion = i

    distancia_actual = posicion_calendario - ultima_posicion
    return distancia_actual >= distancia_minima


# ═══════════════════════════════════════════════════════════
# DISTRIBUCIÓN INTELIGENTE POR CATEGORÍA
# ═══════════════════════════════════════════════════════════

def filtrar_y_limitar_por_lifecycle(videos, cuenta):
    """Filtra videos según lifecycle y aplica límites de testing.

    - dropped: se eliminan completamente
    - testing: se limitan a max_videos_test acumulativo
    - validated/top_seller: todos pasan

    Returns:
        dict: {categoria: [videos]} donde categoria es 'top_seller', 'validated', 'testing'
    """
    # Contar cuántos videos ya se han programado/publicado por producto testing
    acumulados_testing = get_videos_acumulados_testing(cuenta)

    # Agrupar por categoría
    por_categoria = {'top_seller': [], 'validated': [], 'testing': []}

    # Tracking de cuántos testing añadimos por producto en esta tanda
    testing_esta_tanda = {}

    for video in videos:
        estado = video.get('estado_comercial') or 'testing'

        if estado == 'dropped':
            continue

        if estado == 'testing':
            producto_id = video['producto_id']
            max_test = video.get('max_videos_test') or 20
            ya_programados = acumulados_testing.get(producto_id, 0)
            en_esta_tanda = testing_esta_tanda.get(producto_id, 0)

            if ya_programados + en_esta_tanda >= max_test:
                continue  # Límite alcanzado para este producto

            testing_esta_tanda[producto_id] = en_esta_tanda + 1

        por_categoria[estado].append(video)

    return por_categoria


def calcular_distribucion_slots(total_slots, config, videos_por_categoria):
    """Calcula cuántos slots asignar a cada categoría.

    Usa los porcentajes configurados, pero redistribuye slots sobrantes
    si una categoría no tiene suficientes videos.

    Args:
        total_slots: Total de slots a llenar (videos_por_dia * dias)
        config: dict con pct_top_seller, pct_validated, pct_testing
        videos_por_categoria: dict con {categoria: [videos]}

    Returns:
        dict: {categoria: num_slots}
    """
    pct = {
        'top_seller': config.get('pct_top_seller') or 40,
        'validated': config.get('pct_validated') or 40,
        'testing': config.get('pct_testing') or 20,
    }

    # Calcular slots ideales por porcentaje
    slots = {}
    for cat in ['top_seller', 'validated', 'testing']:
        slots[cat] = round(total_slots * pct[cat] / 100)

    # Ajustar si el total no cuadra por redondeo
    diff = total_slots - sum(slots.values())
    if diff > 0:
        # Dar los extras a top_seller primero
        for cat in ['top_seller', 'validated', 'testing']:
            if diff <= 0:
                break
            slots[cat] += 1
            diff -= 1
    elif diff < 0:
        for cat in ['testing', 'validated', 'top_seller']:
            if diff >= 0:
                break
            if slots[cat] > 0:
                slots[cat] -= 1
                diff += 1

    # Redistribuir slots de categorías sin suficientes videos
    sobrantes = 0
    for cat in ['top_seller', 'validated', 'testing']:
        disponibles = len(videos_por_categoria.get(cat, []))
        if slots[cat] > disponibles:
            sobrantes += slots[cat] - disponibles
            slots[cat] = disponibles

    # Repartir sobrantes entre las categorías que tengan margen
    while sobrantes > 0:
        repartido = False
        for cat in ['top_seller', 'validated', 'testing']:
            if sobrantes <= 0:
                break
            disponibles = len(videos_por_categoria.get(cat, []))
            if slots[cat] < disponibles:
                slots[cat] += 1
                sobrantes -= 1
                repartido = True
        if not repartido:
            break  # No hay más margen en ninguna categoría

    return slots


def construir_cola_priorizada(videos_por_categoria, slots_por_categoria):
    """Construye una cola con TODOS los videos disponibles, ordenados por prioridad.

    Incluye todos los videos (no solo los que caben en los slots) para que
    las restricciones (hook distance, max_producto, etc.) tengan candidatos
    de reemplazo cuando un video no cumple.

    Orden: top_seller primero, luego validated, luego testing.
    Dentro de cada categoría: round-robin por producto para diversidad.

    Returns:
        list: Todos los videos ordenados por prioridad de categoría + diversidad
    """
    cola = []

    for cat in ['top_seller', 'validated', 'testing']:
        videos_cat = videos_por_categoria.get(cat, [])
        if not videos_cat:
            continue

        # Agrupar por producto dentro de esta categoría
        por_producto = {}
        for v in videos_cat:
            pid = v['producto_id']
            if pid not in por_producto:
                por_producto[pid] = []
            por_producto[pid].append(v)

        # Round-robin por producto (más videos primero)
        productos_ordenados = sorted(por_producto.keys(),
                                     key=lambda p: len(por_producto[p]), reverse=True)
        while any(por_producto[p] for p in productos_ordenados):
            for pid in productos_ordenados:
                if por_producto[pid]:
                    cola.append(por_producto[pid].pop(0))

    return cola


# ═══════════════════════════════════════════════════════════
# PROGRAMACIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════

def programar_calendario(cuenta, dias, fecha_inicio=None, test_mode=False, producto_filter=None, videos_override=None, dry_run=False):
    """
    Programa calendario con distribución inteligente por lifecycle.

    Args:
        cuenta: Nombre de cuenta
        dias: Número de días a programar
        fecha_inicio: Fecha inicio (formato YYYY-MM-DD) o None para mañana
        test_mode: Si True usa Sheet TEST
        producto_filter: Si se especifica, solo programa videos de ese producto
        videos_override: Si se especifica, sobreescribe videos_por_dia de la config
        dry_run: Si True, simula la programación sin escribir nada (BD, Sheet, archivos)
    """
    mode_label = "SIMULACIÓN" if dry_run else "PROGRAMAR CALENDARIO"
    print(f"\n{'='*60}")
    if producto_filter:
        print(f"  {mode_label} - {cuenta} (SOLO: {producto_filter})")
    else:
        print(f"  {mode_label} - {cuenta}")
    print(f"{'='*60}\n")

    # Cargar config
    config = load_cuenta_config(cuenta)
    if not config:
        print(f"[ERROR] Cuenta '{cuenta}' no encontrada")
        return False

    videos_por_dia = videos_override if videos_override else config.get('videos_por_dia', 5)
    max_mismo_producto = config.get('max_mismo_producto_por_dia', 2)
    distancia_minima_hook = config.get('distancia_minima_hook', 12)

    pct_top = config.get('pct_top_seller') or 40
    pct_val = config.get('pct_validated') or 40
    pct_test = config.get('pct_testing') or 20

    print(f"[CONFIG] {cuenta}:")
    print(f"   Videos/día: {videos_por_dia}")
    print(f"   Max mismo producto/día: {max_mismo_producto}")
    print(f"   Distancia mínima hook: {distancia_minima_hook} publicaciones")
    print(f"   Gap mínimo: {config.get('gap_minimo_horas', 1.0)}h")
    print(f"   Distribución: 🔥{pct_top}% ✅{pct_val}% 🧪{pct_test}%")

    # Fecha inicio
    if fecha_inicio:
        fecha_actual = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    else:
        fecha_actual = datetime.now() + timedelta(days=1)

    print(f"\n[CALENDARIO] Desde: {fecha_actual.strftime('%Y-%m-%d')} ({dias} días)")

    # Obtener videos disponibles
    videos = get_videos_disponibles(cuenta, producto_filter=producto_filter)
    if not videos:
        if producto_filter:
            print(f"\n[ERROR] No hay videos disponibles de '{producto_filter}' para programar")
            print(f"[TIP] Genera videos primero:")
            print(f"  python main.py --producto {producto_filter} --batch 20 --cuenta {cuenta}\n")
        else:
            print(f"\n[ERROR] No hay videos disponibles para programar")
            print(f"[TIP] Genera videos primero:")
            print(f"  python main.py --producto X --batch 20 --cuenta {cuenta}\n")
        return False

    # ── Validar existencia de archivos antes de programar ──
    videos_sin_archivo = [v for v in videos if not os.path.exists(v['filepath'])]
    if videos_sin_archivo:
        print(f"\n[WARNING] {len(videos_sin_archivo)} videos tienen archivos que no existen en disco:")
        for v in videos_sin_archivo[:10]:
            print(f"   - {v['video_id']}: {v['filepath']}")
        if len(videos_sin_archivo) > 10:
            print(f"   ... y {len(videos_sin_archivo) - 10} más")
        # Excluir videos sin archivo
        videos = [v for v in videos if os.path.exists(v['filepath'])]
        print(f"  Se excluyen del calendario. Quedan {len(videos)} videos válidos.")
        if not videos:
            print(f"\n[ERROR] No quedan videos con archivos válidos")
            return False

    # Filtrar por lifecycle y aplicar límites de testing
    videos_por_categoria = filtrar_y_limitar_por_lifecycle(videos, cuenta)

    n_top = len(videos_por_categoria['top_seller'])
    n_val = len(videos_por_categoria['validated'])
    n_test = len(videos_por_categoria['testing'])
    n_total = n_top + n_val + n_test

    print(f"\n[STATS] Videos disponibles: {n_total}")
    print(f"   🔥 Top Seller: {n_top}")
    print(f"   ✅ Validated:  {n_val}")
    print(f"   🧪 Testing:    {n_test}")

    if n_total == 0:
        print(f"\n[ERROR] No hay videos elegibles tras aplicar lifecycle")
        return False

    # Calcular distribución de slots para toda la tanda
    total_slots = videos_por_dia * dias
    slots_por_categoria = calcular_distribucion_slots(total_slots, config, videos_por_categoria)

    print(f"\n[DISTRIBUCIÓN] {total_slots} slots totales ({dias} días x {videos_por_dia}/día):")
    print(f"   🔥 Top Seller: {slots_por_categoria['top_seller']} slots")
    print(f"   ✅ Validated:  {slots_por_categoria['validated']} slots")
    print(f"   🧪 Testing:    {slots_por_categoria['testing']} slots")

    # Construir cola priorizada e intercalada
    cola_videos = construir_cola_priorizada(videos_por_categoria, slots_por_categoria)

    # Obtener videos ya programados (para distancia hook)
    videos_programados = get_videos_ya_programados(cuenta)
    posicion_calendario = len(videos_programados)

    print(f"\n[INFO] Videos ya programados: {len(videos_programados)}")

    # Conectar a Sheets (no necesario en dry_run)
    sheet = None
    if not dry_run:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
            client = gspread.authorize(creds)
            sheet_url = SHEET_URL_TEST if test_mode else SHEET_URL_PROD
            sheet = client.open_by_url(sheet_url).sheet1
            print(f"[OK] Conectado a Google Sheets ({'TEST' if test_mode else 'PROD'})")
        except Exception as e:
            print(f"[ERROR] No se pudo conectar a Sheets: {e}")
            return False

    # ── Protección anti-duplicados: consultar BD (no Sheet) ──
    # Un video con estado != 'Generado' ya está en uso o descartado
    conn_dup = get_connection()
    cursor_dup = conn_dup.cursor()
    cursor_dup.execute("""
        SELECT video_id FROM videos
        WHERE cuenta = ? AND estado != 'Generado'
    """, (cuenta,))
    videos_no_disponibles = {row['video_id'] for row in cursor_dup.fetchall()}
    conn_dup.close()
    if videos_no_disponibles:
        print(f"[INFO] {len(videos_no_disponibles)} videos ya usados/descartados en BD (se excluirán)")

    # ── Programar día a día ──
    calendario = []
    videos_usados = set()  # IDs ya usados (para no repetir)

    # Tracking de distribución por categoría (soft target)
    cat_programados = {'top_seller': 0, 'validated': 0, 'testing': 0}
    cat_target = dict(slots_por_categoria)  # target ideal

    for dia in range(dias):
        fecha_str = fecha_actual.strftime("%Y-%m-%d")
        print(f"\n[DÍA] {fecha_str}")

        videos_dia = []

        # Pre-cargar productos ya programados para este día (de tandas anteriores)
        productos_usados_hoy = {}
        conn_dia = get_connection()
        cursor_dia = conn_dia.cursor()
        cursor_dia.execute("""
            SELECT producto_id, COUNT(*) as cnt FROM videos
            WHERE cuenta = ? AND fecha_programada = ?
            AND estado IN ('En Calendario', 'Borrador', 'Programado')
            GROUP BY producto_id
        """, (cuenta, fecha_str))
        for row_dia in cursor_dia.fetchall():
            productos_usados_hoy[row_dia['producto_id']] = row_dia['cnt']
        conn_dia.close()

        videos_ya_hoy = sum(productos_usados_hoy.values())
        if videos_ya_hoy:
            print(f"  [INFO] Productos ya programados hoy: {videos_ya_hoy} videos")

        # Calcular cuántos videos NUEVOS necesitamos para este día
        videos_nuevos_hoy = max(0, videos_por_dia - videos_ya_hoy)
        if videos_nuevos_hoy == 0:
            print(f"  [INFO] Día completo ({videos_ya_hoy}/{videos_por_dia}), saltando")
            fecha_actual += timedelta(days=1)
            continue

        # Generar horarios solo para los slots vacíos, respetando horas ya ocupadas
        horarios = generar_horario(config, videos_nuevos_hoy, fecha_str, cuenta=cuenta)

        # Último producto programado (para anti-consecutivos)
        ultimo_producto_id = None

        for horario in horarios:
            video_seleccionado = None

            # Buscar en TODA la cola (pool completo de videos disponibles)
            # Dos pasadas: 1ª respetando anti-consecutivos, 2ª relajando
            for pasada in range(2):
                for video in cola_videos:
                    # Ya usado en esta tanda?
                    if video['id'] in videos_usados:
                        continue

                    # Ya en uso en BD? (anti-duplicados)
                    if video['video_id'] in videos_no_disponibles:
                        videos_usados.add(video['id'])
                        continue

                    producto_id = video['producto_id']
                    hook_id = video['hook_id']
                    seo_text = video['seo_text']
                    cat = video.get('estado_comercial') or 'testing'

                    # Pasada 1: respetar anti-consecutivos
                    if pasada == 0 and ultimo_producto_id is not None and producto_id == ultimo_producto_id:
                        continue

                    # Max producto/día (hard limit)
                    if productos_usados_hoy.get(producto_id, 0) >= max_mismo_producto:
                        continue

                    # Distancia hook
                    if not cumple_distancia_hook(hook_id, posicion_calendario, videos_programados, distancia_minima_hook):
                        continue

                    # Distancia SEO (misma lógica que hooks)
                    if not cumple_distancia_seo(seo_text, posicion_calendario, videos_programados, distancia_minima_hook):
                        continue

                    # Video válido!
                    video_seleccionado = video
                    break

                if video_seleccionado:
                    break

            if not video_seleccionado:
                print(f"  [WARNING] {horario} - No hay videos que cumplan restricciones")
                continue

            # Registrar video
            videos_dia.append({
                'video': video_seleccionado,
                'fecha': fecha_str,
                'hora': horario
            })

            # Actualizar contadores
            cat_sel = video_seleccionado.get('estado_comercial') or 'testing'
            cat_programados[cat_sel] = cat_programados.get(cat_sel, 0) + 1
            videos_usados.add(video_seleccionado['id'])
            productos_usados_hoy[video_seleccionado['producto_id']] = \
                productos_usados_hoy.get(video_seleccionado['producto_id'], 0) + 1
            ultimo_producto_id = video_seleccionado['producto_id']

            # Añadir a programados (para distancia hook)
            videos_programados.append({
                'video_id': video_seleccionado['video_id'],
                'fecha': fecha_str,
                'hook_id': video_seleccionado['hook_id'],
                'producto_id': video_seleccionado['producto_id'],
                'seo_text': video_seleccionado.get('seo_text', '')
            })
            posicion_calendario += 1

            estado_emoji = {'top_seller': '🔥', 'validated': '✅', 'testing': '🧪'}.get(
                video_seleccionado.get('estado_comercial', 'testing'), '?')
            print(f"  {estado_emoji} {horario} - {video_seleccionado['producto'][:25]} - {video_seleccionado['hook'][:25]}...")

        print(f"  [OK] {len(videos_dia)} videos programados")
        calendario.extend(videos_dia)

        # Siguiente día
        fecha_actual += timedelta(days=1)

    if not calendario:
        print(f"\n[ERROR] No se pudo programar ningún video")
        return False

    # ── Resumen por categoría ──
    resumen_cat = {'top_seller': 0, 'validated': 0, 'testing': 0}
    for item in calendario:
        cat = item['video'].get('estado_comercial') or 'testing'
        resumen_cat[cat] = resumen_cat.get(cat, 0) + 1

    print(f"\n{'='*60}")
    print(f"[RESUMEN] {len(calendario)} videos en {dias} días")
    print(f"   🔥 Top Seller: {resumen_cat['top_seller']}")
    print(f"   ✅ Validated:  {resumen_cat['validated']}")
    print(f"   🧪 Testing:    {resumen_cat['testing']}")
    print(f"{'='*60}\n")

    # ── Resumen por día (útil para simulación) ──
    resumen_dias = {}
    for item in calendario:
        fecha = item['fecha']
        resumen_dias[fecha] = resumen_dias.get(fecha, 0) + 1

    videos_por_dia_config = videos_override if videos_override else config.get('videos_por_dia', 5)
    dias_incompletos = 0
    for fecha_r, count_r in sorted(resumen_dias.items()):
        status = "OK" if count_r >= videos_por_dia_config else f"INCOMPLETO ({videos_por_dia_config - count_r} faltan)"
        if count_r < videos_por_dia_config:
            dias_incompletos += 1
        print(f"  {fecha_r}: {count_r}/{videos_por_dia_config} videos - {status}")

    if dias_incompletos > 0:
        print(f"\n  [WARNING] {dias_incompletos} días incompletos")

    # ── DRY RUN: parar aquí sin escribir nada ──
    if dry_run:
        print(f"\n[SIMULACIÓN] Fin del dry run. No se ha escrito nada.")
        # Devolver el calendario simulado para que cli.py pueda mostrarlo
        return calendario

    # ── Actualizar DB, ficheros, Sheet, Drive ──
    print(f"[SYNC] Actualizando base de datos y Google Sheets...")

    conn = get_connection()
    cursor = conn.cursor()

    rows_to_append = []
    videos_programados_ids = []
    programado_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Migrar columna si no existe (para BD existentes)
    try:
        cursor.execute("SELECT programado_at FROM videos LIMIT 1")
    except Exception:
        cursor.execute("ALTER TABLE videos ADD COLUMN programado_at TIMESTAMP")
        conn.commit()

    try:
        for item in calendario:
            video = item['video']
            fecha = item['fecha']
            hora = item['hora']

            fecha_sheet = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d-%m-%Y")

            # Actualizar DB
            cursor.execute("""
                UPDATE videos
                SET estado = 'En Calendario',
                    fecha_programada = ?,
                    hora_programada = ?,
                    programado_at = ?
                WHERE id = ?
            """, (fecha, hora, programado_at, video['id']))

            videos_programados_ids.append(video['video_id'])

            # Mover archivo físico
            en_carpeta = False
            origen = video['filepath']
            cuenta_dir = os.path.join(OUTPUT_DIR, cuenta)
            fecha_carpeta = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d-%m-%Y")
            destino_dir = os.path.join(cuenta_dir, 'calendario', fecha_carpeta)
            os.makedirs(destino_dir, exist_ok=True)
            destino = os.path.join(destino_dir, os.path.basename(origen))

            try:
                if os.path.exists(origen):
                    os.rename(origen, destino)
                    cursor.execute("UPDATE videos SET filepath = ? WHERE id = ?", (destino, video['id']))
                    # Copiar a Drive
                    drive_result = copiar_a_drive(destino, cuenta, fecha)
                    en_carpeta = drive_result is not None
            except Exception as e:
                print(f"[WARNING] Error moviendo {video['video_id']}: {e}")

            # Preparar row para Sheet (columna L = en_carpeta)
            rows_to_append.append([
                cuenta,
                video['producto'],
                fecha_sheet,
                hora,
                video['video_id'],
                video['hook'],
                video['deal_math'],
                video['seo_text'],
                video['hashtags'],
                video['url_producto'],
                'En Calendario',
                en_carpeta  # Columna L: "en carpeta" (TRUE/FALSE)
            ])

        conn.commit()
        conn.close()

    except KeyboardInterrupt:
        print(f"\n\n[!] Programación interrumpida! Deshaciendo {len(videos_programados_ids)} videos...")
        conn.rollback()
        conn.close()

        from rollback_calendario import rollback_calendario as do_rollback
        do_rollback(
            cuenta,
            video_ids=videos_programados_ids,
            test_mode=test_mode,
            skip_sheet=True
        )
        print("[OK] Rollback completado. No se han perdido datos.")
        return False

    # Append a Sheet (batch) con retry
    import time
    import logging

    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    sheet_logger = logging.getLogger('sheet_sync')
    if not sheet_logger.handlers:
        fh = logging.FileHandler(os.path.join(log_dir, 'sheet_writes.log'), encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        sheet_logger.addHandler(fh)
        sheet_logger.setLevel(logging.INFO)

    max_reintentos = 3
    sheet_ok = False
    for intento in range(1, max_reintentos + 1):
        try:
            sheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
            print(f"[OK] {len(rows_to_append)} filas añadidas a Google Sheets")
            sheet_logger.info(f"OK: {len(rows_to_append)} filas escritas para {cuenta} (intento {intento})")
            sheet_ok = True
            break
        except Exception as e:
            sheet_logger.warning(f"FALLO intento {intento}/{max_reintentos} para {cuenta}: {e}")
            print(f"[WARNING] Error escribiendo en Sheet (intento {intento}/{max_reintentos}): {e}")
            if intento < max_reintentos:
                wait_secs = intento * 5
                print(f"  Reintentando en {wait_secs}s...")
                time.sleep(wait_secs)

    if not sheet_ok:
        sheet_logger.error(f"FALLO DEFINITIVO: {len(rows_to_append)} filas NO escritas para {cuenta}")
        print(f"[ERROR] No se pudieron escribir las filas en Sheet tras {max_reintentos} intentos")
        print(f"[TIP] Ejecuta repair_sheet.py para reparar:")
        print(f"  python repair_sheet.py --cuenta {cuenta}")
        print(f"[TIP] O puedes deshacer con:")
        print(f"  python rollback_calendario.py --cuenta {cuenta} --ultima")

    print(f"\n{'='*60}")
    print(f"  CALENDARIO GENERADO")
    print(f"{'='*60}")
    print(f"\n[NEXT] Los videos están en:")
    print(f"  videos_generados_py/{cuenta}/calendario/DD-MM-YYYY/")
    print(f"\n[TIP] Para deshacer esta programación:")
    print(f"  python rollback_calendario.py --cuenta {cuenta} --ultima\n")

    # ── Registrar en historial (Cambio 3.8) ──
    try:
        from scripts.db_config import registrar_historial
        fechas_cal = sorted(set(item['fecha'] for item in calendario))
        registrar_historial(
            accion='programar',
            cuenta=cuenta,
            num_videos=len(calendario),
            fecha_inicio=fechas_cal[0] if fechas_cal else None,
            fecha_fin=fechas_cal[-1] if fechas_cal else None,
            dias=dias,
            detalles=f"sheet_ok={sheet_ok}" if 'sheet_ok' in dir() else None
        )
    except Exception as e:
        print(f"[WARNING] No se pudo registrar en historial: {e}")

    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Programar calendario TikTok')
    parser.add_argument('--cuenta', required=True, help='Nombre de la cuenta')
    parser.add_argument('--dias', type=int, required=True, help='Días a programar')
    parser.add_argument('--fecha-inicio', help='Fecha inicio (YYYY-MM-DD), default: mañana')
    parser.add_argument('--test', action='store_true', help='Usar Sheet TEST')
    parser.add_argument('--producto', help='Forzar solo videos de este producto')
    parser.add_argument('--videos-dia', type=int, help='Sobreescribir videos/dia (sin tocar config)')
    parser.add_argument('--dry-run', action='store_true', help='Simular sin escribir (dry run)')

    args = parser.parse_args()

    success = programar_calendario(
        args.cuenta,
        args.dias,
        args.fecha_inicio,
        args.test,
        args.producto,
        args.videos_dia,
        dry_run=args.dry_run
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
