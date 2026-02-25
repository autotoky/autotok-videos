# 🎬 BOF AUTO-GENERATOR v1.2

Sistema automático de generación de guiones BOF para TikTok Shop.

---

## 📋 **¿QUÉ HACE?**

Genera automáticamente:
1. **Guion de audio BOF** completo (7 pasos)
2. **Hashtags** optimizados
3. **Variaciones de overlay** (configurable, default 6)
4. **Textos SEO** para cada variación

**Compatible 100% con `import_bof.py` de video_generator**

---

## 🚀 **USO RÁPIDO**

### **1. Crear JSON de entrada:**

```json
{
  "marca": "Aldous",
  "producto": "Melatonina",
  "caracteristicas": ["5mg", "500 comprimidos", "sabor natural"],
  "deal_math": "50% OFF",
  "url_producto": "https://s.click.aliexpress.com/e/_tu_link"
}
```

### **2. Generar BOF:**

```bash
python bof_generator.py --input input_melatonina.json --variaciones 6
```

### **3. Importar a video_generator:**

```bash
python import_bof.py melatonina bof_melatonina.json
```

---

## 📦 **ESTRUCTURA JSON**

### **INPUT (lo que TÚ creas):**
```json
{
  "marca": "Aldous",                    // Opcional
  "producto": "Melatonina",             // REQUERIDO
  "caracteristicas": [                  // Opcional (para hashtags)
    "5mg",
    "500 comprimidos"
  ],
  "deal_math": "50% OFF",               // REQUERIDO
  "url_producto": "https://..."         // REQUERIDO
}
```

### **OUTPUT (lo que genera):**
```json
{
  "deal_math": "50% OFF",
  "guion_audio": "50% OFF de Melatonina Aldous\n\n¿No me crees?...",
  "hashtags": "#melatonina #aldous #5mg #oferta",
  "url_producto": "https://...",
  "variantes": [
    {
      "overlay_line1": "MELATONINA ALDOUS",
      "overlay_line2": "50% OFF SOLO HOY",
      "seo_text": "50% OFF en Melatonina Aldous 🔥..."
    }
    // ... más variantes
  ]
}
```

---

## 🎯 **DETECCIÓN AUTOMÁTICA DE TIPO**

El sistema detecta automáticamente el tipo de Deal Math del texto:

| Deal Math | Tipo detectado |
|-----------|----------------|
| "50% OFF" | anchor_collapse |
| "1 BOTE GRATIS" | free_unit |
| "POR MENOS DE 22€" | threshold |
| "TE QUEDAS CON 15€" | reinvestment |
| "42 POR PRECIO DE 14" | bundle_compression |
| "CUPÓN + ENVÍO GRATIS" | double_discount |

No necesitas especificar el tipo manualmente ✅

---

## 📂 **EJEMPLOS INCLUIDOS**

```
ejemplos_bof/
├── input_01_manta.json          (threshold)
├── input_02_plancha_anchor.json (anchor_collapse)
├── input_03_proyector.json      (threshold)
├── input_04_colageno.json       (free_unit)
├── input_05_melatonina.json     (anchor_collapse)
├── input_06_cable.json          (threshold)
├── input_07_tiras.json          (bundle_compression)
└── input_08_palo_selfie.json    (anchor_collapse)
```

---

## 🔧 **OPCIONES DEL COMANDO**

```bash
python bof_generator.py \
  --input input.json \        # Archivo JSON de entrada (REQUERIDO)
  --variaciones 10 \          # Número de variantes (default: 6)
  --output custom.json        # Nombre archivo salida (opcional)
```

---

## 📝 **WORKFLOW COMPLETO**

```
1. Crear Deal Math (Custom GPT o manual)
   ↓
2. Crear JSON input con: producto, marca, características, deal_math, url
   ↓
3. python bof_generator.py --input mi_producto.json --variaciones 10
   ↓
4. Revisar bof_OUTPUT.json generado
   ↓
5. python import_bof.py nombre_producto bof_OUTPUT.json
   ↓
6. python scan_material.py nombre_producto
   ↓
7. python main.py --producto nombre_producto --batch 20
```

---

## ✅ **VERIFICACIÓN RÁPIDA**

```bash
# Generar BOF de ejemplo
python bof_generator.py --input ejemplos_bof/input_05_melatonina.json

# Verificar estructura
cat bof_melatonina.json

# Debería tener:
# ✓ deal_math
# ✓ guion_audio
# ✓ hashtags
# ✓ url_producto
# ✓ variantes[] (6 elementos)
```

---

## 🎨 **REGLAS DE OVERLAY**

- ✅ Marca y producto SIEMPRE en la misma línea
- ✅ Mismo ángulo en todas las variaciones
- ✅ Máximo 30 caracteres por línea
- ✅ 6 estructuras diferentes rotando

**Ejemplos válidos:**
```
MELATONINA ALDOUS          ALDOUS MELATONINA
50% OFF SOLO HOY     vs    50% DESCUENTO LIMITADO
```

---

## 🏷️ **GENERACIÓN DE HASHTAGS**

Automática a partir de:
1. Producto (normalizado)
2. Marca (si existe)
3. Características (primeras 2-3)
4. Genéricos: #oferta #descuento

**Ejemplo:**
```
Input: 
  producto: "Melatonina"
  marca: "Aldous"
  características: ["5mg", "500 comprimidos", "sabor natural"]

Output:
  #melatonina #aldous #5mg #500comprimidos #sabornatural #oferta
```

Máximo 6 hashtags.

---

## 🔄 **ACTUALIZACIÓN FUTURA**

**Fase 2 (planificada):**
- Leer datos desde Google Sheets en vez de JSON
- Auto-población de `url_producto` desde hoja de cálculo
- Generación batch de múltiples BOFs

---

## 📌 **NOTAS IMPORTANTES**

### **Lo que el sistema NO genera:**
- ❌ Deal Math (lo pasas tú en el JSON)
- ❌ URLs de producto (las pasas tú en el JSON)

### **Lo que SÍ genera:**
- ✅ Guion audio completo (7 pasos BOF)
- ✅ Hashtags optimizados
- ✅ Variaciones de overlay
- ✅ Textos SEO

---

## 🆘 **TROUBLESHOOTING**

**Error: "Faltan campos requeridos"**
→ Verifica que tu JSON tenga `producto` y `deal_math`

**Las variantes son muy similares**
→ Aumenta número: `--variaciones 10`

**Hashtag muy largo (>20 caracteres)**
→ El sistema los filtra automáticamente

**Tipo de deal math incorrecto**
→ El sistema detecta automáticamente, pero puedes revisar la detección en el código

---

**¡Sistema listo para producción!** 🚀
