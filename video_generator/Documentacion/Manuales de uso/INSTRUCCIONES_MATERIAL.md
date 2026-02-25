# 📁 INSTRUCCIONES DE MATERIAL - AUTOTOK

**Versión:** 3.0  
**Fecha:** 2026-02-12  
**Para:** Mar, Sara, Carol

---

## ⚠️ ACTUALIZACIÓN v3.0 (2026-02-12)

**Sistema con Base de Datos:**
- ✅ **Overlays ahora en DB** (BOFs), NO en CSV
- ✅ **Material se registra con scripts**, NO escaneo manual  
- ✅ Ver README_V3.md para workflow completo actualizado

**Esta guía sigue vigente para naming conventions de archivos.**

---

## 🎯 RESUMEN RÁPIDO

**3 tipos de archivos:**
1. **Hooks** → Clips intro (3-4 seg)
2. **Brolls** → Clips producto (cualquier duración)
3. **Audios** → Voice-overs (10-20 seg)

---

## 📂 DÓNDE GUARDAR

```
Google Drive/Mi unidad/recursos_videos/
└── [PRODUCTO]/              (ej: melatonina, proyector_magcubic)
    ├── hooks/
    ├── brolls/
    └── audios/
```

**Nota:** Ya NO se necesita `overlays.csv` (ahora son BOFs en DB)

---

## 🎬 HOOKS

### Formato de nombre:
```
LETRA_descripcion.mp4
```

### Ejemplos:
```
A_hook_patas.mp4
B_hook_boom.mp4
C_hook_explosion_START2.mp4     ← Empieza desde segundo 2
D_hook_intro.mp4
```

### Reglas:
- ✅ **LETRA mayúscula** al inicio (A-Z)
- ✅ Guion bajo después de la letra: `A_`
- ✅ Descripción corta (para identificar)
- ✅ Opcional: `_START2` para empezar desde segundo específico
- ✅ Duración: 3-6 segundos

### ¿Por qué la letra?
- Identifica videos generados: `melatonina_hookA_001.mp4`
- Evita repetir mismo hook en mismo día del calendario

---

## 🎨 BROLLS

### Opción 1: Sin grupos (simple)
```
producto_frente.mp4
mano_sosteniendo.mp4
detalle_pastillas.mp4
```

### Opción 2: Con grupos (recomendado)
```
A_producto_frente.mp4
A_producto_lado.mp4
B_mano_sosteniendo.mp4
B_mano_abriendo.mp4
C_fondo_blanco.mp4
```

### Reglas:
- ✅ Si usas grupos: Mismo formato que hooks (`LETRA_nombre.mp4`)
- ✅ Sin grupos: Cualquier nombre
- ✅ Duración: Libre (se ajusta automáticamente)
- ✅ Opcional: `_START2` para empezar desde segundo específico

### ¿Grupos o no?
- **Con grupos:** Sistema evita usar 2 clips del mismo grupo en 1 video
- **Sin grupos:** Más simple, menos control
- **Configurar en:** `config.py` → `USE_BROLL_GROUPS = True/False`

---

## 🎵 AUDIOS

### Formato de nombre:
```
prefijo_producto_variante.mp3
```

### Ejemplos:
```
a1_melatonina_problemas_dormir.mp3
a2_melatonina_insomnio.mp3
b1_melatonina_natural_seguro.mp3
b2_melatonina_sin_receta.mp3
```

### Reglas:
- ✅ **Prefijo** al inicio (ej: `a1`, `a2`, `b1`)
- ✅ Guion bajo después: `a1_`
- ✅ Nombre descriptivo
- ✅ Formato: `.mp3`, `.m4a`, o `.wav`
- ✅ Duración: 10-20 segundos

### ¿Por qué el prefijo?
- Conecta con overlays correctos en `overlays.csv`
- Audio `a1_producto.mp3` usa solo overlays con `audio_id = a1`

---

## 💬 OVERLAYS.CSV

### Ubicación:
```
recursos_videos/[PRODUCTO]/overlays.csv
```

### Formato CSV:
```csv
line1,line2,audio_id,deal_math
OFERTA ESPECIAL,2x1 HOY,a1,2x1
DESCUENTO,50% OFF,a2,50%
PACK AHORRO,Compra 3 paga 2,b1,3x2
ENVÍO GRATIS,Compra ya,b2,envio_gratis
```

### Columnas:
- **line1:** Texto línea superior (ej: "OFERTA")
- **line2:** Texto línea inferior (ej: "2x1")
- **audio_id:** Prefijo del audio compatible (ej: `a1`)
- **deal_math:** Para análisis futuro (ej: "2x1", "50%", "3x2")

### Reglas:
- ✅ Primera fila: headers (line1, line2, audio_id, deal_math)
- ✅ Resto: datos (una fila = un overlay)
- ✅ `audio_id` debe coincidir con prefijo de audios
- ✅ Guardar como `.csv` (UTF-8)

### Ejemplo completo:
```
Audio: a1_melatonina_dormir.mp3
Overlay en CSV:
  line1: OFERTA
  line2: 2x1 HOY
  audio_id: a1        ← Coincide con prefijo del audio
  deal_math: 2x1

Resultado: Video usa ese audio + ese overlay automáticamente
```

---

## ✅ CHECKLIST SETUP PRODUCTO NUEVO

**Para crear material de un producto nuevo:**

1. **Crear estructura en Drive:**
   ```
   recursos_videos/
   └── nombre_producto/
       ├── hooks/
       ├── brolls/
       ├── audios/
       └── overlays.csv
   ```

2. **Subir hooks:**
   - Mínimo 6 hooks
   - Nombrados: `A_descripcion.mp4`, `B_descripcion.mp4`, etc.

3. **Subir brolls:**
   - Mínimo 20 clips
   - Con o sin grupos (tu elección)

4. **Subir audios:**
   - Mínimo 10 audios
   - Nombrados: `a1_producto.mp3`, `a2_producto.mp3`, etc.

5. **Crear overlays.csv:**
   - Mínimo 20 filas
   - Conectar audio_id con prefijos de audios

6. **Esperar sincronización Drive** (icono nube ✓)

7. **Probar:**
   ```bash
   python main.py --producto nombre_producto --batch 5 --cuenta lotopdevicky
   ```

---

## 🔮 MEJORAS PLANTEADAS

**Próximamente:**
- Migrar `overlays.csv` a Google Sheets
- Script automático para setup de producto
- Generar deal_math, SEO, hashtags automáticamente
- Integración con sistema Fase 0

---

## 🆘 PROBLEMAS COMUNES

**"No se generan videos"**
→ Verifica nombres de archivos (letra mayúscula, guiones bajos)

**"Solo genera 1 video por día en calendario"**
→ Necesitas más hooks únicos (mínimo 4-6 para 4 videos/día)

**"Overlays no aparecen"**
→ Verifica que `audio_id` coincida con prefijo del audio

**"Videos sin deal_math"**
→ Normal si video se generó sin overlay (ej: sin --cuenta)

---

**Última actualización:** 2026-02-07
