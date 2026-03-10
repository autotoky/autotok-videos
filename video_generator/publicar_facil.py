#!/usr/bin/env python3
"""
PUBLICAR_FACIL.PY — Wrapper amigable para operadoras (QUA-43)

La operadora hace doble-click en PUBLICAR.bat → este script:
  1. Busca automáticamente lotes pendientes (API o Drive)
  2. Muestra resumen de lo que va a hacer
  3. Publica los videos pendientes
  4. Busca el siguiente lote y repite hasta que no queden más
  5. Muestra resultado en pantalla (sin jerga técnica)

NO necesita: base de datos, credenciales de Sheet, ni argumentos CLI.
Solo necesita: Python, Playwright, Chrome con sesión de TikTok abierta.
"""

import os
import sys
import json
import glob
import time
import argparse
from datetime import datetime

# Añadir parent al path para imports
sys.path.insert(0, os.path.dirname(__file__))


def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')


def mostrar_banner():
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║                                              ║")
    print("  ║        AUTOTOK — Publicador Automático       ║")
    print("  ║                                              ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()


def _find_config_operadora():
    """Finds config_operadora.json path (QUA-184).

    Search order:
      1. %LOCALAPPDATA%/AutoTok/config_operadora.json (per-PC, outside Synology)
      2. kevin/config_operadora.json (legacy, shared via Synology)
    """
    localappdata = os.environ.get('LOCALAPPDATA', '')
    if localappdata:
        local_path = os.path.join(localappdata, 'AutoTok', 'config_operadora.json')
        if os.path.exists(local_path):
            return local_path

    legacy_path = os.path.join(os.path.dirname(__file__), 'config_operadora.json')
    if os.path.exists(legacy_path):
        return legacy_path

    return None


def cargar_config():
    """Carga configuración del operador desde config_operadora.json (QUA-184).

    Busca primero en %LOCALAPPDATA%/AutoTok/ (per-PC), luego en kevin/ (legacy).
    """
    config_path = _find_config_operadora()
    if not config_path:
        print("  [!] No se encontró config_operadora.json")
        print("  [!] Ejecuta INSTALAR.bat primero para configurar tu cuenta.")
        print()
        input("  Pulsa ENTER para salir...")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    cuenta = config.get('cuenta', '')
    drive_path = config.get('drive_path', '')

    if not cuenta or not drive_path:
        print("  [!] La configuración está incompleta.")
        print("  [!] Ejecuta INSTALAR.bat de nuevo.")
        print()
        input("  Pulsa ENTER para salir...")
        sys.exit(1)

    return cuenta, drive_path


def buscar_todos_lotes_pendientes(cuenta, drive_path):
    """Busca TODOS los lotes pendientes — híbrido API + local (QUA-184).

    Siempre busca en AMBAS fuentes y hace merge por fecha para no perder
    lotes que solo existan localmente (ej: sincronizados via Synology pero
    no exportados a API, o API caída).

    Returns:
        list[dict]: lista de lotes, cada uno con claves:
            fecha, n_pendientes, total_videos, lote_data, lote_path
    """
    lotes_por_fecha = {}  # fecha → lote_info (merge key)

    # ── Fuente 1: API ──
    try:
        from api_client import obtener_todos_lotes, is_api_configured
        if is_api_configured():
            api_lotes = obtener_todos_lotes(cuenta)
            if api_lotes:
                lotes_dir = os.path.join(drive_path, cuenta, '_lotes')
                os.makedirs(lotes_dir, exist_ok=True)

                for api_lote in api_lotes:
                    fecha = api_lote.get('fecha', 'unknown')
                    local_path = os.path.join(lotes_dir, f"lote_{cuenta}_{fecha}.json")

                    resultados = api_lote.get('resultados', {})
                    videos = api_lote.get('videos', [])
                    pendientes = [
                        v for v in videos
                        if v['video_id'] not in resultados
                        or resultados[v['video_id']].get('estado') == 'Error'
                    ]

                    if pendientes:
                        # Guardar copia local del lote de API
                        with open(local_path, 'w', encoding='utf-8') as f:
                            json.dump(api_lote, f, ensure_ascii=False, indent=2)
                        lotes_por_fecha[fecha] = {
                            'fecha': fecha,
                            'n_pendientes': len(pendientes),
                            'total_videos': len(videos),
                            'lote_data': api_lote,
                            'lote_path': local_path,
                        }
    except Exception:
        pass  # Silencioso — seguimos con búsqueda local

    # ── Fuente 2: Drive local (archivos JSON en _lotes/) ──
    lotes_dir = os.path.join(drive_path, cuenta, '_lotes')
    if os.path.exists(lotes_dir):
        pattern = os.path.join(lotes_dir, 'lote_*.json')
        archivos = sorted(glob.glob(pattern), key=os.path.getmtime)

        for filepath in archivos:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lote = json.load(f)

                fecha = lote.get('fecha', '?')

                # Si ya tenemos este lote de API, API gana (tiene resultados frescos)
                if fecha in lotes_por_fecha:
                    continue

                resultados = lote.get('resultados', {})
                videos = lote.get('videos', [])
                pendientes = [
                    v for v in videos
                    if v['video_id'] not in resultados
                    or resultados[v['video_id']].get('estado') == 'Error'
                ]

                if pendientes:
                    lotes_por_fecha[fecha] = {
                        'fecha': fecha,
                        'n_pendientes': len(pendientes),
                        'total_videos': len(videos),
                        'lote_data': lote,
                        'lote_path': filepath,
                    }
            except Exception:
                continue

    # ── QUA-190: Cross-check con BD (Turso) ──
    # Los archivos locales pueden estar desactualizados si se hicieron
    # cambios desde el dashboard (ej: "Quitar"). Verificamos el estado
    # actual de cada video directamente en la BD.
    if lotes_por_fecha:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
            from db_config import get_connection
            conn = get_connection()
            cur = conn.cursor()

            # Recopilar todos los video_ids de todos los lotes
            all_video_ids = []
            for lote_info in lotes_por_fecha.values():
                for v in lote_info['lote_data'].get('videos', []):
                    all_video_ids.append(v['video_id'])

            if all_video_ids:
                # Consultar estados actuales en la BD
                # (Turso HTTP soporta placeholders, SQLite también)
                ph = ",".join(["?" for _ in all_video_ids])
                cur.execute(
                    f"SELECT video_id, estado FROM videos WHERE video_id IN ({ph})",
                    all_video_ids
                )
                estados_bd = {row['video_id']: row['estado'] for row in cur.fetchall()}
                conn.close()

                ESTADOS_PUBLICABLES = ('En Calendario', 'Borrador', 'Programado')

                # Filtrar videos no publicables de cada lote
                fechas_a_borrar = []
                for fecha, lote_info in lotes_por_fecha.items():
                    lote_data = lote_info['lote_data']
                    videos_orig = lote_data.get('videos', [])

                    # Solo mantener videos en estado publicable
                    videos_filtrados = [
                        v for v in videos_orig
                        if estados_bd.get(v['video_id']) in ESTADOS_PUBLICABLES
                    ]
                    lote_data['videos'] = videos_filtrados
                    lote_data['total_videos'] = len(videos_filtrados)

                    # Recalcular pendientes
                    resultados = lote_data.get('resultados', {})
                    pendientes = [
                        v for v in videos_filtrados
                        if v['video_id'] not in resultados
                        or resultados[v['video_id']].get('estado') == 'Error'
                    ]

                    if pendientes:
                        lote_info['n_pendientes'] = len(pendientes)
                        lote_info['total_videos'] = len(videos_filtrados)
                    else:
                        fechas_a_borrar.append(fecha)

                for fecha in fechas_a_borrar:
                    del lotes_por_fecha[fecha]

        except Exception:
            pass  # Si falla la BD, usar datos tal cual (backward compatible)

    # Devolver ordenados por fecha
    return sorted(lotes_por_fecha.values(), key=lambda x: x['fecha'])


def mostrar_resumen_lote(lote, n_pendientes, lote_path):
    """Muestra resumen amigable del lote."""
    fecha = lote.get('fecha', '?')
    cuenta = lote.get('cuenta', '?')
    total = lote.get('total_videos', len(lote.get('videos', [])))
    ya_hechos = total - n_pendientes

    print(f"  Cuenta:    {cuenta}")
    print(f"  Fecha:     {fecha}")
    print(f"  Total:     {total} videos")

    if ya_hechos > 0:
        print(f"  Ya hechos: {ya_hechos}")

    print(f"  Pendientes: {n_pendientes}")
    print(f"  Archivo:   {os.path.basename(lote_path)}")
    print()


def mostrar_resultado(stats):
    """Muestra resultado final de forma amigable."""
    print()
    print(f"  ╔══════════════════════════════════════════════╗")
    print(f"  ║              RESULTADO DEL LOTE               ║")
    print(f"  ╚══════════════════════════════════════════════╝")
    print()

    exitosos = stats.get('exitosos', 0)
    fallidos = stats.get('fallidos', 0)
    saltados = stats.get('saltados', 0)

    if exitosos > 0:
        print(f"  Publicados OK:  {exitosos}")
    if fallidos > 0:
        print(f"  Con error:      {fallidos}")
    if saltados > 0:
        print(f"  Saltados:       {saltados}")

    print()

    if fallidos == 0 and exitosos > 0:
        print("  Todo perfecto. Los videos se publicarán a la hora programada.")
    elif fallidos > 0 and exitosos > 0:
        print(f"  {exitosos} videos se publicarán correctamente.")
        print(f"  {fallidos} tuvieron error — se reintentarán en la próxima ejecución.")
    elif exitosos == 0 and fallidos > 0:
        print("  Ningún video se pudo publicar.")
        print("  Comprueba que estás logueada en TikTok Studio en Chrome")
        print("  y vuelve a intentarlo.")
    else:
        print("  No había videos pendientes.")

    print()

    return exitosos, fallidos, saltados


def mostrar_resumen_total(totales):
    """Muestra resumen acumulado de todos los lotes procesados."""
    print()
    print(f"  ╔══════════════════════════════════════════════╗")
    print(f"  ║              RESUMEN TOTAL                    ║")
    print(f"  ╚══════════════════════════════════════════════╝")
    print()
    print(f"  Lotes procesados:  {totales['lotes']}")
    print(f"  Publicados OK:     {totales['exitosos']}")
    if totales['fallidos'] > 0:
        print(f"  Con error:         {totales['fallidos']}")
    if totales['saltados'] > 0:
        print(f"  Saltados:          {totales['saltados']}")
    print()

    if totales['fallidos'] == 0 and totales['exitosos'] > 0:
        print("  Todo perfecto. Todos los videos se publicarán a sus horas.")
    elif totales['fallidos'] > 0:
        print(f"  {totales['fallidos']} videos tuvieron error.")
        print("  Se reintentarán en la próxima ejecución.")
    print()


def check_actualizacion():
    """Comprueba si hay una versión más nueva de Kevin disponible (QUA-149)."""
    try:
        version_path = os.path.join(os.path.dirname(__file__), 'VERSION')
        if not os.path.exists(version_path):
            return
        with open(version_path, 'r') as f:
            local_version = f.read().strip()

        from api_client import check_version, is_api_configured
        if not is_api_configured():
            return

        result = check_version(local_version)
        if result and result.get('needs_update'):
            print(f"  ╔══════════════════════════════════════════════╗")
            print(f"  ║  HAY UNA ACTUALIZACIÓN DISPONIBLE            ║")
            print(f"  ║  Tu versión: {local_version:<10s}                       ║")
            print(f"  ║  Nueva:      {result['remote_version']:<10s}                       ║")
            print(f"  ╚══════════════════════════════════════════════╝")
            if result.get('changelog'):
                print(f"  Cambios: {result['changelog']}")
            print()
            print("  Avisa a Sara para actualizar antes de publicar.")
            print()
    except Exception:
        pass  # No bloquear si falla el check


def publicar_lote(publisher, lote_path):
    """Publica un lote y devuelve stats."""
    print("  Publicando... (esto puede tardar unos minutos)")
    print("  No cierres esta ventana ni Chrome.")
    print()
    return publisher.run_from_lote(lote_path)


def main():
    # Parsear argumentos opcionales (para Sara; operadoras usan PUBLICAR.bat sin args)
    parser = argparse.ArgumentParser(description='AutoTok Publicador')
    parser.add_argument('--cuenta', help='Cuenta a publicar (sobrescribe config_operadora)')
    args = parser.parse_args()

    limpiar_pantalla()
    mostrar_banner()

    # 0. Check de versión (no bloquea)
    check_actualizacion()

    # 1. Cargar config
    cuenta, drive_path = cargar_config()

    # Override cuenta si se pasa por argumento
    if args.cuenta:
        cuenta = args.cuenta
        print(f"  [*] Cuenta override: {cuenta}")
        print()

    # 2. Buscar TODOS los lotes pendientes
    print("  Buscando videos pendientes...")
    todos_lotes = buscar_todos_lotes_pendientes(cuenta, drive_path)

    if not todos_lotes:
        print()
        print("  No hay videos pendientes de publicar.")
        print("  Cuando Sara programe nuevos videos, aparecerán aquí.")
        print()
        input("  Pulsa ENTER para salir...")
        return 0

    # 3. Mostrar todos los lotes disponibles
    print()
    print(f"  Cuenta: {cuenta}")
    print(f"  Lotes pendientes: {len(todos_lotes)}")
    print()
    print("  ─────────────────────────────────────────────")

    total_videos = 0
    for i, lote_info in enumerate(todos_lotes):
        letra = chr(65 + i)  # A, B, C...
        fecha = lote_info['fecha']
        n = lote_info['n_pendientes']
        total = lote_info['total_videos']
        total_videos += n

        if n == total:
            print(f"    {letra})  {fecha}  —  {n} videos")
        else:
            print(f"    {letra})  {fecha}  —  {n} pendientes (de {total})")

    print()
    print(f"  Total: {total_videos} videos pendientes")
    print("  ─────────────────────────────────────────────")
    print()

    # 4. Pedir selección
    if len(todos_lotes) == 1:
        respuesta = input("  ¿Publicar? (S/N): ").strip().upper()
        if respuesta not in ('S', 'SI', 'SÍ', 'Y', 'YES', ''):
            print()
            print("  Cancelado. No se ha publicado nada.")
            print()
            input("  Pulsa ENTER para salir...")
            return 0
        seleccion = [0]
    else:
        letras_max = chr(65 + len(todos_lotes) - 1)
        print(f"  Escribe las letras de los lotes que quieres publicar.")
        print(f"  Ejemplos:  A      (solo el primero)")
        print(f"             A,C    (varios separados por coma)")
        print(f"             TODOS  (todos los pendientes)")
        print()
        respuesta = input("  Tu selección: ").strip().upper()

        if not respuesta or respuesta == 'N':
            print()
            print("  Cancelado. No se ha publicado nada.")
            print()
            input("  Pulsa ENTER para salir...")
            return 0

        if respuesta in ('TODOS', 'TODO', 'ALL', '*', 'S', 'SI', 'SÍ'):
            seleccion = list(range(len(todos_lotes)))
        else:
            # Parsear letras: "A,C" o "A C" o "AC"
            letras = [c.strip() for c in respuesta.replace(',', ' ').split()]
            # También aceptar "AC" sin separador
            if len(letras) == 1 and len(letras[0]) > 1:
                letras = list(letras[0])

            seleccion = []
            for letra in letras:
                idx = ord(letra) - 65
                if 0 <= idx < len(todos_lotes):
                    seleccion.append(idx)
                else:
                    print(f"  [!] '{letra}' no es válido, se ignora.")

            if not seleccion:
                print()
                print("  No se seleccionó ningún lote válido.")
                print()
                input("  Pulsa ENTER para salir...")
                return 0

    # Mostrar selección
    lotes_elegidos = [todos_lotes[i] for i in sorted(set(seleccion))]
    n_videos = sum(l['n_pendientes'] for l in lotes_elegidos)
    fechas = ', '.join(l['fecha'] for l in lotes_elegidos)
    print()
    print(f"  Publicando {n_videos} videos de {len(lotes_elegidos)} lote(s): {fechas}")
    print("  No cierres esta ventana ni Chrome.")

    # 5. Publicar lotes seleccionados sin interrupción
    totales = {'lotes': 0, 'exitosos': 0, 'fallidos': 0, 'saltados': 0}

    try:
        from tiktok_publisher import TikTokPublisher
        publisher = TikTokPublisher(cuenta, cdp_mode=False)

        for i, lote_info in enumerate(lotes_elegidos):
            fecha = lote_info['fecha']
            lote_path = lote_info['lote_path']
            n = lote_info['n_pendientes']

            print()
            print(f"  ── Lote {i+1}/{len(lotes_elegidos)}: {fecha} ({n} videos) ──")
            print()
            print("  Publicando...")
            print()

            stats = publisher.run_from_lote(lote_path)
            exitosos, fallidos, saltados = mostrar_resultado(stats)

            totales['lotes'] += 1
            totales['exitosos'] += exitosos
            totales['fallidos'] += fallidos
            totales['saltados'] += saltados

    except KeyboardInterrupt:
        print("\n\n  Publicación cancelada por el usuario.")
        print("  Los videos que ya se publicaron están guardados.")
        print("  Puedes volver a ejecutar para continuar con los pendientes.")
        print()
        input("  Pulsa ENTER para salir...")
        return 1
    except Exception as e:
        print(f"\n\n  Error inesperado: {e}")
        print()
        print("  Cosas que puedes probar:")
        print("  1. Abre Chrome y entra en TikTok Studio para verificar tu sesión")
        print("  2. Cierra todas las ventanas de Chrome y vuelve a ejecutar")
        print("  3. Avisa a Sara con una captura de este error")
        print()
        input("  Pulsa ENTER para salir...")
        return 1

    # 6. Resumen final
    if totales['lotes'] > 1:
        mostrar_resumen_total(totales)

    input("  Pulsa ENTER para salir...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
