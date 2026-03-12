# ⚙️ CONFIGURACIÓN DEL SISTEMA TIKTOK SHOP

# 📊 IDs DE GOOGLE SHEETS
SHEETS_CONFIG = {
    'carol_input': '1VQLzrHhWaohjOWhKFCpMpJgCupCqcrWhdWKy6TQ8ewg',
    'produccion_mar': '10D8_w6RyonnWO4VhneijHz3MIkmXWLxIkIuFJvSqpw4',
    'creditos_tracking': '1LwjsvfVk8GhOjXUJp5F1BDArtoAFhfzttJKr800j0gQ',
    'bof_learning': '1EIsD_FoQCJlPXvcFiqDx00_AEYDQWW4faBIoSzcDqrk',
    'metricas_tiktok': '1eXuPwNcHn3wy4nFmK8jkhZf2ESmjtylaaXwj78TFWx0'
}

# 💰 CONFIGURACIÓN DE COSTES
COSTES = {
    'hailuo': {
        'plan': 'Pro',
        'mensual': 27.99,  # USD
        'creditos_mes': 4500,
        'creditos_por_video': 12,  # Para 6 segundos
        'coste_por_credito': 27.99 / 4500
    },
    'heygen': {
        'plan': 'Creator',
        'mensual': 25.00,  # EUR
        'videos_mes': 'ilimitado',
        'coste_por_video': 0.00  # Ilimitado en plan manual
    }
}

# 🎯 CONFIGURACIÓN BOF
BOF_CONFIG = {
    'palabras_urgencia': [
        'solo hoy', 'última oportunidad', 'quedan pocas', 'se acaba',
        'último día', 'oferta flash', 'termina esta noche', 'antes de que suba',
        'no esperes', 'aprovecha ahora', 'últimas unidades', 'activa ahora'
    ],
    'palabras_cta': [
        'toca el carrito', 'toca el carrito naranja', 'no esperes',
        'aprovecha ahora', 'hit the cart', 'tap the cart', 'activa ya',
        'consigue el tuyo', 'no te quedes sin'
    ],
    'estructura_esperada': [
        'open_loop', 'transition', 'cta_1', 'why_should_they',
        'value_breakdown', 'close_loop', 'cta_2'
    ]
}

# 📁 RUTAS DE ARCHIVOS
CREDENTIALS_FILE = 'service_account.json'  # Credenciales Google API
LOG_FILE = 'system.log'
REPORTS_DIR = 'reports/'

# 🔧 CONFIGURACIÓN SISTEMA
DEBUG_MODE = False
AUTO_BACKUP = True
BACKUP_FREQUENCY_HOURS = 24

# 📧 EMAIL PARA NOTIFICACIONES (opcional)
NOTIFICATION_EMAIL = 'autotok@gmail.com'

# ⏰ HORARIOS DE EJECUCIÓN (para cuando se automatice completamente)
SCHEDULE = {
    'check_new_scripts': '08:00',  # Carol sube scripts por la mañana
    'generate_prompts': '08:30',   # Sistema genera prompts
    'check_mar_feedback': '18:00', # Mar termina videos por la tarde
    'analyze_learning': '19:00',   # Sistema analiza y aprende
    'generate_report': '20:00'     # Reporte diario
}
