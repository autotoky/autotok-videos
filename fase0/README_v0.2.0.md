# 🚀 TikTok Shop Automation - Fase 0

**Versión actual:** v0.2.0  
**Última actualización:** 2026-01-31  
**Estado:** Activo ✅

---

## 📊 QUÉ HACE EL SISTEMA

Automatiza la producción de 25 videos TikTok Shop diarios:

```
CAROL → Genera scripts BOF
   ↓
SISTEMA → Genera prompts IA automáticos
   ↓
MAR → Produce 25 videos/día + feedback
   ↓
SARA → Programa publicación TikTok
   ↓
SISTEMA → (Futuro) Tracking métricas + ROI
```

---

## ✅ FUNCIONALIDADES ACTIVAS

- ✅ Carol genera scripts → Google Sheets automático
- ✅ Sistema lee y genera prompts HeyGen/Hailuo
- ✅ Mar produce videos con feedback integrado
- ✅ Sara genera CSV para bulk upload TikTok
- ⏳ Tracking métricas (pendiente - necesita datos reales)
- ⏳ Reportes ROI (pendiente - necesita datos reales)

---

## 🚀 INICIO RÁPIDO

### **Carol:**
1. Abre `carol_input` sheet
2. Genera 25 scripts BOF
3. Done ✅

### **Sistema:**
```bash
cd fase0
python main.py
```

### **Mar:**
1. Lee `DOC_MAR.md`
2. Abre `produccion_mar` sheet
3. Genera 25 videos siguiendo prompts
4. Done ✅

### **Sara:**
```bash
cd fase0
python generate_upload_csv.py
```
Luego sube CSV a TikTok Studio

---

## 📁 ARCHIVOS PRINCIPALES

### Scripts (`/fase0`)
- `main.py` - Proceso diario principal
- `sheets_manager.py` - Google Sheets API
- `prompt_generator.py` - Generador prompts
- `bof_learning.py` - Sistema aprendizaje
- `generate_upload_csv.py` - CSV para Sara
- `config.py` - Configuración
- `verify_setup.py` - Verificador setup

### Documentación
- `DOC_MAR.md` - Guía Mar (producción)
- `DOC_SARA.md` - Guía Sara (publicación)
- `CHANGELOG.md` - Historial cambios
- `README.md` - Este archivo

---

## 📊 GOOGLE SHEETS

5 sheets activas:

1. **carol_input** - Carol rellena scripts
2. **produccion_mar** - Mar ejecuta + feedback
3. **creditos_tracking** - Sistema (automático)
4. **bof_learning** - Sistema (automático)
5. **metricas_tiktok** - Futuro tracking

---

## ⚙️ SETUP INICIAL

**Una sola vez:**

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Configurar Google API:
   - Ver `SETUP_COMPLETE.md` (completo)

3. Verificar:
```bash
python verify_setup.py
```

---

## 🆘 PROBLEMAS

**Sistema no lee sheets:**
→ Ejecuta `python verify_setup.py`

**Prompts no se generan:**
→ Verifica que Carol rellenó carol_input

**CSV no se crea:**
→ Verifica que Mar completó videos (status=done)

---

## 📈 ROADMAP

### Ahora (v0.2.0)
- ✅ Producción 25 videos/día
- ✅ Bulk upload preparado

### Próximo (v0.3.0)
- Tracking métricas real
- Cálculo ROI con datos reales
- Reportes automáticos

### Futuro (v1.0.0)
- API TikTok oficial
- 100% automatizado
- Scaling a 100+ videos/día

---

## 🔧 MANTENIMIENTO

**Ver cambios:**
```bash
cat CHANGELOG.md
```

**Actualizar código:**
1. Backup: `cp archivo.py archivo_backup.py`
2. Modificar
3. Probar
4. Actualizar CHANGELOG.md

---

## 📞 CONTACTO

- Carol: Scripts y estrategia contenido
- Mar: Producción videos
- Sara: Publicación y tracking
- Sistema: Automatización

---

**Última actualización:** 2026-01-31  
**Versión:** v0.2.0
