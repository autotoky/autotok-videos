# 🔧 FIXES PENDIENTES - AUTOTOK

**Versión:** 1.0  
**Fecha creación:** 2026-02-13  
**Última revisión:** 2026-02-13

---

## 📋 ÍNDICE DE FIXES

- [Prioridad Alta](#prioridad-alta)
- [Prioridad Media](#prioridad-media)
- [Prioridad Baja](#prioridad-baja)

---

## 🔴 PRIORIDAD ALTA

*Ningún fix pendiente*

---

## 🟡 PRIORIDAD MEDIA

### **FIX #001: Mover manualmente archivo BOF generado para generar múltiples BOFs por producto**

**Módulo:** Generación de videos  
**Estado:** Pendiente de evaluar  
**Fecha reportado:** 2026-02-13

**Problema actual:**
Para generar varios BOFs del mismo producto, hay que mover manualmente el archivo del BOF generado a otra carpeta después de cada generación.

**Impacto:**
- Proceso manual tedioso
- Frena la generación en batch de múltiples BOFs
- Posibilidad de error humano (olvidar mover, mover a carpeta incorrecta)

**Workflow actual:**
1. Generar video con BOF_A
2. Mover manualmente el video generado a otra carpeta
3. Generar video con BOF_B
4. Repetir...

**Soluciones a evaluar:**
- [ ] Permitir flag `--generar-todos-bofs` que genere automáticamente un video por cada BOF disponible
- [ ] Sistema de carpetas automático por BOF
- [ ] Queue de BOFs pendientes que se procesa secuencialmente
- [ ] Mejorar lógica de tracking para no requerir movimiento manual

**Decisión:** Pendiente de análisis y validación de solución

---

## 🟢 PRIORIDAD BAJA

*Ningún fix pendiente*

---

## 📊 ESTADÍSTICAS

**Total fixes:** 1  
**Por prioridad:**
- 🔴 Alta: 0
- 🟡 Media: 1
- 🟢 Baja: 0

**Por estado:**
- Pendiente de evaluar: 1
- En análisis: 0
- En desarrollo: 0
- Resuelto: 0

---

## 📝 PLANTILLA PARA NUEVOS FIXES

```markdown
### **FIX #XXX: Título descriptivo del problema**

**Módulo:** [Generación / Programación / Sincronización / etc.]  
**Estado:** [Pendiente de evaluar / En análisis / En desarrollo / Resuelto]  
**Fecha reportado:** YYYY-MM-DD  
**Fecha resuelto:** YYYY-MM-DD (si aplica)

**Problema actual:**
Descripción clara del problema

**Impacto:**
- Consecuencia 1
- Consecuencia 2

**Workflow actual:**
Pasos que muestran el problema

**Soluciones a evaluar:**
- [ ] Opción 1
- [ ] Opción 2

**Decisión:** [Descripción de la decisión tomada o pendiente]
```

---

## 🔄 PROCESO DE REVISIÓN

- **Semanal:** Revisar fixes pendientes, actualizar estados
- **Al resolver:** Mover a sección "Resueltos" con fecha y solución implementada
- **Criterios de priorización:**
  - 🔴 **Alta:** Bloquea operación, pérdida de datos, afecta producción
  - 🟡 **Media:** Impacto moderado, workaround manual existe pero tedioso
  - 🟢 **Baja:** Impacto mínimo, mejora incremental

---

**FIN DOCUMENTO FIXES v1.0**
