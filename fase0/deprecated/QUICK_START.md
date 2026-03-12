# ⚡ QUICK START - EMPIEZA AHORA SIN ESPERAR AL CÓDIGO

## 🎯 OBJETIVO:

Carol y Mar pueden empezar a trabajar HOY mientras se termina el código automático.

---

## 👩‍💼 CAROL - EMPIEZA YA:

### PASO 1: Abre tu sheet "carol_input"

Links de tus sheets:
- carol_input: https://docs.google.com/spreadsheets/d/1eXuPwNcHn3wy4nFmK8jkhZf2ESmjtylaaXwj78TFWx0
- produccion_mar: https://docs.google.com/spreadsheets/d/1EIsD_FoQCJlPXvcFiqDx00_AEYDQWW4faBIoSzcDqrk
- creditos_tracking: https://docs.google.com/spreadsheets/d/1LwjsvfVk8GhOjXUJp5F1BDArtoAFhfzttJKr800j0gQ
- bof_learning: https://docs.google.com/spreadsheets/d/10D8_w6RyonnWO4VhneijHz3MIkmXWLxIkIuFJvSqpw4
- metricas_tiktok: https://docs.google.com/spreadsheets/d/1VQLzrHhWaohjOWhKFCpMpJgCupCqcrWhdWKy6TQ8ewg

### PASO 2: Añade estos headers en la primera fila:

```
producto | variacion | script_bof | seo_verbiage | hashtags | url_producto | video_tool
```

### PASO 3: Empieza a rellenar siguiendo este ejemplo:

**Producto:** Batería Magnética iPhone
**Variación 1:**
- producto: `Batería Magnética iPhone`
- variacion: `1`
- script_bof: `¿1 batería magnética gratis? Para conseguirlo, solo... Toca el carrito naranja. Para desbloquear la oferta flash. Añade tres al carrito. Como superas los 20€, TikTok te da envío gratis. Así, en lugar de pagar envío por cada una, te llevas tres por el precio de dos. Solo hoy - toca el carrito ya.`
- seo_verbiage: `3 baterías magnéticas por menos de 24€ envío incluido. Compatible iPhone 12/13/14/15. 5000mAh.`
- hashtags: `#iPhone #bateria #magsafe #oferta #tecnologia`
- url_producto: `https://es.aliexpress.com/item/...` (tu link real)
- video_tool: `heygen`

### PASO 4: Genera 4 variaciones más del mismo producto

Cambia:
- El gancho (open loop)
- La urgencia
- El ángulo del deal
- Pero mantén el producto igual

### PASO 5: Repite con 4 productos más

**Total hoy: 25 filas (5 productos × 5 variaciones)**

---

## 👩‍🎨 MAR - EMPIEZA YA (PROCESO MANUAL HOY):

### PASO 1: Abre sheet "produccion_mar"

### PASO 2: Añade estos headers:

```
id | fecha | producto | script_bof | prompt_heygen | prompt_hailuo | imagen_url | status | feedback_calidad | feedback_notas
```

### PASO 3: COPIA manualmente desde carol_input:

Por ahora (hasta que el código automático esté):
1. Ve a sheet de Carol
2. Copia la fila 2 (primera con datos)
3. Pega en tu sheet en las columnas: producto, script_bof
4. Añade:
   - id: `001`
   - fecha: `2026-01-31`
   - status: `pending`

### PASO 4: GENERA los prompts manualmente:

**Si video_tool = heygen:**

Escribe en `prompt_heygen`:
```
Create a 15-second UGC-style video featuring a young adult presenter holding [PRODUCTO] with natural hand gestures.

Script to present (in Spanish):
[COPIA AQUÍ EL SCRIPT_BOF DE CAROL]

Style: Casual, energetic, authentic home background, good lighting, maintain natural eye contact, show product clearly in hands during key moments.

Voice: Spanish (Spain), conversational tone, enthusiastic delivery matching the urgency in the script.
```

**Si video_tool = hailuo:**

Escribe en `prompt_hailuo`:
```
Product showcase video of [PRODUCTO]. 
Camera: Smooth 360° rotation around product on clean white surface. 
Lighting: Professional studio setup with soft shadows. 
Movement: Product slightly rotates, elegant reveal of features. 
Style: High-end commercial, cinematic quality.
Duration: 10 seconds
```

### PASO 5: Busca la imagen:

1. Ve al `url_producto` de Carol
2. Descarga mejor foto del producto
3. Limpia fondo: https://www.remove.bg (gratis)
4. Sube a Google Drive o Imgur
5. Pega link en `imagen_url`

### PASO 6: Genera el video:

**HeyGen:**
- Ve a HeyGen
- Pega el prompt
- Sube la imagen
- Genera
- Descarga

**Hailuo:**
- Ve a Hailuo
- Pega el prompt
- Sube la imagen
- Genera
- Descarga

### PASO 7: Da feedback:

- `status`: `done`
- `feedback_calidad`: `1-5` (5=perfecto)
- `feedback_notas`: Escribe qué mejorar

Ejemplos notas:
- "Avatar demasiado serio, necesita sonreír"
- "Script muy largo, se corta al final"
- "Manos no se ven bien el producto"
- "Perfecto, mantener este estilo"

### PASO 8: Repite con siguiente fila

**Meta: 25 videos hoy**

---

## 🚀 CUANDO EL CÓDIGO ESTÉ LISTO:

El código automático hará esto por ti:
- ✅ Leer automáticamente de carol_input
- ✅ Generar prompts optimizados
- ✅ Escribir automáticamente a produccion_mar
- ✅ Calcular créditos
- ✅ Analizar patrones BOF
- ✅ Mejorar con feedback de Mar

**Pero por ahora, esto funciona manual para empezar YA.** ✨

---

## 📊 FORMATO BONITO (OPCIONAL PERO RECOMENDADO):

### En carol_input:
1. Selecciona fila 1 (headers)
2. Formato → Negrita
3. Formato → Fondo gris oscuro
4. Formato → Texto blanco

### En produccion_mar:
1. Lo mismo con headers
2. Columna `status`:
   - Selecciona toda la columna
   - Formato → Formato condicional
   - Si texto contiene "pending" → fondo amarillo
   - Si texto contiene "done" → fondo verde

3. Columna `feedback_calidad`:
   - Formato condicional
   - Si valor = 5 → verde oscuro
   - Si valor = 4 → verde claro
   - Si valor = 3 → amarillo
   - Si valor = 2 → naranja
   - Si valor = 1 → rojo

---

## ⏰ TIMING ESTIMADO:

**Carol:**
- 5 productos × 5 variaciones = 25 scripts
- Tiempo: ~2-3 horas
- (Con práctica bajará a 1-2 horas)

**Mar:**
- 25 videos
- Tiempo por video: ~5-10 min
- Total: ~2-4 horas
- (Con práctica bajará a 3-5 min/video → 2h total)

---

## ✅ CHECKLIST INICIO:

**Carol:**
- [ ] Sheet abierto
- [ ] Headers añadidos
- [ ] Entiendo qué es cada columna
- [ ] Tengo Custom GPT listo para generar scripts
- [ ] Tengo URLs de productos preparados

**Mar:**
- [ ] Sheet abierto
- [ ] Headers añadidos
- [ ] Tengo acceso a HeyGen (plan Creator €25/mes)
- [ ] Tengo acceso a Hailuo (plan Pro $28/mes)
- [ ] Tengo Remove.bg o Photopea para limpiar fondos

---

## 🆘 PROBLEMAS COMUNES:

**Carol: "¿Cómo genero variaciones?"**
→ Usa tu Custom GPT, dale el producto y pídele 5 scripts diferentes con distintos ángulos

**Mar: "¿Qué pongo en prompt si no sé?"**
→ Usa los templates de arriba, solo cambia [PRODUCTO] y el script

**Mar: "¿La imagen debe estar limpia?"**
→ SÍ, sin fondo. Usa remove.bg gratis

**Mar: "¿Qué hago si el video sale mal?"**
→ Pon feedback_calidad bajo (1-2) y explica en notas qué falló

---

## 💡 TIPS PRO:

**Carol:**
- Guarda tus mejores scripts como plantillas
- Reutiliza estructura que funciona
- Varía solo el ángulo y urgencia

**Mar:**
- Descarga todas las imágenes al inicio
- Procesa todas con remove.bg de golpe
- Genera varios videos seguidos

---

**¡A TRABAJAR! El código automático llegará pronto pero no es excusa para no empezar.** 💪🚀
