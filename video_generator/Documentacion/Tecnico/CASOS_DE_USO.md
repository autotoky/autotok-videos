# CASOS DE USO — AUTOTOK

**Version:** 1.1
**Fecha:** 2026-03-08
**Diagrama visual:** `FLUJOS_CASOS_DE_USO.html` (abrir en navegador)

---

## CREAR VIDEOS — Sara

| # | Caso de uso | Estado | Ticket | Notas |
|---|-------------|--------|--------|-------|
| 1 | Generar videos de 1 producto, X cantidad, para 1 cuenta | ✅ Cubierto | — | cli.py opcion 3 |
| 2 | Generar videos de 1 producto, X cantidad, para varias cuentas | ⚠️ Parcial | QUA-172 | Funciona con "Ambas cuentas" pero con 3 cuentas faltara seleccion flexible |
| 3 | Generar videos de varios productos en lote (masivo) | ⚠️ Parcial | QUA-161 | cli.py opcion 4. No permite indicar que productos son IA y cuales no, todos comparten el mismo setting |
| 4 | Regenerar videos con material nuevo | ⚠️ Parcial | QUA-164 | Se puede generar mas, pero no detecta material nuevo vs ya usado |
| 5 | Dar de alta un producto nuevo completo | ⚠️ UX pobre | QUA-165 | Funciona pero proceso muy manual: crear JSON, generar BOF, obtener ID, renombrar audios, re-escanear. Lifecycle falla con frecuencia |
| 6 | Editar un BOF existente | ⚠️ Mejorable | QUA-52, QUA-69, QUA-34 | Funciona pero proceso mejorable, tickets abiertos |
| 7 | Importar un BOF externo | ⚠️ Mejorable | QUA-52, QUA-69, QUA-34 | Idem caso 6 |
| 8 | Escanear material nuevo | ✅ Cubierto | — | cli.py opcion 1 |
| 9 | Validar material completo | ✅ Cubierto | — | cli.py opcion 2 |

## PROGRAMAR CALENDARIO — Sara

| # | Caso de uso | Estado | Ticket | Notas |
|---|-------------|--------|--------|-------|
| 10 | Programar X dias para 1 cuenta | ✅ Cubierto | — | cli.py opcion 7 |
| 11 | Programar X dias para varias cuentas | ⚠️ Parcial | QUA-172 | Funciona con "Ambas" pero misma limitacion que caso 2 |
| 12 | Programar desde fecha especifica | ✅ Cubierto | — | --fecha-inicio YYYY-MM-DD |
| 13 | Rollback tanda completa | ✅ Cubierto | — | rollback_calendario.py v3.0 --ultima. QUA-151: solo revierte BD, no mueve ficheros |
| 14 | Rollback por fecha | ✅ Cubierto | — | rollback_calendario.py v3.0 --fecha-desde. QUA-151: solo revierte BD |
| 15 | Cambiar videos individuales sin rollback del dia entero | ❌ No cubierto | Pendiente (relacionado con QUA-155) | Hay que diseñar flujo |
| 16 | Descartar video y reemplazo automatico | ✅ Cubierto | — | Marcar Descartado → sync → reemplazo |
| 17 | Marcar Violation y reemplazo | ✅ Cubierto | — | Mismo flujo que descarte |
| 18 | Ver stock de videos disponibles por producto/cuenta | ❌ No cubierto | QUA-166 | Necesita vista en dashboard Vercel |
| 19 | Ver calendario programado de una cuenta | ⚠️ Parcial | Relacionado con QUA-155 | Depende de Sheet. Debe moverse a dashboard Vercel |

## PUBLICAR VIDEOS — Carol / Vicky

| # | Caso de uso | Estado | Ticket | Notas |
|---|-------------|--------|--------|-------|
| 20 | Publicar videos del dia con doble-click | ✅ Cubierto | — | PUBLICAR.bat |
| 21 | Ver resumen antes de publicar | ⚠️ Parcial | Relacionado con QUA-155 | Funcional pero poco amigable. Debe moverse a dashboard |
| 22 | Reintentar solo los que dieron error | ✅ Cubierto | QUA-143 | Publisher filtra OK, solo reintenta Error |
| 23 | Saber si hay que hacer algo manual antes (escaparate, re-login) | ❌ No cubierto | QUA-171 | Mostrar lista de productos que deben estar en escaparate antes de publicar |

## MONITORIZAR RESULTADOS — Sara

| # | Caso de uso | Estado | Ticket | Notas |
|---|-------------|--------|--------|-------|
| 24 | Vista global del estado de publicaciones | ❌ No fiable | QUA-155 | Ni Sheet ni dashboard reflejan realidad. Critico |
| 25 | Ver que se publico y que fallo hoy, con detalle | ✅ Cubierto | QUA-167 (mejora) | Email tiene la info. Dashboard mejoraria la experiencia |
| 26 | Resultados de operadoras llegan a BD automaticamente | ❌ No cubierto | QUA-155 | PROBLEMA CRITICO. API no conectada con BD local |
| 27 | Sheet/dashboard refleje estado real | ❌ No cubierto | QUA-155 | Depende de resolver sync API↔BD |
| 28 | Copiar SEO, hashtags, URL rapidamente | ❌ No cubierto | Relacionado con QUA-155 | Dashboard tiene botones pero no datos reales. Debe funcionar con datos |
| 29 | Ver enlace directo al video en TikTok | ⚠️ Parcial | Relacionado con QUA-155 | tiktok_post_id se guarda. Dashboard /api/estado da error 500 actualmente |

## GESTIONAR ERRORES — Sara

| # | Caso de uso | Estado | Ticket | Notas |
|---|-------------|--------|--------|-------|
| 30 | Diagnosticar por que fallo un video | ✅ Cubierto | — | Email + JSON tienen error y suggestion. Suficiente por ahora |
| 31 | Reintentar video con error | ✅ Cubierto | — | Relanzar PUBLICAR.bat |
| 32 | Descartar video con error y reemplazo | ⚠️ Parcial | Relacionado con QUA-155 | Proceso manual multi-paso. Debe ser automatico desde un unico punto |
| 33 | Corregir datos de un video y reintentar | ❌ No cubierto | QUA-170 | Caso habitual. No hay flujo definido |

## GESTIONAR PRODUCTOS — Sara

| # | Caso de uso | Estado | Ticket | Notas |
|---|-------------|--------|--------|-------|
| 34 | Cambiar estado comercial | ✅ Cubierto | — | Sheet Productos → cli.py opcion 11 |
| 35 | Anadir/quitar productos del escaparate | ✅ Cubierto | — | Editar config_publisher.json manual |
| 36 | Ver estadisticas de un producto | ⚠️ Parcial | QUA-169 | diagnostico.py da info basica. Dashboard mejoraria |

## INSTALACION Y MANTENIMIENTO — Sara

| # | Caso de uso | Estado | Ticket | Notas |
|---|-------------|--------|--------|-------|
| 37 | Instalar en PC nuevo de operadora | ✅ Cubierto | — | INSTALAR.bat + setup_operadora.py + manual 05 |
| 38 | Actualizar codigo en operadoras | ✅ Cubierto | — | Synology auto-sync + VERSION check |
| 39 | Backup BD | ✅ Cubierto | — | cli.py opcion 12 |
| 40 | Verificar coherencia BD/Sheet/archivos/API | ❌ No cubierto | QUA-155 | CRITICO. No hay comando que compare los 4 sistemas |

## DISTRIBUCION — Sistema automatico

| # | Caso de uso | Estado | Ticket | Notas |
|---|-------------|--------|--------|-------|
| 41 | Videos y lotes llegan a operadoras | ✅ Cubierto | — | Synology Drive auto-sync |
| 42 | Resultados vuelven a BD central | ❌ No cubierto | QUA-155 | Solo vuelven al ejecutar programador. Debe ser automatico |
| 43 | Actualizaciones de codigo llegan a operadoras | ✅ Cubierto | — | Synology + VERSION check |

## PROTECCIONES AUTOMATICAS — Sistema

| # | Caso de uso | Estado | Ticket | Notas |
|---|-------------|--------|--------|-------|
| 44 | No publicar duplicados | ⚠️ Parcial | QUA-88 | Anti-dup en programacion OK. Vulnerabilidad C1: crash post-publicacion puede duplicar |
| 45 | No publicar con datos incompletos | ✅ Cubierto | — | Validacion pre-publicacion |
| 46 | No repetir hook mismo dia | ✅ Cubierto | — | max_mismo_hook_por_dia en config |
| 47 | No exceder videos/dia | ✅ Cubierto | — | videos_por_dia en config |
| 48 | Registrar estado correctamente aunque haya crash | ⚠️ Parcial | QUA-88 | Vulnerabilidad C3 del pain test |

## MATERIAL IA — Mar

| # | Caso de uso | Estado | Ticket | Notas |
|---|-------------|--------|--------|-------|
| 49 | Saber que productos necesitan material nuevo | ❌ No cubierto | — | Depende de comunicacion con Sara. Mejora futura |
| 50 | Entregar material en formato correcto | ✅ Cubierto | — | Documentado en manual 01 |

---

## RESUMEN

| Estado | Cantidad | Porcentaje |
|--------|----------|------------|
| ✅ Cubierto | 21 | 42% |
| ⚠️ Parcial / UX pobre | 14 | 28% |
| ❌ No cubierto | 15 | 30% |
| **Total** | **50** | |

### Problemas criticos (bloquean operativa diaria)

| Caso | Problema | Ticket |
|------|----------|--------|
| #26, #42 | Resultados de operadoras no vuelven a BD | QUA-155 ✅ Resuelto: Turso es BD unica, resultados van directo a Turso |
| #27, #24 | Ninguna vista es fiable | QUA-155 ✅ Parcialmente resuelto: Dashboard v2.0 lee de Turso |
| #40 | No hay verificacion de coherencia entre sistemas | QUA-151 simplifica: solo BD + archivos (sin Sheet/Drive sync) |
| #28 | Dashboard tiene UI pero sin datos reales | QUA-92 ✅ + QUA-155 ✅: Dashboard conectado a Turso |

### Mejoras de mayor impacto

| Caso | Mejora | Ticket |
|------|--------|--------|
| #15 | Editar programacion sin rollback completo | Pendiente |
| #32 | Descarte automatico desde un unico punto | QUA-155 |
| #33 | Corregir datos de video y reintentar | QUA-170 |
| #5 | Flujo guiado para alta de producto | QUA-165 |
| #23 | Verificacion de escaparate antes de publicar | QUA-171 |

---

**Ultima actualizacion:** 2026-03-08
