# 🚀 ROADMAP DE MEJORAS - AUTOTOK
**Priorización y Plan de Implementación**  
**v3.2 - 2026-02-12 (Phase 2 completada)**

---

## 🎯 ESTADO ACTUAL

### ✅ Completado (Phase 2 - 2026-02-12)
- ✅ **Base de datos SQLite** - Sistema 100% funcional
- ✅ **Scripts setup DB** - 5 scripts operativos
  - create_db.py
  - migrate_data.py
  - import_bofs.py
  - scan_material.py
  - register_audio.py
- ✅ **Core refactorizado** - generator.py, programador.py, mover_videos.py v3.0
- ✅ **Parámetro `--fecha-inicio`** - Programar desde fecha específica
- ✅ **Comando `--sync`** - Sincronización completa desde Sheet
- ✅ **Testing completo** - Workflow validado con proyector_magcubic
- ✅ **Documentación** - CASOS_DE_USO.md iniciado

### ✅ Completado (Anteriormente)
- ✅ Generación de videos automática
- ✅ Calendario Google Sheets
- ✅ Sistema de estados (4 estados + carpetas por fecha)
- ✅ Rotación de hooks equitativa
- ✅ Audio-overlay matching por prefijos
- ✅ Flag --require-overlay
- ✅ Fix rate limits Sheets (batch append)
- ✅ Fix duplicados calendario
- ✅ Consolidación archivos config
- ✅ Workflow validado con Carol

---

## 🟡 PRIORIDAD MEDIA (Próximas 1-2 semanas)

### 1. **Registro Masivo de Audios**
**Tiempo estimado:** 2 horas  
**Impacto:** Medio  
**Esfuerzo:** Bajo

**Problema actual:** Registrar audios uno a uno es tedioso
```bash
python scripts/register_audio.py X a1.mp3 --bof-id 1
python scripts/register_audio.py X a2.mp3 --bof-id 1
# ... repetir 20+ veces
```

**Solución propuesta:**
```bash
# Escanear todos los audios y asignar interactivamente
python scripts/register_audio.py PRODUCTO --scan-all

# Modo batch: todos los aX → BOF 1, todos los bX → BOF 2
python scripts/register_audio.py PRODUCTO --batch
```

**Beneficio:**
- ✅ Ahorra 15-20 min por producto
- ✅ Reduce errores de tipeo
- ✅ Facilita setup productos nuevos

---

### 2. **Validación Pre-Generación**
**Tiempo estimado:** 1 hora  
**Impacto:** Medio  
**Esfuerzo:** Bajo

**Problema actual:** Si falta material, generación falla parcialmente

**Solución:**
```python
# Antes de generar, verificar:
- Todos los archivos existen físicamente
- Audio durations correctas
- BOFs disponibles suficientes
- Material mínimo para batch size

# Si falta algo, mostrar warning claro
```

**Beneficio:**
- ✅ Errores más claros
- ✅ Menos videos fallidos
- ✅ Mejor UX

---

### 3. **Definir Estrategia SEO + Tags**
**Tiempo estimado:** 1 hora (conversación)  
**Impacto:** Medio  
**Esfuerzo:** Bajo

**Decisiones pendientes:**
- ¿Rotación de SEO texts o asignación fija?
- ¿Hashtags por producto o por BOF?
- ¿Dónde se ven en workflow?
- ¿Formato de hashtags en Sheet?

**Implementación:** Ya está en DB (`producto_bofs.seo_text` y `producto_bofs.hashtags`), solo definir estrategia de uso

---

### 4. **Decidir: Tracking Combinaciones por Cuenta**
**Tiempo estimado:** 15 min (decisión) + 30 min (código si aplica)  
**Impacto:** Medio  
**Esfuerzo:** Bajo

**Decisión pendiente:**
- Actual: Tracking global por producto
- ¿Permitir mismas combinaciones entre cuentas?

**Pros tracking independiente:**
- Más videos únicos totales
- Cuentas no se afectan entre sí

**Contras:**
- Más complejo
- Posible duplicación si cuentas muy similares

**Con DB:** Cambio trivial en queries, solo decidir estrategia

---

## 🟢 PRIORIDAD BAJA (Mes 1-2)

### 5. **Dashboard de Estado en Terminal**
**Tiempo estimado:** 4 horas  
**Impacto:** Medio  
**Esfuerzo:** Medio

**Descripción:**
```bash
python dashboard.py

╔════════════════════════════════════════════════════╗
║  DASHBOARD AUTOTOK - 2026-02-12                    ║
╠════════════════════════════════════════════════════╣
║  CUENTA           | GENERADOS | CALENDARIO | PROG  ║
╠════════════════════════════════════════════════════╣
║  lotopdevicky     |    45     |     12     |   8   ║
║  ofertastrendy20  |    32     |      8     |   5   ║
╚════════════════════════════════════════════════════╝
```

**Beneficio:** Visión general rápida del estado

---

### 6. **Pestañas Analytics en Google Sheets**
**Tiempo estimado:** 2-3 horas  
**Impacto:** Alto  
**Esfuerzo:** Bajo (con DB)

**Pestañas propuestas:**
- **Stats:** Resumen diario/semanal
- **Historial:** Todos los videos generados
- **Material:** Inventario hooks/brolls/audios
- **Performance:** Análisis por hook/producto/deal

**Con DB:** Queries SQL simples, fácil implementación

---

### 7. **Backup Automático de DB**
**Tiempo estimado:** 2 horas  
**Impacto:** Alto (seguridad)  
**Esfuerzo:** Bajo

**Implementación:**
```bash
# Script diario (cron/Task Scheduler)
python backup_db.py
# Guarda: backups/autotok_2026-02-12.db
# Mantiene últimos 30 días
```

**Beneficio:** Protección contra pérdida de datos

---

### 8. **Validación de BOFs al Importar**
**Tiempo estimado:** 3 horas  
**Impacto:** Medio  
**Esfuerzo:** Medio

**Validaciones:**
- Todos los campos requeridos presentes
- Longitud textos (overlay < 30 chars, etc.)
- Formato hashtags correcto (#palabra sin espacios)
- Deal math tiene sentido
- URL producto válida

**Beneficio:** Detectar errores antes de generar videos

---

### 9. **Estadísticas de Uso de Material**
**Tiempo estimado:** 2 horas  
**Impacto:** Bajo  
**Esfuerzo:** Bajo

**Descripción:**
```bash
python stats.py --producto proyector_magcubic --tipo hooks

HOOKS MÁS USADOS:
  A_hook.mp4: 45 veces
  C_hook.mp4: 38 veces
  B_hook.mp4: 32 veces

HOOKS MENOS USADOS:
  F_hook.mp4: 2 veces
  G_hook.mp4: 1 vez
```

**Beneficio:** Identificar material que funciona mejor

---

### 10. **Setup Automático Productos Nuevos**
**Tiempo estimado:** 2-3 horas  
**Impacto:** Medio  
**Esfuerzo:** Medio

**Script que automatiza:**
```bash
python setup_producto.py nombre_producto

# Hace:
1. Crea entrada en tabla productos
2. Crea estructura carpetas Drive
3. Genera template BOF JSON
4. Registra en sistema
```

**Beneficio:** Reduce setup de 1h a 5 min

---

## 🔮 PRIORIDAD FUTURA (3+ meses)

### 11. **Generación Automática de BOFs con IA**
**Tiempo estimado:** 1 semana  
**Impacto:** Muy Alto (automatización crítica)  
**Esfuerzo:** Alto

**Descripción:** Lógica Custom GPT en código Python

**Input:**
- URL producto Amazon
- Descuento deseado
- Producto info (de Excel Carol)

**Output:**
- 30 BOFs en DB directamente
- deal_math, guion_audio, seo_text, overlay_line1/2, hashtags, url_producto

**Tecnología:** API Anthropic Claude / GPT-4

**Beneficio:** Escalar a decenas de productos sin escribir manualmente

---

### 12. **TTS (Text-to-Speech) para Audios**
**Tiempo estimado:** 3-4 días  
**Impacto:** Muy Alto  
**Esfuerzo:** Medio

**Descripción:** Generar voice-overs automáticamente desde guion

**APIs opciones:**
- **ElevenLabs** (mejor calidad, $$$)
- **Google Cloud TTS** (buena, $$)
- **Amazon Polly** (decente, $)

**Workflow:**
```bash
python generate_audio.py --bof-id 1 --voice "es-ES-Neural2-A"
# Lee guion_audio del BOF
# Genera audio.mp3
# Registra en DB automáticamente
```

**Costo:** ~$0.10 por audio (ElevenLabs)

**Beneficio:** Escalar sin grabar audios manualmente

---

### 13. **IA para Hooks/Brolls (Runway/Pika)**
**Tiempo estimado:** 1-2 semanas  
**Impacto:** Muy Alto  
**Esfuerzo:** Alto

**Descripción:** Generar clips video con IA

**APIs:**
- Runway Gen-2
- Pika Labs
- Stable Video Diffusion

**Problema actual:** Calidad variable, caro, lento

**Decisión:** Esperar 6-12 meses a que mejore tecnología

---

### 14. **Migración a Google Sheets como DB** (Exploratorio)
**Tiempo estimado:** 2 semanas  
**Impacto:** Medio  
**Esfuerzo:** Alto

**Pros:**
- ✅ Carol edita directamente
- ✅ Colaboración tiempo real
- ✅ No necesita acceso servidor

**Contras:**
- ⚠️ Límites API (lectura/escritura)
- ⚠️ Velocidad menor que SQLite
- ⚠️ Requiere internet

**Decisión:** Evaluar en 3-6 meses según uso real de DB actual

---

## 💡 IDEAS EXPLORATORIAS (Sin priorizar)

### Análisis de Rendimiento por BOF
- Conectar con TikTok Analytics API
- Métrica: Qué BOFs/hooks generan más views/engagement
- Beneficio: Optimizar contenido basado en datos
- Bloqueador: API TikTok no disponible fácilmente

### A/B Testing Automático
- Publicar 2 versiones del mismo BOF
- Objetivo: Ver qué overlay/hook funciona mejor
- Implementación: Programar 2 videos idénticos excepto 1 variable

### Notificaciones Telegram/Slack
- Bot que notifica cuando:
  - Videos generados listos
  - Errores en generación
  - Calendario actualizado
- Beneficio: Awareness tiempo real

---

## 📊 CRITERIOS DE PRIORIZACIÓN

### ⭐⭐⭐ Alta
- Ahorra > 2 horas/semana
- Previene pérdida de datos
- Crítico para escalar

### ⭐⭐ Media
- Ahorra 30 min - 2 horas/semana
- Mejora UX significativamente
- Facilita troubleshooting

### ⭐ Baja
- Ahorra < 30 min/semana
- Nice to have
- Optimización incremental

---

## 🔄 PROCESO DE REVISIÓN

### Semanal
- Revisar items "Pendientes" de prioridad media
- Actualizar frecuencias de casos de uso
- Mover a "En progreso" si se trabaja

### Mensual
- Evaluar prioridad media → subir si urgente
- Añadir nuevas ideas que surjan
- Re-priorizar según feedback operativo

### Trimestral
- Revisar futuro y exploratorias
- Decidir implementación
- Re-evaluar tecnologías disponibles

---

## 📝 CHANGELOG ROADMAP

**2026-02-12:**
- Phase 2 completada: DB, scripts, core refactor
- Items 1-2 del roadmap anterior completados
- Nuevos items añadidos: validación pre-gen, registro masivo audios
- Re-priorizado según estado actual

**2026-02-09:**
- Roadmap creado
- DB como prioridad #1

---

**FIN ROADMAP v3.2 (2026-02-12 13:30) - Phase 2 completada, Phase 3 planificada**
