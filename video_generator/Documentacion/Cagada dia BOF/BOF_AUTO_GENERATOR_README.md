# 🤖 BOF AUTO-GENERATOR

Sistema automático de generación de contenido BOF (Bottom of Funnel) para TikTok Shop.

---

## 📋 ¿QUÉ HACE?

Genera automáticamente:
- ✅ **Guión de audio** completo (7 pasos)
- ✅ **Variaciones de overlay** (mismo ángulo, diferentes formulaciones)
- ✅ **SEO text optimizado**
- ✅ **Hashtags**

---

## 🎯 LO QUE SE HACE MANUAL VS AUTOMÁTICO

### 🖐️ MANUAL (Custom GPT):
- **Deal Math** - El hook principal de la oferta

### 🤖 AUTOMÁTICO (Esta herramienta):
- **Guión audio** - Sistema de 7 pasos completo
- **Variaciones overlay** - 5 variaciones por BOF
- **SEO text** - Optimizado para búsquedas
- **Hashtags** - Optimizados para alcance

---

## 📥 ESTRUCTURA JSON DE ENTRADA

```json
{
  "producto": "Melatonina Aldous",
  "marca": "Aldous",
  "caracteristicas": [
    "5mg por dosis",
    "Sabor natural",
    "Te ayuda a dormir mejor"
  ],
  "tipo_deal_math": "free_unit",
  "hook_deal_math": "2 FRASCOS GRATIS",
  "precio_individual": 25.0,
  "precio_pack": 50.0,
  "unidades_pack": 3,
  "ahorro_real": 25.0,
  "tiene_cupon": true,
  "tiene_envio_gratis": true,
  "url_producto": "https://example.com/producto",
  "umbral": 40
}
```

### Campos requeridos:
- `producto` (string)
- `tipo_deal_math` (string)
- `hook_deal_math` (string)

### Campos opcionales:
- `marca`, `caracteristicas`, `precio_individual`, `precio_pack`, `unidades_pack`, `ahorro_real`, `tiene_cupon`, `tiene_envio_gratis`, `url_producto`, `umbral`

---

## 🔢 TIPOS DE DEAL MATH SOPORTADOS

1. **free_unit** - "1 GRATIS", "2 FRASCOS GRATIS"
2. **bundle_compression** - "42 TIRAS POR EL PRECIO DE 14"
3. **threshold** - "POR MENOS DE 7€", "POR DEBAJO DE 40€"
4. **anchor_collapse** - "40% DE DESCUENTO", "CASI 50% OFF"
5. **reinvestment** - "TE QUEDAS CON 20€"
6. **serving_math** - "0,03€ POR UNIDAD"
7. **double_discount** - "CUPÓN + ENVÍO GRATIS"
8. **stack_advantage** - "EL PACK 3 ES EL HACK"
9. **time_based** - "PRECIO MÁS BAJO EN 30 DÍAS"
10. **inventory_scarcity** - "ÚLTIMO RESTOCK CON DESCUENTO"

---

## 🚀 USO

### 1. Crear archivo JSON con datos del producto

```bash
# Ejemplo: melatonina.json
{
  "producto": "Melatonina Aldous",
  "marca": "Aldous",
  "tipo_deal_math": "free_unit",
  "hook_deal_math": "2 FRASCOS GRATIS",
  "precio_individual": 25.0,
  "precio_pack": 50.0,
  "unidades_pack": 3,
  "ahorro_real": 25.0,
  "url_producto": "https://example.com"
}
```

### 2. Generar BOF

```bash
python generar_bof.py melatonina.json
```

### 3. Resultado

El sistema genera:
- **Archivo de salida:** `melatonina_bof_output.json`
- **Pantalla:** Muestra guión, overlays, hashtags
- **BOF ID:** Para sistema de feedback

---

## 📊 SISTEMA DE FEEDBACK

### PowerShell (Windows):

```powershell
.\bof_feedback.ps1
```

El script pregunta:
1. **ID del BOF** (generado al crear el BOF)
2. **Producto**
3. **Tipo de Deal Math**
4. **Puntuación** (1-5 estrellas)
5. **Comentarios** (texto libre)

### Python directo:

```bash
python bof_feedback.py
```

### Ver estadísticas:

```python
from bof_feedback import BOFFeedbackSystem
system = BOFFeedbackSystem()
system.show_stats()
```

---

## 🎨 VARIACIONES DE OVERLAY

Las variaciones **mantienen el mismo ángulo** pero varían formulación:

### ✅ CORRECTO (mismo ángulo):
```
Variación 1:
  MELATONINA ALDOUS
  50% OFF SOLO HOY

Variación 2:
  50% DESCUENTO LIMITADO
  ALDOUS MELATONINA

Variación 3:
  MELATONINA ALDOUS
  TOCA EL CARRITO
```

### ❌ INCORRECTO (ángulos diferentes):
```
Variación 1:
  MELATONINA ALDOUS
  50% OFF SOLO HOY

Variación 2:
  2X1 EN MELATONINA    ← ÁNGULO DIFERENTE
  SE ESTÁN ACABANDO
```

---

## 🔧 ESTRUCTURA DEL SISTEMA

```
bof_generator.py        # Generador principal
generar_bof.py          # Comando CLI
bof_feedback.py         # Sistema de feedback Python
bof_feedback.ps1        # Script PowerShell feedback
bof_input_structure.json # Ejemplo de estructura
```

---

## 📝 EJEMPLOS DE USO

### Ejemplo 1: Free Unit

```json
{
  "producto": "Colágeno Vital Proteins",
  "marca": "Vital Proteins",
  "tipo_deal_math": "free_unit",
  "hook_deal_math": "1 BOTE GRATIS",
  "precio_individual": 30.0,
  "precio_pack": 60.0,
  "unidades_pack": 3,
  "ahorro_real": 30.0,
  "url_producto": "https://example.com"
}
```

```bash
python generar_bof.py colageno.json
```

### Ejemplo 2: Threshold

```json
{
  "producto": "Cable 4 en 1 GOOJODOQ",
  "tipo_deal_math": "threshold",
  "hook_deal_math": "POR MENOS DE 7€",
  "umbral": 7,
  "url_producto": "https://example.com"
}
```

```bash
python generar_bof.py cable.json
```

---

## 🧠 CÓMO FUNCIONA

### Pasos del sistema:

1. **Lee JSON** con datos del producto
2. **Identifica tipo de Deal Math**
3. **Selecciona plantillas** apropiadas para Paso 5 y 6
4. **Genera guión** siguiendo sistema de 7 pasos:
   - 1️⃣ Open Loop (usa hook_deal_math)
   - 2️⃣ Transition (fijo)
   - 3️⃣ CTA #1 (fijo)
   - 4️⃣ Why Should They (opciones predefinidas)
   - 5️⃣ Value (plantilla según tipo)
   - 6️⃣ Close the Loop (plantilla según tipo)
   - 7️⃣ CTA #2 (urgencia)
5. **Genera variaciones** de overlay (mismo ángulo)
6. **Optimiza SEO** text y hashtags
7. **Guarda resultado** en JSON

---

## 💡 TIPS

### Para mejores resultados:

1. **Usa el tipo de deal math correcto**
2. **Incluye todos los datos opcionales** cuando estén disponibles
3. **Da feedback regularmente** (cada 10-15 BOFs)
4. **Revisa estadísticas** para identificar qué tipos funcionan mejor

### Frecuencia de feedback recomendada:

- **Cada 10-15 BOFs generados**
- **Semanal** como mínimo
- **Inmediato** si encuentras problemas graves

---

## 🔄 MEJORA CONTINUA

El sistema usa feedback **determinista** y **simple**:

1. Generas BOF
2. Lo usas en producción
3. Evalúas resultado (1-5 estrellas)
4. Das feedback con comentarios
5. El sistema guarda métricas por tipo de deal math
6. Identificas qué tipos funcionan mejor
7. Ajustas plantillas manualmente según feedback

**No es un sistema de ML complejo** - es determinista y basado en plantillas que mejoras iterativamente con tu feedback.

---

## 📁 ARCHIVOS GENERADOS

### Por cada BOF generado:

- `{producto}_bof_output.json` - BOF completo
- `bof_feedback.json` - Feedback acumulado (si das feedback)

### Estructura de output:

```json
{
  "guion_audio": "...",
  "variantes": [
    {
      "overlay_line1": "...",
      "overlay_line2": "...",
      "seo_text": "..."
    }
  ],
  "hashtags": "...",
  "deal_math": "...",
  "url_producto": "..."
}
```

---

## ⚠️ IMPORTANTE

- **Deal Math** sigue siendo MANUAL (Custom GPT)
- Solo automatiza guión, overlays y SEO
- Las plantillas son **deterministas** (no IA generativa)
- **Mejora continua** basada en tu feedback

---

## 🎯 PRÓXIMOS PASOS

1. Genera primer BOF de prueba
2. Revisa calidad del guión
3. Usa en producción
4. Da feedback
5. Repite y mejora

---

**¡Sistema listo para generar BOFs automáticamente!** 🚀
