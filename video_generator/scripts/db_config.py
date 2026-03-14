"""
DB_CONFIG.PY - Configuración Base de Datos (Turso HTTP API + SQLite fallback)
Versión: 4.1 - QUA-155: Turso como fuente de verdad via HTTP API
Fecha: 2026-03-08

Conexión a Turso cloud via HTTP API (zero deps — solo urllib).
Si turso_config.json no existe, cae a SQLite local (backward compatible).

La config de Turso se lee de turso_config.json en la raíz del proyecto:
    {
        "sync_url": "libsql://autotok-autotok.aws-eu-west-1.turso.io",
        "auth_token": "...",
        "local_replica": "autotok_replica.db"
    }

Notas:
- sync_url se convierte automáticamente a HTTPS (libsql:// → https://)
- En modo Turso: TODAS las queries van a la nube, zero dependencias extra
- En modo SQLite: funciona como antes (backward compatible para operadoras)
"""

import sqlite3
import os
import json
import logging
from contextlib import contextmanager
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

log = logging.getLogger('tiktok_publisher')

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN DE RUTAS Y CONEXIÓN
# ═══════════════════════════════════════════════════════════

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_DIR, "autotok.db")
TURSO_CONFIG_PATH = os.path.join(PROJECT_DIR, "turso_config.json")

_USE_TURSO = False
_turso_url = None      # HTTPS URL for HTTP API
_turso_token = None

if os.path.exists(TURSO_CONFIG_PATH):
    try:
        with open(TURSO_CONFIG_PATH, 'r') as f:
            _cfg = json.load(f)
        _url = _cfg.get('sync_url', '')
        _token = _cfg.get('auth_token', '')
        if _url and _token:
            # Convertir libsql:// a https:// para HTTP API
            _turso_url = _url.replace('libsql://', 'https://')
            _turso_token = _token
            _USE_TURSO = True
            log.info("[DB] Turso HTTP API habilitada")
        else:
            log.warning("[DB] turso_config.json incompleto, usando SQLite local")
    except Exception as e:
        log.warning(f"[DB] Error leyendo turso_config.json: {e}, usando SQLite local")
else:
    log.info("[DB] turso_config.json no encontrado, usando SQLite local")


# ═══════════════════════════════════════════════════════════
# DICTROW — EMULA sqlite3.Row
# ═══════════════════════════════════════════════════════════

class DictRow:
    """Emula sqlite3.Row — acceso por nombre y por índice.

    Uso idéntico a sqlite3.Row:
        row['nombre']   -> acceso por columna
        row[0]          -> acceso por índice
        row.keys()      -> nombres de columnas
        dict(zip(row.keys(), row.values())) -> convertir a dict
        tuple(row)      -> convertir a tupla
    """
    __slots__ = ('_data', '_keys')

    def __init__(self, keys, values):
        self._keys = keys
        self._data = values

    def __getitem__(self, key):
        if isinstance(key, str):
            try:
                idx = self._keys.index(key)
            except ValueError:
                raise KeyError(f"No column named '{key}'")
            return self._data[idx]
        return self._data[key]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        return f"DictRow({dict(zip(self._keys, self._data))})"

    def keys(self):
        return self._keys

    def values(self):
        return self._data

    def items(self):
        return zip(self._keys, self._data)

    def __eq__(self, other):
        if isinstance(other, DictRow):
            return self._data == other._data
        if isinstance(other, tuple):
            return self._data == other
        return NotImplemented


# ═══════════════════════════════════════════════════════════
# TURSO HTTP API — CURSOR Y CONEXIÓN
# ═══════════════════════════════════════════════════════════

def _turso_value_to_python(val):
    """Convierte un valor Turso HTTP API a tipo Python nativo."""
    if val is None or val.get('type') == 'null':
        return None
    vtype = val.get('type', 'text')
    raw = val.get('value')
    if vtype == 'integer':
        return int(raw)
    elif vtype == 'float':
        return float(raw)
    elif vtype == 'blob':
        import base64
        return base64.b64decode(raw)
    else:  # text, etc
        return str(raw) if raw is not None else None


def _python_to_turso_arg(val):
    """Convierte un valor Python a argumento Turso HTTP API."""
    if val is None:
        return {"type": "null"}
    elif isinstance(val, int):
        return {"type": "integer", "value": str(val)}
    elif isinstance(val, float):
        return {"type": "float", "value": val}
    elif isinstance(val, bytes):
        import base64
        return {"type": "blob", "base64": base64.b64encode(val).decode()}
    else:
        return {"type": "text", "value": str(val)}


class TursoHTTPCursor:
    """Cursor que ejecuta queries contra Turso via HTTP API /v2/pipeline.

    Cada execute() envía la query a Turso y almacena el resultado.
    fetchone/fetchall devuelven DictRow (compatible con sqlite3.Row).
    """

    def __init__(self, api_url, auth_token):
        self._api_url = api_url + "/v2/pipeline"
        self._auth_token = auth_token
        self._column_names = None
        self._rows = []
        self._row_index = 0
        self._lastrowid = None
        self._rowcount = -1
        self._description = None

    def _http_call(self, statements, _max_retries=3):
        """Ejecuta statements via HTTP pipeline. Devuelve results array.

        Incluye retry con backoff exponencial para errores de conexión.
        """
        import time as _time

        requests_body = []
        for stmt in statements:
            req_obj = {"type": "execute", "stmt": {"sql": stmt["sql"]}}
            if stmt.get("args"):
                req_obj["stmt"]["args"] = [_python_to_turso_arg(a) for a in stmt["args"]]
            requests_body.append(req_obj)
        requests_body.append({"type": "close"})

        body = json.dumps({"requests": requests_body}).encode('utf-8')

        for attempt in range(_max_retries):
            try:
                req = Request(self._api_url, data=body, method='POST')
                req.add_header('Authorization', f'Bearer {self._auth_token}')
                req.add_header('Content-Type', 'application/json')
                resp = urlopen(req, timeout=30)
                data = json.loads(resp.read().decode('utf-8'))
                return data.get('results', [])
            except HTTPError as e:
                error_body = e.read().decode('utf-8', errors='replace')
                raise RuntimeError(f"Turso HTTP error {e.code}: {error_body}")
            except URLError as e:
                if attempt < _max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    log.warning(f"[DB] Turso connection error (attempt {attempt+1}/{_max_retries}), retrying in {wait}s: {e.reason}")
                    _time.sleep(wait)
                else:
                    raise RuntimeError(f"Turso connection error after {_max_retries} attempts: {e.reason}")

    def execute(self, sql, params=None):
        """Ejecuta una query SQL contra Turso."""
        stmt = {"sql": sql}
        if params:
            stmt["args"] = list(params)

        results = self._http_call([stmt])

        self._rows = []
        self._row_index = 0
        self._column_names = None
        self._description = None

        if not results:
            return self

        result = results[0]
        if result.get('type') == 'error':
            raise RuntimeError(f"SQL error: {result['error'].get('message', str(result['error']))}")

        resp = result.get('response', {}).get('result', {})

        # Parsear columnas
        cols = resp.get('cols', [])
        if cols:
            self._column_names = [c['name'] for c in cols]
            self._description = tuple(
                (c['name'], None, None, None, None, None, None) for c in cols
            )

        # Parsear filas
        raw_rows = resp.get('rows', [])
        self._rows = []
        for raw_row in raw_rows:
            py_row = tuple(_turso_value_to_python(v) for v in raw_row)
            self._rows.append(py_row)

        # Metadata
        self._lastrowid = resp.get('last_insert_rowid')
        affected = resp.get('affected_row_count', 0)
        self._rowcount = affected if affected else len(self._rows)

        return self

    def executemany(self, sql, params_list):
        """Ejecuta la misma query con múltiples sets de parámetros."""
        stmts = [{"sql": sql, "args": list(p)} for p in params_list]
        results = self._http_call(stmts)
        total_affected = 0
        for result in results:
            if result.get('type') == 'error':
                raise RuntimeError(f"SQL error: {result['error'].get('message', '')}")
            resp = result.get('response', {}).get('result', {})
            total_affected += resp.get('affected_row_count', 0)
        self._rowcount = total_affected
        return self

    def executescript(self, sql_script):
        """Ejecuta múltiples statements separados por ;"""
        import re
        # Separar por ; pero ignorar dentro de strings
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]
        if not statements:
            return self
        stmts = [{"sql": s} for s in statements]
        # Enviar en batches de 20 para no sobrecargar
        BATCH = 20
        for i in range(0, len(stmts), BATCH):
            batch = stmts[i:i+BATCH]
            results = self._http_call(batch)
            for result in results:
                if result.get('type') == 'error':
                    msg = result['error'].get('message', '')
                    if 'already exists' not in msg:  # Ignorar IF NOT EXISTS errors
                        raise RuntimeError(f"SQL error: {msg}")
        return self

    def fetchone(self):
        if self._row_index >= len(self._rows) or self._column_names is None:
            return None
        row = self._rows[self._row_index]
        self._row_index += 1
        return DictRow(self._column_names, row)

    def fetchall(self):
        if not self._rows or self._column_names is None:
            return []
        remaining = self._rows[self._row_index:]
        self._row_index = len(self._rows)
        return [DictRow(self._column_names, r) for r in remaining]

    def fetchmany(self, size=None):
        if size is None:
            size = 1
        if not self._rows or self._column_names is None:
            return []
        end = min(self._row_index + size, len(self._rows))
        batch = self._rows[self._row_index:end]
        self._row_index = end
        return [DictRow(self._column_names, r) for r in batch]

    @property
    def lastrowid(self):
        return self._lastrowid

    @property
    def rowcount(self):
        return self._rowcount

    @property
    def description(self):
        return self._description

    def close(self):
        pass

    def __iter__(self):
        return self

    def __next__(self):
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row


class TursoHTTPConnection:
    """Conexión a Turso via HTTP API. Emula sqlite3.Connection.

    Cada execute() va directamente a Turso (auto-commit por statement).
    commit()/rollback() son esencialmente no-ops ya que cada statement
    se auto-comitea en Turso.
    """

    def __init__(self, api_url, auth_token):
        self._api_url = api_url
        self._auth_token = auth_token
        self._closed = False

    def cursor(self):
        return TursoHTTPCursor(self._api_url, self._auth_token)

    def execute(self, sql, params=None):
        """Atajo — crea cursor, ejecuta y devuelve."""
        c = self.cursor()
        c.execute(sql, params)
        return c

    def commit(self):
        pass  # Auto-commit por statement en Turso HTTP

    def rollback(self):
        log.warning("[DB] rollback() llamado en modo Turso HTTP — no tiene efecto (auto-commit)")

    def close(self):
        self._closed = True

    def sync(self):
        """No-op — HTTP API no necesita sync."""
        pass

    @property
    def row_factory(self):
        return None

    @row_factory.setter
    def row_factory(self, value):
        pass  # Ignorar — usamos DictRow automáticamente

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# ═══════════════════════════════════════════════════════════
# WRAPPER SQLITE LOCAL (para backward compatible)
# ═══════════════════════════════════════════════════════════

class WrappedCursor:
    """Wrapper de cursor SQLite que convierte filas a DictRow."""

    def __init__(self, real_cursor):
        self._cursor = real_cursor
        self._column_names = None

    def execute(self, sql, params=None):
        if params is not None:
            self._cursor.execute(sql, params)
        else:
            self._cursor.execute(sql)
        desc = self._cursor.description
        if desc:
            self._column_names = [d[0] for d in desc]
        else:
            self._column_names = None
        return self

    def executemany(self, sql, params_list):
        self._cursor.executemany(sql, params_list)
        return self

    def executescript(self, sql):
        self._cursor.executescript(sql)
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        if row is None or self._column_names is None:
            return row
        return DictRow(self._column_names, tuple(row))

    def fetchall(self):
        rows = self._cursor.fetchall()
        if not rows or self._column_names is None:
            return rows
        return [DictRow(self._column_names, tuple(r)) for r in rows]

    def fetchmany(self, size=None):
        rows = self._cursor.fetchmany(size) if size else self._cursor.fetchmany()
        if not rows or self._column_names is None:
            return rows
        return [DictRow(self._column_names, tuple(r)) for r in rows]

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def description(self):
        return self._cursor.description

    def close(self):
        if hasattr(self._cursor, 'close'):
            self._cursor.close()

    def __iter__(self):
        return self

    def __next__(self):
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row


class WrappedConnection:
    """Wrapper de conexión SQLite que devuelve WrappedCursor con DictRow."""

    def __init__(self, real_conn):
        self._conn = real_conn

    def cursor(self):
        return WrappedCursor(self._conn.cursor())

    def execute(self, sql, params=None):
        c = WrappedCursor(self._conn.cursor())
        c.execute(sql, params)
        return c

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def sync(self):
        pass  # No-op para SQLite local

    @property
    def row_factory(self):
        return None

    @row_factory.setter
    def row_factory(self, value):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# ═══════════════════════════════════════════════════════════
# FUNCIONES DE CONEXIÓN PÚBLICAS
# ═══════════════════════════════════════════════════════════

def get_connection():
    """Obtiene conexión a la base de datos (legacy — preferir db_connection()).

    Mantiene compatibilidad con código existente que usa:
        conn = get_connection()
        ...
        conn.close()

    Para código nuevo, usar db_connection() que auto-commit/rollback/close.
    """
    if _USE_TURSO:
        return TursoHTTPConnection(_turso_url, _turso_token)
    else:
        conn = sqlite3.connect(DB_PATH)
        return WrappedConnection(conn)


@contextmanager
def db_connection():
    """Context manager para conexiones BD con auto-commit/rollback/close.

    QUA-85: Garantiza que:
    - Si todo va bien: commit automático al salir del bloque
    - Si hay excepción: rollback automático
    - Siempre: cierra la conexión (evita file locks en Windows)

    Uso:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE videos SET ...")
            # commit automático al salir del with
            # rollback automático si hay excepción

    Para operaciones que necesitan commit intermedio:
        with db_connection() as conn:
            for video in videos:
                cursor.execute(...)
                conn.commit()  # commit explícito por video
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def sync_replica():
    """No-op — mantenida por compatibilidad."""
    pass


def is_turso_enabled():
    """Devuelve True si estamos conectados a Turso."""
    return _USE_TURSO


# ═══════════════════════════════════════════════════════════
# SCHEMA DATABASE v3.5
# ═══════════════════════════════════════════════════════════

SCHEMA_V3_5 = """
-- ============================================================
-- TABLA 1: PRODUCTOS
-- ============================================================
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    descripcion TEXT,
    precio_amazon REAL,
    estado_comercial TEXT DEFAULT 'testing' CHECK(estado_comercial IN ('testing', 'validated', 'top_seller', 'dropped')),
    max_videos_test INTEGER DEFAULT 20,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLA 2: PRODUCTO_BOFS (Sin overlay/seo - solo deal+guion)
-- ============================================================
CREATE TABLE IF NOT EXISTS producto_bofs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    deal_math TEXT NOT NULL,
    guion_audio TEXT NOT NULL,
    hashtags TEXT,
    url_producto TEXT,
    veces_usado INTEGER DEFAULT 0,
    activo INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- ============================================================
-- TABLA 3: VARIANTES_OVERLAY_SEO (Exclusivas de cada BOF)
-- ============================================================
CREATE TABLE IF NOT EXISTS variantes_overlay_seo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bof_id INTEGER NOT NULL,
    overlay_line1 TEXT NOT NULL,
    overlay_line2 TEXT,
    seo_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bof_id) REFERENCES producto_bofs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_variantes_bof ON variantes_overlay_seo(bof_id);

-- ============================================================
-- TABLA 4: AUDIOS (Vinculados a BOF)
-- ============================================================
CREATE TABLE IF NOT EXISTS audios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    bof_id INTEGER,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL DEFAULT '',
    duracion REAL,
    veces_usado INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (bof_id) REFERENCES producto_bofs(id),
    UNIQUE(producto_id, filename)
);

CREATE INDEX IF NOT EXISTS idx_audios_producto ON audios(producto_id);
CREATE INDEX IF NOT EXISTS idx_audios_bof ON audios(bof_id);

-- ============================================================
-- TABLA 5: MATERIAL (Hooks + Brolls compartidos)
-- ============================================================
CREATE TABLE IF NOT EXISTS material (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('hook', 'broll')),
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    grupo TEXT,
    start_time REAL DEFAULT 0.0,
    duracion REAL,
    veces_usado INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    UNIQUE(producto_id, filename)
);

CREATE INDEX IF NOT EXISTS idx_material_producto ON material(producto_id);
CREATE INDEX IF NOT EXISTS idx_material_tipo ON material(tipo);

-- ============================================================
-- TABLA 6: VIDEOS (Videos generados)
-- ============================================================
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE NOT NULL,
    producto_id INTEGER NOT NULL,
    cuenta TEXT NOT NULL,
    bof_id INTEGER NOT NULL,
    variante_id INTEGER NOT NULL,
    hook_id INTEGER NOT NULL,
    audio_id INTEGER NOT NULL,
    estado TEXT DEFAULT 'Generado' CHECK(estado IN ('Generado', 'En Calendario', 'Borrador', 'Programado', 'Descartado', 'Violation', 'Publicando', 'Error')),
    fecha_programada DATE,
    hora_programada TIME,
    filepath TEXT,
    duracion REAL,
    filesize_mb REAL,
    batch_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    programado_at TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (bof_id) REFERENCES producto_bofs(id),
    FOREIGN KEY (variante_id) REFERENCES variantes_overlay_seo(id),
    FOREIGN KEY (hook_id) REFERENCES material(id),
    FOREIGN KEY (audio_id) REFERENCES audios(id)
);

CREATE INDEX IF NOT EXISTS idx_videos_producto ON videos(producto_id);
CREATE INDEX IF NOT EXISTS idx_videos_cuenta ON videos(cuenta);
CREATE INDEX IF NOT EXISTS idx_videos_estado ON videos(estado);
CREATE INDEX IF NOT EXISTS idx_videos_fecha ON videos(fecha_programada);

-- ============================================================
-- TABLA 7: HOOK_VARIANTE_USADO (Tracking global)
-- ============================================================
CREATE TABLE IF NOT EXISTS hook_variante_usado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hook_id INTEGER NOT NULL,
    variante_id INTEGER NOT NULL,
    video_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hook_id) REFERENCES material(id),
    FOREIGN KEY (variante_id) REFERENCES variantes_overlay_seo(id),
    FOREIGN KEY (video_id) REFERENCES videos(id),
    UNIQUE(hook_id, variante_id)
);

CREATE INDEX IF NOT EXISTS idx_hook_variante ON hook_variante_usado(hook_id, variante_id);

-- ============================================================
-- TABLA 8: FORMATO_MATERIAL (QUA-201: material por formato)
-- ============================================================
CREATE TABLE IF NOT EXISTS formato_material (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bof_id INTEGER NOT NULL,
    material_id INTEGER,
    audio_id INTEGER,
    tipo TEXT NOT NULL CHECK(tipo IN ('hook', 'broll', 'audio')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bof_id) REFERENCES producto_bofs(id),
    FOREIGN KEY (material_id) REFERENCES material(id),
    FOREIGN KEY (audio_id) REFERENCES audios(id)
);

CREATE INDEX IF NOT EXISTS idx_formato_material_bof ON formato_material(bof_id);
CREATE INDEX IF NOT EXISTS idx_formato_material_tipo ON formato_material(bof_id, tipo);

-- ============================================================
-- TABLA 9: COMBINACIONES_USADAS (Backup legacy)
-- ============================================================
CREATE TABLE IF NOT EXISTS combinaciones_usadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    hook_id INTEGER NOT NULL,
    brolls_ids TEXT NOT NULL,
    audio_id INTEGER NOT NULL,
    bof_id INTEGER NOT NULL,
    variante_id INTEGER NOT NULL,
    video_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

-- ============================================================
-- TABLA 9: CUENTAS_CONFIG (Config cuentas)
-- ============================================================
CREATE TABLE IF NOT EXISTS cuentas_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    activa BOOLEAN DEFAULT 1,
    videos_por_dia INTEGER DEFAULT 5,
    max_mismo_hook_por_dia INTEGER DEFAULT 1,
    max_mismo_producto_por_dia INTEGER DEFAULT 2,
    distancia_minima_hook INTEGER DEFAULT 12,
    gap_minimo_horas REAL DEFAULT 1.0,
    horario_inicio TEXT DEFAULT '08:00',
    horario_fin TEXT DEFAULT '21:30',
    overlay_style TEXT,
    pct_top_seller INTEGER DEFAULT 40,
    pct_validated INTEGER DEFAULT 40,
    pct_testing INTEGER DEFAULT 20,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLA 10: HISTORIAL_PROGRAMACION (Cambio 3.8)
-- ============================================================
CREATE TABLE IF NOT EXISTS historial_programacion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    accion TEXT NOT NULL CHECK(accion IN ('programar', 'rollback', 'descartar', 'sync', 'reemplazar')),
    cuenta TEXT NOT NULL,
    num_videos INTEGER NOT NULL DEFAULT 0,
    fecha_inicio TEXT,
    fecha_fin TEXT,
    dias INTEGER,
    detalles TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_historial_cuenta ON historial_programacion(cuenta);
CREATE INDEX IF NOT EXISTS idx_historial_accion ON historial_programacion(accion);

-- ============================================================
-- TABLA 11: TIKTOK_STUDIO_DAILY (QUA-263: engagement CSV import)
-- ============================================================
CREATE TABLE IF NOT EXISTS tiktok_studio_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cuenta TEXT NOT NULL,
    fecha DATE NOT NULL,
    video_views INTEGER DEFAULT 0,
    profile_views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cuenta, fecha)
);

CREATE INDEX IF NOT EXISTS idx_studio_daily_cuenta ON tiktok_studio_daily(cuenta);
CREATE INDEX IF NOT EXISTS idx_studio_daily_fecha ON tiktok_studio_daily(fecha);
"""


def create_database(force=False):
    """Crea la base de datos con schema v3.5 (solo SQLite local)."""
    if force and os.path.exists(DB_PATH):
        print(f"[WARNING] Borrando base de datos existente: {DB_PATH}")
        os.remove(DB_PATH)

    print(f"[INFO] Creando base de datos v3.5: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executescript(SCHEMA_V3_5)
    conn.commit()
    conn.close()
    print("[OK] Base de datos v3.5 creada correctamente")


def ensure_historial_table():
    """Crea tabla historial_programacion si no existe."""
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM historial_programacion LIMIT 1")
        except Exception:
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS historial_programacion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    accion TEXT NOT NULL CHECK(accion IN ('programar', 'rollback', 'descartar', 'sync', 'reemplazar')),
                    cuenta TEXT NOT NULL,
                    num_videos INTEGER NOT NULL DEFAULT 0,
                    fecha_inicio TEXT,
                    fecha_fin TEXT,
                    dias INTEGER,
                    detalles TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_historial_cuenta ON historial_programacion(cuenta);
                CREATE INDEX IF NOT EXISTS idx_historial_accion ON historial_programacion(accion);
            """)


def ensure_formato_material_table():
    """QUA-201: Crea tabla formato_material si no existe."""
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM formato_material LIMIT 1")
        except Exception:
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS formato_material (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bof_id INTEGER NOT NULL,
                    material_id INTEGER,
                    audio_id INTEGER,
                    tipo TEXT NOT NULL CHECK(tipo IN ('hook', 'broll', 'audio')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bof_id) REFERENCES producto_bofs(id),
                    FOREIGN KEY (material_id) REFERENCES material(id),
                    FOREIGN KEY (audio_id) REFERENCES audios(id)
                );
                CREATE INDEX IF NOT EXISTS idx_formato_material_bof ON formato_material(bof_id);
                CREATE INDEX IF NOT EXISTS idx_formato_material_tipo ON formato_material(bof_id, tipo);
            """)
            print("[MIGRATION] Tabla formato_material creada (QUA-201)")


def ensure_bof_activo_column():
    """Añade columna 'activo' a producto_bofs si no existe."""
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT activo FROM producto_bofs LIMIT 1")
        except Exception:
            cursor.execute("ALTER TABLE producto_bofs ADD COLUMN activo INTEGER DEFAULT 1")
            print("[MIGRATION] Columna 'activo' añadida a producto_bofs")


def registrar_historial(accion, cuenta, num_videos, fecha_inicio=None, fecha_fin=None, dias=None, detalles=None):
    """Registra una acción en historial_programacion."""
    ensure_historial_table()
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO historial_programacion (accion, cuenta, num_videos, fecha_inicio, fecha_fin, dias, detalles)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (accion, cuenta, num_videos, fecha_inicio, fecha_fin, dias, detalles))


def log_publish_attempt(video_id, result, error_type=None, error_message=None,
                        screenshot_path=None, session_id=None):
    """Registra un intento de publicación en video_publish_log."""
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM video_publish_log WHERE video_id = ?",
            (video_id,)
        )
        attempt_number = cursor.fetchone()[0] + 1
        cursor.execute("""
            INSERT INTO video_publish_log
            (video_id, attempt_number, result, error_type, error_message, screenshot_path, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (video_id, attempt_number, result, error_type, error_message, screenshot_path, session_id))


def update_video_publish_status(video_id, publish_attempts=None, last_error=None,
                                 published_at=None, tiktok_post_id=None):
    """Actualiza campos de tracking de publicación en la tabla videos."""
    with db_connection() as conn:
        cursor = conn.cursor()
        updates = []
        params = []
        if publish_attempts is not None:
            updates.append("publish_attempts = ?")
            params.append(publish_attempts)
        if last_error is not None:
            updates.append("last_error = ?")
            params.append(last_error)
        if published_at is not None:
            updates.append("published_at = ?")
            params.append(published_at)
        if tiktok_post_id is not None:
            updates.append("tiktok_post_id = ?")
            params.append(tiktok_post_id)
        if updates:
            params.append(video_id)
            cursor.execute(
                f"UPDATE videos SET {', '.join(updates)} WHERE video_id = ?",
                params
            )


if __name__ == "__main__":
    import sys
    import time

    force = "--force" in sys.argv

    if _USE_TURSO:
        print(f"[INFO] Modo: Turso HTTP API")
        print(f"[INFO] URL: {_turso_url}")
    else:
        print(f"[INFO] Modo: SQLite local")
        print(f"[INFO] Path: {DB_PATH}")

    if force:
        create_database(force=True)
    else:
        # Verificar conexión
        start = time.time()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM productos")
        count = cursor.fetchone()['total']
        elapsed = time.time() - start
        print(f"[OK] Conexión exitosa — {count} productos ({elapsed:.2f}s)")
        conn.close()
