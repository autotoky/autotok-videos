---
Versión: v0.2.0
Última actualización: 2026-01-31
Estado: ACTIVO
Para: Mar (Producción de videos)
---

# 🎨 GUÍA MAR - PRODUCCIÓN DE VIDEOS

## 🎯 TU MISIÓN:

Generar **25 videos de alta calidad por día** usando los prompts que el sistema genera automáticamente.

---

## ✅ TU TRABAJO:

1. ✅ Generar 25 videos/día con HeyGen o Hailuo
2. ✅ Dar feedback de calidad para mejorar prompts futuros
3. ✅ Mantener calidad promedio >4/5

## ❌ NO ES TU TRABAJO:

- ❌ Generar scripts BOF (lo hace Carol)
- ❌ Crear prompts (lo hace el sistema)
- ❌ Programar publicaciones TikTok (lo hace Sara)
- ❌ Tracking de métricas (lo hace el sistema)

---

## 🔄 PROCESO DIARIO (3-4 horas):

### **PASO 1: Abrir tu sheet (9:00 AM)**

Link: https://docs.google.com/spreadsheets/d/10D8_w6RyonnWO4VhneijHz3MIkmXWLxIkIuFJvSqpw4

Verás algo así:

| id | producto | prompt_heygen | prompt_hailuo | status |
|----|----------|---------------|---------------|--------|
| 001 | Batería iPhone | Create a 15-sec... | Product showcase... | **pending** |
| 002 | Batería iPhone | Create a 15-sec... | Product showcase... | **pending** |

---

### **PASO 2: Filtrar pendientes**

1. Click en cabecera columna `status`
2. Filtro → Mostrar solo: **pending**
3. Ahora solo ves los que tienes que hacer

---

### **PASO 3: Generar cada video (10-15 min/video)**

#### **3.1. Decidir herramienta:**

**Usa HEYGEN si:**
- El producto necesita manos/persona mostrándolo
- Gadgets, dispositivos electrónicos
- Productos que se sostienen

**Usa HAILUO si:**
- Solo necesitas movimiento de cámara
- Productos planos (decoración, ropa, accesorios)
- Necesitas movimiento cinematográfico

#### **3.2. Buscar imagen producto:**

1. Click en el link `url_producto` de esa fila
2. Descarga la mejor imagen del producto
3. Limpia fondo con https://remove.bg (gratis)
4. Guarda imagen limpia

#### **3.3A. Si eliges HEYGEN:**

1. Abre HeyGen
2. Crea nuevo video
3. **COPIA el texto de columna `prompt_heygen`**
4. Pégalo en HeyGen
5. Sube la imagen limpia del producto
6. Genera video
7. Descarga cuando esté listo
8. Nombra archivo: `video_001.mp4` (usando el número del `id`)

#### **3.3B. Si eliges HAILUO:**

1. Abre Hailuo
2. Crea nuevo video
3. **COPIA el texto de columna `prompt_hailuo`**
4. Pégalo en Hailuo
5. Sube la imagen limpia del producto
6. Genera video
7. Descarga cuando esté listo
8. Nombra archivo: `video_001.mp4` (usando el número del `id`)

#### **3.4. Guardar video:**

Guarda en carpeta: `videos_listos/`

```
videos_listos/
├── video_001.mp4
├── video_002.mp4
└── ...
```

---

### **PASO 4: Actualizar la sheet (2 min/video)**

| Columna | Qué poner | Ejemplo |
|---------|-----------|---------|
| **herramienta_usada** | heygen o hailuo | `heygen` |
| **status** | Cambiar a: **done** | `done` |
| **feedback_calidad** | Calidad 1-5 | `4` |
| **feedback_notas** | Qué mejorar | "Avatar debería sonreír más" |

---

## ⭐ SISTEMA DE CALIFICACIÓN:

**5/5 - Perfecto** ✅  
Todo impecable, nada que mejorar

**4/5 - Muy bueno** ✅  
Pequeños detalles mejorables

**3/5 - Aceptable** ⚠️  
Funciona pero tiene issues evidentes

**2/5 - Mejorable** ❌  
Problemas que afectan calidad

**1/5 - Malo** ❌  
No sirve, hay que regenerar

---

## 💡 FEEDBACK ÚTIL (ejemplos):

### **Buenos ejemplos:**

✅ "Avatar demasiado serio, necesita sonreír más"  
✅ "Movimiento de cámara muy rápido"  
✅ "Producto apenas visible, necesita más zoom"  
✅ "Perfecto, mantener este estilo"  

### **Malos ejemplos:**

❌ "No me gusta"  
❌ "Está mal"

**Siempre explica QUÉ mejorar específicamente**

---

## ✅ CHECKLIST DIARIO:

- [ ] 25 filas con `status=done`
- [ ] Todas tienen `herramienta_usada`
- [ ] Todas tienen `feedback_calidad`
- [ ] 25 archivos en `/videos_listos/`
- [ ] Archivos nombrados: `video_001.mp4`, `video_002.mp4`, etc.

---

## 🆘 PROBLEMAS COMUNES:

**"No veo filas pending"**  
→ Sistema aún no procesó scripts de Carol

**"Prompt muy largo"**  
→ Copia solo lo importante, anota en feedback

**"Video sale mal"**  
→ Califica bajo (1-2), explica qué falla

---

**¡A crear videos increíbles!** 🚀🎬
