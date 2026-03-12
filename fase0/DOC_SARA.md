---
Versión: v0.2.0
Última actualización: 2026-01-31
Estado: ACTIVO
Para: Sara (Publicación y tracking)
---

# 📤 GUÍA SARA - PUBLICACIÓN TIKTOK

## 🎯 TU MISIÓN:

Programar la publicación de los 25 videos diarios que Mar genera, distribuyéndolos estratégicamente entre las 4 cuentas TikTok.

---

## ✅ TU TRABAJO:

1. ✅ Descargar videos completados por Mar
2. ✅ Generar CSV para bulk upload TikTok
3. ✅ Programar publicaciones estratégicamente
4. ✅ Distribuir entre cuentas (2 España + 2 USA)

---

## 🔄 PROCESO DIARIO (30-60 min):

### **PASO 1: Generar CSV automático (6:00 PM)**

```bash
cd fase0
python generate_upload_csv.py
```

**Output:**
```
📊 ESTADÍSTICAS PRODUCCIÓN
════════════════════════════════════
📹 Videos totales: 25
✅ Completados: 25
⭐ Calidad promedio: 4.2/5
🎨 Por herramienta:
  • HeyGen: 12 videos
  • Hailuo: 13 videos
════════════════════════════════════

✅ CSV generado: upload_batch_2026-01-31.csv
```

**El CSV incluye automáticamente:**
- Nombres archivo corratos
- Captions (scripts BOF)
- Hashtags
- Horarios escalonados (cada 30 min)

---

### **PASO 2A: Subir con bulk upload** (cuando esté disponible)

1. Abre TikTok Studio: https://www.tiktok.com/studio
2. Ve a "Upload" → "Bulk upload"
3. Sube CSV: `upload_batch_2026-01-31.csv`
4. Sube videos de `/videos_listos/`
5. Distribuye entre cuentas:
   - @cuenta_esp_1: 7 videos
   - @cuenta_esp_2: 6 videos
   - @cuenta_usa_1: 7 videos
   - @cuenta_usa_2: 5 videos

---

### **PASO 2B: Subir manual** (si bulk NO disponible)

Para cada video:

1. Abre TikTok Studio
2. Upload video: `video_001.mp4`
3. **Caption:** Abre produccion_mar, copia `script_bof` del id correspondiente
4. **Hashtags:** Abre produccion_mar o carol_input
5. Programa fecha/hora
6. Repite 25 veces

**Distribución cuentas:**
- España principal: 7 videos
- España secundaria: 6 videos
- USA principal: 7 videos
- USA secundaria: 5 videos

**Horarios sugeridos:**
10:00, 12:00, 14:00, 16:00, 18:00, 20:00, 22:00

---

## 📊 ESTRATEGIA DISTRIBUCIÓN:

### **Por cuenta:**

**@cuenta_esp_1:** Best-sellers, 7-8 videos/día  
**@cuenta_esp_2:** Test productos, 5-6 videos/día  
**@cuenta_usa_1:** Top USA, 7-8 videos/día  
**@cuenta_usa_2:** Nicho USA, 5-6 videos/día  

### **Por horario:**

Peak engagement: **6:00 PM - 10:00 PM**  
Programar más videos en estas horas.

Variar diariamente para optimizar.

---

## ⏰ TIMING:

```
6:00 PM - Generar CSV
6:10 PM - Revisar/ajustar
6:20 PM - Subir TikTok
6:50 PM - Done! ✅
```

**Meta:** 30-60 min/día (con bulk: 15 min)

---

## ✅ CHECKLIST:

- [ ] 25 videos programados
- [ ] 4 cuentas balanceadas
- [ ] Horarios variados
- [ ] CSV guardado (histórico)

---

## 🆘 PROBLEMAS:

**"Script no funciona"**  
→ Ejecuta: `python verify_setup.py`

**"No hay bulk upload"**  
→ Usa proceso manual (PASO 2B)

**"Horarios CSV no me gustan"**  
→ Abre CSV con Excel, edita `scheduled_time`

---

**¡A automatizar TikTok!** 🚀📱
