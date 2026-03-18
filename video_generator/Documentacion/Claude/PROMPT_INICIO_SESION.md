# PROMPT DE INICIO DE SESION

**Version:** 1.1
**Fecha:** 2026-03-16
**Uso:** Copiar y pegar este prompt AL INICIO de cada nueva sesion con Claude.

---

## El prompt

Copia desde aqui ↓

---

Hola, vamos a trabajar en el proyecto AutoTok. Antes de hacer NADA, necesito que sigas este protocolo obligatorio:

**PASO 1 — Lee estos archivos en este orden exacto (no te saltes ninguno):**

1. `autotok-videos/video_generator/Documentacion/Claude/INSTRUCCIONES_CLAUDE.md`
2. `autotok-videos/video_generator/Documentacion/Claude/Sesiones/SESION_[FECHA MAS RECIENTE].md`
3. `autotok-videos/video_generator/Documentacion/Claude/ESTADO_EJECUTIVO.md`

**PASO 2 — Si la tarea de hoy toca el dashboard web, lee tambien:**

4. `autotok-videos/video_generator/Documentacion/Tecnico/MAPA_DASHBOARD.md`
5. El archivo .py completo de cada pagina que vayas a modificar

**PASO 3 — Confirma que has entendido estas reglas NO NEGOCIABLES:**

- **No parchear sin analizar.** Antes de tocar codigo, escribe: que archivos vas a tocar, que otros archivos dependen de ellos, y si alguno esta en Kevin (Synology). Yo te doy OK antes de que empieces.
- **Kevin siempre.** Si modificas un archivo que existe en Kevin (`SynologyDrive/kevin/`), lo copias de proyecto → Kevin INMEDIATAMENTE despues del cambio. No al final, no despues. Ahora.
- **No inventes.** Si no sabes algo, di "no lo se, necesito mirar el codigo". No especules, no inventes explicaciones, no asumas.
- **Un cambio, un commit limpio.** Nada de 5 commits parcheando el mismo bug. Analiza primero, implementa despues.
- **Log de sesion en tiempo real.** Actualiza `Documentacion/Claude/Sesiones/SESION_YYYY-MM-DD.md` MIENTRAS trabajas, no al final.
- **Si toco el dashboard:** no toco la estructura HTML/CSS de ninguna pagina sin mi OK explicito. Los cambios de layout/estilo se hacen primero en el prototipo HTML y luego se integran pagina por pagina.
- **Paridad programador.** Si tocas `autotok-api/api/programar.py`, verificas que el cambio se replica en `video_generator/programador.py` y viceversa.
- **Todo trabajo pasa por Linear.** Antes de empezar cualquier tarea, comprueba si existe ticket en Linear. Si no existe, crealo con: titulo claro, descripcion del trabajo a hacer, archivos implicados. Actualiza el ticket con cada decision o cambio de estado mientras trabajas. Sin ticket = no se trabaja.

**PASO 4 — Dime que has leido todo y resumeme en 3-4 lineas:**
- Que se hizo en la ultima sesion
- Que quedo pendiente
- Estado general del proyecto

Despues de eso te digo que vamos a hacer hoy.

---

Copia hasta aqui ↑

---

## Notas para Sara

- **Cambia `[FECHA MAS RECIENTE]`** por la fecha del ultimo log de sesion (ej: SESION_2026-03-14.md)
- Si necesitas que trabaje en algo del dashboard, dile despues del paso 4: "Hoy vamos a tocar [pagina]. Lee el archivo completo antes de proponer nada."
- Si ves que empieza a escribir codigo sin haber hecho el paso 1-3, paralo con: "Para. Lee las instrucciones primero."
- Si inventa una explicacion sospechosa, pregunta: "¿Eso lo has verificado en el codigo o lo estas inventando?"
- Si hace un cambio y no menciona Kevin, pregunta: "¿Ese archivo esta en Kevin?"

## Por que este prompt funciona

El problema principal es que Claude pierde contexto entre sesiones y dentro de sesiones largas. Este prompt fuerza:

1. **Lectura obligatoria** antes de tocar nada — evita los errores por desconocimiento
2. **Confirmacion explicita** de las reglas — fuerza a Claude a procesarlas, no solo leerlas
3. **Aprobacion previa** antes de cada cambio — evita parches en cascada
4. **Log en tiempo real** — si el contexto se compacta, al menos el log esta al dia

No es infalible (Claude puede decir que ha leido algo y no haberlo procesado bien), pero reduce drasticamente los errores mas comunes que hemos tenido.

---

**Ultima actualizacion:** 2026-03-16
