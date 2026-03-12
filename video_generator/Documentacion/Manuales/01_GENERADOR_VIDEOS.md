# MANUAL: GENERADOR DE VIDEOS

**Version:** 1.0
**Fecha:** 2026-03-03
**Para:** Sara

---

## Que hace

Genera videos cortos para TikTok combinando automaticamente hooks (clips intro), brolls (clips producto), audios (voiceovers) y overlays (texto en pantalla). Cada video es unico porque el sistema combina material diferente y controla que no se repitan combinaciones.

---

## Preparar un producto nuevo

### 1. Crear carpeta en Synology

```
C:\Users\gasco\SynologyDrive\recursos_videos\
└── nombre_producto/
    ├── input_producto.json
    ├── hooks/
    ├── brolls/
    └── audios/
```

> **Nota:** Desde QUA-201, RECURSOS_BASE apunta a Synology (`SynologyDrive/recursos_videos`), no a Google Drive.

**Naming de carpeta:** `{producto}_{marca}_{caracteristica}` — Ejemplos: `melatonina_aldous_500comp`, `cable_goojodoq_65w`, `proyector_magcubic_hy300`

### 2. Crear input_producto.json

```json
{
  "marca": "Aldous Bio",
  "producto": "Melatonina Pura",
  "caracteristicas": ["500 comprimidos", "5mg", "tienda oficial"],
  "deal_math": "40% OFF",
  "url_producto": "https://s.click.aliexpress.com/tu-link"
}
```

### 3. Subir material

**hooks/** — Clips intro de 3-6 segundos
- Naming: `A_descripcion.mp4`, `B_descripcion.mp4`, etc. (letra mayuscula + guion bajo)
- Opcional: `_START2` para empezar desde segundo especifico
- Minimo recomendado: 10 hooks
- La letra identifica el hook en el calendario (evita repetir mismo hook en el mismo dia)

**brolls/** — Clips de producto, cualquier duracion
- Sin grupos: `producto_frente.mp4`, `mano_sosteniendo.mp4`
- Con grupos (recomendado): `A_producto_frente.mp4`, `B_mano.mp4` — el sistema evita usar 2 clips del mismo grupo en 1 video
- Minimo recomendado: 20 clips

**audios/** — Voiceovers de 10-20 segundos
- Naming: `bof{ID}_nombre.mp3` — El numero conecta con el BOF en BD
- Formatos: `.mp3`, `.m4a`, `.wav`
- Minimo recomendado: 3 audios por BOF

### 4. Escanear y registrar todo

```bash
# Comando unico que hace todo (genera BOF + importa + escanea material)
python scan_material.py nombre_producto --auto-bof

# O paso a paso:
python bof_generator.py --input "G:\Mi unidad\recursos_videos\nombre_producto"
python import_bof.py nombre_producto bof_generado.json
python scripts/scan_material.py nombre_producto
```

### 5. Validar

```bash
python scripts/validate_bof.py nombre_producto
```

Verifica: 10+ hooks, 20+ brolls, 5+ variantes overlay, 3+ audios vinculados.

---

## Generar videos

### Comando basico

```bash
python main.py --producto PRODUCTO --batch N --cuenta CUENTA
```

### Ejemplos

```bash
# 20 videos de un producto
python main.py --producto proyector_magcubic --batch 20 --cuenta lotopdevicky

# Ver estadisticas sin generar
python main.py --producto proyector_magcubic --cuenta lotopdevicky --stats

# Listar productos disponibles
python main.py --list-productos

# Ver configuracion
python main.py --config
```

### Generacion masiva (CLI interactivo)

```bash
python cli.py
# → Opcion 4: Generar videos (multiples productos)
```

Selecciona varios productos, elige cuentas, define cantidad, confirma y ejecuta automaticamente.

### Parametros main.py

| Parametro | Descripcion |
|-----------|-------------|
| `--producto` | Nombre producto (debe coincidir con carpeta Drive) |
| `--batch` | Cantidad de videos a generar |
| `--cuenta` | Cuenta TikTok (requerido) |
| `--stats` | Solo mostrar estadisticas |
| `--config` | Ver configuracion actual |
| `--list-productos` | Listar productos en BD |

---

## Gestion de material por formato (QUA-201)

Desde la sesion 2026-03-11, el material (hooks, brolls, audios) se asigna a formatos individuales via la tabla `formato_material`.

### Asignar material desde dashboard

1. Ir a `/api/formatos`
2. Click en boton "Material" del formato
3. En el modal: marcar checkboxes de hooks, brolls y audios que aplican
4. Boton "Todos" por seccion para seleccionar todo
5. Indicador de capacidad muestra combinaciones unicas posibles

### Registrar material nuevo desde dashboard

1. En el modal de material, click "+ Añadir" en la seccion deseada
2. Seleccionar archivo(s) del disco
3. Se registra automaticamente con duracion detectada via HTML5 Audio/Video API

### Editar grupo y start_time (QUA-208)

En el modal de material:
- **Brolls:** input para grupo (texto) + start_time (segundos)
- **Hooks:** input para start_time (segundos)
- Guardar: click icono de guardar o blur del campo

### Como funciona en el generador

El generador lee `formato_material` para cada BOF y filtra el material disponible. Si un formato tiene asignaciones en formato_material, SOLO usa ese material. Si no tiene asignaciones (legacy), usa todo el material del producto.

---

## Gestion de BOFs

### Desde CLI interactivo

```bash
python cli.py
# → Opcion 21: Gestionar BOFs de producto
```

Permite activar/desactivar BOFs individuales. Un BOF desactivado no se usa para generar videos nuevos pero se mantiene en BD para integridad referencial con videos historicos.

### Forzar BOF especifico

```bash
python main.py --producto PRODUCTO --batch 20 --cuenta CUENTA --bof-id 5
```

---

## Procedimiento: Cambio de precio en producto

**Contexto:** Cuando un producto cambia de precio hay que reemplazar TODOS los videos existentes porque el BOF contiene el precio en deal_math, guion de audio y overlays.

**Prerrequisitos:** JSON del nuevo BOF preparado, audios nuevos grabados, Carol ha marcado como "Descartado" en Sheet los videos con precio viejo.

| Paso | Accion | CLI |
|------|--------|-----|
| 1 | Sincronizar Sheet (elegir N, sin reemplazar) — Para que los descartados por Carol se reflejen en BD | Opcion 9 → N |
| 2 | Desactivar BOF viejo | Opcion 21 |
| 3 | Descartar videos "Generado" del BOF viejo (repetir por cuenta) | Opcion 6 |
| 4 | Colocar JSON nuevo como bof_generado.json, escanear material | Opcion 1 |
| 5 | Registrar audios nuevos (naming: `bof{NUEVO_ID}_audio.mp3`), escanear | Opcion 1 |
| 6 | Generar videos nuevos para ambas cuentas | Opcion 4 |
| 7 | Sincronizar con reemplazo (elegir P, producto concreto) | Opcion 9 → P |
| 8 | Verificar en Sheet, Drive y CLI | Sheet + Drive + Opcion 10 |

**Notas:** El BOF viejo NO se borra, queda inactivo. Audios viejos se quedan vinculados al BOF inactivo. El paso 1 es critico: sin el, la BD no sabe que Carol ha descartado videos. Tiempo estimado: 1-2 horas.

**Issues relacionados:** QUA-67, QUA-68, QUA-69

---

## Nombres de producto

El nombre del producto se define en 3 lugares que deben coincidir:

1. Carpeta Drive: `recursos_videos/PRODUCTO/`
2. Comando import: `python scripts/import_bof.py PRODUCTO ...`
3. Todos los comandos: `--producto PRODUCTO`

El JSON del BOF puede llamarse como quieras — solo contiene la info del BOF, NO define el nombre del producto.

---

## Troubleshooting

**"No se generan videos"** → Verifica nombres de archivos (letra mayuscula, guiones bajos)

**"Solo genera 1 video por dia en calendario"** → Necesitas mas hooks unicos (minimo 4-6 para 4 videos/dia)

**"Material no encontrado"** → `python scripts/scan_material.py PRODUCTO`

**"No se encontro input_producto.json"** → Crea el archivo en la carpeta del producto

**"BOF ya existe"** → Borra `bof_generado.json` para regenerar

---

**Ultima actualizacion:** 2026-03-11 (QUA-201: material por formato, QUA-208: editable grupo/start_time)
