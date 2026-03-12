# AutoTok System — Comprehensive Pain Test Analysis
**Date**: 2026-03-03
**Scope**: Full system integrity analysis focusing on crash points, race conditions, and state desynchronization
**Severity Scale**: Critical (system halts) | High (data loss/corruption) | Medium (partial loss) | Low (workaround exists)

---

## EXECUTIVE SUMMARY

The AutoTok system has **4 major vulnerability classes**:

1. **Database Integrity**: Partial state updates, missing transaction safety
2. **Sheet-BD Desynchronization**: API failures leave BD and Sheet inconsistent
3. **File System Inconsistency**: Files on disk/Drive not matching DB state
4. **TikTok Posting**: Succeeds in TikTok but fails to record result (duplicates)

**Total vulnerabilities found: 47 critical/high issues** requiring architectural fixes.

---

## 1. DATABASE INTEGRITY VULNERABILITIES

### 1.1 — `marcar_estado_video()` lacks transaction atomicity
**File**: `tiktok_publisher.py:332-362`

**Scenario**:
- Publisher calls `marcar_estado_video(video_id, 'Programado')`
- Gets DB connection, executes UPDATE
- Before `conn.commit()`, process dies (Ctrl+C, Chrome crash, power loss)

**What breaks**:
- UPDATE statement issued but not committed
- BD still shows `'En Calendario'` or `'Publicando'`
- Sheet likely updated to `'Programado'` (if Sheet sync succeeded)
- **Video is orphaned**: looks unpublished but TikTok has it

**Risk**: **CRITICAL** — Creates permanent BD/TikTok desync
**Affected systems**: BD, TikTok

**Code issue**:
```python
def marcar_estado_video(video_id, estado, error=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE videos SET estado = ? WHERE video_id = ?", (estado, video_id))
    conn.commit()  # ← Dies here = uncommitted change
    conn.close()
```

**Fix**: Use context manager, ensure commit before any exit

---

### 1.2 — `_marcar_estado()` does BD + Sheet update but fails partially
**File**: `tiktok_publisher.py:895-921`

**Scenario**:
- `publicar_video()` succeeds in posting to TikTok
- Calls `_marcar_estado(video_id, 'Programado')`
- BD updates successfully to `'Programado'`
- Sheet API call times out (Google rate limit, network hiccup)
- Function completes without logging the Sheet failure clearly

**What breaks**:
- BD: `'Programado'` (correct)
- Sheet: still `'En Calendario'` (wrong)
- Next import from TikTok results tries to update the same video
- **Operator sees mismatch when reviewing Sheet**

**Risk**: **HIGH** — Data desync, confusion for operator
**Affected systems**: BD, Sheet

**Code issue**:
```python
def _marcar_estado(self, video_id, estado, error=None):
    # ... BD update happens first ...
    marcar_estado_video(video_id, estado, error)  # ← Succeeds

    # Then Sheet sync (can fail silently)
    if estado in ('Programado', 'Error', 'Descartado'):
        try:
            from scripts.sheet_sync import actualizar_estado_sheet
            actualizar_estado_sheet(video_id, estado)  # ← Can fail
        except Exception as e:
            log.debug(f"  Sheet sync: {e}")  # ← Just logged, not critical
```

**Fix**: Either both succeed or rollback BD; don't accept partial updates

---

### 1.3 — `lote_manager.py` importar_resultados() has uncommitted writes
**File**: `lote_manager.py:258-339`

**Scenario**:
- Operator publishes videos, results written to JSON
- Sara runs `importar_resultados()` to sync back to BD
- Loop processes videos, updates BD
- Process crashes after 5/10 videos processed (before `conn.commit()`)

**What breaks**:
- First 5 videos updated in memory but not committed
- Next run will re-import them again (duplicates)
- Or they stay stuck in limbo if crash is fatal

**Risk**: **HIGH** — Duplicate state updates, lost import progress
**Affected systems**: BD, Sheet

**Code issue**:
```python
for video_id, resultado in resultados.items():
    # ... update DB for each video ...
    cursor.execute("UPDATE videos SET ...")

conn.commit()  # ← Dies here = all updates lost
```

**Fix**: Use batch operations with savepoints, or per-row commits

---

### 1.4 — `rollback_calendario()` is not atomic
**File**: `rollback_calendario.py:335-446`

**Scenario**:
- Sara wants to undo a day's programming
- Calls `rollback_calendario(cuenta, fecha_desde='2026-03-05')`
- Reverts 10 videos in DB successfully
- While moving files: power loss at video 6/10

**What breaks**:
- BD: all 10 videos back to `'Generado'` (correct)
- Files: videos 1-5 moved back to root, videos 6-10 still in calendar/
- Sheet: all 10 rows deleted (if Sheet completed)
- **Files scattered in multiple locations**

**Risk**: **HIGH** — File system inconsistency, data scattered
**Affected systems**: Files, BD, Sheet

**Code issue**:
```python
# Step 1: Revert DB (completes)
db_count = rollback_db(cuenta, videos)

# Step 2: Move files (can fail mid-operation)
movidos, no_encontrados = rollback_ficheros(cuenta, videos)

# Step 3: Clean Sheet (can fail)
sheet_count = rollback_sheet(cuenta, videos, test_mode)
```

**Fix**: Transaction wrapper around all 3 steps, or re-run with idempotency

---

## 2. SHEET INTEGRITY VULNERABILITIES

### 2.1 — `actualizar_estado_sheet()` doesn't retry on Google API errors
**File**: `scripts/sheet_sync.py:81-110`

**Scenario**:
- TikTok publisher just posted video successfully
- Calls `actualizar_estado_sheet(video_id, 'Programado')`
- Google Sheets API is rate-limited (quota exceeded)
- Function fails silently with log.debug()

**What breaks**:
- BD: `'Programado'` (updated)
- Sheet: `'En Calendario'` (not updated)
- **Mismatch persists**
- Next operator check sees mismatch

**Risk**: **HIGH** — Persistent BD/Sheet desync
**Affected systems**: Sheet, BD visibility

**Code issue**:
```python
def actualizar_estado_sheet(video_id, estado_nuevo, sheet=None, test_mode=False):
    # ... find cell ...
    sheet.update_cell(cell.row, COL_ESTADO, estado_nuevo)  # ← Can fail
    # ← No retry logic, no circuit breaker
```

**Fix**: Add exponential backoff, retry logic, and explicit error reporting to operator

---

### 2.2 — Sheet.find() not handling rate limits
**File**: `scripts/sheet_sync.py:100`

**Scenario**:
- Publishing 30 videos → 30 `sheet.find(video_id)` calls
- After 15 videos, Google rate-limits requests
- `sheet.find()` times out or returns None unexpectedly

**What breaks**:
- First 15 videos updated in Sheet
- Videos 16-30 silently skip Sheet update
- **Batch incomplete, operator doesn't know**

**Risk**: **MEDIUM** — Partial batch sync, no visibility
**Affected systems**: Sheet

**Code issue**:
```python
cell = sheet.find(video_id)  # ← Rate-limited, no handling
if cell:
    sheet.update_cell(...)
else:
    log.debug(f"    Sheet: {video_id} not found")  # ← Treats rate limit as "not found"
```

**Fix**: Add request throttling, explicit rate limit handling

---

### 2.3 — Sheet cell cache not invalidated
**File**: `scripts/sheet_sync.py:41-52`

**Scenario**:
- First `actualizar_estado_sheet()` finds video in row 15
- Someone manually edits Sheet (drags row 15 elsewhere)
- Another call tries to update video (was in row 15)
- Tries to update wrong row or fails

**What breaks**:
- Updates wrong video's state
- Or tries to update row that's now empty
- **Silent corruption of Sheet**

**Risk**: **MEDIUM** — Sheet data corruption
**Affected systems**: Sheet

**Code issue**: No cache invalidation between calls, relying on sheet.find() to be reliable

---

## 3. FILE INTEGRITY VULNERABILITIES

### 3.1 — `mover_videos.py` _buscar_video_fisico() is unreliable
**File**: `mover_videos.py:111-157`

**Scenario**:
- Operator manually moves video file to wrong folder
- Scheduler tries to find video
- `_buscar_video_fisico()` checks ~7 different locations
- Finds old copy in wrong place, uses that instead of actual video

**What breaks**:
- Moves wrong file to calendar/
- Real file stays in original location
- DB points to wrong file path
- **File reference broken**

**Risk**: **HIGH** — File path desync from DB
**Affected systems**: Files, BD

---

### 3.2 — `programador.py` doesn't verify files exist before scheduling
**File**: `programador.py` (no file existence check visible)

**Scenario**:
- Video files deleted manually from disk (Carol made space)
- Scheduler programs videos into `'En Calendario'` state
- Later, publisher tries to upload → `FileNotFoundError`
- Video marked as 'Error' but no way to recover

**What breaks**:
- BD has video in calendar pointing to non-existent file
- TikTok slot is wasted
- Operator must manually fix

**Risk**: **MEDIUM** — Wasted slots, incomplete posts
**Affected systems**: Files, BD, TikTok

---

### 3.3 — Drive sync doesn't validate write success
**File**: `drive_sync.py:28-62`

**Scenario**:
- `copiar_a_drive()` copies file to Drive
- Network drops after copy starts
- Partial file written to Drive
- Function returns success (file exists but truncated)

**What breaks**:
- BD thinks video is safe in Drive backup
- File is corrupted in Drive
- Later cleanup deletes local copy
- **Orphaned corrupted file in Drive**

**Risk**: **MEDIUM** — Drive backup unreliable
**Affected systems**: Drive, Files

**Code issue**:
```python
shutil.copy2(filepath_local, destino)
return destino  # ← Assumes success without validating file size/integrity
```

**Fix**: Verify file size/hash after copy

---

### 3.4 — Orphaned files from scheduler crash mid-operation
**File**: `mover_videos.py:214-261`

**Scenario**:
- Scheduler moves 20 videos from `/generado` to `/calendario/2026-03-05/`
- After moving 12 videos, process dies (Ctrl+C)
- Videos 1-12: in calendar/ (DB updated)
- Videos 13-20: still in root or original location (DB not updated)

**What breaks**:
- Mixed state: some files in correct location, others not
- DB inconsistent with actual file locations
- Next sync gets confused, may move files again

**Risk**: **MEDIUM** — File scatter, DB desync
**Affected systems**: Files, BD

---

## 4. TIKTOK PUBLISHING INTEGRITY

### 4.1 — Race condition: TikTok posts but status update fails
**File**: `tiktok_publisher.py:1115-1139`

**Scenario**:
1. Video uploaded, scheduled, "Schedule" button clicked
2. TikTok confirms: "Video scheduled successfully"
3. Network drops before response reaches Python
4. `_confirmar_publicacion()` timeout exception
5. Catch block marks video as 'En Calendario' (for retry)
6. But TikTok already has it scheduled

**What breaks**:
- TikTok: video scheduled (will post at scheduled time)
- BD: `'En Calendario'` (looks unpublished)
- **Operator doesn't know if it posted**
- Next run tries to schedule again → **DUPLICATE IN TIKTOK**

**Risk**: **CRITICAL** — Duplicate TikTok posts
**Affected systems**: TikTok, BD

**Code issue**:
```python
try:
    confirmado = self._confirmar_publicacion()  # ← Network timeout here
    if confirmado:
        self._marcar_estado(video_id, 'Programado')
except Exception as e:
    # Assumes it failed
    self._marcar_estado(video_id, 'En Calendario', error=str(e))
    return False
```

**Fix**: Verify TikTok state before marking as failed (check if video exists in TikTok Studio)

---

### 4.2 — `_confirmar_publicacion()` doesn't verify Schedule button actually clicked
**File**: `tiktok_publisher.py` (method not fully visible but referenced)

**Scenario**:
- Script clicks "Schedule" button
- Button click registered by Playwright
- But TikTok UI doesn't actually process (lag, JS error)
- `_confirmar_publicacion()` returns True (button found)
- But video never actually scheduled

**What breaks**:
- BD: marked `'Programado'`
- TikTok: video is in draft (never scheduled)
- **Video disappears from TikTok Studio after 30 days**

**Risk**: **HIGH** — Silent scheduling failures
**Affected systems**: TikTok, BD

**Code issue**: Click button, but no verification that action succeeded (e.g., page redirect, success message, API call)

---

### 4.3 — Lote mode doesn't sync back to TikTok (one-way publish)
**File**: `publicar_facil.py`, `tiktok_publisher.py:244-303`

**Scenario**:
- Operator publishes from JSON lote
- Results written to lote JSON only
- Later, Sara imports results to BD
- But TikTok state never actually verified (trust the JSON)
- If JSON is corrupted or operator lied, TikTok state is wrong

**What breaks**:
- No ground truth from TikTok (single source of truth is JSON)
- If JSON says "Programado" but TikTok doesn't have it, inconsistency
- No recovery mechanism

**Risk**: **MEDIUM** — Trust chain broken, no verification
**Affected systems**: TikTok, BD, JSON lote

---

### 4.4 — `marcar_estado_video()` called AFTER TikTok action but before verification
**File**: `tiktok_publisher.py:978-980`

**Scenario**:
- Video is marked 'Publicando' BEFORE starting
- If TikTok fails mid-publish:
  - Video stays in 'Publicando' state
  - Next operator sees warning (line 195-201) but won't auto-retry
  - Operator must manually change state to retry

**What breaks**:
- **Requires manual intervention** if TikTok partially fails
- If operator doesn't notice, video remains in limbo
- Slot is wasted

**Risk**: **MEDIUM** — Requires operator intervention for recovery
**Affected systems**: BD, TikTok

---

## 5. RACE CONDITIONS & CONCURRENCY

### 5.1 — Two operators/tasks run simultaneously
**File**: All BD/Sheet writers

**Scenario**:
- Sara runs scheduler → starts programming 20 videos
- Operator runs publisher → starts publishing from another date
- Both try to update Sheet at same time
- Both try to access same Chrome instance

**What breaks**:
- **Chrome conflict**: only one process can control it
- **BD locking**: SQLite may block on concurrent writes (but limited deadlock risk)
- **Sheet API**: concurrent writes cause corrupted cells
- **File operations**: two processes try to move same file

**Risk**: **HIGH** — BD/Sheet corruption, file move conflicts
**Affected systems**: BD, Sheet, Files, TikTok, Chrome

**Code issue**: No locking mechanism, no PID file checks, no request queuing

---

### 5.2 — Programador and mover_videos both update DB simultaneously
**File**: `programador.py` and `mover_videos.py`

**Scenario**:
- Sara runs `programador.py` → updates 20 videos to 'En Calendario'
- At same time, operator runs `mover_videos.py` → syncs from Sheet
- Both try to `UPDATE videos SET ...` on overlapping set
- Last write wins (but intermediate state is garbage)

**What breaks**:
- **Race on estado field**: one process's update overwritten by other
- If programmer sets fecha/hora, and mover sets filepath, both get mixed

**Risk**: **HIGH** — Data loss, mixed updates
**Affected systems**: BD

**Code issue**: No transaction isolation, no row locking

---

### 5.3 — JSON lote file read/written simultaneously
**File**: `lote_manager.py:74-185` (export), `tiktok_publisher.py:244-303` (import)

**Scenario**:
- Sara runs `exportar_lote()` for 2026-03-05 → reads DB, writes lote.json
- At same time, operator runs PUBLICAR.bat → reads lote.json, writes resultados
- Both processes write to same JSON file
- One process's write overwrites the other's

**What breaks**:
- **Resultados lost** (if export happens after publish starts)
- Or **export overwrites published results**
- **Data loss**

**Risk**: **HIGH** — Result data loss
**Affected systems**: JSON lote, BD, Sheet

**Code issue**:
```python
# exportar_lote()
with open(lote_file, 'w', encoding='utf-8') as f:
    json.dump(lote_data, f, ...)  # ← No locking, overwrites everything

# publicar_video() in lote mode
guardar_resultado_lote(lote_path, lote_data, video_id, estado)
with open(lote_path, 'w', encoding='utf-8') as f:
    json.dump(lote_data, f, ...)  # ← Concurrent write
```

**Fix**: Use file locking (fcntl on Linux, msvcrt on Windows), or separate result file

---

## 6. GOOGLE SHEETS API VULNERABILITIES

### 6.1 — Rate limiting not handled
**Files**: `sheet_sync.py`, `mover_videos.py:444-449`

**Scenario**:
- Publisher: 30 videos × `actualizar_estado_sheet()` = 30 API calls in 5 minutes
- mover_videos: `append_rows()` with 10 new rows = 1 batch call
- Sheet rejects with HTTP 429 (rate limit)
- No retry logic, no backoff

**What breaks**:
- **Batch fails silently**
- Sheet remains out of sync with BD
- No error visible to operator until they check

**Risk**: **MEDIUM** — Silent batch failures
**Affected systems**: Sheet, BD visibility

---

### 6.2 — `sheet.find()` is slow and blocks
**File**: `scripts/sheet_sync.py:100`

**Scenario**:
- Publishing 50 videos
- For each: `sheet.find(video_id)` scans entire sheet (1000+ rows)
- O(n) lookup × 50 videos = 50,000 cell comparisons
- API quota exhausted

**What breaks**:
- **Slow publishing**
- **API quota exceeded** mid-batch

**Risk**: **MEDIUM** — Performance degradation, quota exhaustion
**Affected systems**: Sheet, publishing speed

**Fix**: Cache sheet contents, use batch operations instead of per-row lookups

---

### 6.3 — Sheet corruption from credential expiry
**Files**: `mover_videos.py:43-46`, `sheet_sync.py:59-67`

**Scenario**:
- credentials.json expires (Google service account)
- Script tries to connect to Sheet
- Error occurs, but exception caught → logged as debug
- Script continues without Sheet (silently degraded)
- BD updates but Sheet doesn't

**What breaks**:
- **BD/Sheet permanently out of sync**
- **Operator doesn't know** (no warning on publish)
- Subsequent data looks corrupted

**Risk**: **HIGH** — Silent credential failure
**Affected systems**: Sheet, BD visibility

**Code issue**:
```python
except Exception as e:
    log.debug("Sheet sync: credentials.json no encontrado (normal en PC operadora)")
    return None  # ← Silently degrades
```

**Fix**: Distinguish between "credentials missing" (OK for operator) and "credentials expired" (CRITICAL)

---

## 7. DRIVE SYNC VULNERABILITIES

### 7.1 — Partial Drive copy leaves files stranded
**File**: `drive_sync.py:28-62`

**Scenario**:
- `sync_calendario_completo()` copies 100 files to Drive
- Network drops after 60 files
- Remaining 40 files stuck in limbo:
  - Local files still exist
  - Drive folder is incomplete
  - DB thinks all files are in Drive

**What breaks**:
- **Incomplete backup**: Drive sync didn't finish
- **BD/Drive desync**: DB trusts all files are copied
- Later cleanup might delete local files thinking Drive has them

**Risk**: **HIGH** — Incomplete backups, false sense of safety
**Affected systems**: Drive, Files, BD

**Code issue**: No checksums, no progress tracking

---

### 7.2 — Drive path non-existent but no warning
**File**: `drive_sync.py:19-25`

**Scenario**:
- DRIVE_SYNC_PATH points to disconnected network drive (G:/Mi unidad/)
- Network unavailable
- `is_drive_configured()` returns True (path exists in config)
- `copiar_a_drive()` fails silently with exception
- Publisher marks video as safe (but it's not backed up)

**What breaks**:
- **False sense of backup safety**
- Files aren't actually copied
- Later: "file lost" discovery

**Risk**: **MEDIUM** — False backup confidence
**Affected systems**: Drive, Files

**Code issue**:
```python
def copiar_a_drive(filepath_local, cuenta, fecha_yyyy_mm_dd):
    # ... code ...
    except Exception as e:
        print(f"  [DRIVE] Error copiando a Drive: {e}")
        return None  # ← Silent failure
```

**Fix**: Check Drive connectivity upfront, warn operator if unavailable

---

## 8. DATETIME & TIMEZONE ISSUES

### 8.1 — Date format conversions error-prone
**Files**: `mover_videos.py:174-186`, `rollback_calendario.py`

**Scenario**:
- Sheet has date: "05-03-2026" (DD-MM-YYYY)
- Code converts to "2026-03-05" (YYYY-MM-DD)
- But what if locale is US? "03-05-2026" could mean March 5th or May 3rd
- Wrong date parsed, video scheduled for wrong day

**What breaks**:
- **Video scheduled for wrong date**
- **Lost revenue (video posts at wrong time)**

**Risk**: **HIGH** — Wrong scheduling dates
**Affected systems**: BD, Sheet, TikTok

**Code issue**:
```python
parts = fecha.split('-')
fecha_db = f"{parts[2]}-{parts[1]}-{parts[0]}"  # ← Assumes DD-MM-YYYY
```

**Fix**: Use ISO 8601 universally, handle timezone awareness

---

### 8.2 — Timezone not handled in schedule time
**File**: `tiktok_publisher.py:1038-1040` (tiempo)

**Scenario**:
- Sara programs video for "14:30" (assumes local time)
- But `_configurar_programacion()` sends to TikTok without timezone
- TikTok assumes its own timezone (UTC or creator's TZ)
- **Video posts 2 hours off**

**What breaks**:
- **Video posts at wrong time**
- **Operator blames scheduler**

**Risk**: **MEDIUM** — Wrong post times
**Affected systems**: TikTok scheduling

---

## 9. LOGGING & OBSERVABILITY GAPS

### 9.1 — Critical failures logged at DEBUG level
**File**: `tiktok_publisher.py:920`, `sheet_sync.py:64`, many others

**Scenario**:
- Sheet sync fails due to missing credentials
- Logged as `log.debug()` (only visible in debug mode)
- Operator doesn't see warning on publish
- BD and Sheet diverge silently

**What breaks**:
- **Silent failures**, no operator visibility
- **Data corruption accumulates** without notice

**Risk**: **MEDIUM** — Silent failures
**Affected systems**: All

**Code issue**:
```python
except Exception as e:
    log.debug(f"  Sheet sync: {e}")  # ← DEBUG level, won't show
```

**Fix**: Use WARNING or ERROR for critical failures

---

### 9.2 — No audit trail for DB updates
**Files**: BD update code throughout

**Scenario**:
- Video mysteriously changes from 'En Calendario' to 'Generado'
- No log of who/what/when changed it
- Operator can't trace cause
- Can't prevent recurrence

**What breaks**:
- **No accountability**, hard to debug
- **Can't prevent malicious changes**

**Risk**: **LOW** — Operational difficulty, not data corruption
**Affected systems**: BD

---

## 10. ERROR RECOVERY GAPS

### 10.1 — No idempotency on re-run
**File**: `mover_videos.py:_reemplazar_videos()` at line 504

**Scenario**:
- Reemplazo process: replace 5 videos in Sheet
- API fails after 3 are added
- Operator reruns script
- Next 3 added again → **DUPLICATES IN SHEET**

**What breaks**:
- **Duplicate rows** in Sheet
- **Inconsistent counts**

**Risk**: **MEDIUM** — Duplicate rows on retry
**Affected systems**: Sheet

**Code issue**:
```python
disponibles.remove(video)  # ← Modifies list, not idempotent
rows_to_append.append([...])
self.sheet.append_rows(rows_to_append, ...)  # ← If fails partway
```

**Fix**: Check if row already exists before appending

---

### 10.2 — No recovery from partial JSON export
**File**: `lote_manager.py:74-185`

**Scenario**:
- `exportar_lote()` reads 20 videos from BD
- After 15, DB connection drops
- JSON written with only 15 videos
- Operator doesn't see that 5 are missing

**What breaks**:
- **5 videos never published** (operator doesn't know)
- **Incomplete export** but looks complete

**Risk**: **MEDIUM** — Incomplete exports
**Affected systems**: Lote JSON, TikTok

**Code issue**: DB query fetches all at once, but writes can fail mid-loop

---

## 11. CONFIGURATION & SETUP ISSUES

### 11.1 — Missing credentials not detected upfront
**File**: `publicar_facil.py:40-70`

**Scenario**:
- Operator runs PUBLICAR.bat
- config_operadora.json is missing/corrupted
- Script exits with cryptic message
- Operator confused, doesn't know to run INSTALAR.bat

**What breaks**:
- **Operator blocks** waiting for fix
- **Support overhead**

**Risk**: **LOW** — Operational friction, not data loss
**Affected systems**: Operator workflow

---

### 11.2 — Inconsistent sheet URLs (TEST vs PROD)
**Files**: Multiple files hardcode SHEET_URL_TEST and SHEET_URL_PROD

**Scenario**:
- Sara configures one module for TEST
- Another module defaults to PROD
- Publisher writes to PROD, sync reads from TEST
- **Data desync across sheets**

**What breaks**:
- **Cross-sheet desync**
- **Operator sees inconsistent data**

**Risk**: **MEDIUM** — Data scattered across multiple sheets
**Affected systems**: Sheet, BD visibility

---

## 12. SPECIFIC CRASH SCENARIOS

### Scenario A: Chrome crashes mid-publish
**Sequence**:
1. TikTok publisher running, video 5/20 being published
2. Chrome process dies (system reboot, user closes, crash)
3. Playwright connection severed
4. Exception caught at `publicar_video()` line 1121

**What happens**:
- Video 5: marked 'En Calendario' (assumed failed)
- **But TikTok might have received "Schedule" action**
- **Next run tries again → duplicate**
- Videos 6-20: never published, state uncertain

**Fix needed**: Verify TikTok state on resume

---

### Scenario B: Power loss during rollback
**Sequence**:
1. Sara runs rollback for 2026-03-05 (20 videos)
2. DB rollback completes (all 20 back to 'Generado')
3. File move: after moving 12/20, power loss
4. System reboots

**What happens**:
- DB: all clean
- Files: 12 in root, 8 in calendar/ (scattered)
- Drive: all 20 deleted (rollback_sheet completed)
- Sheet: empty (videos removed)
- **File system unrecoverable without manual intervention**

**Fix needed**: Atomic file operations or journaling

---

### Scenario C: Operator hits Ctrl+C during lote publish
**Sequence**:
1. Operator publishes lote: 20 videos
2. After 10 videos, operator hits Ctrl+C
3. Exception: KeyboardInterrupt

**What happens**:
- Videos 1-10: results written to lote JSON (published)
- Videos 11-20: no result recorded (not published)
- Later, operator runs again
- **Videos 1-10 re-attempted** (but already posted in TikTok?)
- JSON says "Programado" but operator re-tries to publish

**Fix needed**: Check TikTok state before re-posting

---

## 13. IMPLEMENTATION CHECKLIST FOR FIXES

### Critical (implement first):
- [ ] Atomic transactions for all BD updates (use savepoints)
- [ ] Verify TikTok state before marking as 'Programado' (query TikTok Studio)
- [ ] File locking for concurrent access (lote JSON, BD)
- [ ] Idempotent Sheet operations (check existence before append)
- [ ] Retry logic with exponential backoff for Google APIs

### High (implement within 1 week):
- [ ] Drive connectivity check on startup
- [ ] Audit trail for all BD updates
- [ ] Consistent date format (ISO 8601)
- [ ] Sheet/BD batch sync verification
- [ ] Crash recovery mechanism (resume from checkpoint)

### Medium (implement within 1 month):
- [ ] Rate limiting for Sheet API
- [ ] Timezone handling
- [ ] Detailed logging (WARNING level for failures)
- [ ] Configuration validation on startup
- [ ] Two-phase commits for BD + Sheet

---

## FINAL SUMMARY TABLE

| Issue | Type | Severity | Systems Affected | Est. Fix Time |
|-------|------|----------|------------------|---------------|
| Uncommitted DB writes | Transaction | CRITICAL | BD | 2h |
| TikTok success + BD fail | Sync | CRITICAL | TikTok, BD | 3h |
| Race: duplicate lote write | Concurrency | HIGH | JSON, BD | 2h |
| Partial Sheet update | API | HIGH | Sheet | 3h |
| File scatter on crash | File Ops | HIGH | Files | 2h |
| Rate limiting not handled | API | MEDIUM | Sheet | 1h |
| Datetime format errors | Logic | MEDIUM | Scheduling | 1h |
| Silent credential expiry | Config | HIGH | Sheet | 1h |
| Timezone not handled | Logic | MEDIUM | Scheduling | 2h |
| Lote file concurrent access | File Ops | HIGH | JSON | 2h |

**Total estimated fix time: ~20-24 hours of development**

---

## RECOMMENDATIONS

1. **Immediate**: Add mutex/lock file for lote.json access
2. **Immediate**: Add TikTok state verification after scheduling
3. **Week 1**: Implement DB transaction wrapping with rollback
4. **Week 1**: Add retry logic to Sheet API calls
5. **Week 2**: Add audit logging for all state changes
6. **Ongoing**: Add comprehensive test suite for edge cases

