# 📋 CHULETA DE COMANDOS v4.0

**Referencia rápida de todos los comandos del sistema.**
**Actualizado:** 2026-02-16

---

## 🚀 **SETUP INICIAL**

```bash
# Validar material disponible
python scripts/validate_bof.py PRODUCTO

# Importar BOF con variantes (PRODUCTO define el nombre, no el JSON)
python scripts/import_bof.py PRODUCTO bof_archivo.json

# Escanear hooks + brolls + audios
python scripts/scan_material.py PRODUCTO
```

**⚠️ IMPORTANTE:** El nombre del producto se define en el COMANDO, NO en el JSON.
- Comando: `python scripts/import_bof.py proyector_magcubic bof.json`
- Carpeta Drive: `recursos_videos/proyector_magcubic/`
- JSON: Puede llamarse como quieras (solo contiene info del BOF)

---

## 🎬 **GENERACIÓN DE VIDEOS**

```bash
# Generar lote (usa BATCH_SIZE de config.py)
python main.py --producto PRODUCTO --cuenta CUENTA

# Generar lote específico
python main.py --producto PRODUCTO --batch 20 --cuenta CUENTA

# Ver estadísticas
python main.py --producto PRODUCTO --cuenta CUENTA --stats

# Listar productos disponibles
python main.py --list-productos

# Ver configuración
python main.py --config
```

**Ejemplos:**
```bash
python main.py --producto proyector_magcubic --batch 50 --cuenta lotopdevicky
python main.py --producto melatonina --batch 20 --cuenta autotoky
```

---

## 📅 **PROGRAMACIÓN CALENDARIO**

```bash
# Programar N días (desde mañana)
python programador.py --cuenta CUENTA --dias N --test

# Programar desde fecha específica
python programador.py --cuenta CUENTA --dias N --fecha-inicio YYYY-MM-DD --test

# Usar Sheet PRODUCCIÓN (quita --test)
python programador.py --cuenta CUENTA --dias N
```

**Ejemplos:**
```bash
# 7 días desde mañana
python programador.py --cuenta lotopdevicky --dias 7 --test

# 14 días desde 15 de febrero
python programador.py --cuenta lotopdevicky --dias 14 --fecha-inicio 2026-02-15 --test

# Producción (Sheet real)
python programador.py --cuenta lotopdevicky --dias 30
```

---

## 🔄 **SINCRONIZACIÓN VIDEOS**

```bash
# Sincronizar cuenta específica (Sheet TEST)
python mover_videos.py --cuenta CUENTA --sync --test

# Sincronizar todas las cuentas (Sheet TEST)
python mover_videos.py --sync --test

# Sincronizar producción (Sheet real)
python mover_videos.py --cuenta CUENTA --sync
```

**Workflow:**
1. Cambiar estados en Google Sheet
2. Ejecutar sincronización
3. Videos se mueven automáticamente
4. Si hay Descartado/Violation, se busca reemplazo automáticamente

**Nota v4:** La sincronización ahora detecta videos que pasan a Descartado o Violation y busca un reemplazo automático en el mismo slot (fecha/hora). No reemplaza fechas pasadas.

---

## 🔄 **SYNC LIFECYCLE (ESTADOS COMERCIALES)**

```bash
# Desde CLI interactivo (Opción 11)
python cli.py
# → Opción 11: Sync lifecycle desde Sheet

# Lee el Sheet de Productos y actualiza estado_comercial en BD
# Sheet: https://docs.google.com/spreadsheets/d/18b5aQZUby4JHYpnrlZPyisC-aW21z44VKxFJk_3dviQ/
# Columna B = nombre producto, Columna E = estado comercial
```

**Estados comerciales y prioridad:**
- Activo → lifecycle_priority = 1 (se programa primero)
- En pausa → lifecycle_priority = 2
- Descatalogado → lifecycle_priority = 3 (se programa último)

---

## ↩️ **ROLLBACK**

```bash
# Desde CLI interactivo (Opción 10)
python cli.py
# → Opción 10: Deshacer programación
# → Pregunta: última tanda o por fecha
# → Pregunta: Sheet PROD o TEST

# Desde línea de comandos
python rollback_calendario.py --cuenta CUENTA --ultima --test --si
python rollback_calendario.py --cuenta CUENTA --fecha 2026-02-28 --si
```

**Nota v4:** El rollback ahora revierte TODOS los estados post-generado (En Calendario, Descartado, Violation, Borrador, Programado) a Generado. También busca ficheros en carpetas `descartados/` y `violations/`.

---

## 🗄️ **MIGRACIONES**

```bash
# Migración v4: añade estado_comercial y lifecycle_priority
python scripts/migrate_v4.py

# Migración v4 fix: añade 'Violation' al CHECK constraint
python scripts/migrate_v4_fix_violation.py

# Migración v3 (legacy)
python migrate_to_v3.py --reset-db
```

---

## 🔍 **DIAGNÓSTICO Y DEBUG**

```bash
# Ver estado de videos
python diagnostico.py CUENTA

# Corregir paths mal formados
python fix_paths.py CUENTA

# Verificar DB vacía/datos
python -c "
from scripts.db_config import get_connection
conn = get_connection()
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM videos')
print(f'Videos: {cursor.fetchone()[0]}')
"
```

---

## 🗄️ **BASE DE DATOS**

```bash
# Crear/resetear DB
python scripts/db_config.py --force

# Ver schema
python scripts/db_config.py --show-schema
```

---

## 📦 **GESTIÓN MATERIAL**

```bash
# Registrar hooks + brolls + audios (automático)
python scripts/scan_material.py PRODUCTO

# [OBSOLETO] Registrar audio individual
python scripts/register_audio.py PRODUCTO audio.mp3 --bof-id N
```

**Convenciones nombres:**
- Hooks: `hook_nombre_START2.mp4` (START opcional)
- Brolls: `A_clip.mp4` (letra = grupo)
- Audios: `bof1_nombre.mp3` (número = BOF ID)

---

## 🔄 **MIGRACIÓN**

```bash
# Migración completa con reset DB
python migrate_to_v3.py --reset-db

# Migración sin tocar DB
python migrate_to_v3.py
```

---

## 📊 **REPORTES Y ANÁLISIS**

```bash
# Estadísticas producto
python main.py --producto PRODUCTO --cuenta CUENTA --stats

# Exportar combinaciones (obsoleto v2)
# En v3.5 todo está en la DB
```

---

## ⚙️ **CONFIGURACIÓN**

```bash
# Ver config actual
python main.py --config

# Editar manualmente
notepad config.py                # Windows
nano config.py                   # Linux/Mac

# Config cuentas
notepad config_cuentas.json
```

---

## 🎯 **WORKFLOWS TÍPICOS**

### **Workflow 1: Producto Nuevo**
```bash
# 1. Crear carpeta en Drive
#    G:\Mi unidad\recursos_videos\nuevo_producto\
#    Subir hooks/, brolls/, audios/

# 2. Validar material
python scripts/validate_bof.py nuevo_producto

# 3. Crear BOF
#    Duplicar PLANTILLA_BOF.json → bof_nuevo_producto.json
#    Rellenar información

# 4. Importar BOF (IMPORTANTE: nombre en comando)
python scripts/import_bof.py nuevo_producto bof_nuevo_producto.json

# 5. Escanear material
python scripts/scan_material.py nuevo_producto

# 6. Generar videos
python main.py --producto nuevo_producto --batch 30 --cuenta lotopdevicky

# 7. Programar
python programador.py --cuenta lotopdevicky --dias 7 --test
```

---

### **Workflow 2: Generar Más Videos**
```bash
# 1. Generar
python main.py --producto proyector_magcubic --batch 20 --cuenta lotopdevicky

# 2. Programar
python programador.py --cuenta lotopdevicky --dias 5 --test
```

---

### **Workflow 3: Sincronizar Estados**
```bash
# 1. Cambiar estados en Google Sheet
#    (En Calendario → Borrador → Programado)

# 2. Sincronizar
python mover_videos.py --cuenta lotopdevicky --sync --test

# 3. Verificar
python diagnostico.py lotopdevicky
```

---

### **Workflow 4: Ciclo Completo con Reemplazo (v4)**
```bash
# 1. Sync estados comerciales desde Sheet Productos
#    CLI → Opción 11

# 2. Programar calendario
python programador.py --cuenta lotopdevicky --dias 7 --test

# 3. Carol/Sara revisan videos en Sheet, marcan Descartado/Violation

# 4. Sincronizar (detecta cambios y reemplaza automáticamente)
python mover_videos.py --cuenta lotopdevicky --sync --test

# 5. Si algo sale mal, rollback completo
python rollback_calendario.py --cuenta lotopdevicky --ultima --test --si
```

---

### **Workflow 5: Añadir Material**
```bash
# 1. Subir nuevos archivos a Drive (hooks/brolls/audios)

# 2. Esperar sincronización Drive

# 3. Re-escanear
python scripts/scan_material.py PRODUCTO

# 4. Generar con nuevo material
python main.py --producto PRODUCTO --batch 20 --cuenta CUENTA
```

---

## 📤 **PUBLICACIÓN AUTOMÁTICA (TikTok Publisher)**

```bash
# Publicar videos de una cuenta/fecha (modo normal, con BD)
python tiktok_publisher.py --cuenta ofertastrendy20 --fecha 2026-03-05

# Publicar solo los primeros 5
python tiktok_publisher.py --cuenta ofertastrendy20 --fecha 2026-03-05 --limite 5

# Simular sin publicar (dry-run)
python tiktok_publisher.py --cuenta ofertastrendy20 --fecha 2026-03-05 --dry-run

# Publicar desde JSON de lote (modo operadora, sin BD)
python tiktok_publisher.py --lote "G:/Mi unidad/material_programar/ofertastrendy20/_lotes/lote_ofertastrendy20_2026-03-05.json"

# Ver videos pendientes
python tiktok_publisher.py --listar
python tiktok_publisher.py --listar --cuenta ofertastrendy20
```

---

## 📦 **LOTES JSON (Flujo operadoras)**

```bash
# Exportar lote manualmente (normalmente se hace automáticamente al programar)
python -m scripts.lote_manager --exportar --cuenta ofertastrendy20 --fecha 2026-03-05

# Importar resultados de operadoras
python -m scripts.lote_manager --importar --cuenta ofertastrendy20

# Listar lotes de una cuenta
python -m scripts.lote_manager --listar --cuenta ofertastrendy20
```

**NOTA:** Al ejecutar `programador.py`, los lotes se exportan automáticamente a Drive. Al volver a programar, los resultados pendientes se importan automáticamente antes.

---

### **Workflow 6: Publicación con operadoras (QUA-43)**

```bash
# LADO SARA:
# 1. Programar calendario (auto-export de lotes a Drive)
python programador.py --cuenta ofertastrendy20 --dias 7

# 2. (Operadora publica con PUBLICAR.bat)

# 3. Volver a programar → auto-import de resultados
python programador.py --cuenta ofertastrendy20 --dias 7

# LADO OPERADORA (en su PC):
# 1. Primera vez: ejecutar INSTALAR.bat
# 2. Cada día: doble-click en PUBLICAR.bat
```

---

## 🚨 **TROUBLESHOOTING RÁPIDO**

```bash
# Material no encontrado
python scripts/scan_material.py PRODUCTO

# Videos no se mueven
python fix_paths.py CUENTA

# DB corrupta
python scripts/db_config.py --force

# Verificar todo está bien
python diagnostico.py CUENTA
python main.py --producto PRODUCTO --cuenta CUENTA --stats
```

---

## 💡 **TIPS RÁPIDOS**

**Generar masivamente:**
```bash
# Lote grande
python main.py --producto PRODUCTO --batch 100 --cuenta CUENTA
```

**Programar con anticipación:**
```bash
# 30 días desde fecha futura
python programador.py --cuenta CUENTA --dias 30 --fecha-inicio 2026-03-01 --test
```

**Múltiples productos:**
```bash
# Producto 1
python main.py --producto melatonina --batch 20 --cuenta lotopdevicky

# Producto 2
python main.py --producto proyector --batch 20 --cuenta lotopdevicky

# Programar mezclados
python programador.py --cuenta lotopdevicky --dias 10 --test
```

---

## 📋 **PARÁMETROS IMPORTANTES**

### **main.py**
- `--producto` - Nombre producto (debe coincidir con carpeta Drive)
- `--batch` - Cantidad videos
- `--cuenta` - Cuenta TikTok (requerido)
- `--stats` - Solo estadísticas
- `--config` - Ver configuración
- `--list-productos` - Listar productos

### **programador.py**
- `--cuenta` - Cuenta TikTok
- `--dias` - Días a programar
- `--fecha-inicio` - Fecha inicio (YYYY-MM-DD)
- `--test` - Usar Sheet TEST

### **tiktok_publisher.py**
- `--cuenta` - Cuenta TikTok
- `--fecha` - Fecha a publicar (YYYY-MM-DD)
- `--limite` - Máximo de videos
- `--lote` - Ruta a JSON de lote (modo operadora)
- `--dry-run` - Simular sin publicar
- `--listar` - Ver pendientes
- `--cdp` - Conectar a Chrome ya abierto

### **mover_videos.py**
- `--cuenta` - Cuenta específica (opcional)
- `--sync` - Sincronizar (requerido)
- `--test` - Usar Sheet TEST

---

## 📝 **NOTAS SOBRE NOMBRES**

**El nombre del producto se define en 3 lugares (deben coincidir):**
1. Carpeta Drive: `recursos_videos/PRODUCTO/`
2. Comando import: `python scripts/import_bof.py PRODUCTO ...`
3. Todos los comandos: `--producto PRODUCTO`

**El JSON del BOF:**
- Puede llamarse como quieras: `bof.json`, `bof_magcubic.json`, `mi_bof.json`
- Solo contiene la info del BOF (deal, variantes, etc.)
- NO define el nombre del producto

**Ejemplo correcto:**
```bash
# Drive tiene: recursos_videos/proyector_magcubic/
# JSON se llama: bof_magcubic.json (o cualquier nombre)
# Comando: 
python scripts/import_bof.py proyector_magcubic bof_magcubic.json
                             ^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^
                             Nombre producto   Nombre archivo
```

---

**¡Guarda este archivo para referencia rápida!** 📌
