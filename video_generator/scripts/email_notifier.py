#!/usr/bin/env python3
"""
EMAIL_NOTIFIER.PY - Notificaciones por email (QUA-41)

Envía reporte de publicación por Gmail SMTP.
Destinatarios: Sara + operadora configurada.

Uso:
    from scripts.email_notifier import enviar_reporte_publicacion
    enviar_reporte_publicacion(reporte_dict)
"""

import smtplib
import json
import os
import logging
import base64
from datetime import datetime

log = logging.getLogger("autotok.email")

# Ruta al config
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_publisher.json")


def _cargar_config_completa():
    """Carga config_publisher.json completo."""
    if not os.path.exists(CONFIG_PATH):
        log.warning(f"Config no encontrado: {CONFIG_PATH}")
        return None

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _cargar_config_email():
    """Carga la sección 'email' de config_publisher.json."""
    config = _cargar_config_completa()
    if not config:
        return None

    email_config = config.get('email')
    if not email_config:
        log.debug("Sección 'email' no encontrada en config")
        return None

    if not email_config.get('enabled', False):
        log.info("Email desactivado en config (enabled=false)")
        return None

    # Validar campos requeridos
    required = ['smtp_server', 'smtp_port', 'from_email', 'app_password', 'admin_email']
    for field in required:
        if not email_config.get(field):
            log.warning(f"Campo email requerido vacío: {field}")
            return None

    return email_config


def _resolver_destinatarios(cuenta):
    """Construye lista de destinatarios: operadora de la cuenta + admin (Sara) siempre.

    Args:
        cuenta: Nombre de la cuenta TikTok (ej: 'ofertastrendy20')

    Returns:
        list[str]: Emails únicos de destinatarios
    """
    config = _cargar_config_completa()
    if not config:
        return []

    email_config = config.get('email', {})
    admin_email = email_config.get('admin_email', '')

    destinatarios = set()

    # 1. Admin (Sara) siempre recibe
    if admin_email:
        destinatarios.add(admin_email)

    # 2. Email de la operadora de esta cuenta
    cuenta_config = config.get('cuentas', {}).get(cuenta, {})
    operadora_email = cuenta_config.get('email', '')
    if operadora_email:
        destinatarios.add(operadora_email)

    return list(destinatarios)


def _generar_asunto(reporte):
    """Genera el asunto del email según resultado."""
    cuenta = reporte.get('cuenta', '?')
    total = reporte.get('total', 0)
    exitosos = reporte.get('exitosos', 0)
    fallidos = reporte.get('fallidos', 0)

    if reporte.get('todo_ok'):
        return f"✅ AutoTok [{cuenta}]: {exitosos}/{total} videos publicados OK"
    else:
        return f"❌ AutoTok [{cuenta}]: {fallidos} error(es) de {total} videos"


_ERROR_LABELS = {
    'tiktok_schedule_limit': 'Límite de TikTok alcanzado',
    'login_failed': 'Sesión caducada',
    'upload_failed': 'Error al subir video',
    'file_not_found': 'Archivo no encontrado',
    'schedule_failed': 'Error al programar',
    'navigation_error': 'Error de navegación',
    'timeout': 'Tiempo de espera agotado',
    'product_search_failed': 'Producto no encontrado',
    'validation_failed': 'Datos incompletos',
    'unknown': 'Error desconocido',
}


def _generar_html(reporte):
    """Genera el cuerpo HTML del email."""
    cuenta = reporte.get('cuenta', '?')
    session_id = reporte.get('session_id', '?')
    total = reporte.get('total', 0)
    exitosos = reporte.get('exitosos', 0)
    fallidos = reporte.get('fallidos', 0)
    saltados = reporte.get('saltados', 0)
    todo_ok = reporte.get('todo_ok', False)

    # Color del encabezado
    header_color = '#2e7d32' if todo_ok else '#c62828'
    header_emoji = '✅' if todo_ok else '❌'

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: {header_color}; color: white; padding: 15px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">{header_emoji} Reporte AutoTok — {cuenta}</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">Sesión: {session_id}</p>
        </div>

        <div style="background-color: #f5f5f5; padding: 15px; border: 1px solid #ddd;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Total videos</td>
                    <td style="padding: 8px; text-align: right;">{total}</td>
                </tr>
                <tr style="background-color: #e8f5e9;">
                    <td style="padding: 8px;">✅ Exitosos</td>
                    <td style="padding: 8px; text-align: right; font-weight: bold; color: #2e7d32;">{exitosos}</td>
                </tr>
                <tr style="background-color: #ffebee;">
                    <td style="padding: 8px;">❌ Fallidos</td>
                    <td style="padding: 8px; text-align: right; font-weight: bold; color: #c62828;">{fallidos}</td>
                </tr>
                <tr>
                    <td style="padding: 8px;">⏭ Saltados</td>
                    <td style="padding: 8px; text-align: right;">{saltados}</td>
                </tr>
            </table>
        </div>
    """

    # Errores detallados
    errores_por_tipo = reporte.get('errores_por_tipo', {})
    sugerencias = reporte.get('sugerencias', {})

    if errores_por_tipo:
        html += """
        <div style="background-color: #fff3e0; padding: 15px; border: 1px solid #ddd; border-top: none;">
            <h3 style="margin-top: 0; color: #e65100;">Errores detallados</h3>
        """
        for error_type, videos_err in errores_por_tipo.items():
            label = _ERROR_LABELS.get(error_type, error_type)
            html += f"""
            <div style="margin-bottom: 12px; padding: 10px; background: white; border-left: 4px solid #e65100; border-radius: 4px;">
                <strong>{label}</strong>
                <span style="color: #666;">({len(videos_err)} video{'s' if len(videos_err) > 1 else ''})</span>
                <ul style="margin: 5px 0; padding-left: 20px;">
            """
            for v in videos_err:
                vid = v.get('video_id', '?')
                msg = v.get('error_message', '')
                msg_corto = msg.split('\n')[0][:80] if msg else ''
                html += f"<li><code>{vid}</code>: {msg_corto}</li>\n"

            sugerencia = sugerencias.get(error_type, '')
            html += f"""
                </ul>
                <p style="margin: 5px 0 0 0; color: #1565c0; font-style: italic;">
                    💡 {sugerencia}
                </p>
            </div>
            """

        html += "</div>"

    # Footer
    html += f"""
        <div style="padding: 10px; text-align: center; color: #999; font-size: 12px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 8px 8px;">
            AutoTok Publisher — {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </body>
    </html>
    """
    return html


def _generar_texto_plano(reporte):
    """Genera versión texto plano del reporte."""
    cuenta = reporte.get('cuenta', '?')
    session_id = reporte.get('session_id', '?')
    total = reporte.get('total', 0)
    exitosos = reporte.get('exitosos', 0)
    fallidos = reporte.get('fallidos', 0)
    saltados = reporte.get('saltados', 0)

    lines = [
        f"REPORTE AUTOTOK — {cuenta}",
        f"Sesión: {session_id}",
        "=" * 40,
        f"Total:    {total}",
        f"Exitosos: {exitosos}",
        f"Fallidos: {fallidos}",
        f"Saltados: {saltados}",
    ]

    errores_por_tipo = reporte.get('errores_por_tipo', {})
    sugerencias = reporte.get('sugerencias', {})

    if errores_por_tipo:
        lines.append("")
        lines.append("ERRORES:")
        lines.append("-" * 40)

        for error_type, videos_err in errores_por_tipo.items():
            label = _ERROR_LABELS.get(error_type, error_type)
            lines.append(f"\n{label.upper()} ({len(videos_err)} videos):")
            for v in videos_err:
                vid = v.get('video_id', '?')
                msg = v.get('error_message', '')
                msg_corto = msg.split('\n')[0][:80] if msg else ''
                lines.append(f"  - {vid}: {msg_corto}")
            sugerencia = sugerencias.get(error_type, '')
            lines.append(f"  -> Sugerencia: {sugerencia}")

    return "\n".join(lines)


def enviar_reporte_publicacion(reporte):
    """Envía el reporte de publicación por email.

    Destinatarios: operadora de la cuenta + Sara (admin) siempre.

    Args:
        reporte: dict generado por TikTokPublisher._generar_reporte_dict()

    Returns:
        bool: True si se envió correctamente
    """
    config = _cargar_config_email()
    if not config:
        return False

    # Resolver destinatarios según la cuenta
    cuenta = reporte.get('cuenta', '')
    destinatarios = _resolver_destinatarios(cuenta)

    if not destinatarios:
        log.warning("  No hay destinatarios configurados para esta cuenta")
        return False

    asunto = _generar_asunto(reporte)
    html = _generar_html(reporte)
    texto = _generar_texto_plano(reporte)

    # Construir email RAW a mano — 100% ASCII, sin usar as_string() ni
    # MIMEText ni EmailMessage que fallan con acentos en Python
    # Todo el contenido no-ASCII va en base64
    boundary = f"====AutoTok_{datetime.now().strftime('%Y%m%d%H%M%S')}===="

    # Subject en RFC2047 B-encoding (base64)
    subject_b64 = base64.b64encode(asunto.encode('utf-8')).decode('ascii')
    subject_encoded = f"=?utf-8?B?{subject_b64}?="

    # Body parts en base64
    texto_b64 = base64.b64encode(texto.encode('utf-8')).decode('ascii')
    html_b64 = base64.b64encode(html.encode('utf-8')).decode('ascii')

    raw_email = (
        f"From: {config['from_email']}\r\n"
        f"To: {', '.join(destinatarios)}\r\n"
        f"Subject: {subject_encoded}\r\n"
        f"MIME-Version: 1.0\r\n"
        f"Content-Type: multipart/alternative; boundary=\"{boundary}\"\r\n"
        f"\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n"
        f"Content-Transfer-Encoding: base64\r\n"
        f"\r\n"
        f"{texto_b64}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Transfer-Encoding: base64\r\n"
        f"\r\n"
        f"{html_b64}\r\n"
        f"--{boundary}--\r\n"
    )

    try:
        log.info(f"  Enviando email a: {', '.join(destinatarios)}")

        # DEBUG: verificar que todo es ASCII antes de enviar
        try:
            raw_bytes = raw_email.encode('ascii')
            log.info(f"  Raw email: {len(raw_bytes)} bytes, 100% ASCII OK")
        except UnicodeEncodeError as ue:
            log.error(f"  RAW tiene non-ASCII en pos {ue.start}: ...{ue.object[max(0,ue.start-10):ue.start+10]!r}...")
            raise

        with smtplib.SMTP(config['smtp_server'], config['smtp_port'],
                          local_hostname='localhost') as server:
            log.info("  SMTP conectado")
            server.starttls()
            log.info("  STARTTLS OK")
            server.login(config['from_email'], config['app_password'])
            log.info("  Login OK")
            server.sendmail(config['from_email'], destinatarios, raw_bytes)
            log.info("  sendmail OK")

        log.info(f"  ✅ Email enviado correctamente")
        return True

    except smtplib.SMTPAuthenticationError:
        log.error("  ❌ Error de autenticación SMTP — verifica app_password en config")
        return False
    except smtplib.SMTPException as e:
        log.error(f"  ❌ Error SMTP: {e}")
        return False
    except Exception as e:
        import traceback
        log.error(f"  ❌ Error enviando email: {e}")
        log.error(f"  Traceback completo:")
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Test rápido con reporte de ejemplo
    logging.basicConfig(level=logging.INFO)

    # Importar sugerencias del publisher para que el test sea realista
    try:
        from tiktok_publisher import TikTokPublisher
        _sugg = TikTokPublisher._error_suggestion
    except Exception:
        _sugg = lambda t: 'Contacta a Sara'

    reporte_test = {
        'session_id': '20260303_120000',
        'cuenta': 'totokydeals',
        'total': 8,
        'exitosos': 5,
        'fallidos': 2,
        'saltados': 1,
        'todo_ok': False,
        'errores_por_tipo': {
            'timeout': [
                {'video_id': 'VIDEO_perro_01', 'error_message': 'Page.goto timeout after 30000ms'},
            ],
            'schedule_failed': [
                {'video_id': 'VIDEO_gato_03', 'error_message': 'No se pudo seleccionar la fecha en el calendario'},
            ],
        },
        'sugerencias': {
            'timeout': _sugg('timeout'),
            'schedule_failed': _sugg('schedule_failed'),
        }
    }

    print("Asunto:", _generar_asunto(reporte_test))
    print()
    print(_generar_texto_plano(reporte_test))
    print()

    # Enviar de verdad si hay config
    config = _cargar_config_email()
    if config:
        print("Enviando email de prueba...")
        ok = enviar_reporte_publicacion(reporte_test)
        if ok:
            print("✅ Email enviado — revisa tu bandeja de entrada")
        else:
            print("❌ Email no se pudo enviar — revisa el log arriba")
    else:
        print("(Email no configurado — revisa config_publisher.json)")
