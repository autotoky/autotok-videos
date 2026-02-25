# 🐛 CASOS DE USO Y EDGE CASES - AUTOTOK

**Versión:** 1.0  
**Fecha creación:** 2026-02-11  
**Última revisión:** 2026-02-11

---

## 📋 ÍNDICE

1. [Gestión de Materiales](#gestión-de-materiales)
2. [Generación de Videos](#generación-de-videos)
3. [Programación y Calendario](#programación-y-calendario)
4. [Sincronización y Estados](#sincronización-y-estados)

---

## 🎬 GESTIÓN DE MATERIALES

### **CASO #001: Archivo de audio renombrado después de registro**

**Módulo:** Gestión de materiales  
**Escenario:** Archivo de audio ya en BBDD se renombra manualmente en Drive  
**Incidencia:** El sistema busca el audio por filename registrado y al no encontrarlo da error. La generación de videos falla.

**Ejemplo:**
```
1. Audio registrado: a1_magcubic.mp3
2. Usuario renombra en Drive: a1_magcubic_nuevo.mp3
3. Generator intenta usar a1_magcubic.mp3
4. Error: Archivo no encontrado
```

**Impacto:** 
- Generación de videos falla parcialmente
- Videos que no usan ese audio se generan OK
- Videos que lo necesitan se saltan

**Soluciones propuestas:**

**A) Solución operativa (actual):**
- ✅ **NO renombrar archivos** una vez registrados en DB
- ✅ Si necesitas renombrar: 
  1. Eliminar registro de DB
  2. Renombrar archivo
  3. Re-registrar con nuevo nombre

**B) Solución en código (futura - TBD):**
- [ ] Validación pre-generación: verificar que todos los archivos existen
- [ ] Auto-detección de cambios: escanear y actualizar filenames si hash coincide
- [ ] Gestión de errores graceful: skip y continuar con siguiente combinación
- [ ] Warning al usuario: "X archivos registrados no encontrados"

**Estado:** Pendiente de análisis  
**Prioridad:** ⭐ Baja (workaround operativo funciona)  
**Frecuencia observada:** 1 vez (2026-02-11)  
**Decisión:** Evaluar en revisión mensual si se repite

---

### **CASO #003: Desincronización por movimiento manual de archivos**

**Módulo:** Sincronización y Estados  
**Escenario:** Video está marcado con un estado en Sheet (ej: "Borrador") y en su carpeta correspondiente. Usuario mueve manualmente el archivo a otra carpeta (ej: `programados/`) sin actualizar el estado en Sheet primero.

**Incidencia:** 
- Sheet indica un estado (ej: "Borrador")
- Archivo físico está en otra ubicación (ej: `programados/`)
- Al ejecutar `--sync`, el sistema intenta mover el video de vuelta a la ubicación que indica Sheet, deshaciendo el cambio manual

**Ejemplo:**
```
1. Video en Sheet: "Borrador", carpeta: borrador/2026-02-15/
2. Usuario mueve manualmente a: programados/2026-02-15/
3. Ejecuta: python mover_videos.py --sync
4. Sistema busca video para "Borrador"
5. Lo encuentra en programados/ y lo mueve de vuelta a borrador/
6. Cambio manual perdido
```

**Impacto:**
- Desincronización entre Sheet, filesystem y DB
- Pérdida de cambios manuales
- Confusión sobre estado real del video

**Soluciones propuestas:**

**A) Solución operativa (ACTUAL):**
- ✅ **REGLA: NO mover archivos manualmente** una vez que están en Sheet
- ✅ **Workflow correcto:**
  1. Actualizar estado en Sheet primero
  2. Ejecutar `python mover_videos.py --sync`
  3. Sistema mueve automáticamente
- ✅ **Antes de programar:** Ejecutar siempre `--sync` para asegurar que todo está actualizado

**B) Solución en código (futura - TBD):**
- [ ] Comando `--reconciliar`: Detecta conflictos filesystem vs Sheet y pregunta qué hacer
- [ ] Modo inteligente: Al hacer `--sync`, detectar y notificar conflictos antes de mover
- [ ] Validación preventiva: Avisar si archivos se movieron manualmente

**Estado:** Pendiente de análisis  
**Prioridad:** ⭐ Baja (workaround operativo claro)  
**Frecuencia observada:** 0 veces (preventivo, detectado en diseño)  
**Decisión:** Usar regla operativa, evaluar necesidad de código si se repite > 3 veces/mes

---

## 📝 PLANTILLA PARA NUEVOS CASOS

```markdown
### **CASO #XXX: Título descriptivo**

**Módulo:** [Gestión de materiales / Generación / Programación / Estados]  
**Escenario:** Descripción detallada de qué pasa  
**Incidencia:** Qué error o problema causa  

**Ejemplo:**
[Pasos para reproducir]

**Impacto:**
- Consecuencia 1
- Consecuencia 2

**Soluciones propuestas:**

**A) Solución operativa:**
- Regla/proceso manual

**B) Solución en código:**
- [ ] Opción técnica 1
- [ ] Opción técnica 2

**Estado:** [Pendiente / En análisis / Resuelto]  
**Prioridad:** [⭐ Baja / ⭐⭐ Media / ⭐⭐⭐ Alta / 🔥 Crítica]  
**Frecuencia observada:** X veces (fechas)  
**Decisión:** [Acción tomada o pendiente]
```

---

## 📊 ESTADÍSTICAS

**Total casos documentados:** 3  
**Por prioridad:**
- 🔥 Crítica: 0
- ⭐⭐⭐ Alta: 0
- ⭐⭐ Media: 0
- ⭐ Baja: 3

**Por estado:**
- Pendiente: 3
- En análisis: 0
- Resuelto: 0

---

## 🔄 PROCESO DE REVISIÓN

### **Revisión semanal:**
- Ver casos nuevos
- Actualizar frecuencias
- Re-priorizar según impacto real

### **Revisión mensual:**
- Casos con frecuencia > 5: considerar solución código
- Casos con prioridad Alta/Crítica: implementar solución
- Casos Baja sin repetición: mantener solución operativa

### **Criterios de priorización:**

**🔥 Crítica:** 
- Bloquea operación completamente
- Pérdida de datos
- Afecta a todos los usuarios

**⭐⭐⭐ Alta:**
- Impacto significativo en productividad
- Workaround complejo
- Frecuencia > 1 vez/semana

**⭐⭐ Media:**
- Impacto moderado
- Workaround simple existe
- Frecuencia ocasional

**⭐ Baja:**
- Impacto mínimo
- Workaround muy simple
- Frecuencia rara

---

## 📝 CHANGELOG

**2026-02-11:**
- Documento creado
- Caso #001 añadido: Audio renombrado
- Caso #002 añadido: Fecha inicio programación (resuelto con `--fecha-inicio`)
- Caso #003 añadido: Desincronización por movimiento manual
