# 📝 LOG DE SESIÓN - 2026-02-14 (Parte 2)

**Inicio:** 10:45 CET  
**Estado:** En progreso

---

## 🎯 OBJETIVO DE LA SESIÓN

Continuación de trabajo tras primer cierre de sesión.

---

## ✅ CAMBIOS REALIZADOS

### 1. Cálculo videos necesarios para 7 días con restricciones (10:50)

**Usuario pregunta:** ¿Cuántos videos por producto necesito para llenar 7 días?

**Configuración:**
- Cuenta Trendy: 15 videos/día
- Cuenta Lotopdevicky: 7 videos/día
- **Total:** 22 videos/día × 7 días = **154 videos totales**

**Restricciones activas:**
1. Max 2 videos del mismo producto/día
2. Distancia mínima hooks: 12 publicaciones
3. Gap entre videos: 1 hora

**Análisis:**

**BUG CRÍTICO DETECTADO (10:55):**
- Setting `max_mismo_producto_por_dia` está configurado POR CUENTA
- Código actual lo aplica GLOBALMENTE por día (error)
- Debe verificar max por producto POR CUENTA, no sumando ambas cuentas

**Impacto:**
- Con 2 cuentas activas, se limita incorrectamente a 2 videos/producto/día TOTAL
- Debería permitir 2 videos/producto/día EN CADA CUENTA = 4 total/día

**Solución necesaria:**
Modificar `programador.py` línea 286 para que `productos_usados` sea por cuenta actual, no global.

**RESOLUCIÓN (11:05):**
- ❌ NO hay bug - Código está CORRECTO
- Confusión del asistente: El programador se ejecuta UNA VEZ POR CUENTA
- Cada ejecución filtra por su propia cuenta (línea 91: `WHERE cuenta = ?`)
- Restricciones son INDEPENDIENTES por cuenta

**Confirmado:**
- `max_mismo_producto_por_dia = 2` aplica POR CUENTA
- Distancia hooks (12 pub) se calcula POR CUENTA
- Ambas cuentas pueden usar mismo hook/producto el mismo día

**Cálculo final correcto:**
- Trendy: 15 videos/día × 7 días = 105 videos
- Lotopdevicky: 7 videos/día × 7 días = 49 videos
- Total necesario: 154 videos
- Con 10 productos: **22-24 videos por producto** (suficiente con 60 combos disponibles)
- ✅ Material actual (10 hooks × 6 variantes = 60 combos) es SUFICIENTE

---

### 2. Error registrando audios con scan_material.py (11:10)

**Usuario ejecuta:**
```powershell
python scripts\scan_material.py Taza_cafe_inteligente_tapa
```

**Error:**
```
[ERROR] NOT NULL constraint failed: audios.bof_id
```

**Causa:**
- `scan_material.py` intenta extraer `bof_id` del nombre del audio
- Si no encuentra BOF, `bof_id_real` queda en `None`
- Tabla `audios` requiere `bof_id` NOT NULL
- INSERT falla

**Causa REAL del bug:**
- `scan_material.py` usaba `LIMIT 1 OFFSET bof_id - 1` 
- Asumía que `bof1_` = primer BOF del producto, `bof2_` = segundo, etc.
- PERO el número en `bofN_` es el **BOF ID global**, no posición en producto
- Con `bof10_` buscaba el 10º BOF del producto (OFFSET 9)
- Producto solo tiene 1 BOF → No encuentra nada → `bof_id_real = None`

**Fix aplicado (11:15):**
```python
# ANTES (INCORRECTO):
SELECT id FROM producto_bofs 
WHERE producto_id = ?
ORDER BY id
LIMIT 1 OFFSET ?  # Busca por posición

# DESPUÉS (CORRECTO):
SELECT id FROM producto_bofs 
WHERE id = ? AND producto_id = ?  # Busca por ID exacto
```

**Archivo modificado:**
- `scan_material.py` (líneas 227-240)

**Ahora funciona correctamente:**
```powershell
python scripts\scan_material.py Taza_cafe_inteligente_tapa
```

**Confirmado por usuario (11:20):**
✅ 3 audios nuevos registrados correctamente

---

### 3. Añadida mejora: Interfaz CLI para tareas comunes (11:25)

**Usuario solicita:** Añadir a issues una interfaz para facilitar tareas comunes

**Añadido a ISSUES.md - Mejoras Futuras (Prioridad Media):**

**Interfaz CLI para tareas comunes**
- Menú interactivo para operaciones frecuentes
- Funciones principales:
  - Escanear material de un producto
  - Validar material disponible
  - Generar videos para todas las cuentas activas
  - Programar calendario para todas las cuentas
  - Ver estado de productos
- Tiempo estimado: 3-4 horas
- Reduce fricción y errores de sintaxis
- Ejemplo: `python cli.py` → menú interactivo

**Flexibilidad del módulo programador:**
- Análisis de casos de uso + implementación (6-8h total)
- Permitir reglas personalizadas por producto
- Casos: Priorizar productos, reglas específicas, ventanas horarias
- Requiere análisis previo de necesidades reales

---

### 4. Prototipo CLI interactivo creado (11:30)

**Archivo creado:** `cli.py` (prototipo funcional)

**Funcionalidades implementadas:**
1. ✅ Escanear material de un producto
2. ✅ Validar material disponible (muestra conteos + estado)
3. ✅ Generar videos (1 cuenta, 2 cuentas, o ambas)
4. ✅ Ver estado de todos los productos (tabla resumen)
5. ✅ Programar calendario (1 cuenta, 2 cuentas, o ambas)

**Características:**
- Menú interactivo con números
- Selección de productos desde BD
- Ejecuta comandos automáticamente
- Interfaz limpia con emojis
- Manejo de errores básico

**Uso:**
```powershell
python cli.py
```

**Mejoras futuras posibles:**
- [ ] Añadir exportar/editar BOFs
- [ ] Ver estadísticas de generación
- [ ] Configuración de cuentas
- [ ] Logs de ejecución

**Feedback usuario (11:35):**
✅ CLI funcionando correctamente
✅ "Ahorra un montón de trabajo"
✅ "Previene errores de tipeo"
🎉 Usuario muy satisfecho con la herramienta

**Bugs corregidos durante pruebas:**
- Fix 1: Nombres de tablas incorrectos (material_hooks → material con tipo='hook')
- Fix 2: Query de audios corregida
- Fix 3: Ver estado productos actualizado

---

### 5. Añadida mejora: Integración TikTok Analytics API (11:40)

**Usuario solicita:** Trackear rendimiento de videos publicados en TikTok

**Añadido a ISSUES.md - Mejoras Futuras (Prioridad Baja):**

**Integración TikTok Analytics API**
- 3 fases de implementación (8-12h total)
- Fase 1: Setup TikTok Business API + autenticación
- Fase 2: Sincronización de métricas (views, likes, comments, shares)
- Fase 3: Dashboard de análisis y reportes
- Beneficios:
  - Optimizar contenido basado en datos reales
  - Identificar hooks/BOFs más efectivos
  - A/B testing de overlays/SEO text
  - Decisiones informadas sobre productos
- Requisitos: Cuentas Business + URLs guardadas en BD

---

### 6. Error FFmpeg con caracteres especiales en nombres (11:45)

**Error encontrado:**
```
Error opening input file ...Manta_elÃ©ctrica_160Ã—130...
```

**Causa:**
- Nombre producto: `NIKLOK_Manta_eléctrica_160×130`
- Caracteres especiales: `é` y `×`
- FFmpeg en Windows tiene problemas con encoding UTF-8 en rutas temporales

**Posibles soluciones:**
1. Sanitizar nombres de archivo (eliminar/reemplazar caracteres especiales)
2. Usar rutas cortas (8.3 format) en Windows
3. Configurar encoding en subprocess calls

**Pendiente:** Determinar mejor solución e implementar

---

### 7. Añadido FIX #008: Sistema de moderación de contenido (12:00)

**Usuario solicita:** Sistema para manejar contenido descartado por baneo o moderación

**Situaciones a cubrir:**
1. **Baneo TikTok:** Producto completo o desde fecha
2. **Moderación por elemento:** Hook, broll, audio, overlay específico

**Necesidad:**
- Producir material nuevo sin regenerar contenido problemático
- Incorporar feedback de moderación fácilmente

**Propuestas de diseño añadidas:**
- Opción A: Tabla `material_blacklist` centralizada
- Opción B: Campo `status` en tablas existentes
- Opción C: Sistema de tags flexible

**Casos de uso documentados:**
- TikTok banea producto → No generar más videos
- Hook problemático → Saltar en futuras generaciones
- Audio con guion no permitido → Marcar como descartado

**Funcionalidades necesarias:**
- Marcar/reactivar contenido
- Listar descartados
- Validación pre-generación
- Búsqueda inversa (videos que usan material descartado)
- Reportes

**Preguntas pendientes:**
- ¿Desprogramar automáticamente videos afectados?
- ¿Blacklist temporal?
- ¿Por cuenta?
- ¿Auditoría de cambios?

**Fases:** Diseño (2-3h) + Implementación (6-8h) + CLI (4-6h) = 12-17h total

**Prioridad:** 🔴 ALTA - Crítico para operación continua

**Estado:** Pendiente de análisis y validación de diseño con usuario

---

### 8. CLI actualizado con generación masiva (12:15)

**Usuario solicita:** Generar videos de múltiples productos sin esperar cada uno

**Implementado:**
- Nueva opción 4 en menú: "Generar videos para MÚLTIPLES productos"
- Selección múltiple de productos (por números o "todos")
- Filtra automáticamente productos con material completo
- Resumen antes de ejecutar con total de videos
- Ejecución secuencial automática

**Características:**
- Muestra solo productos listos (hooks >= 10, brolls >= 20, audios >= 3, bofs >= 1)
- Permite seleccionar por números (1,3,5) o escribir "todos"
- Elige cuentas (trendy, lotopdevicky, o ambas)
- Define cantidad de videos por producto
- Confirmación con resumen antes de ejecutar
- Procesa todo automáticamente

**Beneficio:** Usuario puede lanzar generación masiva e irse a hacer otra cosa

---

### 9. Mejora añadida: Contador de progreso (12:18)

**Usuario solicita:** Mostrar progreso durante generación (video X de Y, tiempo estimado)

**Añadido a ISSUES - Prioridad Media:**
- Contador video actual / total
- Contador producto actual / total
- Tiempo transcurrido y estimado restante
- Barra de progreso visual opcional
- Tiempo estimado: 2-3 horas implementación

---

## ✅ RESUMEN SESIÓN PARTE 2

**Duración:** ~3 horas (10:45 - 13:30 CET)

**Logros principales:**
1. ✅ Bug caracteres especiales corregido (2 productos: Manta, Aceite)
2. ✅ Auditoría completa de código realizada (15 issues detectados)
3. ✅ 4 fixes críticos añadidos a ISSUES
4. ✅ CLI prototipo creado y probado
5. ✅ CLI mejorado con generación masiva
6. ✅ Sistema de moderación de contenido diseñado
7. ✅ Script limpiar_producto.py creado

**Archivos creados/modificados:**
- `AUDITORIA_CODIGO.md` (nuevo) - 15 issues detectados
- `ISSUES.md` - 4 fixes críticos + 1 moderación + mejoras
- `cli.py` - Prototipo funcional + generación masiva
- `limpiar_producto.py` - Utilidad para renombrar productos
- `scan_material.py` - Bug bof_id corregido
- `SESION_2026-02-14_parte2.md` - Este log

**Issues críticos añadidos:**
- FIX #005: Sanitizar caracteres especiales (ALTA - 2-3h)
- FIX #006: Mejorar manejo de errores (ALTA - 4-6h)
- FIX #007: Encoding en subprocess (ALTA - 1h)
- FIX #008: Sistema moderación contenido (ALTA - 12-17h)

**Mejoras implementadas:**
- CLI interactivo funcional (5 opciones)
- Generación masiva de múltiples productos
- Validación de material por producto
- Estado visual de todos los productos

**Bugs resueltos:**
- Caracteres especiales en nombres (workaround + fix permanente pendiente)
- Bug extracción bof_id en scan_material.py
- Queries BD en CLI (tabla material con tipo)

**Pendiente para próxima sesión:**
- Implementar FIX #005 (sanitización) antes de siguiente generación masiva
- Decidir diseño sistema moderación (Opción A, B o C)
- Implementar contador de progreso en generación
- Testing duplicación variantes entre BOFs

**Estado del sistema:**
- ✅ Generación masiva en progreso (~320 videos)
- ✅ PC configurado sin suspensión
- ✅ Material de 8-9 productos listo
- ✅ CLI operativo y mejorado

---

**Fin de sesión parte 2:** 2026-02-14 13:30 CET  
**Próxima sesión:** Pendiente feedback de generación masiva

---

**ARCHIVOS PARA ENTREGAR AL USUARIO:**
- SESION_2026-02-14_parte2.md
- AUDITORIA_CODIGO.md
- ISSUES.md
- cli.py (versión con generación masiva)


## 📋 DECISIONES TOMADAS

*Pendiente*

---

## 🔄 PENDIENTE

*A definir según avance de la sesión*

---

**Última actualización:** 2026-02-14 10:45 CET
