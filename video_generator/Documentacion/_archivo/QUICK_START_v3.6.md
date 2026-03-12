# 🚀 QUICK START - WORKFLOW v3.6

**Fecha:** 2026-02-13  
**Sistema:** Workflow unificado con carpetas de producto

---

## 📁 **ESTRUCTURA EN GOOGLE DRIVE**

```
G:\Mi unidad\recursos_videos\
├── melatonina_aldous_500comp/
│   ├── input_producto.json       ← TÚ creas este
│   ├── bof_generado.json          ← Se genera automáticamente
│   ├── hooks/
│   │   ├── hook_1.mp4
│   │   └── hook_2.mp4
│   ├── brolls/
│   │   ├── A_producto.mp4
│   │   ├── B_mano.mp4
│   │   └── C_fondo.mp4
│   └── audios/
│       ├── bof1_andaluz.mp3
│       └── bof1_chavalita.mp3
│
├── cable_goojodoq_65w/
│   ├── input_producto.json
│   ├── bof_generado.json
│   ├── hooks/
│   ├── brolls/
│   └── audios/
│
└── ... (más productos)
```

---

## 📝 **PASO 1: CREAR ESTRUCTURA DE PRODUCTO**

### **1.1. Crear carpeta en Drive:**
```
G:\Mi unidad\recursos_videos\melatonina_aldous_500comp\
```

**Naming:** `{producto}_{marca}_{caracteristica_distintiva}`

Ejemplos:
- `melatonina_aldous_500comp`
- `cable_goojodoq_65w`
- `proyector_magcubic_hy300`
- `manta_niklok_160x130`

---

### **1.2. Crear `input_producto.json`:**

Dentro de la carpeta del producto, crea `input_producto.json`:

```json
{
  "marca": "Aldous Bio",
  "producto": "Melatonina Pura",
  "caracteristicas": ["500 comprimidos", "5mg", "tienda oficial"],
  "deal_math": "40% OFF",
  "url_producto": "https://s.click.aliexpress.com/tu-link"
}
```

**Campos:**
- `marca`: Marca del producto (puede estar vacía: `""`)
- `producto`: Nombre legible del producto
- `caracteristicas`: Lista de características clave
- `deal_math`: Deal Math exacto (40% OFF, MENOS DE 20€, etc.)
- `url_producto`: URL afiliada del producto

---

### **1.3. Subir material:**

Dentro de la carpeta del producto:

**hooks/**
- Mínimo 10 clips de 3.5s
- Formato: `.mp4` o `.mov`
- Naming: `hook_1.mp4`, `hook_boom_START2.mp4`, etc.

**brolls/**
- Mínimo 20 clips de 3.5s
- Con grupos: `A_producto.mp4`, `B_mano.mp4`, `C_fondo.mp4`
- Sin grupos: `broll_1.mp4`, `broll_2.mp4`

**audios/**
- Mínimo 3 audios por BOF
- Naming: `bof1_andaluz.mp3`, `bof1_chavalita.mp3`
- Formato: `.mp3`, `.wav`, `.m4a`

---

## 🎬 **PASO 2: ESCANEAR Y GENERAR TODO**

### **Comando único (recomendado):**

```powershell
python scan_material.py melatonina_aldous_500comp --auto-bof
```

**Este comando hace TODO:**
1. ✅ Lee `input_producto.json`
2. ✅ Genera `bof_generado.json` automáticamente
3. ✅ Importa BOF a la base de datos
4. ✅ Escanea hooks, brolls y audios
5. ✅ Registra todo en la BD

---

### **Modo tradicional (paso a paso):**

Si prefieres hacer cada paso manualmente:

**2.1. Generar BOF:**
```powershell
python bof_generator.py --input "G:\Mi unidad\recursos_videos\melatonina_aldous_500comp"
```

**2.2. Importar BOF:**
```powershell
python import_bof.py melatonina_aldous_500comp "G:\Mi unidad\recursos_videos\melatonina_aldous_500comp\bof_generado.json"
```

**2.3. Escanear material:**
```powershell
python scan_material.py melatonina_aldous_500comp
```

---

## 📊 **PASO 3: VALIDAR**

```powershell
python validate_bof.py melatonina_aldous_500comp
```

**Verifica:**
- ✅ 10+ hooks
- ✅ 20+ brolls (6 grupos)
- ✅ 5+ variantes de overlay
- ✅ 3+ audios vinculados

---

## 🎥 **PASO 4: GENERAR VIDEOS**

```powershell
python main.py --producto melatonina_aldous_500comp --batch 20 --cuenta lotopdevicky
```

**Output:** 20 videos en `C:/Users/TuUsuario/Videos/videos_generados_py/lotopdevicky/`

---

## 📅 **PASO 5: PROGRAMAR**

```powershell
python programador.py --cuenta lotopdevicky --dias 7
```

**Crea calendario de 7 días con:**
- Distancia entre hooks: 12 publicaciones
- Gap entre videos: 1 hora
- Max 2 videos del mismo producto/día

---

## ✅ **VENTAJAS DEL NUEVO SISTEMA**

### **Todo autocontenido:**
- ✅ Cada producto tiene su carpeta única
- ✅ JSON de entrada en la misma carpeta
- ✅ BOF generado en la misma carpeta
- ✅ Material organizado (hooks/brolls/audios)

### **Naming limpio:**
- ✅ Nombres legibles en JSON (`"Melatonina Pura"`)
- ✅ Identificadores únicos en carpetas (`melatonina_aldous_500comp`)
- ✅ No hay confusión de nombres

### **Un solo comando:**
- ✅ `--auto-bof` hace todo el trabajo
- ✅ Genera + Importa + Escanea en un paso
- ✅ Ahorra tiempo y errores

---

## 🎯 **EJEMPLOS COMPLETOS**

### **Producto 1: Melatonina Aldous**

```powershell
# 1. Crear carpeta
mkdir "G:\Mi unidad\recursos_videos\melatonina_aldous_500comp"

# 2. Crear input_producto.json
# (editarlo manualmente con los datos)

# 3. Subir material a hooks/, brolls/, audios/

# 4. Escanear todo
python scan_material.py melatonina_aldous_500comp --auto-bof

# 5. Generar videos
python main.py --producto melatonina_aldous_500comp --batch 20 --cuenta lotopdevicky
```

---

### **Producto 2: Cable GOOJODOQ (múltiples BOFs)**

```powershell
# Carpeta
mkdir "G:\Mi unidad\recursos_videos\cable_goojodoq_65w"

# BOF 1: Threshold
# input_producto.json con "deal_math": "POR MENOS DE 7€"
python scan_material.py cable_goojodoq_65w --auto-bof

# BOF 2: Reinvestment (misma carpeta, diferente deal_math)
# Editar input_producto.json → "deal_math": "TE QUEDAS CON 3€"
# Borrar bof_generado.json
python scan_material.py cable_goojodoq_65w --auto-bof

# Ahora tienes 2 BOFs del mismo producto con diferentes ángulos
```

---

## ⚠️ **IMPORTANTE**

### **Nombre de carpeta = Identificador único:**
- La carpeta debe tener nombre único: `producto_marca_caract`
- Ese nombre es el que usas en todos los comandos
- NO importa cómo se llame el producto dentro del JSON

### **JSON legible, carpeta identificable:**
- JSON: `"producto": "Melatonina Pura"` (legible)
- Carpeta: `melatonina_aldous_500comp` (identificador único)
- Comandos: `melatonina_aldous_500comp`

---

## 🔄 **REGENERAR BOF**

Si quieres regenerar el BOF (por ejemplo, cambiar deal_math):

```powershell
# 1. Editar input_producto.json con nuevo deal_math
# 2. Borrar bof_generado.json
del "G:\Mi unidad\recursos_videos\melatonina_aldous_500comp\bof_generado.json"

# 3. Regenerar
python scan_material.py melatonina_aldous_500comp --auto-bof
```

---

## 🆘 **TROUBLESHOOTING**

**"No se encontró input_producto.json"**
→ Crea el archivo en la carpeta del producto

**"BOF ya existe"**
→ Borra `bof_generado.json` para regenerar

**"Carpeta del producto no existe"**
→ Verifica ruta en `config.py` (GOOGLE_DRIVE_PATH)
→ Crea la carpeta en `G:\Mi unidad\recursos_videos\`

**"No se encontró bof_generator.py"**
→ Ejecuta desde la carpeta raíz del proyecto (`video_generator/`)

---

**¡Sistema listo!** 🚀
