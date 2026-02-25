# 🎮 CHULETA DE COMANDOS - AUTOTOK
**Referencia Rápida**  
**v3.2 - 2026-02-12**

---

## 📦 GENERACIÓN

```bash
# Listar productos
python main.py --list-productos

# Ver config
python main.py --config --producto proyector_magcubic

# Ver stats
python main.py --producto proyector_magcubic --cuenta lotopdevicky --stats

# Generar CON overlay (recomendado)
python main.py --producto proyector_magcubic --batch 20 --cuenta lotopdevicky --require-overlay

# Generar SIN forzar overlay
python main.py --producto proyector_magcubic --batch 20 --cuenta lotopdevicky

# Exportar combinaciones
python main.py --producto proyector_magcubic --export-csv combinaciones.csv
```

---

## 📅 CALENDARIO

```bash
# Programar desde mañana (default)
python programador.py --cuenta lotopdevicky --dias 7

# Programar desde fecha específica
python programador.py --cuenta lotopdevicky --dias 7 --fecha-inicio 2026-02-20
```

---

## 📁 SINCRONIZACIÓN

```bash
# Sincronizar TODAS las cuentas
python mover_videos.py --sync

# Sincronizar solo una cuenta
python mover_videos.py --cuenta lotopdevicky --sync
```

---

## 🔧 SETUP NUEVO PRODUCTO

```bash
# 1. Crear DB (solo primera vez)
python scripts/create_db.py

# 2. Importar BOFs
python scripts/import_bofs.py proyector_magcubic bof_proyector.json

# 3. Escanear material (hooks + brolls)
python scripts/scan_material.py proyector_magcubic

# 4. Registrar audios
python scripts/register_audio.py proyector_magcubic a1_audio.mp3 --bof-id 1
python scripts/register_audio.py proyector_magcubic a2_audio.mp3 --bof-id 1
```

---

## 🔄 WORKFLOW DIARIO

### Sara (Generación + Programación)
```bash
# 1. Sincronizar (SIEMPRE PRIMERO)
python mover_videos.py --sync

# 2. Generar videos
python main.py --producto proyector_magcubic --batch 20 --cuenta lotopdevicky --require-overlay
python main.py --producto melatonina --batch 30 --cuenta ofertastrendy20 --require-overlay

# 3. Programar calendario
python programador.py --cuenta lotopdevicky --dias 3
python programador.py --cuenta ofertastrendy20 --dias 3
```

### Sara (Subir a TikTok)
```bash
# 1. Abrir /calendario/2026-02-12/
# 2. Subir videos a TikTok Studio como borradores
# 3. En Google Sheet: Cambiar estado "En Calendario" → "Borrador"
# 4. Sincronizar
python mover_videos.py --sync
```

### Carol (Programar publicación)
```bash
# 1. Revisar borradores en TikTok Studio
# 2. Programar publicación en TikTok
# 3. En Google Sheet: Cambiar estado "Borrador" → "Programado"
# 4. Sincronizar
python mover_videos.py --sync
```

---

## 🛠️ UTILIDADES

```bash
# Ver videos en DB por cuenta
python check_videos.py lotopdevicky

# Resetear estados (solo testing)
python reset_estados.py lotopdevicky
```

---

## 🚨 TROUBLESHOOTING

### No hay videos para programar
```bash
# Ver qué videos hay
python check_videos.py lotopdevicky

# Generar más
python main.py --producto X --batch 20 --cuenta lotopdevicky
```

### Faltan overlays/BOFs
```bash
# Ver stats
python main.py --producto X --cuenta Y --stats

# Si no hay BOFs, importar
python scripts/import_bofs.py X bof_archivo.json
```

### Videos no se mueven con --sync
```bash
# Verificar que estado en Sheet es válido:
# - En Calendario
# - Borrador
# - Programado
# - Descartado

# Verificar que video existe físicamente
# Ver output del comando para detalles
```

### Rate Limit Google Sheets
```bash
# Esperar 1 minuto
sleep 60

# Reintentar
python programador.py --cuenta lotopdevicky --dias 3
```

---

## 💡 TIPS

- **SIEMPRE** ejecutar `--sync` antes de empezar a trabajar
- Usar `--require-overlay` para forzar BOFs
- NO mover archivos manualmente, usar `--sync`
- NO renombrar archivos ya registrados en DB
- Actualizar estado en Sheet PRIMERO, luego `--sync`
- Mínimo 10 BOFs por producto para funcionar bien

---

## 📋 REGLAS IMPORTANTES

### 🚫 NO HACER:
1. NO renombrar archivos registrados en DB
2. NO mover archivos manualmente (usar `--sync`)
3. NO editar DB directamente (usar scripts)

### ✅ HACER:
1. Actualizar Sheet primero, luego `--sync`
2. Ejecutar `--sync` antes de programar nueva tanda
3. Backup de `autotok.db` periódicamente

---

## 🔗 ENLACES

**Google Sheet TEST:** https://docs.google.com/spreadsheets/d/1NeepTinvfUrYDP0t9jIqzUe_d2wjfNYQpuxII22Mej8/

**Google Sheet PROD:** https://docs.google.com/spreadsheets/d/1QCb4xYKoLJPaMrGaBW311VQIyDg2Xa08V5DmsD2H81g/

---

**Actualizado:** 2026-02-12 - Phase 2 completada
