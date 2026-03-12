# 📚 AUTOTOK - DOCUMENTACIÓN COMPLETA v3.6

**Fecha última actualización:** 2026-02-13  
**Versión sistema:** 3.6  
**Estado:** Producción

---

## 📋 ÍNDICE

1. [Quick Start](#quick-start)
2. [Información General](#información-general)
3. [Sistema BOF Auto-Generator](#sistema-bof-auto-generator)
4. [Issues y Mejoras](#issues-y-mejoras)
5. [Comandos Esenciales](#comandos-esenciales)

---

# 🚀 QUICK START

## Estructura en Google Drive

```
G:\Mi unidad\recursos_videos\
├── melatonina_aldous_500comp/
│   ├── input_producto.json       ← TÚ creas este
│   ├── bof_generado.json          ← Se genera automáticamente
│   ├── hooks/
│   ├── brolls/
│   └── audios/
└── ... (más productos)
```

## Workflow completo (4 pasos)

### 1. Crear estructura de producto

```powershell
# Crear carpeta
mkdir "G:\Mi unidad\recursos_videos\melatonina_aldous_500comp"

# Crear input_producto.json
{
  "marca": "Aldous Bio",
  "producto": "Melatonina Pura",
  "caracteristicas": ["500 comprimidos", "5mg"],
  "deal_math": "40% OFF",
  "url_producto": "https://s.click.aliexpress.com/..."
}

# Subir material a hooks/, brolls/, audios/
```

### 2. Escanear y generar TODO (un solo comando)

```powershell
python scan_material.py melatonina_aldous_500comp --auto-bof
```

Este comando hace:
- ✅ Lee input_producto.json
- ✅ Genera bof_generado.json automáticamente
- ✅ Importa BOF a la base de datos
- ✅ Escanea hooks, brolls y audios
- ✅ Registra todo en la BD

### 3. Generar videos

```powershell
python main.py --producto melatonina_aldous_500comp --batch 20 --cuenta lotopdevicky
```

### 4. Programar

```powershell
python programador.py --cuenta lotopdevicky --dias 7
```

---

# 📖 INFORMACIÓN GENERAL

## ¿Qué es Autotok?

Sistema automatizado de generación de videos para TikTok Shop con:
- Generación automática de videos (hooks + brolls + audio + overlays)
- Sistema BOF Auto-Generator para crear guiones automáticamente
- Base de datos SQLite para tracking
- Calendario automático en Google Sheets
- Gestión de estados (Generado → En Calendario → Borrador → Programado)

## Arquitectura

### Base de datos SQLite (9 tablas)

1. **productos** - Información de productos
2. **producto_bofs** - BOFs completos (deal_math + guion)
3. **variantes_overlay_seo** - Variantes de overlay exclusivas por BOF
4. **audios** - Audios vinculados a BOF
5. **material** - Hooks + Brolls compartidos
6. **videos** - Videos generados (CORE)
7. **hook_variante_usado** - Tracking global (hook + variante único)
8. **combinaciones_usadas** - Backup legacy
9. **cuentas_config** - Config de cuentas

### Archivos principales

```
video_generator/
├── main.py                      # Generador principal
├── generator.py                 # Lógica generación con variantes
├── programador.py               # Programación calendario (+ auto-export lotes)
├── tiktok_publisher.py          # Publicación automática en TikTok Studio
├── publicar_facil.py            # Wrapper amigable para operadoras
├── mover_videos.py              # Sincronización con Sheet
├── bof_generator.py             # Auto-generador BOF
├── config.py                    # Configuración global
├── config_cuentas.json          # Config cuentas TikTok
├── config_publisher.json        # Config publisher (perfiles Chrome, productos)
├── config_operadora.json        # Config PC operadora (cuenta, ruta Drive)
├── PUBLICAR.bat                 # Doble-click para operadoras
├── INSTALAR.bat                 # Instalación inicial en PC operadora
└── scripts/
    ├── db_config.py             # Schema DB SQLite
    ├── sheet_sync.py            # Sync centralizado BD↔Sheet
    ├── lote_manager.py          # Gestión lotes JSON para operadoras
    ├── email_notifier.py        # Notificaciones por email
    ├── import_bof.py            # Importar BOF + variantes
    ├── scan_material.py         # Escanear material
    ├── validate_bof.py          # Validar requisitos
    └── register_audio.py        # Registrar audios
```

## Sistema de variantes

- **1 BOF** = 1 oferta con múltiples variantes de overlay
- Cada variante es exclusiva del BOF
- **Tracking global:** Hook + Variante nunca se repite
- Tabla `hook_variante_usado` con constraint UNIQUE

## Reglas de programación

- Distancia mínima entre hooks: 12 publicaciones
- Gap mínimo entre videos: 1 hora
- Max 2 videos del mismo producto/día
- Formato fecha compatible Windows: `DD-MM-YYYY`

## Sistema de publicación automática (TikTok Publisher)

El publisher automatiza la subida de videos a TikTok Studio con Playwright. Funciona en dos modos:

**Modo normal (Sara):** Lee videos de la BD, publica en TikTok, actualiza BD + Sheet simultáneamente.

**Modo lote (operadoras):** Lee videos de un JSON exportado a Drive, publica en TikTok, escribe resultados en el JSON. No necesita BD ni credenciales de Sheet.

### Sincronización BD↔Sheet centralizada

El módulo `scripts/sheet_sync.py` garantiza que cualquier cambio de estado se refleje en BD y Sheet al mismo momento. Antes de esto, el publisher solo actualizaba la BD y la Sheet quedaba desincronizada.

### Flujo de operadoras (lotes JSON)

```
Sara programa calendario
  → BD + Sheet + auto-export JSON a Drive

Operadora hace doble-click en PUBLICAR.bat
  → Lee JSON del lote más reciente
  → Publica videos pendientes en TikTok Studio
  → Escribe resultados en el JSON (video a video)

Sara vuelve a programar
  → Auto-import resultados del JSON → BD + Sheet
  → Exporta nuevos lotes
```

**Garantías anti-desync:** Import siempre antes de export; JSON preserva resultados previos al regenerarse; el publisher actualiza BD + Sheet al momento (estados finales: Programado, Error).

### Estructura en Drive

```
G:\Mi unidad\material_programar\
├── ofertastrendy20/
│   ├── calendario/DD-MM-YYYY/video.mp4
│   └── _lotes/
│       ├── lote_ofertastrendy20_2026-03-05.json
│       └── lote_ofertastrendy20_2026-03-06.json
└── lotopdevicky/
    ├── calendario/...
    └── _lotes/...
```

---

# 🤖 SISTEMA BOF AUTO-GENERATOR

## ¿Qué es un BOF?

BOF (Bottom of Funnel) = Guion de audio estructurado en 7 pasos para convertir.

### Estructura de 7 pasos

1. **Open Loop** - Hook del deal (usa deal_math)
2. **Transition** - "¿No me crees?" o "Para conseguirlo, solo..."
3. **CTA #1** - "Toca el carrito naranja."
4. **Why Should They** - "Para desbloquear la oferta flash inicial,"
5. **Value** - VARIABLE según tipo de Deal Math ⭐
6. **Close the Loop** - VARIABLE según tipo de Deal Math ⭐
7. **CTA #2** - Urgencia

## 10 tipos de Deal Math

| Tipo | Ejemplo | Paso 5 | Paso 6 |
|------|---------|--------|--------|
| free_unit | "1 GRATIS" | "elige el pack de 3..." | "estés bloqueando 3 por precio de 2..." |
| bundle_compression | "42 POR 14" | "elige pack grande..." | "pack completo por precio de fracción..." |
| threshold | "MENOS DE 22€" | "aplica cupón..." | "bloqueando por debajo del umbral..." |
| anchor_collapse | "50% OFF" | "aplica cupón..." | "bloqueando gran descuento..." |
| reinvestment | "TE QUEDAS 20€" | "aplica cupón..." | "quedándote con ahorro real..." |
| serving_math | "0,03€/UNIDAD" | "elige pack grande..." | "pagando fracción del precio..." |
| double_discount | "CUPÓN+ENVÍO" | "aplica cupón..." | "acumulando cupón + envío gratis..." |
| time_based | "BAJO 30 DÍAS" | "activa oferta flash..." | "asegurando precio más bajo..." |
| stack_advantage | "PACK 3=MAX" | "elige pack grande..." | "desbloqueando nivel superior..." |
| inventory_scarcity | "ÚLTIMO LOTE" | "activa oferta..." | "bloqueando último lote con descuento..." |

## Reglas de overlay (CRÍTICAS)

### ✅ VÁLIDO (mismo ángulo):
```
MELATONINA ALDOUS
50% OFF SOLO HOY

50% DESCUENTO
ALDOUS MELATONINA
```

### ❌ INVÁLIDO (ángulos diferentes):
```
MELATONINA ALDOUS    vs    2X1 EN MELATONINA
50% OFF SOLO HOY           SE ESTÁN ACABANDO
```

### Límites de caracteres (ESTRICTOS)

- **Línea 1:** Máximo 20 caracteres
- **Línea 2:** Máximo 30 caracteres

**Comportamiento:**
- `bof_generator.py` → TRUNCA automáticamente
- `import_bof.py` → RECHAZA importación si excede

## Generación automática con --auto-bof

```powershell
python scan_material.py producto --auto-bof
```

**Hace TODO automáticamente:**
1. Lee `input_producto.json`
2. Genera guion BOF completo
3. Crea 6 variantes de overlay
4. Importa a base de datos
5. Registra material

**NO hay paso de revisión manual** → Truncado automático garantiza límites.

---

# 🔧 ISSUES Y MEJORAS

**Ver documento separado:** `ISSUES.md`

Este documento contiene:
- 🔴 Bugs críticos
- 🟡 Problemas conocidos
- 🔵 Edge cases documentados
- 💡 Mejoras futuras (roadmap)

El documento ISSUES.md se actualiza frecuentemente según vayan surgiendo problemas o completándose mejoras.

---

# 🎯 COMANDOS ESENCIALES

## Gestión de productos

```powershell
# Escanear y generar TODO (recomendado)
python scan_material.py PRODUCTO --auto-bof

# Validar material
python validate_bof.py PRODUCTO

# Solo escanear material
python scan_material.py PRODUCTO
```

## Generación de videos

```powershell
# Generar batch
python main.py --producto PRODUCTO --batch 20 --cuenta CUENTA

# Con overlay obligatorio
python main.py --producto PRODUCTO --batch 20 --cuenta CUENTA --require-overlay
```

## Programación

```powershell
# Preview (no escribe)
python programador.py --cuenta CUENTA --dias 7 --test

# Generar calendario
python programador.py --cuenta CUENTA --dias 7

# Desde fecha específica
python programador.py --cuenta CUENTA --dias 7 --fecha-inicio 2026-02-20
```

## Sincronización

```powershell
# Sincronizar desde Sheet
python mover_videos.py --sync

# Solo preview
python mover_videos.py --sync --test
```

## BOF Generator

```powershell
# Generar BOF
python bof_generator.py --input ruta/input_producto.json

# Con más variaciones
python bof_generator.py --input ruta/input.json --variaciones 10

# Especificar output
python bof_generator.py --input X.json --output custom.json
```

## Base de datos

```powershell
# Conectar a DB
sqlite3 autotok.db

# Ver BOFs
SELECT id, deal_math, substr(guion_audio, 1, 50) FROM producto_bofs;

# Ver variantes de un BOF
SELECT id, overlay_line1, overlay_line2 FROM variantes_overlay_seo WHERE bof_id = 5;

# Editar guion
UPDATE producto_bofs SET guion_audio = 'NUEVO TEXTO' WHERE id = 5;

# Editar variante
UPDATE variantes_overlay_seo 
SET overlay_line1 = 'LÍNEA 1', overlay_line2 = 'LÍNEA 2' 
WHERE id = 10;
```

---

# 📁 CONVENCIONES

## Naming de archivos

### Hooks
```
hook_boom_START2.mp4        # Empieza desde segundo 2
hook_patas.mp4              # Empieza desde 0
```

### Brolls (con grupos)
```
A_producto_frente.mp4       # Grupo A
B_mano_sosteniendo.mp4      # Grupo B
C_fondo_blanco.mp4          # Grupo C
```

### Audios (vinculados a BOF)
```
bof1_andaluz.mp3            # BOF ID 1
bof1_chavalita.mp3          # BOF ID 1
bof2_voz_seria.mp3          # BOF ID 2
```

### Carpetas de producto
```
producto_marca_caracteristica
melatonina_aldous_500comp
cable_goojodoq_65w
proyector_magcubic_hy300
```

---

# ⚠️ TROUBLESHOOTING

## "No se encontró input_producto.json"
→ Crear archivo en carpeta del producto

## "BOF ya existe"
→ Borrar `bof_generado.json` para regenerar

## "Overlay excede X caracteres"
→ Sistema trunca automáticamente, revisar warnings

## "No hay variantes disponibles"
→ Añadir más variantes al BOF (--variaciones 10)

## "Hooks duplicados"
→ Sistema genera automáticamente hooks diferentes

## "Error al importar BOF"
→ Verificar JSON tiene todos los campos
→ Usar generador automático

---

# 📊 REQUISITOS MÍNIMOS

Para crear un BOF necesitas:
- ✅ 10+ hooks
- ✅ 20+ brolls (6 grupos diferentes)
- ✅ 5+ variantes por BOF
- ✅ 3+ audios por BOF

---

# 🔒 INFORMACIÓN CRÍTICA

## Sistema determinista
- Plantillas FIJAS para cada tipo de Deal Math
- NO usamos bof_learning.py (era probabilístico)
- Pasos 5 y 6 tienen texto predefinido
- Variaciones solo en overlay y partes fijas

## Deal Math manual
- Se genera con Custom GPT (no automático)
- Sistema solo genera guion y overlays
- Razón: Requiere análisis estratégico

## Flujo completo

```
Custom GPT → Deal Math
    ↓
Crear input_producto.json
    ↓
scan_material.py --auto-bof
    ↓
Generar videos
    ↓
Programar calendario
    ↓
Publicar en TikTok
```

---

**Última actualización:** 2026-02-13 20:15 CET  
**Mantenedor:** Claude + Usuario  
**Versión:** 3.6

---

*Este documento consolida: README, FIXES, CASOS_DE_USO, ROADMAP, QUICK_START y BACKUP_BOF*
