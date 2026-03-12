# 📅 SISTEMA DE PROGRAMACIÓN DE VIDEOS TIKTOK

**Versión:** 3.0  
**Fecha:** 2026-02-12  
**Para:** Sara y Carol

---

## ⚠️ ACTUALIZACIÓN v3.0 (2026-02-12)

**Comandos actualizados:**
- ✅ `--generar-calendario` → ahora es `--cuenta --dias`
- ✅ `--actualizar` → ahora es `--sync`
- ✅ `--preview` eliminado
- ✅ Añadido `--fecha-inicio` para programar fechas específicas
- ✅ Google Sheets (NO CSV)

**Ver CHULETA_COMANDOS.md para comandos actualizados.**

---

## 🎯 QUÉ HACE ESTE SISTEMA

Automatiza la planificación de publicaciones en TikTok:
- ✅ Genera calendario semanal respetando reglas de cada cuenta
- ✅ Evita repetir mismo hook en el mismo día
- ✅ Distribuye horarios aleatorios naturales
- ✅ Organiza videos por carpetas según estado
- ✅ Mantiene control en Google Sheets

---

## 📁 ESTRUCTURA DE CARPETAS

```
videos_generados_py/
├── lotopdevicky/
│   ├── video1.mp4              ← Generados (raíz)
│   ├── video2.mp4
│   ├── calendario/             ← En Calendario (por fecha)
│   │   ├── 2026-02-12/
│   │   └── 2026-02-13/
│   ├── borrador/               ← Borrador (por fecha)
│   │   └── 2026-02-12/
│   ├── programados/            ← Programado (por fecha)
│   │   └── 2026-02-12/
│   └── descartados/            ← Descartado (sin fecha)
├── ofertastrendy20/
│   └── ...
└── autotoky/
    └── ...
```

---

## ⚙️ CONFIGURACIÓN DE CUENTAS

**Archivo:** `config_cuentas.json`

```json
{
  "ofertastrendy20": {
    "activa": true,
    "videos_por_dia": 4,
    "max_mismo_hook_por_dia": 1,
    "max_mismo_producto_por_dia": 0,
    "horarios": {
      "inicio": "09:00",
      "fin": "22:30"
    }
  }
}
```

**Valores configurables:**
- `activa`: true/false (activar/desactivar cuenta)
- `videos_por_dia`: Cuántos videos publicar diariamente
- `max_mismo_hook_por_dia`: Máximo veces que puede aparecer mismo hook (normalmente 1)
- `max_mismo_producto_por_dia`: Máximo mismo producto (0 = sin límite)
- `horarios.inicio/fin`: Rango horario para publicaciones

**Para ajustar:**
1. Abrir `config_cuentas.json`
2. Cambiar valores
3. Guardar
4. Volver a generar calendario

---

## 🚀 WORKFLOW COMPLETO

### **PASO 1: Generar videos (Sara)**

```bash
python main.py --producto melatonina --batch 50 --cuenta lotopdevicky
```

✅ Videos se guardan en: `/videos_generados_py/lotopdevicky/`

---

### **PASO 2: Crear calendario (Sara, 1 vez/semana)**

```bash
python programador.py --generar-calendario --dias 7
```

**Lo que hace:**
1. Escanea videos disponibles en carpetas de cuentas
2. Respeta configuración de cada cuenta
3. Genera calendario balanceado
4. Crea `calendario_tiktok.csv` con plan semanal

**Output esperado:**
```
[SCAN] Escaneando videos por cuenta...
   ✅ ofertastrendy20: 28 videos encontrados
   ✅ lotopdevicky: 42 videos encontrados

[CALENDAR] Generando calendario para 7 días desde 2026-02-07
   ✅ ofertastrendy20: Suficientes videos (28 disponibles)
   ✅ lotopdevicky: Suficientes videos (42 disponibles)

[SUCCESS] Calendario generado: 70 videos programados
[CSV] Calendario exportado a: calendario_tiktok.csv
```

---

### **PASO 3: Revisar calendario (Sara)**

Abrir `calendario_tiktok.csv`:

```csv
video,cuenta,producto,hook_display,deal_math,fecha_prog,hora,estado,notas
melatonina_hookA_001.mp4,lotopdevicky,melatonina,A_patas,2x1,2026-02-07,08:23,Generado,
aceite_hookB_002.mp4,lotopdevicky,aceite,B_boom,50%,2026-02-07,11:47,Generado,
...
```

**Revisar:**
- ✓ Fechas cubren la semana
- ✓ Horarios distribuidos
- ✓ No se repiten hooks el mismo día
- ✓ Productos balanceados (si hay límite)

---

### **PASO 4: Subir a TikTok como borradores (Sara, diario ~10 min)**

**Para cada día:**

1. **Ver qué videos subir hoy:**
   - Abrir `calendario_tiktok.csv`
   - Filtrar por `fecha_prog = HOY`

2. **Subir videos a TikTok:**
   - Ir a carpeta: `/videos_generados_py/lotopdevicky/`
   - Subir videos de la lista
   - **Guardar como BORRADOR** (no programar todavía)

3. **Actualizar CSV:**
   - Cambiar `estado` de `Generado` → `Borrador` para videos subidos
   - Guardar CSV

4. **Mover archivos automáticamente:**
   ```bash
   python mover_videos.py --actualizar
   ```
   
   ✅ Videos se mueven a `/lotopdevicky/borrador/`

---

### **PASO 5: Programar publicaciones (Carol, diario ~5 min)**

**Carol trabaja SOLO con:**
- Borradores en TikTok
- `calendario_tiktok.csv`

**Proceso:**

1. **Abrir TikTok Creator Studio**
   - Ver borradores disponibles

2. **Programar según calendario:**
   - Abrir `calendario_tiktok.csv`
   - Filtrar por `estado = Borrador` y `fecha_prog = HOY` (o próximos días)
   - Para cada video:
     - Buscar en borradores TikTok
     - Programar con fecha/hora del CSV
     - **Carol puede cambiar hora si necesita** ✅

3. **Actualizar CSV:**
   - Cambiar `estado` de `Borrador` → `Programado`
   - Guardar CSV

4. **Mover archivos (opcional, Sara lo hace):**
   ```bash
   python mover_videos.py --actualizar
   ```
   
   ✅ Videos se mueven a `/lotopdevicky/programados/`

---

## 📊 COLUMNAS DEL CSV

| Columna | Descripción | Editable por Carol |
|---------|-------------|-------------------|
| video | Nombre del archivo | ❌ |
| cuenta | Cuenta TikTok | ❌ |
| producto | Nombre producto | ❌ |
| hook_display | Hook (ej: A_patas) | ❌ |
| deal_math | Oferta (ej: 2x1) | ❌ |
| fecha_prog | Fecha publicación | ✅ |
| hora | Hora publicación | ✅ |
| estado | Generado/Borrador/Programado | ✅ |
| notas | Texto libre | ✅ |

**Carol puede cambiar:**
- ✅ Fecha
- ✅ Hora
- ✅ Estado
- ✅ Notas

**Carol NO debe cambiar:**
- ❌ Nombre video
- ❌ Cuenta
- ❌ Producto
- ❌ Hook
- ❌ Deal Math

---

## 🔧 COMANDOS ÚTILES

### **Generar calendario para más días:**
```bash
python programador.py --generar-calendario --dias 14
```

### **Exportar calendario con nombre custom:**
```bash
python programador.py --generar-calendario --export-csv calendario_febrero.csv
```

### **Actualizar desde CSV específico:**
```bash
python mover_videos.py --csv calendario_febrero.csv --actualizar
```

### **Verificar estructura de carpetas:**
```bash
python mover_videos.py --verificar-estructura
```

---

## ⚠️ SITUACIONES ESPECIALES

### **No hay suficientes videos para la semana**

**Mensaje del script:**
```
⚠️  lotopdevicky: Videos insuficientes
   Disponibles: 15
   Necesarios: 42 (6/día × 7 días)
   Se programarán 2 días completos
```

**Solución:**
1. Generar más videos:
   ```bash
   python main.py --producto melatonina --batch 50 --cuenta lotopdevicky
   ```
2. Volver a generar calendario

---

### **Cambiar configuración de una cuenta**

**Ejemplo:** Pasar de 4 a 6 videos/día en ofertastrendy20

1. Editar `config_cuentas.json`:
   ```json
   "ofertastrendy20": {
     "videos_por_dia": 6  // Cambiar de 4 a 6
   }
   ```

2. Regenerar calendario:
   ```bash
   python programador.py --generar-calendario --dias 7
   ```

---

### **Activar cuenta que estaba inactiva**

**Ejemplo:** Activar autotoky

1. Generar videos para esa cuenta:
   ```bash
   python main.py --producto aceite --batch 50 --cuenta autotoky
   ```

2. Activar en config:
   ```json
   "autotoky": {
     "activa": true,
     "videos_por_dia": 5
   }
   ```

3. Regenerar calendario

---

### **Carol necesita cambiar hora de un video**

**✅ SIN PROBLEMA**

1. Abrir `calendario_tiktok.csv`
2. Cambiar valor en columna `hora`
3. Guardar
4. Programar en TikTok con nueva hora

El sistema respeta los cambios de Carol.

---

## 🐛 TROUBLESHOOTING

### **"CSV no encontrado"**
```
❌ CSV no encontrado: calendario_tiktok.csv
```

**Solución:** Generar calendario primero:
```bash
python programador.py --generar-calendario --dias 7
```

---

### **"Video no encontrado"**
```
❌ Video no encontrado: melatonina_hookA_001.mp4
```

**Causas posibles:**
- Video ya se movió manualmente
- Nombre en CSV no coincide con archivo real

**Solución:**
1. Verificar que video existe en alguna carpeta de la cuenta
2. Verificar que nombre en CSV es exacto

---

### **"Carpeta no existe"**
```
⚠️  lotopdevicky: Carpeta no existe
```

**Solución:** Crear estructura:
```bash
python mover_videos.py --verificar-estructura
```

---

### **Videos no se mueven**

**Verificar:**
1. CSV tiene estados actualizados
2. Ejecutar: `python mover_videos.py --actualizar`
3. Revisar mensajes de error

---

## 💡 TIPS PRO

### **Generar calendario solo para días laborables:**
- Generar 5 días en lugar de 7
- Carol programa fin de semana manualmente si necesita

### **Tener backup del calendario:**
```bash
cp calendario_tiktok.csv backups/calendario_2026-02-07.csv
```

### **Ver videos de un producto específico:**
Abrir CSV en Excel → Filtrar columna `producto`

### **Ver todos los videos de un hook:**
Abrir CSV en Excel → Filtrar columna `hook_display`

---

## 📞 DUDAS FRECUENTES

**¿Puedo generar calendario de 1 día?**
✅ Sí: `python programador.py --generar-calendario --dias 1`

**¿Puedo tener varios CSV?**
✅ Sí, especifica con `--export-csv nombre.csv`

**¿El sistema programa automáticamente en TikTok?**
❌ No, Sara/Carol suben manualmente (más seguro, evita bans)

**¿Qué pasa si no completo un día?**
✅ Nada, Carol programa lo que pueda. El sistema no obliga.

**¿Puedo cambiar orden de videos?**
✅ Sí, Carol puede cambiar fechas/horas en CSV

---

## 🎓 PRÓXIMOS UPGRADES

**Fase 2 (próximas semanas):**
- ✅ Integración con Google Sheets (en lugar de CSV)
- ✅ Actualización automática de estados
- ✅ Dashboard visual

**Fase 3 (futuro):**
- ✅ API TikTok para programación automática
- ✅ Analytics de performance

---

**¡Sistema listo para usar!** 🚀

**Cualquier duda:** Revisar esta guía o preguntar a Sara
