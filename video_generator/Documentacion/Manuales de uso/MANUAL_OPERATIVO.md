# MANUAL OPERATIVO - AUTOTOK

**Fecha:** 2026-03-02
**Version:** 1.0

Documento vivo que recoge los procedimientos operativos del dia a dia. Cada vez que se presente una situacion nueva, se documenta aqui con los pasos exactos.

---

## PROC-001: Cambio de precio en un producto

**Fecha del caso:** 2026-03-02
**Producto ejemplo:** bateria_power_bank_5000

**Contexto:** Cuando un producto cambia de precio, hay que reemplazar TODOS los videos existentes porque el BOF contiene el precio en el deal_math, el guion de audio y los overlays. Usar un video con precio incorrecto es un error critico.

### Prerrequisitos

- JSON del nuevo BOF preparado (con deal_math, guion, variantes y SEO actualizados al nuevo precio)
- Audios nuevos grabados con el guion actualizado
- Carol ha marcado como "Descartado" en Google Sheet los videos programados con el precio viejo

### Pasos

| Paso | Accion | CLI |
|------|--------|-----|
| **1** | **Sincronizar Sheet (sin reemplazar)** — Para que los videos descartados por Carol en Sheet se reflejen en la BD. Elegir **N** (no reemplazar). Sin este paso la BD sigue viendolos como "En Calendario". | Opcion 9 → N |
| **2** | **Desactivar el BOF viejo** — Marcar como inactivo para que el generador nunca lo seleccione. Seleccionar producto → D → elegir BOF viejo → S. | Opcion 21 |
| **3** | **Descartar videos "Generado" del BOF viejo** — Los que aun no se programaron. Filtrar por producto. **Repetir para cada cuenta.** | Opcion 6 |
| **4** | **Crear BOF nuevo** — Renombrar `bof_generado.json` actual (ej: `bof_generado_id11.json`). Colocar el JSON nuevo como `bof_generado.json`. Escanear material. **Apuntar el nuevo BOF ID.** | Opcion 1 |
| **5** | **Registrar audios nuevos** — Nombrar: `bof{NUEVO_ID}_audio1.mp3`, etc. Colocar en carpeta `audios/`. Escanear material de nuevo para registrarlos. | Opcion 1 |
| **6** | **Generar videos nuevos** — Si hay mas de 1 BOF, el sistema pregunta cual usar. Elegir el nuevo o Enter (auto solo usa activos). Generar para ambas cuentas. | Opcion 4 |
| **7** | **Reemplazar en calendario** — Sincronizar desde Sheet con reemplazo. Elegir **P** (producto concreto). El sistema llena los huecos con los videos nuevos. | Opcion 9 → P |
| **8** | **Verificar** — Comprobar en Sheet que los slots estan cubiertos. Comprobar en Drive que los archivos estan subidos. Comprobar contadores en CLI. | Sheet + Drive + Opcion 10 |

### Notas importantes

- El BOF viejo NO se borra. Queda inactivo para mantener integridad referencial con videos historicos.
- Los audios viejos se quedan en la carpeta y en BD vinculados al BOF inactivo. No molestan.
- El paso 1 (sync sin reemplazar) es CRITICO: sin el, la BD no sabe que Carol ha descartado videos.
- Si necesitas anadir videos al calendario (no solo reemplazar descartados), usa opcion 7 despues del paso 7.

### Tiempo estimado

El proceso completo toma 1-2 horas. El paso mas largo es la generacion de videos (paso 6).

### Issues relacionados en Linear

- QUA-67: Campo activo en producto_bofs (implementado 2026-03-02)
- QUA-68: Parametro --bof-id para forzar seleccion de BOF (implementado 2026-03-02)
- QUA-69: Mejorar flujo de gestion de BOFs (backlog — simplificaria los pasos 4-5)

---

*Siguiente procedimiento se anade aqui cuando surja un caso nuevo.*
