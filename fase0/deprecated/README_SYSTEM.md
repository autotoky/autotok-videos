# 🚀 SISTEMA AUTOMATIZADO TIKTOK SHOP - FASE 0

Sistema completo de automatización para generación de videos TikTok Shop con Google Sheets + AI.

---

## 🎯 QUÉ HACE ESTE SISTEMA

### Para Carol (Custom GPT):
- ✅ Genera scripts BOF diariamente (25 scripts = 5 productos × 5 variaciones)
- ✅ Los sube a Google Sheets con un click
- ✅ El sistema lee automáticamente y procesa

### Para el Sistema (Automático):
- ✅ Lee scripts de Carol de Google Sheets
- ✅ Genera prompts optimizados para HeyGen y Hailuo
- ✅ Escribe resultados en sheet de Mar
- ✅ Analiza patrones y aprende del feedback
- ✅ Calcula costes y créditos automáticamente

### Para Mar (Ejecución):
- ✅ Lee prompts generados en su sheet
- ✅ Busca imágenes de productos
- ✅ Genera videos en HeyGen/Hailuo
- ✅ Da feedback para mejorar el sistema

### Para Ti (Monitorización):
- ✅ Estadísticas en tiempo real
- ✅ Tracking de créditos y costes
- ✅ Análisis de calidad de videos
- ✅ Reportes de aprendizaje BOF

---

## 📦 LO QUE INCLUYE

### Scripts Python:
- `main.py` - Script principal (ejecuta todo el proceso)
- `sheets_manager.py` - Gestor Google Sheets API
- `prompt_generator.py` - Generador de prompts HeyGen/Hailuo
- `bof_learning.py` - Sistema de aprendizaje BOF
- `config.py` - Configuración del sistema
- `verify_setup.py` - Verificador de setup

### Documentación:
- `SETUP_COMPLETE.md` - Guía completa de instalación
- `GUIA_GOOGLE_SHEETS.md` - Guía para Carol y Mar
- `EJEMPLOS_SHEETS.md` - Ejemplos para copiar a las sheets
- `QUICK_START.md` - Inicio rápido sin código

### Configuración:
- `requirements.txt` - Dependencias Python
- `service_account.json` - (Lo creas tú - credenciales Google)

---

## ⚡ INICIO RÁPIDO

### 1. Instalar:
```bash
pip install -r requirements.txt
```

### 2. Configurar credenciales:
Sigue `SETUP_COMPLETE.md` - Paso 2

### 3. Verificar:
```bash
python verify_setup.py
```

### 4. Ejecutar:
```bash
python main.py
```

---

## 📊 GOOGLE SHEETS

El sistema usa 5 sheets:

1. **carol_input** - Carol rellena scripts aquí
2. **produccion_mar** - Mar ejecuta desde aquí
3. **creditos_tracking** - Sistema automático
4. **bof_learning** - Sistema automático
5. **metricas_tiktok** - Para después

---

## 💰 COSTES FASE 0

```
HeyGen Creator:  €25/mes (videos ilimitados manual)
Hailuo Pro:      $28/mes (375 videos)
────────────────────────
TOTAL:           €50/mes
Por video:       €0.07
```

Sin APIs costosas, sin DALL-E, sin Claude API (por ahora).

---

## 🔄 FLUJO DIARIO

```
1. CAROL (mañana):
   └─ Genera 25 scripts BOF
   └─ Sube a Google Sheets

2. SISTEMA (automático):
   └─ Lee scripts
   └─ Genera prompts
   └─ Escribe a sheet de Mar

3. MAR (tarde):
   └─ Lee prompts
   └─ Genera 25 videos
   └─ Da feedback

4. SISTEMA (noche):
   └─ Analiza feedback
   └─ Aprende patrones
   └─ Genera reporte
```

---

## 🧠 SISTEMA DE APRENDIZAJE

El sistema analiza:
- ✅ Palabras de urgencia más usadas por Carol
- ✅ Estructura de scripts exitosos
- ✅ Patrones de CTAs efectivos
- ✅ Longitud óptima de scripts
- ✅ Feedback de calidad de Mar

Y mejora automáticamente:
- ✅ Generación de prompts
- ✅ Adaptación al estilo de Carol
- ✅ Optimización según feedback

---

## 📈 ROADMAP

### ✅ Fase 0 (Actual - Semanas 1-2):
- Manual: Carol genera, Mar ejecuta
- Sistema: Lee, genera prompts, analiza
- Objetivo: Validar 25 videos/día

### ⏳ Fase 1 (Semanas 3-4):
- Mixto: 25 manual + 20 API
- Mejora prompts con feedback
- Sistema aprende patrones

### ⏳ Fase 2 (Semana 5+):
- Automático: 100 videos/día
- Sistema genera scripts BOF solo
- Full automatización

---

## 🆘 SOPORTE

### Si algo no funciona:

1. **Primero:** `python verify_setup.py`
2. **Lee:** `SETUP_COMPLETE.md`
3. **Revisa:** Los mensajes de error
4. **Test individual:**
   ```bash
   python sheets_manager.py     # Test conexión
   python prompt_generator.py   # Test prompts
   python bof_learning.py       # Test aprendizaje
   ```

### Errores comunes:
- "No module named X" → `pip install -r requirements.txt`
- "service_account.json not found" → Sigue PASO 2 del setup
- "Permission denied" → Da permisos Editor al service account en TODAS las sheets
- "API not enabled" → Activa APIs en Google Cloud Console

---

## 🔒 SEGURIDAD

**CRÍTICO:**
- ❌ NO compartas `service_account.json`
- ❌ NO lo subas a GitHub
- ✅ Guárdalo solo en tu computadora
- ✅ Haz backup encriptado

---

## 📞 ESTRUCTURA DEL PROYECTO

```
tiktok-shop-automation/
│
├── 🐍 PYTHON SCRIPTS
│   ├── main.py                    # Script principal
│   ├── sheets_manager.py          # Google Sheets
│   ├── prompt_generator.py        # Generador prompts
│   ├── bof_learning.py            # Aprendizaje
│   ├── config.py                  # Configuración
│   └── verify_setup.py            # Verificador
│
├── 📄 DOCUMENTACIÓN
│   ├── README.md                  # Este archivo
│   ├── SETUP_COMPLETE.md          # Setup completo
│   ├── GUIA_GOOGLE_SHEETS.md     # Guía sheets
│   ├── EJEMPLOS_SHEETS.md        # Ejemplos
│   └── QUICK_START.md            # Inicio rápido
│
├── ⚙️  CONFIGURACIÓN
│   ├── requirements.txt           # Dependencias
│   └── service_account.json       # Credenciales (TÚ LO CREAS)
│
└── 📊 GOOGLE SHEETS (externos)
    ├── carol_input
    ├── produccion_mar
    ├── creditos_tracking
    ├── bof_learning
    └── metricas_tiktok
```

---

## 🎓 APRENDIZAJE CONTINUO

El sistema mejora cada día:

**Día 1-7:**
- Aprende estilo de Carol
- Identifica palabras clave
- Analiza estructura

**Día 8-14:**
- Compara con feedback de Mar
- Ajusta generación de prompts
- Optimiza patrones

**Día 15-30:**
- Genera scripts similares a Carol
- Predice calidad de videos
- Auto-optimización continua

**Día 30+:**
- Sistema maduro
- Genera contenido autónomo
- Escala a 100+ videos/día

---

## 💡 MEJORAS FUTURAS

### Corto plazo (2-3 días):
- ✅ Prompts mejorados con info HeyGen/Hailuo
- ✅ Análisis más profundo de feedback

### Medio plazo (1-2 semanas):
- ⏳ Sistema genera scripts BOF automáticamente
- ⏳ Integración métricas TikTok
- ⏳ Predicción de performance

### Largo plazo (1 mes+):
- ⏳ API HeyGen/Hailuo (100% automático)
- ⏳ A/B testing automático
- ⏳ Optimización por conversiones

---

## 📊 MÉTRICAS DE ÉXITO

### Fase 0:
- ✅ 25 videos/día generados
- ✅ Calidad promedio > 3.5/5
- ✅ Carol gasta < 2h/día
- ✅ Mar gasta < 4h/día
- ✅ Conversión TikTok > 0

### Fase 1:
- ⏳ 45 videos/día
- ⏳ Calidad > 4/5
- ⏳ Sistema genera prompts indistinguibles de humanos

### Fase 2:
- ⏳ 100 videos/día
- ⏳ Full automatización
- ⏳ ROI > 400%

---

## 🤝 EQUIPO

- **Carol:** Generación scripts BOF (Custom GPT)
- **Mar:** Ejecución manual videos + Feedback
- **Sistema:** Automatización + Aprendizaje
- **Tú:** Monitorización + Estrategia

---

## 🎉 EMPEZAR

```bash
# 1. Instalar
pip install -r requirements.txt

# 2. Configurar (sigue SETUP_COMPLETE.md)
# ... crear service_account.json
# ... dar permisos sheets

# 3. Verificar
python verify_setup.py

# 4. ¡Ejecutar!
python main.py
```

---

**¡A automatizar TikTok Shop!** 🚀📱💰
