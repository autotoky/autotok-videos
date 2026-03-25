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
from datetime import datetime, timedelta
import random
# Añadir parent al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.db_config import db_connection
from config import OUTPUT_DIR


def load_cuenta_config(cuenta_nombre):
    """Carga configuración de cuenta desde Turso (cuentas_config)."""
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cuentas_config WHERE nombre = ?", (cuenta_nombre,))
        row = cursor.fetchone()

    if row:
        return dict(row)

    print(f"[ERROR] Cuenta '{cuenta_nombre}' no encontrada en cuentas_config (Turso)")
    print(f"  → Usa el panel web /api/cuentas para crear la cuenta")
    return {}


def get_videos_disponibles(cuenta, producto_filter=None):
    """Obtiene videos 'Generado' con info de lifecycle del producto.

    Args:
        cuenta: Nombre de la cuenta
        producto_filter: Si se especifica, solo devuelve videos de ese producto

    Returns:
        list[dict]: Videos con estado_comercial y max_videos_test del producto
    """
    with db_connection() as conn:
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
                b.gancho,
                var.seo_text,
                b.hashtags,
                b.url_producto
            FROM videos v
            JOIN productos p ON v.producto_id = p.id
            JOIN material h ON v.hook_id = h.id
            JOIN producto_bofs b ON v.bof_id = b.id
            JOIN variantes_overlay_seo var ON v.variante_id = var.id
            WHERE v.cuenta = ? AND v.estado = 'Generado'
            AND p.estado_comercial != 'dropped'
            AND b.activo = 1
        """
        params = [cuenta]

        if producto_filter:
            query += " AND p.nombre = ?"
            params.append(producto_filter)

        query += """ ORDER BY
            CASE p.estado_comercial
                WHEN 'top_seller' THEN 1
                WHEN 'validated' THEN 2
                WHEN 'testing' THEN 3
                ELSE 4
            END,
            v.created_at ASC
            LIMIT 500"""

        cursor.execute(query, params)
        videos = [dict(row) for row in cursor.fetchall()]

    return videos


def get_videos_ya_programados(cuenta):
    """Obtiene videos ya programados (para distancia hook)"""
    with db_connection() as conn:
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

    return programados


def get_videos_acumulados_testing(cuenta):
    """Cuenta cuántos videos ya se han programado/publicado por producto en testing.

    Para saber cuánto margen queda de max_videos_test.

    Returns:
        dict: {producto_id: count} con videos en cualquier estado post-generado
    """
    with db_connection() as conn:
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

    return result


def get_horas_ocupadas(cuenta, fecha):
    """Obtiene las horas ya programadas para un día/cuenta desde BD.

    Returns:
        list[datetime]: Horas ya ocupadas como objetos datetime
    """
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hora_programada FROM videos
            WHERE cuenta = ? AND fecha_programada = ?
            AND estado IN ('En Calendario', 'Borrador', 'Programado')
            AND hora_programada IS NOT NULL
        """, (cuenta, fecha))
        horas = [row['hora_programada'] for row in cursor.fetchall()]

    return horas


def redondear_5min(dt):
    """Redondea un datetime al siguiente intervalo de 5 minutos (TikTok only allows 5-min intervals)."""
    minutos = dt.minute
    resto = minutos % 5
    if resto != 0:
        dt += timedelta(minutes=(5 - resto))
    return dt.replace(second=0, microsecond=0)


def _parse_ventana_horaria(config, fecha):
    """Parsea la ventana horaria de la config, con soporte para cruce de medianoche.

    Si la fecha es hoy, ajusta el inicio a "ahora + 15 min" para no asignar
    horas en el pasado.

    Returns:
        tuple: (inicio_dt, fin_dt, minutos_totales)
    """
    inicio = config.get('horario_inicio', '08:00')
    fin = config.get('horario_fin', '21:30')

    inicio_dt = datetime.strptime(f"{fecha} {inicio}", "%Y-%m-%d %H:%M")
    fin_dt = datetime.strptime(f"{fecha} {fin}", "%Y-%m-%d %H:%M")

    if fin_dt <= inicio_dt:
        fin_dt += timedelta(days=1)

    # Si es hoy, no programar en el pasado
    ahora = datetime.now()
    if inicio_dt.date() == ahora.date() and ahora > inicio_dt:
        # Margen de 30 min desde ahora (redondeado a 5 min) — QUA-231, parity with web
        minimo = ahora + timedelta(minutes=30)
        # Redondear al siguiente múltiplo de 5
        minuto = minimo.minute
        resto = minuto % 5
        if resto:
            minimo += timedelta(minutes=5 - resto)
        minimo = minimo.replace(second=0, microsecond=0)
        inicio_dt = minimo
        print(f"  [INFO] Fecha es hoy — inicio ajustado a {inicio_dt.strftime('%H:%M')}")

    minutos_totales = (fin_dt - inicio_dt).total_seconds() / 60
    return inicio_dt, fin_dt, minutos_totales


def _get_horas_ocupadas_dt(cuenta, fecha, inicio_dt):
    """Obtiene horas ocupadas como datetimes, ajustando para cruce de medianoche."""
    horas_ocupadas = []
    if cuenta:
        horas_str = get_horas_ocupadas(cuenta, fecha)
        for h in horas_str:
            try:
                h_dt = datetime.strptime(f"{fecha} {h}", "%Y-%m-%d %H:%M")
                if h_dt < inicio_dt:
                    h_dt += timedelta(days=1)
                horas_ocupadas.append(h_dt)
            except ValueError:
                continue
    return horas_ocupadas


def generar_horario_huecos(config, videos_nuevos, fecha, cuenta=None):
    """Genera horarios buscando los N huecos más grandes del día.

    Ideal para añadir videos de un producto específico: los separa lo máximo
    posible entre sí y respecto a los videos existentes.

    Args:
        config: Configuración de la cuenta
        videos_nuevos: Cuántos videos NUEVOS colocar
        fecha: Fecha en formato YYYY-MM-DD
        cuenta: Nombre de cuenta (para consultar horas ocupadas en BD)

    Returns:
        list[str]: Horarios en formato HH:MM
    """
    GAP_MINIMO_ABSOLUTO = 15

    inicio_dt, fin_dt, minutos_totales = _parse_ventana_horaria(config, fecha)
    horas_ocupadas = _get_horas_ocupadas_dt(cuenta, fecha, inicio_dt)

    if horas_ocupadas:
        print(f"  [INFO] {len(horas_ocupadas)} horas ya ocupadas")

    if videos_nuevos <= 0:
        return []

    ocupados = sorted(horas_ocupadas)
    horarios_finales = []

    # Colocar videos uno a uno, siempre en el hueco más grande disponible
    todos_puntos = sorted([inicio_dt] + ocupados + [fin_dt])

    for _ in range(videos_nuevos):
        # Calcular huecos entre puntos existentes
        huecos = []
        for j in range(len(todos_puntos) - 1):
            hueco_min = (todos_puntos[j + 1] - todos_puntos[j]).total_seconds() / 60
            if hueco_min >= GAP_MINIMO_ABSOLUTO * 2:
                centro = todos_puntos[j] + timedelta(minutes=hueco_min / 2)
                centro = redondear_5min(centro)
                # Añadir variación aleatoria (±10 min en tramos de 5)
                variacion = random.choice([-10, -5, 0, 5, 10])
                candidato = redondear_5min(centro + timedelta(minutes=variacion))
                # Verificar que sigue dentro del hueco y la ventana
                if candidato <= todos_puntos[j] + timedelta(minutes=GAP_MINIMO_ABSOLUTO):
                    candidato = centro  # volver al centro si la variación lo saca
                if candidato >= todos_puntos[j + 1] - timedelta(minutes=GAP_MINIMO_ABSOLUTO):
                    candidato = centro
                if candidato < inicio_dt or candidato > fin_dt:
                    candidato = centro
                huecos.append((hueco_min, candidato))

        if not huecos:
            print(f"  [WARNING] No hay más huecos disponibles (colocados {len(horarios_finales)}/{videos_nuevos})")
            break

        # Ordenar por tamaño de hueco descendente, tomar el más grande
        huecos.sort(key=lambda x: x[0], reverse=True)
        _, mejor = huecos[0]

        horarios_finales.append(mejor.strftime("%H:%M"))
        todos_puntos.append(mejor)
        todos_puntos.sort()

    print(f"  [INFO] Ventana: {minutos_totales:.0f} min | Huecos usados: {len(horarios_finales)}/{videos_nuevos}")
    return sorted(horarios_finales)


def generar_horario(config, videos_nuevos, fecha, cuenta=None):
    """Genera horarios distribuidos uniformemente con variación aleatoria.

    Lógica:
    1. Calcula el gap ideal = minutos_disponibles / videos_totales
    2. Distribuye videos uniformemente a lo largo de la ventana horaria
    3. Añade variación aleatoria (±10 min en tramos de 5 min)
    4. Garantiza separación mínima de 15 min entre cualquier par de videos
    5. Todo en intervalos de 5 min (requisito TikTok)

    Args:
        config: Configuración de la cuenta
        videos_nuevos: Cuántos videos NUEVOS hay que programar en este día
        fecha: Fecha en formato YYYY-MM-DD
        cuenta: Nombre de cuenta (para consultar horas ocupadas en BD)

    Returns:
        list[str]: Horarios en formato HH:MM, solo para los slots nuevos
    """
    GAP_MINIMO_ABSOLUTO = 15  # minutos — nunca menos que esto entre dos videos

    inicio_dt, fin_dt, minutos_totales = _parse_ventana_horaria(config, fecha)
    horas_ocupadas = _get_horas_ocupadas_dt(cuenta, fecha, inicio_dt)

    if horas_ocupadas:
        print(f"  [INFO] {len(horas_ocupadas)} horas ya ocupadas: {', '.join(sorted(h.strftime('%H:%M') for h in horas_ocupadas))}")

    if videos_nuevos <= 0:
        return []

    ocupados = sorted(horas_ocupadas)
    total_videos = len(ocupados) + videos_nuevos

    # Calcular gap ideal basado en el total de videos (ocupados + nuevos)
    gap_ideal = minutos_totales / total_videos if total_videos > 0 else minutos_totales

    if gap_ideal < GAP_MINIMO_ABSOLUTO:
        max_posibles = int(minutos_totales / GAP_MINIMO_ABSOLUTO)
        disponibles = max_posibles - len(ocupados)
        if disponibles < videos_nuevos:
            print(f"  [WARNING] Solo caben {disponibles} videos nuevos con gap mínimo de {GAP_MINIMO_ABSOLUTO} min (solicitados: {videos_nuevos})")
            videos_nuevos = max(0, disponibles)
            if videos_nuevos == 0:
                return []
        total_videos = len(ocupados) + videos_nuevos
        gap_ideal = minutos_totales / total_videos

    print(f"  [INFO] Ventana: {minutos_totales:.0f} min | Videos totales: {total_videos} | Gap ideal: {gap_ideal:.0f} min")

    # Calcular variación máxima: no más del 20% del gap ideal, en tramos de 5 min, máx ±10 min
    variacion_max = min(10, int(gap_ideal * 0.2 / 5) * 5)
    variacion_max = max(variacion_max, 5)  # al menos ±5 min
    variaciones_posibles = list(range(-variacion_max, variacion_max + 1, 5))

    # Estrategia: generar todos los puntos (ocupados + nuevos) distribuidos,
    # quedarnos solo con los nuevos
    todos_los_puntos = []

    for i in range(total_videos):
        offset_minutos = gap_ideal * i + gap_ideal / 2
        base_dt = inicio_dt + timedelta(minutes=offset_minutos)
        base_dt = redondear_5min(base_dt)

        if base_dt > fin_dt:
            base_dt = redondear_5min(fin_dt - timedelta(minutes=5))

        todos_los_puntos.append(base_dt)

    # Asignar cada punto: si coincide con un ocupado existente, lo marcamos como ocupado
    ocupados_restantes = list(ocupados)
    slots_nuevos_dt = []

    for punto in todos_los_puntos:
        matched = False
        for oc in ocupados_restantes:
            if abs((punto - oc).total_seconds()) / 60 < gap_ideal / 2:
                ocupados_restantes.remove(oc)
                matched = True
                break
        if not matched:
            slots_nuevos_dt.append(punto)

    # Añadir variación aleatoria a cada slot nuevo
    horarios_finales = []
    todos_definitivos = sorted(ocupados)

    for slot in slots_nuevos_dt:
        if len(horarios_finales) >= videos_nuevos:
            break

        vars_shuffled = [v for v in variaciones_posibles if v != 0]
        random.shuffle(vars_shuffled)
        vars_shuffled.append(0)
        colocado = False

        for var in vars_shuffled:
            candidato = redondear_5min(slot + timedelta(minutes=var))

            if candidato < inicio_dt or candidato > fin_dt:
                continue

            ok = all(
                abs((candidato - d).total_seconds()) / 60 >= GAP_MINIMO_ABSOLUTO
                for d in todos_definitivos
            )

            if ok:
                horarios_finales.append(candidato.strftime("%H:%M"))
                todos_definitivos.append(candidato)
                todos_definitivos.sort()
                colocado = True
                break

        if not colocado:
            puntos_ord = sorted([inicio_dt] + todos_definitivos + [fin_dt])
            mejor_hueco = None
            mejor_centro = None
            for j in range(len(puntos_ord) - 1):
                hueco = (puntos_ord[j + 1] - puntos_ord[j]).total_seconds() / 60
                if hueco >= GAP_MINIMO_ABSOLUTO * 2:
                    centro = puntos_ord[j] + timedelta(minutes=hueco / 2)
                    centro = redondear_5min(centro)
                    if mejor_hueco is None or hueco > mejor_hueco:
                        mejor_hueco = hueco
                        mejor_centro = centro

            if mejor_centro and inicio_dt <= mejor_centro <= fin_dt:
                ok = all(
                    abs((mejor_centro - d).total_seconds()) / 60 >= GAP_MINIMO_ABSOLUTO
                    for d in todos_definitivos
                )
                if ok:
                    horarios_finales.append(mejor_centro.strftime("%H:%M"))
                    todos_definitivos.append(mejor_centro)
                    todos_definitivos.sort()

    if len(horarios_finales) < videos_nuevos:
        print(f"  [WARNING] Solo hay espacio para {len(horarios_finales)} videos nuevos de {videos_nuevos} solicitados")

    return sorted(horarios_finales)


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


def cumple_distancia_producto(producto_id, posicion_calendario, videos_programados, distancia_minima):
    """Verifica si producto cumple distancia mínima de publicaciones (QUA-298).
    Matches web programar.py: _cumple_distancia_producto()."""
    if not producto_id:
        return True
    ultima_posicion = -999
    for i, video in enumerate(videos_programados):
        if str(video.get('producto_id', '')) == str(producto_id):
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
    print(f"   Gap mínimo: 15 min (absoluto)")
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

    # Calcular distancia SEO dinámica basada en la diversidad del pool
    seos_unicos = set(v.get('seo_text', '') for v in cola_videos)
    distancia_seo = max(1, len(seos_unicos) - 1)  # nunca más que los SEOs únicos - 1
    distancia_seo = min(distancia_seo, distancia_minima_hook)  # nunca más que la distancia de hooks
    print(f"[INFO] SEO texts únicos: {len(seos_unicos)} → distancia SEO: {distancia_seo}")

    # QUA-298: Dynamic product distance
    productos_unicos = set(str(v.get('producto_id', '')) for v in cola_videos if v.get('producto_id'))
    distancia_producto = max(1, min(len(productos_unicos) - 1, 3))
    print(f"[INFO] Productos únicos: {len(productos_unicos)} → distancia producto: {distancia_producto}")

    # ── Protección anti-duplicados: consultar BD (no Sheet) ──
    # Un video con estado != 'Generado' ya está en uso o descartado
    with db_connection() as conn_dup:
        cursor_dup = conn_dup.cursor()
        cursor_dup.execute("""
            SELECT video_id FROM videos
            WHERE cuenta = ? AND estado != 'Generado'
        """, (cuenta,))
        videos_no_disponibles = {row['video_id'] for row in cursor_dup.fetchall()}
    if videos_no_disponibles:
        print(f"[INFO] {len(videos_no_disponibles)} videos ya usados/descartados en BD (se excluirán)")

    # QUA-231: Detect overnight window for date adjustment
    _h_ini = config.get('horario_inicio', '08:00') or '08:00'
    _h_fin = config.get('horario_fin', '21:30') or '21:30'
    _ini_parts = _h_ini.split(':')
    _fin_parts = _h_fin.split(':')
    _ini_total = int(_ini_parts[0]) * 60 + int(_ini_parts[1])
    _fin_total = int(_fin_parts[0]) * 60 + int(_fin_parts[1])
    is_overnight = _fin_total <= _ini_total

    # ── Programar día a día ──
    calendario = []
    videos_usados = set()  # IDs ya usados (para no repetir)
    slots_fallidos = []  # Slots donde no hubo video que cumpliera restricciones
    restricciones_relajadas = False  # Se activa si el usuario lo pide

    # Tracking de distribución por categoría (soft target)
    cat_programados = {'top_seller': 0, 'validated': 0, 'testing': 0}
    cat_target = dict(slots_por_categoria)  # target ideal

    for dia in range(dias):
        fecha_str = fecha_actual.strftime("%Y-%m-%d")
        print(f"\n[DÍA] {fecha_str}")

        videos_dia = []

        # Pre-cargar productos ya programados para este día (de tandas anteriores)
        productos_usados_hoy = {}
        with db_connection() as conn_dia:
            cursor_dia = conn_dia.cursor()
            cursor_dia.execute("""
                SELECT producto_id, COUNT(*) as cnt FROM videos
                WHERE cuenta = ? AND fecha_programada = ?
                AND estado IN ('En Calendario', 'Borrador', 'Programado')
                GROUP BY producto_id
            """, (cuenta, fecha_str))
            for row_dia in cursor_dia.fetchall():
                productos_usados_hoy[row_dia['producto_id']] = row_dia['cnt']

        videos_ya_hoy = sum(productos_usados_hoy.values())
        if videos_ya_hoy:
            print(f"  [INFO] Productos ya programados hoy: {videos_ya_hoy} videos")

        # Calcular cuántos videos NUEVOS necesitamos para este día
        # videos_por_dia siempre es cuántos AÑADIR (no total objetivo)
        videos_nuevos_hoy = videos_por_dia

        # Generar horarios: huecos máximos si es producto específico, uniforme si es general
        if producto_filter:
            horarios = generar_horario_huecos(config, videos_nuevos_hoy, fecha_str, cuenta=cuenta)
        else:
            horarios = generar_horario(config, videos_nuevos_hoy, fecha_str, cuenta=cuenta)

        # Último producto programado (para anti-consecutivos)
        ultimo_producto_id = None

        for horario in horarios:
            video_seleccionado = None

            # Buscar en TODA la cola con restricciones progresivas:
            #   Pasada 0: todas las restricciones + límites categoría + distancia producto
            #   Pasada 1: todas las restricciones + límites categoría (sin distancia producto)
            #   Pasada 2: todas las restricciones sin límites categoría (overflow)
            #   Pasada 3: sin SEO (si restricciones_relajadas)
            #   Pasada 4: sin hook ni SEO (si restricciones_relajadas)
            #   Anti-consecutivo: restricción DURA en TODAS las pasadas (QUA-373)
            max_pasadas = 5 if restricciones_relajadas else 3
            for pasada in range(max_pasadas):
                for video in cola_videos:
                    if video['id'] in videos_usados:
                        continue

                    if video['video_id'] in videos_no_disponibles:
                        videos_usados.add(video['id'])
                        continue

                    producto_id = video['producto_id']
                    hook_id = video['hook_id']
                    seo_text = video['seo_text']
                    video_cat = video.get('estado_comercial') or 'testing'

                    # Pasadas 0-1: respetar límites de slots por categoría
                    if pasada < 2:
                        if cat_programados.get(video_cat, 0) >= cat_target.get(video_cat, 0):
                            continue

                    # QUA-373: anti-consecutivo en TODAS las pasadas (restricción dura)
                    if ultimo_producto_id is not None and producto_id == ultimo_producto_id:
                        continue

                    # Pasadas 0-1: distancia producto (QUA-298)
                    if pasada < 2:
                        if not cumple_distancia_producto(producto_id, posicion_calendario,
                                                         videos_programados, distancia_producto):
                            continue

                    # Max producto/día (hard limit, siempre aplica)
                    if productos_usados_hoy.get(producto_id, 0) >= max_mismo_producto:
                        continue

                    # Distancia hook (se salta en pasada 4)
                    if pasada < 4:
                        if not cumple_distancia_hook(hook_id, posicion_calendario, videos_programados, distancia_minima_hook):
                            continue

                    # Distancia SEO (se salta en pasada 3+)
                    if pasada < 3:
                        if not cumple_distancia_seo(seo_text, posicion_calendario, videos_programados, distancia_seo):
                            continue

                    video_seleccionado = video
                    break

                if video_seleccionado:
                    break

            if not video_seleccionado:
                slots_fallidos.append({'fecha': fecha_str, 'hora': horario})
                print(f"  [WARNING] {horario} - No hay videos que cumplan restricciones")
                continue

            # QUA-231: If overnight window and hour is after midnight, date = next day
            video_fecha = fecha_str
            if is_overnight:
                hp = horario.split(':')
                h_min = int(hp[0]) * 60 + int(hp[1])
                if h_min < _ini_total:
                    video_fecha = (datetime.strptime(fecha_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

            # Registrar video
            videos_dia.append({
                'video': video_seleccionado,
                'fecha': video_fecha,
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
                'fecha': video_fecha,
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

    # ── Pregunta interactiva si hay slots fallidos por restricciones ──
    if slots_fallidos and not restricciones_relajadas:
        videos_disponibles_restantes = sum(1 for v in cola_videos if v['id'] not in videos_usados and v['video_id'] not in videos_no_disponibles)
        print(f"\n  [!] {len(slots_fallidos)} slots no pudieron llenarse por restricciones de hook/SEO")
        print(f"      Videos disponibles sin usar: {videos_disponibles_restantes}")
        respuesta = input("  ¿Relajar restricciones de hook/SEO para completar? (S/N): ").strip().upper()
        if respuesta == 'S' and videos_disponibles_restantes > 0:
            restricciones_relajadas = True
            # Volver a intentar los slots fallidos
            print(f"\n  [RETRY] Reintentando {len(slots_fallidos)} slots con restricciones relajadas...")
            for slot_info in slots_fallidos:
                sf_fecha = slot_info['fecha']
                sf_hora = slot_info['hora']
                video_seleccionado = None

                # Recalcular productos usados hoy para esta fecha
                productos_hoy_retry = {}
                for item in calendario:
                    if item['fecha'] == sf_fecha:
                        pid = item['video']['producto_id']
                        productos_hoy_retry[pid] = productos_hoy_retry.get(pid, 0) + 1

                for pasada in range(4):  # 4 pasadas con relajación progresiva
                    for video in cola_videos:
                        if video['id'] in videos_usados:
                            continue
                        if video['video_id'] in videos_no_disponibles:
                            videos_usados.add(video['id'])
                            continue

                        producto_id = video['producto_id']
                        hook_id = video['hook_id']
                        seo_text = video['seo_text']

                        if productos_hoy_retry.get(producto_id, 0) >= max_mismo_producto:
                            continue

                        if pasada < 3:
                            if not cumple_distancia_hook(hook_id, posicion_calendario, videos_programados, distancia_minima_hook):
                                continue
                        if pasada < 2:
                            if not cumple_distancia_seo(seo_text, posicion_calendario, videos_programados, distancia_seo):
                                continue

                        video_seleccionado = video
                        break

                    if video_seleccionado:
                        break

                if video_seleccionado:
                    calendario.append({
                        'video': video_seleccionado,
                        'fecha': sf_fecha,
                        'hora': sf_hora
                    })
                    videos_usados.add(video_seleccionado['id'])
                    productos_hoy_retry[video_seleccionado['producto_id']] = \
                        productos_hoy_retry.get(video_seleccionado['producto_id'], 0) + 1

                    videos_programados.append({
                        'video_id': video_seleccionado['video_id'],
                        'fecha': sf_fecha,
                        'hook_id': video_seleccionado['hook_id'],
                        'producto_id': video_seleccionado['producto_id'],
                        'seo_text': video_seleccionado.get('seo_text', '')
                    })
                    posicion_calendario += 1

                    estado_emoji = {'top_seller': '🔥', 'validated': '✅', 'testing': '🧪'}.get(
                        video_seleccionado.get('estado_comercial', 'testing'), '?')
                    print(f"  {estado_emoji} {sf_fecha} {sf_hora} - {video_seleccionado['producto'][:25]} - {video_seleccionado['hook'][:25]}...")
                else:
                    print(f"  [!] {sf_fecha} {sf_hora} - Sin candidatos incluso relajando")

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
        print(f"  {fecha_r}: +{count_r} videos añadidos (pedidos: {videos_por_dia_config}) - {status}")

    if dias_incompletos > 0:
        print(f"\n  [WARNING] {dias_incompletos} días incompletos")

    # ── DRY RUN: parar aquí sin escribir nada ──
    if dry_run:
        print(f"\n[SIMULACIÓN] Fin del dry run. No se ha escrito nada.")
        # Devolver el calendario simulado para que cli.py pueda mostrarlo
        return calendario

    # ── Actualizar BD (Turso) ──
    print(f"[SYNC] Actualizando base de datos...")

    videos_programados_ids = []
    programado_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Migrar columna si no existe (para BD existentes)
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT programado_at FROM videos LIMIT 1")
    except Exception:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("ALTER TABLE videos ADD COLUMN programado_at TIMESTAMP")

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            for item in calendario:
                video = item['video']
                fecha = item['fecha']
                hora = item['hora']

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

                # QUA-151: Ya no movemos archivos. El video se queda donde se generó.
                # El filepath en BD no cambia. El estado se gestiona solo en BD/Turso.

    except KeyboardInterrupt:
        print(f"\n\n[!] Programación interrumpida! Deshaciendo {len(videos_programados_ids)} videos...")

        try:
            from rollback_calendario import rollback_calendario as do_rollback
            do_rollback(
                cuenta,
                video_ids=videos_programados_ids,
                test_mode=test_mode,
                skip_sheet=True
            )
            print("[OK] Rollback completado. No se han perdido datos.")
        except ImportError:
            # QUA-148: rollback_calendario eliminado, revertir directamente en BD
            with db_connection() as rconn:
                rcur = rconn.cursor()
                for vid in videos_programados_ids:
                    rcur.execute("UPDATE videos SET estado='Generado', fecha_programada=NULL, hora_programada=NULL WHERE video_id=?", (vid,))
            print(f"[OK] {len(videos_programados_ids)} videos revertidos a Generado.")
        return False

    print(f"\n  [OK] {len(calendario)} videos guardados en Turso")

    print(f"\n{'='*60}")
    print(f"  CALENDARIO GENERADO")
    print(f"{'='*60}")
    print(f"\n[NEXT] Los videos están en Synology Drive:")
    print(f"  SynologyDrive/{cuenta}/{{video_id}}.mp4")
    print(f"  (almacenamiento plano — los archivos NO se mueven)\n")

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
            detalles=None
        )
    except Exception as e:
        print(f"[WARNING] No se pudo registrar en historial: {e}")

    # ── QUA-189: Limpiar resultados viejos de videos recién programados ──
    # Si un video fue publicado en una tanda anterior y se re-programa,
    # su resultado viejo en la tabla `resultados` de Turso haría que
    # `importar_resultados` lo pase a 'Programado' de vuelta (falso positivo).
    # Borramos esos resultados antes de importar.
    if videos_programados_ids:
        try:
            with db_connection() as clean_conn:
                clean_cur = clean_conn.cursor()
                for vid in videos_programados_ids:
                    clean_cur.execute(
                        "DELETE FROM resultados WHERE video_id = ?", (vid,)
                    )
            print(f"[OK] Limpiados resultados previos de {len(videos_programados_ids)} videos (QUA-189)")
        except Exception as e:
            # No es crítico — la tabla puede no existir en SQLite local
            print(f"[INFO] No se pudieron limpiar resultados previos: {e}")

    # ── Auto-export JSON de lotes para operadoras (QUA-43) ──
    try:
        from scripts.lote_manager import exportar_lote, importar_resultados

        # Primero importar resultados pendientes (garantía anti-desync)
        importar_resultados(cuenta)

        # Exportar un lote por cada fecha programada
        fechas_programadas = sorted(set(item['fecha'] for item in calendario))
        for fecha_export in fechas_programadas:
            lote_file = exportar_lote(cuenta, fecha_export)
            if lote_file:
                print(f"[OK] Lote exportado: {cuenta}/{fecha_export} → {os.path.basename(lote_file)}")
    except ImportError:
        pass  # lote_manager no disponible (no afecta al flujo normal)
    except Exception as e:
        print(f"[WARNING] No se pudieron exportar lotes: {e}")
        print(f"  (No afecta a la programación, solo al flujo de operadoras)")

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
