# MANUAL: PROGRAMADOR DE CALENDARIO

**Version:** 5.1
**Fecha:** 2026-03-18
**Para:** Sara

---

## Que hace

Genera un calendario de publicaciones de TikTok distribuyendo videos generados en franjas horarias, respetando reglas por cuenta (videos/dia, no repetir hook mismo dia, distancia entre hooks). Actualiza estados en la BD (Turso). QUA-151: Ya NO mueve archivos ni copia a Drive.

Disponible en **dos interfaces**: CLI (programador.py) y dashboard web (/api/programar).

---

## Programar desde dashboard web (RECOMENDADO)

**URL:** `https://autotok-api-git-main-autotoky-6890s-projects.vercel.app/api/programar`

Acceso protegido por PIN (el mismo que el dashboard de estado).

### Pasos

1. Seleccionar cuenta (carga config automaticamente desde Turso)
2. Configurar: dias, fecha inicio, videos/dia, filtro producto (opcional)
3. Click "Simular" → preview calendario con estadisticas
4. Revisar distribucion: top_seller / validated / testing
5. Click "Programar" para ejecutar (actualiza BD directamente)

### Algoritmo y restricciones (QUA-228, QUA-298)

El programador web tiene **paridad completa** con el CLI. Ambos aplican exactamente las mismas restricciones:

- Distancia minima entre hooks (configurable por cuenta)
- Distancia minima entre SEO texts (dinamica segun volumen)
- **Distancia minima producto (QUA-298):** Mismo producto separado por minimo N posiciones, donde N = min(unique_products - 1, 3). Aplicado en pasadas 0-1, relajado en pasada 2. Web y CLI tienen paridad.
- Anti-consecutivo: no repetir mismo producto en slots adyacentes
- Testing acumulativo: limite global de videos testing, no solo por programacion
- Distribucion lifecycle: top_seller / validated / testing segun porcentajes de config
- Horas ocupadas: no solapar con videos ya programados en la misma fecha
- Gap-finding: busqueda de huecos para programacion de producto especifico
- Overnight window: soporte para ventanas horarias que cruzan medianoche (ej: 06:00-02:00). Internamente, las horas post-medianoche se representan con +24h (ej: 02:00 = 1560 min). Al programar para hoy: si la hora actual esta en la franja de dia, se limita a medianoche; si esta en la franja post-medianoche, se ajusta la hora actual con +24h para comparacion correcta (QUA-250, 5 commits)
- Buffer 30 min: si se programa para hoy, no asigna horas que ya han pasado + 30min margen
- CET/CEST en Vercel: `_now_cet()` calcula la hora correcta de España en Vercel (que usa UTC), con cambio automatico DST (ultimo domingo marzo → CEST +2h, ultimo domingo octubre → CET +1h)
- 2 pasadas por defecto (relajacion a 4 solo disponible en CLI interactivo)
- Anti-duplicados: excluye videos con estado != 'Generado'
- Export automatico de lotes a tabla `lotes` de Turso para que operadoras los vean en PUBLICAR.bat

### Panel "Ver restricciones aplicadas" (QUA-230)

Debajo del formulario del programador hay un panel colapsible que muestra todas las restricciones activas para la cuenta seleccionada:

- Distancia minima hook
- Distancia minima producto
- Gap minimo horas
- Distribucion lifecycle (pct_top_seller / pct_validated / pct_testing)
- Horario inicio/fin
- Videos por dia

El panel es **de solo lectura** y se carga dinamicamente desde la tabla `cuentas_config` de Turso. Permite a Sara verificar que la configuracion es la correcta antes de programar.

### Ventajas sobre CLI

- No requiere terminal ni acceso al PC local
- Preview visual tipo calendario antes de ejecutar
- Estadisticas de distribucion por lifecycle
- Panel de restricciones para verificar configuracion
- Accesible desde cualquier dispositivo

---

## Programar desde CLI

### Comando basico

```bash
python programador.py --cuenta CUENTA --dias N
```

### Ejemplos

```bash
# 7 dias desde manana
python programador.py --cuenta lotopdevicky --dias 7

# Desde fecha especifica
python programador.py --cuenta lotopdevicky --dias 14 --fecha-inicio 2026-03-15
```

### Que ocurre al programar

1. Escanea videos disponibles con estado "Generado" en BD (Turso)
2. Carga configuracion de cuenta desde tabla `cuentas_config` (Turso)
3. Genera calendario respetando reglas de la cuenta
4. Actualiza estados en BD (Generado → En Calendario)
5. **Auto-export** de lotes JSON a API para operadoras

> **QUA-151:** Ya NO se copian videos a carpetas de calendario ni a Drive. El video se queda donde se genero (`SynologyDrive/{cuenta}/{video_id}.mp4`).

### Parametros programador.py

| Parametro | Descripcion |
|-----------|-------------|
| `--cuenta` | Cuenta TikTok |
| `--dias` | Dias a programar |
| `--fecha-inicio` | Fecha inicio (YYYY-MM-DD), por defecto manana |

---

## Configuracion de cuentas

La configuracion de cuentas vive en la tabla `cuentas_config` de Turso. Se edita desde el panel web `/api/cuentas`.

| Campo | Descripcion |
|-------|-------------|
| `videos_por_dia` | Cuantos videos publicar diariamente |
| `max_mismo_hook_por_dia` | Max veces que puede aparecer mismo hook (0 = sin limite) |
| `max_mismo_producto_por_dia` | Max mismo producto por dia |
| `distancia_minima_hook` | Horas minimas entre el mismo hook |
| `gap_minimo_horas` | Horas minimas entre publicaciones |
| `horario_inicio` / `horario_fin` | Ventana horaria para publicaciones |
| `pct_top_seller` / `pct_validated` / `pct_testing` | Distribucion de slots por estado comercial (%) |

> **QUA-217:** `config_cuentas.json` ya no se usa. Turso es la unica fuente de verdad.

---

## Cambios de estado

Los cambios de estado se hacen directamente en la BD:
- **Programador:** Generado → En Calendario (automatico al programar)
- **Publisher:** En Calendario → Programado (automatico al publicar)
- **Sara:** Marcar Descartado o Violation (via dashboard `/api/estado`)
- **Rollback:** Cualquiera → Generado

> **QUA-217:** `sheet_sync.py` ha sido eliminado. No hay escritura a Google Sheet.

---

## Rollback (deshacer programacion)

### Desde dashboard web (QUA-217)

Panel `/api/estado` → boton rojo "Desprogramar rango":
1. Seleccionar cuenta
2. Elegir fecha desde / hasta
3. Confirmar → videos "En Calendario" vuelven a "Generado"

### Desde CLI

```bash
python cli.py
# → Opcion 8: Deshacer programacion

# Desde linea de comandos
python rollback_calendario.py CUENTA --ultima --si
python rollback_calendario.py CUENTA --fecha-desde 2026-02-28 --si
python rollback_calendario.py CUENTA --video-ids vid1,vid2,vid3 --si
```

> El rollback SOLO revierte la BD (estado → Generado, limpia fecha/hora/programado_at). NO mueve ficheros.

---

## Editar fecha/hora desde dashboard estado (QUA-209, QUA-229)

**URL:** `/api/estado`

Para cambiar la fecha u hora de un video ya programado:

1. Ir al dashboard de estado
2. Click en la fecha del video → aparece input date, editar y pulsar Enter o click ✓
3. Click en la hora del video → aparece input time, editar y pulsar Enter o click ✓
4. Feedback visual: borde verde = guardado OK

**Nota:** No se puede editar fecha/hora de videos ya publicados (con tiktok_post_id).

**Sincronización con lotes (QUA-244):** Cada cambio de fecha/hora/estado en el panel actualiza automáticamente el lote correspondiente en Turso via `_sincronizar_lote()`. Si se cambia la fecha, el video se mueve del lote antiguo al nuevo. Las operadoras siempre obtienen los datos actualizados porque `publicar_facil.py` lee de la API (Turso) primero, no del JSON local. Para refrescar los JSON locales manualmente, usar `SINCRONIZAR.bat`.

---

## Ciclo de vida del video

```
Generado → En Calendario → Programado (automatico, via publisher)
                ↓                ↓
         Descartado / Violation  Error (se reintenta)
                ↓
         Reemplazo automatico
```

---

## Troubleshooting

**"No hay suficientes videos"** → Generar mas con `cli.py` opcion 5

**"Cuenta no encontrada en cuentas_config"** → Crear cuenta en panel `/api/cuentas`

---

**Ultima actualizacion:** 2026-03-18 (QUA-298: distancia minima producto, QUA-230: panel ver restricciones aplicadas)
