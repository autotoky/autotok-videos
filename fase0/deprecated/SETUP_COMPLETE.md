# 🛠️ SETUP COMPLETO DEL SISTEMA

## 📋 ANTES DE EMPEZAR

Este sistema conecta automáticamente con Google Sheets para:
- ✅ Leer scripts de Carol
- ✅ Generar prompts optimizados
- ✅ Escribir resultados para Mar
- ✅ Analizar y aprender de feedback
- ✅ Calcular costes automáticamente

---

## ⚙️ PASO 1: INSTALAR DEPENDENCIAS

### En tu computadora local:

```bash
# Instalar Python (si no lo tienes)
# Descarga desde: https://www.python.org/downloads/
# Versión recomendada: 3.9 o superior

# Instalar dependencias
pip install -r requirements.txt
```

Si da error, prueba:
```bash
pip3 install -r requirements.txt
```

### Verificar instalación:
```bash
python -c "import gspread; print('✅ gspread instalado')"
```

---

## 🔑 PASO 2: CREAR CREDENCIALES GOOGLE API

### 2.1 Crear Proyecto en Google Cloud

1. Ve a: https://console.cloud.google.com/
2. Crea nuevo proyecto:
   - Click "Select a project" (arriba)
   - Click "NEW PROJECT"
   - Nombre: `TikTok Shop Automation`
   - Click "CREATE"

### 2.2 Activar Google Sheets API

1. En el proyecto, ve a: "APIs & Services" → "Library"
2. Busca: `Google Sheets API`
3. Click en el resultado
4. Click "ENABLE"
5. Repite con: `Google Drive API`

### 2.3 Crear Service Account

1. Ve a: "APIs & Services" → "Credentials"
2. Click "CREATE CREDENTIALS" → "Service account"
3. Rellena:
   - Service account name: `tiktok-bot`
   - Service account ID: `tiktok-bot` (auto-genera)
   - Click "CREATE AND CONTINUE"
4. En "Grant this service account access to project":
   - Role: Select `Editor`
   - Click "CONTINUE"
5. Click "DONE"

### 2.4 Crear y Descargar Key

1. En la lista de Service Accounts, click en el que acabas de crear
2. Ve a tab "KEYS"
3. Click "ADD KEY" → "Create new key"
4. Selecciona formato: `JSON`
5. Click "CREATE"
6. Se descargará un archivo JSON

### 2.5 Guardar Credenciales

1. Renombra el archivo descargado a: `service_account.json`
2. Muévelo a la carpeta del proyecto (donde están todos los scripts .py)
3. **IMPORTANTE:** Este archivo es secreto, no lo compartas

---

## 📊 PASO 3: DAR PERMISOS AL SERVICE ACCOUNT EN SHEETS

### 3.1 Encontrar Email del Service Account

Abre el archivo `service_account.json` y busca:
```json
{
  "client_email": "tiktok-bot@proyecto-xxxxx.iam.gserviceaccount.com"
}
```

Copia ese email (será algo como `tiktok-bot@proyecto-xxxxx.iam.gserviceaccount.com`)

### 3.2 Compartir CADA Google Sheet

Para cada una de las 5 sheets:

1. **carol_input**: https://docs.google.com/spreadsheets/d/1eXuPwNcHn3wy4nFmK8jkhZf2ESmjtylaaXwj78TFWx0
2. **produccion_mar**: https://docs.google.com/spreadsheets/d/1EIsD_FoQCJlPXvcFiqDx00_AEYDQWW4faBIoSzcDqrk
3. **creditos_tracking**: https://docs.google.com/spreadsheets/d/1LwjsvfVk8GhOjXUJp5F1BDArtoAFhfzttJKr800j0gQ
4. **bof_learning**: https://docs.google.com/spreadsheets/d/10D8_w6RyonnWO4VhneijHz3MIkmXWLxIkIuFJvSqpw4
5. **metricas_tiktok**: https://docs.google.com/spreadsheets/d/1VQLzrHhWaohjOWhKFCpMpJgCupCqcrWhdWKy6TQ8ewg

Haz esto para cada una:
1. Abre el sheet
2. Click botón "Share" (arriba derecha)
3. Pega el email del service account
4. Selecciona permiso: **Editor**
5. **IMPORTANTE:** Desmarca "Notify people" (no queremos email de notificación)
6. Click "Share"

### Verificar Permisos:

Deberías ver el service account en la lista de "Who has access" de cada sheet.

---

## ✅ PASO 4: VERIFICAR CONEXIÓN

```bash
python sheets_manager.py
```

Si todo está bien, verás:
```
✅ Conectado a Google Sheets exitosamente
✅ Sheets conectadas: ['carol_input', 'produccion_mar', ...]
✅ Registros en carol_input: X
```

Si hay error:
- Verifica que `service_account.json` esté en la carpeta correcta
- Verifica que diste permisos de Editor a TODAS las sheets
- Verifica que las APIs estén activadas en Google Cloud

---

## 🚀 PASO 5: PROBAR EL SISTEMA

### Test Rápido:

```bash
python main.py
```

Debería:
- ✅ Conectar con sheets
- ✅ Leer datos de Carol (si los hay)
- ✅ Generar prompts
- ✅ Escribir a sheet de Mar
- ✅ Mostrar estadísticas

### Test Individual de Módulos:

```bash
# Test generador de prompts
python prompt_generator.py

# Test sistema de aprendizaje BOF
python bof_learning.py

# Test conexión sheets
python sheets_manager.py
```

---

## 📁 ESTRUCTURA DE ARCHIVOS

Tu carpeta debe verse así:

```
tiktok-shop-automation/
├── config.py                    # Configuración del sistema
├── sheets_manager.py            # Gestor Google Sheets
├── prompt_generator.py          # Generador de prompts
├── bof_learning.py              # Sistema aprendizaje BOF
├── main.py                      # Script principal
├── requirements.txt             # Dependencias Python
├── service_account.json         # ⚠️  CREDENCIALES (NO COMPARTIR)
├── GUIA_GOOGLE_SHEETS.md       # Guía para Carol y Mar
├── EJEMPLOS_SHEETS.md          # Ejemplos para copiar
└── QUICK_START.md              # Inicio rápido
```

---

## 🔄 USO DIARIO

### Cuando Carol Sube Nuevos Scripts:

```bash
python main.py
```

Esto automáticamente:
1. Lee los scripts de Carol
2. Genera prompts optimizados
3. Los escribe en la sheet de Mar
4. Calcula créditos
5. Muestra estadísticas

### Manual - Proceso por Pasos:

Si prefieres ejecutar paso a paso:

```bash
# Solo generar prompts
python prompt_generator.py

# Solo analizar feedback
python bof_learning.py

# Solo ver estadísticas
python sheets_manager.py
```

---

## 🐛 TROUBLESHOOTING

### Error: "No module named 'gspread'"
**Solución:** Instala dependencias
```bash
pip install -r requirements.txt
```

### Error: "service_account.json not found"
**Solución:** 
- Verifica que el archivo esté en la carpeta correcta
- Verifica que se llame exactamente `service_account.json`

### Error: "Permission denied" al leer sheets
**Solución:**
- Verifica que diste permisos de Editor al service account en TODAS las sheets
- Usa el email exacto del service account

### Error: "API has not been enabled"
**Solución:**
- Ve a Google Cloud Console
- Activa Google Sheets API
- Activa Google Drive API

### Scripts de Carol no se leen
**Solución:**
- Verifica que la sheet "carol_input" tenga datos
- Verifica que las columnas tengan los nombres exactos
- Ejecuta: `python sheets_manager.py` para debug

### Prompts no se generan bien
**Solución:**
- Los prompts son genéricos por ahora
- En 2-3 días los mejoraremos con info de HeyGen/Hailuo
- Si necesitas cambiar algo, edita `prompt_generator.py`

---

## 📞 SIGUIENTES PASOS

1. ✅ Setup completo
2. ✅ Carol empieza a rellenar scripts
3. ✅ Sistema genera prompts automáticamente
4. ✅ Mar usa prompts para crear videos
5. ⏳ **En 2-3 días:** Mejoramos prompts con feedback
6. ⏳ **En 1-2 semanas:** Sistema aprende del feedback
7. ⏳ **En 3-4 semanas:** Sistema genera scripts BOF automáticamente

---

## 🆘 SOPORTE

Si algo no funciona:

1. Revisa esta guía paso a paso
2. Ejecuta los tests individuales
3. Revisa los mensajes de error
4. Si persiste, contacta con quien configuró el sistema

---

## 🔒 SEGURIDAD

**IMPORTANTE:**
- ❌ NO compartas el archivo `service_account.json`
- ❌ NO lo subas a GitHub o repositorios públicos
- ❌ NO lo envíes por email
- ✅ Manténlo solo en tu computadora local
- ✅ Haz backup en lugar seguro (encriptado)

Si se compromete:
1. Ve a Google Cloud Console
2. Elimina el Service Account
3. Crea uno nuevo
4. Repite el proceso de permisos

---

**¡Listo para automatizar!** 🚀
