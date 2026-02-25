# 🎬 DEMO AUTOTOK - GUÍA PARA PRESENTACIÓN A CAROL

**Fecha:** 2026-02-07  
**Duración estimada:** 20-30 minutos  
**Objetivo:** Mostrar sistema completo end-to-end

---

## 📋 PREPARACIÓN PRE-DEMO (Sara)

### 1. Limpiar entorno de testing
```bash
# Borrar videos de prueba
rm videos_generados_py/lotopdevicky/*.mp4
rm videos_generados_py/ofertastrendy20/*.mp4

# Limpiar Google Sheet (manualmente)
# → Borrar todas las filas excepto headers
```

### 2. Verificar configuración
```bash
python main.py --config
python mover_videos.py --verificar-estructura
```

### 3. Material preparado
- ✅ 12 hooks de melatonina (A-L)
- ✅ 30 brolls organizados
- ✅ 15 audios con prefijos
- ✅ overlays.csv actualizado

---

## 🎯 DEMO - PARTE 1: GENERACIÓN (5 min)

### **Mostrar:** Cómo se generan videos automáticamente

```bash
# Generar 10 videos para lotopdevicky
python main.py --producto melatonina --batch 10 --cuenta lotopdevicky
```

**Puntos a destacar:**
- ✅ Sistema de rotación de hooks (usa todos antes de repetir)
- ✅ Videos van directamente a carpeta `/lotopdevicky/`
- ✅ Nombres incluyen hook ID: `melatonina_hookA_001.mp4`
- ✅ Overlays automáticos con deal_math

**Carol verá:**
- Terminal mostrando progreso
- 10 videos generándose uno a uno
- Archivo de tracking registrando combinaciones

### **Mejoras planteadas:**
- 🔮 Integrar API de Grok para generar video IA completo
- 🔮 Optimizar tiempos de generación (paralelización)

---

## 📅 DEMO - PARTE 2: PROGRAMACIÓN (10 min)

### **Mostrar:** Calendario automático en Google Sheets

```bash
# Generar más videos para tener variedad
python main.py --producto melatonina --batch 10 --cuenta ofertastrendy20

# Crear calendario de 7 días
python programador.py --generar-calendario --dias 7
```

**Abrir Google Sheet en pantalla compartida:**
https://docs.google.com/spreadsheets/d/1QCb4xYKoLJPaMrGaBW311VQIyDg2Xa08V5DmsD2H81g/

**Puntos a destacar:**
- ✅ Calendario se crea automáticamente
- ✅ Respeta configuración de cada cuenta (videos/día, horarios)
- ✅ No repite mismo hook en mismo día
- ✅ Horarios distribuidos aleatoriamente (aspecto natural)
- ✅ Colores por cuenta (rojo=ofertastrendy, azul=lotopdevicky)
- ✅ Columnas editables (fecha, hora, estado, notas)
- ✅ Columnas bloqueadas (video, cuenta, producto, hook, deal_math)

**Carol puede:**
- Ver calendario completo de la semana
- Cambiar fechas u horas si necesario
- Añadir notas
- Actualizar estados con dropdown

### **Mejoras planteadas:**
- 🔮 Pestañas adicionales: Stats, Historial, Material, Análisis
- 🔮 Añadir columnas: descripción SEO, tags/hashtags
- 🔮 Reemplazar overlays.csv por hoja Google integrada
- 🔮 Validaciones automáticas (ej: no programar mismo hook consecutivo)

---

## 📁 DEMO - PARTE 3: GESTIÓN DE ESTADOS (5 min)

### **Mostrar:** Workflow Sara → Carol

**Simular workflow de Sara:**
1. Abre Sheet, selecciona 3 videos
2. Cambia estado: `Generado` → `Borrador`
3. Ejecuta:
   ```bash
   python mover_videos.py --actualizar
   ```

**Carol verá:**
- Terminal mostrando videos moviéndose
- Archivos físicamente en `/borrador/`
- Sistema sincronizado con Sheet

**Simular workflow de Carol:**
1. (Fingir que programa en TikTok)
2. Cambiar estado en Sheet: `Borrador` → `Programado`
3. Ejecutar de nuevo:
   ```bash
   python mover_videos.py --actualizar
   ```

**Carol verá:**
- Videos moviéndose a `/programados/`
- Carpetas organizadas automáticamente

### **Mejoras planteadas:**
- 🔮 Estado "Descartado" con carpeta `/descartados/`
- 🔮 Estado intermedio "En Calendario" (opcional)
- 🔮 Dashboard visual del estado de videos

---

## 📊 DEMO - PARTE 4: CONFIGURACIÓN (5 min)

### **Mostrar:** Flexibilidad del sistema

**Abrir `config_cuentas.json` en pantalla:**
```json
{
  "lotopdevicky": {
    "activa": true,
    "videos_por_dia": 6,
    "max_mismo_hook_por_dia": 1,
    "max_mismo_producto_por_dia": 2,
    "horarios": {
      "inicio": "08:00",
      "fin": "21:30"
    }
  }
}
```

**Explicar:**
- Cada cuenta es configurable independientemente
- Videos/día escalable (empezar con 2, subir a 25)
- Horarios personalizables
- Restricciones flexibles

**Cambiar en vivo:**
- Cambiar `videos_por_dia` de 6 a 8
- Regenerar calendario:
  ```bash
  python programador.py --generar-calendario --dias 3
  ```
- Mostrar que se adapta automáticamente

### **Mejoras planteadas:**
- 🔮 Consolidar `cuentas.json` y `config_cuentas.json` en uno solo
- 🔮 Interfaz gráfica para cambiar config (futuro)

---

## 🎨 DEMO - PARTE 5: MATERIAL Y OVERLAYS (3 min)

### **Mostrar:** Cómo se organiza el material

**Navegación en Drive:**
```
recursos_videos/
└── melatonina/
    ├── hooks/          → Mostrar nombrado A_hook_patas.mp4
    ├── brolls/        → Mostrar grupos A_1.mp4, B_1.mp4
    ├── audios/        → Mostrar prefijos a1_melatonina.mp3
    └── overlays.csv   → Abrir y explicar columnas
```

**Explicar:**
- Hooks con letra identifican video final
- Audio prefix conecta con overlay correcto
- deal_math se exporta para análisis futuro

### **Mejoras planteadas:**
- 🔮 Migrar overlays.csv a Google Sheets
- 🔮 Automatizar setup de producto nuevo (brolls, deal_math, SEO, hashtags)
- 🔮 Aprovechar sistema Fase 0 para generación ágil de material

---

## 🚀 DEMO - CIERRE: VISIÓN FUTURA (2 min)

### **THE BIG THING:**

**Mostrar roadmap en pizarra/papel:**
```
FASE ACTUAL (✅ Completado):
└── Material manual → Sistema genera videos → Calendario Sheets

FASE 2 (🔮 Próxima):
└── API Grok genera clips IA → Todo automático

FASE 3 (🔮 Futuro):
└── Solo dar producto → Sistema genera TODO (clips, guiones, overlays, calendario)
```

**Explicar:**
- Ya tenemos 80% del flujo automatizado
- Siguiente paso: Conectar API Grok (generación video IA)
- Meta: Solo necesitar nombre de producto y link Amazon

---

## 💬 DEMO - Q&A (5 min)

**Preguntas esperadas de Carol:**

**"¿Puedo cambiar videos manualmente?"**
→ Sí, edita fecha/hora en Sheet, mueve archivos manualmente si necesario

**"¿Qué pasa si un video no me gusta?"**
→ Próximamente: Estado "Descartado" + carpeta

**"¿Puedo ver qué hooks funcionan mejor?"**
→ Próximamente: Pestaña "Análisis" en Sheet con stats

**"¿Cuánto tiempo lleva subir los borradores?"**
→ TikTok: ~30 seg/video = 5 min para 10 videos

**"¿Necesito saber programar?"**
→ No, solo Google Sheets (como Excel pero online)

---

## ✅ CHECKLIST POST-DEMO

- [ ] Carol entiende workflow Sara → Carol
- [ ] Carol puede cambiar estados en Sheet
- [ ] Carol sabe dónde encontrar calendario
- [ ] Carol entiende visión a futuro
- [ ] Carol da feedback sobre mejoras prioritarias

---

## 📝 NOTAS PARA SARA

**Durante la demo:**
- Hablar despacio y claro
- Mostrar terminal pero no entrar en detalles técnicos
- Enfocarse en beneficios para Carol (tiempo ahorrado, organización)
- Pedir feedback constantemente

**Después de la demo:**
- Anotar prioridades de Carol
- Definir siguiente sprint
- Planificar integración Grok

---

**¡Suerte con la demo!** 🚀
