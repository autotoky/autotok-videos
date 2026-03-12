#!/usr/bin/env python3
"""
Debug: Captura TODAS las URLs que TikTok Studio llama al programar un video.
Esto nos ayuda a identificar el endpoint correcto para QUA-78.

Uso: Abre TikTok Studio manualmente, sube un video, configura todo, y
ANTES de hacer click en Schedule/Programar, ejecuta este script.
Luego haz click en Schedule/Programar manualmente y espera 10 segundos.
El script mostrará todas las URLs capturadas.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from playwright.sync_api import sync_playwright

print("Conectando al Chrome abierto (puerto 9222)...")
pw = sync_playwright().start()

try:
    browser = pw.chromium.connect_over_cdp("http://localhost:9222")
    contexts = browser.contexts
    if not contexts:
        print("[!] No hay contextos de Chrome abiertos")
        sys.exit(1)

    # Buscar la pestaña de TikTok Studio
    page = None
    for ctx in contexts:
        for p in ctx.pages:
            if 'tiktok' in p.url.lower():
                page = p
                break
        if page:
            break

    if not page:
        print("[!] No se encontró pestaña de TikTok Studio")
        print("    Pestañas abiertas:")
        for ctx in contexts:
            for p in ctx.pages:
                print(f"      {p.url}")
        sys.exit(1)

    print(f"Pestaña encontrada: {page.url[:80]}")
    print()
    print("=" * 70)
    print("  Ahora haz click en 'Schedule' / 'Programar' en TikTok Studio")
    print("  Capturando URLs durante 15 segundos...")
    print("=" * 70)
    print()

    captured = []

    def on_response(response):
        url = response.url
        status = response.status
        # Filtrar assets estáticos
        skip = ('.js', '.css', '.png', '.jpg', '.gif', '.svg', '.woff', '.ico', 'google', 'analytics', 'sentry')
        if any(s in url.lower() for s in skip):
            return
        captured.append((status, url))
        # Intentar leer body si es JSON
        content_type = response.headers.get('content-type', '')
        body_preview = ''
        if 'json' in content_type:
            try:
                body = response.json()
                body_preview = str(body)[:200]
            except Exception:
                body_preview = '(no JSON)'
        print(f"  [{status}] {url[:120]}")
        if body_preview:
            print(f"         BODY: {body_preview}")

    page.on('response', on_response)

    time.sleep(15)

    page.remove_listener('response', on_response)

    print()
    print(f"Total URLs capturadas: {len(captured)}")
    print()
    print("URLs con 'post', 'item', 'create', 'publish', 'schedule' en ellas:")
    keywords = ['post', 'item', 'create', 'publish', 'schedule', 'upload']
    for status, url in captured:
        if any(kw in url.lower() for kw in keywords):
            print(f"  *** [{status}] {url}")

except Exception as e:
    print(f"Error: {e}")
finally:
    pw.stop()
