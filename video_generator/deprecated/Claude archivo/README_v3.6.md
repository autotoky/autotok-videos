Check # 🎬 AUTOTOK - SISTEMA DE GENERACIÓN VIDEOS TIKTOK v3.6

**Versión:** 3.6  
**Fecha:** 2026-02-13  
**Sistema:** Generación con variantes + tracking inteligente + BOF Auto-Generator

---

## 🆕 **NOVEDADES VERSIÓN 3.6**

### ✅ **BOF Auto-Generator v1.2 (NUEVO)**
- Genera guiones BOF automáticamente desde JSON simple
- 10 templates de hooks reales por cada tipo de Deal Math
- Variaciones automáticas para evitar duplicados
- SEO text variado (6 variaciones)
- Hashtags optimizados automáticamente
- Compatible 100% con `import_bof.py`

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
├── bof_generator.py             # ⭐ NUEVO: Auto-generador BOF
│
├── deal_math/                   # ⭐ NUEVO: JSONs de entrada
│   ├── input_01_manta.json
│   ├── input_02_plancha.json
│   └── ... (21 productos)
│
├── bof_generated/               # ⭐ NUEVO: BOFs generados (auto-creada)
│   ├── bof_melatonina.json
│   └── ...
│
├── scripts/
│   ├── db_config.py             # Schema DB SQLite
│   ├── import_bof.py            # Importar BOF + variantes
│   ├── scan_material.py         # Escanear hooks/brolls/audios
│   └── validate_bof.py          # Validar requisitos mínimos
│
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

---

## 🎯 **WORKFLOW COMPLETO (ACTUALIZADO v3.6)**

### **PASO 0: Generar BOF Automáticamente (NUEVO)**

**0.1. Crear JSON de entrada simple:**

Crea un archivo en `deal_math/input_producto.json`:
```json
{
  "marca": "Aldous Bio",
  "producto": "Melatonina Pura",
  "caracteristicas": ["500 comprimidos", "5mg", "tienda oficial"],
  "deal_math": "40% OFF",
  "url_producto": "https://s.click.aliexpress.com/tu-link"
}
```

**0.2. Generar BOF automáticamente:**
```bash
python bof_generator.py --input deal_math\input_melatonina.json --variaciones 6
```

**Output:** `bof_generated/bof_melatonina_pura.json` listo para importar

**Lo que genera automáticamente:**
- ✅ Guion audio completo (7 pasos BOF)
- ✅ Hashtags optimizados
- ✅ 6 variaciones de overlay + SEO text
- ✅ Hooks variados (nunca duplicados)

**Tipos de Deal Math soportados:**
1. `free_unit` - 1 GRATIS, 2X1
2. `bundle_compression` - 42 POR PRECIO DE 14
3. `threshold` - MENOS DE X€
4. `anchor_collapse` - X% OFF
5. `reinvestment` - TE QUEDAS CON X€
6. `double_discount` - CUPÓN + ENVÍO
7. `time_based` - PRECIO MÁS BAJO 30 DÍAS
8. `serving_math` - X€ por unidad
9. `stack_advantage` - Descuentos escalonados
10. `inventory_scarcity` - ÚLTIMAS UNIDADES

---

### **PASO 1: Preparar Material**

**En Google Drive:**
1. Subir 10+ hooks a `hooks/`
2. Subir 20+ brolls a `brolls/` (nombrados: `A_clip.mp4`, `B_clip.mp4`, etc.)
3. Subir 5+ audios a `audios/` (nombrados: `bof1_andaluz.mp3`, `bof1_chavalita.mp3`, etc.)

**Esperar sincronización Drive**

---

### **PASO 2: Validar Material**
```bash
python scripts/validate_bof.py melatonina_pura
```

**Requisitos mínimos:**
- ✅ 10 hooks
- ✅ 20 brolls (6 grupos diferentes)
- ✅ 5 variantes por BOF
- ✅ 3 audios por BOF

---

### **PASO 3: Importar BOF (generado automáticamente)**

```bash
python scripts/import_bof.py melatonina_pura bof_generated/bof_melatonina_pura.json
```

Esto crea en la DB:
- ✅ Producto
- ✅ BOF con deal_math, guion_audio, hashtags, url_producto
- ✅ 6 variantes de overlay/SEO

---

### **PASO 4: Escanear Material**
```bash
python scripts/scan_material.py melatonina_pura
```

**Registra automáticamente:**
- ✅ Hooks → DB
- ✅ Brolls → DB (con grupos)
- ✅ Audios → DB (vinculados a BOF según nombre `bofN_*.mp3`)

---

### **PASO 5: Generar Videos**
```bash
python main.py --producto melatonina_pura --batch 20 --cuenta lotopdevicky
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

---

## 🎨 **BOF AUTO-GENERATOR - GUÍA DETALLADA**

### **Entrada: JSON Simple**
```json
{
  "marca": "NIKLOK",
  "producto": "Manta Eléctrica",
  "caracteristicas": ["160x130cm", "calor ajustable"],
  "deal_math": "POR MENOS DE 40€",
  "url_producto": "https://..."
}
```

### **Salida: BOF Completo**
```json
{
  "deal_math": "POR MENOS DE 40€",
  "guion_audio": "POR MENOS DE 40€ en Manta Eléctrica NIKLOK\n\n¿No me crees?...",
  "hashtags": "#mantaeléctricaniklok #niklok #160x130cm #oferta #descuento",
  "url_producto": "https://...",
  "variantes": [
    {
      "overlay_line1": "MANTA ELÉCTRICA NIKLOK",
      "overlay_line2": "POR MENOS DE 40€ SOLO HOY",
      "seo_text": "POR MENOS DE 40€ en Manta Eléctrica NIKLOK 🔥..."
    }
    // ... 5 variantes más
  ]
}
```

### **Características del Generador:**

**1. Hooks Variados Automáticamente**
- 10 templates reales por cada tipo de Deal Math
- Nunca genera el mismo hook dos veces
- Basado en ejemplos reales de BOFs exitosos

**2. SEO Text con 6 Variaciones**
- Cambia estructura y emojis
- Mantiene el mensaje core
- Optimizado para TikTok

**3. Hashtags Inteligentes**
- Producto completo + marca
- Características principales
- Hashtags de oferta genéricos
- Máximo 7 hashtags

**4. Organización Automática**
- Inputs en `deal_math/`
- Outputs en `bof_generated/`
- Carpetas se crean automáticamente

---

## 🔧 **COMANDOS ÚTILES**

### **BOF Auto-Generator**
```bash
# Generar BOF simple
python bof_generator.py --input deal_math\input_producto.json

# Generar con más variaciones
python bof_generator.py --input deal_math\input_producto.json --variaciones 10

# Especificar nombre de salida
python bof_generator.py --input deal_math\input_producto.json --output custom_name.json
```

### **Gestión de Productos**
```bash
# Ver estadísticas
python main.py --producto melatonina_pura --cuenta lotopdevicky --stats

# Diagnosticar videos
python diagnostico.py lotopdevicky

# Listar productos
python main.py --list-productos

# Ver configuración
python main.py --config
```

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
BOF2: 10 hooks × 6 variantes × 4 audios = 240
Total: 420 videos únicos
```

---

## 💡 **TIPS PRO**

### **Optimizar Producción**
- Genera 2-3 BOFs por producto (diferentes ángulos)
- Usa el auto-generador para crear variaciones rápidamente
- Genera lotes de 20-50 videos a la vez

### **Generar Múltiples BOFs del Mismo Producto**
```bash
# BOF 1: Enfoque en porcentaje
python bof_generator.py --input deal_math\melatonina_anchor.json --output melatonina_v1.json

# BOF 2: Enfoque en ahorro real
python bof_generator.py --input deal_math\melatonina_reinv.json --output melatonina_v2.json

# BOF 3: Enfoque en precio por unidad
python bof_generator.py --input deal_math\melatonina_serving.json --output melatonina_v3.json
```

Los hooks serán siempre diferentes gracias al sistema de variaciones automáticas.

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

### **JSONs de Entrada (deal_math/):**
```
input_01_producto_tipo.json
input_02_producto_tipo.json
```

---

## 🆘 **TROUBLESHOOTING**

### **"No se encontraron hooks/brolls/audios"**
- Verifica sincronización Google Drive
- Revisa rutas en `config.py`
- Ejecuta `python scripts/scan_material.py PRODUCTO`

### **"No hay variantes disponibles"**
- Añade más variantes al BOF (usa `--variaciones 10`)
- Genera nuevo BOF: `python bof_generator.py --input deal_math/producto.json`

### **"Hooks duplicados en BOFs"**
- El sistema genera automáticamente hooks diferentes
- Si necesitas más variación, genera desde diferentes tipos de deal math

### **"Error al importar BOF"**
- Verifica que el JSON tenga todos los campos requeridos
- Usa el generador automático para garantizar estructura correcta

---

## 📚 **DOCUMENTACIÓN ADICIONAL**

**Archivos de referencia:**
- `README_BOF_GENERATOR.md` - Documentación completa del auto-generador
- `CHULETA_COMANDOS.md` - Referencia rápida de comandos
- `INSTRUCCIONES_MATERIAL.md` - Guía preparación material
- `INSTRUCCIONES_PROGRAMACION.md` - Guía programación
- `DB_DESIGN_SQLITE.md` - Estructura base de datos
- `ROADMAP_V3.md` - Roadmap del proyecto

**Archivos útiles:**
- `diagnostico.py` - Verificar estado videos
- `fix_paths.py` - Corregir rutas DB
- `PLANTILLA_BOF.json` - Template BOF (legacy, usar generador automático)

---

## 🔄 **MIGRACIÓN DESDE VERSIÓN ANTIGUA**

```bash
# Reset completo con migración automática
python migrate_to_v3.py --reset-db
```

---

## 📞 **CHANGELOG v3.6**

**2026-02-13:**
- ✅ Añadido BOF Auto-Generator v1.2
- ✅ Sistema de hooks variados por tipo de Deal Math (10 templates por tipo)
- ✅ Generación automática de hashtags optimizados
- ✅ SEO text con 6 variaciones
- ✅ Organización automática en carpetas (deal_math/ y bof_generated/)
- ✅ 21 ejemplos de productos reales incluidos
- ✅ Detección automática de tipo de Deal Math
- ✅ Sistema anti-duplicados en hooks

---

**¡Sistema listo para producción masiva con generación automática de BOFs!** 🚀🎬
