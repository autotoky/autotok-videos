# 🎬 AUTOTOK - SISTEMA DE GENERACIÓN VIDEOS TIKTOK v3.5

**Versión:** 3.5  
**Fecha:** 2026-02-12  
**Sistema:** Generación con variantes + tracking inteligente

---

## 🆕 **NOVEDADES VERSIÓN 3.5**

### ✅ **Sistema de Variantes por BOF**
- 1 BOF (Bottom of Funnel) = 1 Oferta con múltiples variantes de overlay
- Cada variante es exclusiva del BOF
- Tracking global: Hook + Variante nunca se repite

### ✅ **Auto-registro de Audios**
- Convención: `bof1_nombre.mp3` vincula automáticamente al BOF
- Un solo comando escanea hooks + brolls + audios

### ✅ **Programación Inteligente**
- Distancia mínima entre hooks: 12 publicaciones
- Gap mínimo entre videos: 1 hora
- Formato fecha compatible Windows: `DD-MM-YYYY`

### ✅ **Workflow Simplificado**
- Importar BOF con variantes desde JSON
- Sincronización automática con Google Sheets
- Gestión estados: Generado → Calendario → Borrador → Programado → Descartado

---

## 📋 **ESTRUCTURA DEL PROYECTO**

```
video_generator/
├── main.py                      # Generador principal
├── generator.py                 # Lógica generación con variantes
├── programador.py               # Programación calendario
├── mover_videos.py              # Sincronización con Sheet
├── config.py                    # Configuración global
├── config_cuentas.json          # Config cuentas TikTok
├── utils.py                     # Utilidades FFmpeg
├── migrate_to_v3.py             # Script migración
├── diagnostico.py               # Diagnóstico videos
├── fix_paths.py                 # Corrección paths
├── PLANTILLA_BOF.json           # Plantilla BOF
├── credentials.json             # Google Sheets API
├── scripts/
│   ├── db_config.py             # Schema DB SQLite
│   ├── import_bof.py            # Importar BOF + variantes
│   ├── scan_material.py         # Escanear hooks/brolls/audios
│   ├── validate_bof.py          # Validar requisitos mínimos
│   └── register_audio.py        # [OBSOLETO] Usar scan_material
└── deprecated/                  # Archivos legacy
```

---

## 🚀 **INSTALACIÓN**

### **1. Requisitos del Sistema**
- Python 3.7+
- FFmpeg instalado y en PATH
- Google Drive Desktop sincronizado
- Credenciales Google Sheets API

### **2. Instalar Dependencias**
```bash
pip install -r requirements.txt
```

### **3. Configurar Google Drive**
Edita `config.py`:
```python
GOOGLE_DRIVE_PATH = r"G:\Mi unidad"
OUTPUT_DIR = "C:/Users/TuUsuario/Videos/videos_generados_py"
```

### **4. Estructura en Drive**
```
Mi unidad/recursos_videos/
├── proyector_magcubic/
│   ├── hooks/      # Clips intro 3.5s
│   ├── brolls/     # Clips producto 3.5s
│   └── audios/     # Voice-overs (nombrados bofN_*.mp3)
├── melatonina/
└── ...
```

---

## 🎯 **WORKFLOW COMPLETO**

### **PASO 1: Preparar Material**

**En Google Drive:**
1. Subir 10+ hooks a `hooks/`
2. Subir 20+ brolls a `brolls/` (nombrados: `A_clip.mp4`, `B_clip.mp4`, etc.)
3. Subir 5+ audios a `audios/` (nombrados: `bof1_andaluz.mp3`, `bof1_chavalita.mp3`, etc.)

**Esperar sincronización Drive**

---

### **PASO 2: Validar Material**
```bash
python scripts/validate_bof.py proyector_magcubic
```

**Requisitos mínimos:**
- ✅ 10 hooks
- ✅ 20 brolls (6 grupos diferentes)
- ✅ 5 variantes por BOF
- ✅ 3 audios por BOF

---

### **PASO 3: Crear BOF**

**3.1. Duplicar plantilla:**
```bash
cp PLANTILLA_BOF.json bof_proyector_magcubic.json
```

**3.2. Rellenar información:**
```json
{
  "deal_math": "2x1 + Envío gratis",
  "guion_audio": "¿Buscas proyector 4K?...",
  "hashtags": "#proyector #4k #ofertas",
  "url_producto": "https://amzn.to/link",
  "variantes": [
    {
      "overlay_line1": "PROYECTOR 4K",
      "overlay_line2": "2X1 HOY",
      "seo_text": "Proyector 4K oferta 2x1 🔥"
    },
    // ... mínimo 5 variantes
  ]
}
```

**3.3. Importar BOF:**
```bash
python scripts/import_bof.py proyector_magcubic bof_proyector_magcubic.json
```

---

### **PASO 4: Escanear Material**
```bash
python scripts/scan_material.py proyector_magcubic
```

**Registra automáticamente:**
- ✅ Hooks → DB
- ✅ Brolls → DB (con grupos)
- ✅ Audios → DB (vinculados a BOF según nombre `bofN_*.mp3`)

---

### **PASO 5: Generar Videos**
```bash
python main.py --producto proyector_magcubic --batch 20 --cuenta lotopdevicky
```

**Output:** 20 videos en `videos_generados_py/lotopdevicky/`

**Cada video usa:**
- 1 Hook (menos usado)
- 1 Variante (disponible para ese hook)
- 1 Audio (del BOF)
- 3-6 Brolls (según duración audio)

---

### **PASO 6: Programar Calendario**
```bash
python programador.py --cuenta lotopdevicky --dias 7 --test
```

**Aplica reglas:**
- ✅ Distancia hooks: mínimo 12 publicaciones
- ✅ Gap publicaciones: mínimo 1h
- ✅ Max mismo producto/día: 2 videos
- ✅ Formato fecha: `DD-MM-YYYY`

**Output:**
- Videos movidos a `calendario/DD-MM-YYYY/`
- Añadidos a Google Sheet TEST
- Estado DB: `'En Calendario'`

---

### **PASO 7: Gestión Estados (Google Sheet)**

**En Google Sheet, cambiar estados:**
- `En Calendario` → `Borrador` (subido a TikTok Studio)
- `Borrador` → `Programado` (programado en TikTok)
- `Borrador` → `Descartado` (no publicar)

**Sincronizar:**
```bash
python mover_videos.py --cuenta lotopdevicky --sync --test
```

**Mueve videos físicamente:**
- `calendario/` → `borrador/`
- `borrador/` → `programados/`
- `borrador/` → `descartados/`

---

## 🔧 **COMANDOS ÚTILES**

### **Ver Estadísticas**
```bash
python main.py --producto proyector_magcubic --cuenta lotopdevicky --stats
```

### **Diagnosticar Videos**
```bash
python diagnostico.py lotopdevicky
```

### **Listar Productos**
```bash
python main.py --list-productos
```

### **Ver Configuración**
```bash
python main.py --config
```

---

## 📝 **CONVENCIONES DE NOMBRES**

### **Hooks:**
```
hook_boom_START2.mp4        # Empieza desde segundo 2
hook_patas.mp4              # Empieza desde 0
```

### **Brolls (con grupos):**
```
A_producto_frente.mp4       # Grupo A
B_mano_sosteniendo.mp4      # Grupo B
C_fondo_blanco.mp4          # Grupo C
```

### **Audios (vinculados a BOF):**
```
bof1_andaluz.mp3            # BOF ID 1
bof1_chavalita.mp3          # BOF ID 1
bof2_voz_seria.mp3          # BOF ID 2
```

---

## ⚙️ **CONFIGURACIÓN AVANZADA**

**Edita `config.py`:**
```python
# Videos por lote
BATCH_SIZE = 50

# Duración hook
DEFAULT_HOOK_DURATION = 3.5

# Duración clips broll
BROLL_CLIP_DURATION = 3.5
MIN_BROLL_CLIPS = 2
MAX_BROLL_CLIPS = 4

# Sistema de grupos
USE_BROLL_GROUPS = True

# Calidad video
PRESET = "fast"
CRF = 23
```

**Edita `config_cuentas.json`:**
```json
{
  "lotopdevicky": {
    "videos_por_dia": 5,
    "max_mismo_producto_por_dia": 2,
    "distancia_minima_hook": 12,
    "gap_minimo_horas": 1.0,
    "horario_inicio": "08:00",
    "horario_fin": "21:30",
    "overlay_style": "borde_glow"
  }
}
```

---

## 🆘 **TROUBLESHOOTING**

### **"No se encontraron hooks/brolls/audios"**
- Verifica sincronización Google Drive
- Revisa rutas en `config.py`
- Ejecuta `python scripts/scan_material.py PRODUCTO`

### **"No hay variantes disponibles"**
- Añade más variantes al BOF
- Importa nuevo BOF: `python scripts/import_bof.py PRODUCTO bof.json`

### **"Sin overlays disponibles"**
- Verifica que BOF tiene mínimo 5 variantes
- Cada hook puede usar cada variante solo una vez

### **"Videos sin fecha válida" en mover_videos**
- Verifica columna "Fecha" en Sheet tiene formato `DD-MM-YYYY`
- Sin barras `/`, usar guiones `-`

---

## 📊 **CÁLCULO DE CAPACIDAD**

**Fórmula:**
```
Videos posibles = Hooks × Variantes × Audios
```

**Ejemplo:**
```
10 hooks × 6 variantes × 3 audios = 180 videos únicos
```

**Con múltiples BOFs:**
```
BOF1: 10 hooks × 6 variantes × 3 audios = 180
BOF2: 10 hooks × 5 variantes × 4 audios = 200
Total: 380 videos únicos
```

---

## 🔄 **MIGRACIÓN DESDE VERSIÓN ANTIGUA**

```bash
# Reset completo con migración automática
python migrate_to_v3.py --reset-db

# Archiva:
# - JSONs tracking → deprecated/tracking_legacy/
# - Videos antiguos → legacy_pre_12_02_2026/
# - Resetea DB
# - Crea estructura nueva
```

---

## 💡 **TIPS PRO**

### **Optimizar Producción**
- Crea 2-3 BOFs por producto (diferentes ángulos)
- Rota hooks cada 12 videos (distancia automática)
- Genera lotes de 20-50 videos a la vez

### **Calidad vs Velocidad**
```python
# Calidad alta (lento)
PRESET = "slow"
CRF = 20

# Velocidad alta (rápido)
PRESET = "fast"
CRF = 23
```

### **Backup Automático**
```bash
# Exportar DB antes de cambios grandes
cp autotok.db autotok_backup_$(date +%Y%m%d).db
```

---

## 📞 **SOPORTE**

**Documentación adicional:**
- `CHULETA_COMANDOS.md` - Referencia rápida
- `INSTRUCCIONES_MATERIAL.md` - Guía material
- `INSTRUCCIONES_PROGRAMACION.md` - Guía programación
- `DB_DESIGN_SQLITE.md` - Estructura base de datos

**Archivos útiles:**
- `diagnostico.py` - Verificar estado videos
- `fix_paths.py` - Corregir rutas DB
- `PLANTILLA_BOF.json` - Template BOF

---

**¡Sistema listo para producción masiva!** 🚀🎬
