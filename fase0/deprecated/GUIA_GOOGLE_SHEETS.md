# 📊 GUÍA GOOGLE SHEETS - SISTEMA TIKTOK SHOP

## 🎯 SHEETS CREADOS:

1. **carol_input** - Carol rellena aquí diariamente
2. **produccion_mar** - Mar lee y ejecuta desde aquí
3. **creditos_tracking** - Sistema automático (no tocar)
4. **bof_learning** - Sistema automático (no tocar)
5. **metricas_tiktok** - Para después (no usar aún)

---

## 📝 SHEET 1: "carol_input"

### COLUMNAS:

| Columna | Qué poner | Ejemplo |
|---------|-----------|---------|
| **producto** | Nombre del producto | Batería Magnética iPhone |
| **variacion** | Número de variación (1-5) | 1 |
| **script_bof** | Script completo BOF generado | "¿1 batería magnética gratis? Para conseguirlo, solo... Toca el carrito naranja..." |
| **seo_verbiage** | Texto descripción SEO | "3 baterías magnéticas por menos de 24€, envío incluido. Compatible iPhone 12/13/14/15." |
| **hashtags** | Tags separados por espacios | #iPhone #bateria #magsafe #oferta #tecnologia |
| **url_producto** | Link producto TikTok / Kalodata | https://es.aliexpress.com/item/... |
| **video_tool** | Herramienta a usar | heygen ó hailuo |

### INSTRUCCIONES CAROL:

**CADA DÍA:**
1. Elige 5 productos
2. Para cada producto, genera 5 variaciones de scripts BOF
3. Rellena las 25 filas (5 productos × 5 variaciones)
4. Asegúrate de que cada script sigue la estructura BOF:
   - Open Loop (gancho)
   - Transition
   - CTA #1
   - Why Should They
   - Value Breakdown
   - Close the Loop
   - CTA #2

**TIPS:**
- Varía la urgencia: "último día", "quedan pocas", "oferta flash"
- Varía el CTA: "toca el carrito", "no esperes", "aprovecha ahora"
- Usa diferentes ángulos del mismo producto

**EJEMPLOS DE VARIACIÓN (mismo producto):**

**Variación 1 (urgencia temporal):**
"¿1 batería magnética gratis? Para conseguirlo, solo... Toca el carrito naranja. Para desbloquear la oferta flash. Añade tres al carrito. Como superas los 20€, TikTok te da envío gratis. Así, en lugar de pagar envío por cada una, te llevas tres por el precio de dos. Solo hoy - toca el carrito ya."

**Variación 2 (precio bajo):**
"3 baterías por menos de 24€, envío incluido. Para hacerlo, solo... Toca el carrito naranja. Para desbloquear el envío gratis al llevarte 3. Cada batería cuesta solo 7,99€, y al añadir tres, el envío se vuelve gratuito. Así, pagas menos de 24€ total por las tres. Solo por hoy - toca el carrito ya."

**DECISIÓN video_tool:**
- **heygen** → Si el producto necesita manos/persona mostrándolo (dispositivos, gadgets que se sostienen)
- **hailuo** → Si el producto solo necesita movimiento cinematográfico (decoración, productos planos)

---

## 🎨 SHEET 2: "produccion_mar"

### COLUMNAS:

| Columna | Qué es | Mar hace |
|---------|--------|----------|
| **id** | AUTO (sistema lo genera) | No tocar |
| **fecha** | AUTO (sistema lo genera) | No tocar |
| **producto** | Nombre producto | Leer |
| **script_bof** | Script de Carol | Leer |
| **prompt_heygen** | Prompt generado para HeyGen | COPIAR a HeyGen |
| **prompt_hailuo** | Prompt generado para Hailuo | COPIAR a Hailuo |
| **imagen_url** | Link imagen limpia | Mar la busca y pega aquí |
| **status** | Estado | Cambiar a "done" cuando termine |
| **feedback_calidad** | Calidad 1-5 | Mar califica el video |
| **feedback_notas** | Notas | Mar escribe mejoras |

### INSTRUCCIONES MAR:

**PROCESO DIARIO:**

1. **Leer fila siguiente con status "pending"**

2. **Buscar imagen producto:**
   - Ir a `url_producto` de la sheet de Carol
   - Descargar mejor imagen del producto
   - Limpiar fondo (Remove.bg web gratis o Photopea)
   - Subir imagen a algún lugar (Google Drive, Imgur, etc)
   - Pegar link en columna `imagen_url`

3. **Leer el prompt correcto:**
   - Si `video_tool` = heygen → usar columna `prompt_heygen`
   - Si `video_tool` = hailuo → usar columna `prompt_hailuo`

4. **Generar video:**
   
   **Para HeyGen:**
   - Entrar a HeyGen
   - Crear nuevo video
   - Copiar el prompt de `prompt_heygen`
   - Pegar en HeyGen
   - Subir imagen del producto
   - Generar video
   - Descargar

   **Para Hailuo:**
   - Entrar a Hailuo
   - Crear nuevo video
   - Copiar el prompt de `prompt_hailuo`
   - Pegar en Hailuo
   - Subir imagen del producto
   - Generar video
   - Descargar

5. **Dar feedback:**
   - `status`: cambiar a "done"
   - `feedback_calidad`: poner número 1-5
     - 5 = Perfecto
     - 4 = Muy bueno
     - 3 = Aceptable
     - 2 = Mejorable
     - 1 = Malo
   - `feedback_notas`: escribir qué mejorar
     - "Avatar muy serio, debería sonreír más"
     - "Movimiento demasiado rápido"
     - "Fondo distrae del producto"
     - "Hands gestures no naturales"
     - "Script demasiado largo, se corta"

6. **Repetir con siguiente fila**

**IMPORTANTE:**
- El feedback es CRÍTICO para que el sistema aprenda
- Sé específica en las notas
- Si algo no funciona, escribe exactamente qué

---

## 📊 SHEET 3: "creditos_tracking"

**NO TOCAR - SISTEMA AUTOMÁTICO**

El sistema calculará automáticamente:
- Créditos usados por video
- Coste real por video
- Créditos restantes del mes
- Proyección de gasto

---

## 🧠 SHEET 4: "bof_learning"

**NO TOCAR - SISTEMA AUTOMÁTICO**

El sistema analizará automáticamente:
- Patrones en scripts de Carol
- Palabras de urgencia más usadas
- Estructura CTA más efectiva
- Similitud entre sistema y Carol

---

## 📈 SHEET 5: "metricas_tiktok"

**PARA DESPUÉS - NO USAR AÚN**

Cuando tengamos videos publicados, aquí se registrarán:
- Views, likes, shares
- Ventas generadas
- ROI por video
- Qué tipo de script funciona mejor

---

## 🎨 FORMATO RECOMENDADO SHEETS:

### Para que sea más visual:

**Sheet carol_input:**
- Congelar fila 1 (headers)
- Alternar colores filas (más fácil leer)
- Ancho columnas ajustado

**Sheet produccion_mar:**
- Congelar fila 1 (headers)
- Columna `status` con colores:
  - pending = amarillo
  - done = verde
- Columna `feedback_calidad` con formato condicional:
  - 5 = verde oscuro
  - 4 = verde claro
  - 3 = amarillo
  - 2 = naranja
  - 1 = rojo

---

## ⚠️ REGLAS IMPORTANTES:

1. **Carol SOLO escribe en "carol_input"**
2. **Mar SOLO escribe en "produccion_mar"**
3. **NO modificar sheets 3, 4, 5** (sistema automático)
4. **NO borrar columnas** (el sistema las necesita)
5. **NO cambiar nombres de sheets** (el sistema no los encontrará)

---

## 🆘 SI ALGO NO FUNCIONA:

1. Verificar que todas las columnas existen
2. Verificar que los nombres de sheets son exactos
3. Verificar que hay permisos de edición
4. Contactar con quien configuró el sistema

---

## 📞 PREGUNTAS FRECUENTES:

**¿Cuántas filas relleno por día?**
- Carol: 25 filas (5 productos × 5 variaciones)
- Mar: Todas las que pueda (objetivo 25/día)

**¿Qué pasa si me equivoco?**
- Edita la celda y corrige
- Si es grave, avisa para revisar

**¿Puedo añadir más columnas?**
- NO - El sistema no las leerá

**¿Puedo borrar filas antiguas?**
- NO todavía - Necesitamos el histórico para aprender

**¿Cuándo veré resultados del aprendizaje?**
- Después de 1-2 semanas con datos suficientes
