#!/usr/bin/env python3
"""
create_db.py - Script para crear la base de datos SQLite de Autotok
Versión: 1.0
Fecha: 2026-02-09

Crea el schema completo con 7 tablas.
"""

import sqlite3
import os
import sys
from pathlib import Path

# Ruta de la base de datos
DB_PATH = "autotok.db"


def create_database():
    """Crea la base de datos con el schema completo"""
    
    # Verificar si ya existe
    if os.path.exists(DB_PATH):
        print(f"⚠️  Base de datos ya existe: {DB_PATH}")
        response = input("¿Quieres ELIMINARLA y crear una nueva? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Operación cancelada")
            return False
        os.remove(DB_PATH)
        print(f"🗑️  Base de datos eliminada")
    
    print(f"\n🔨 Creando base de datos: {DB_PATH}")
    
    # Conectar y crear schema
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # TABLA 1: productos
    print("   📦 Creando tabla: productos")
    cursor.execute("""
        CREATE TABLE productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            
            -- Info básica (de hoja Excel Carol)
            sector TEXT,
            nuevo BOOLEAN DEFAULT 1,
            activo BOOLEAN DEFAULT 1,
            
            -- URLs
            url_kalodata TEXT,
            url_producto TEXT,
            
            -- Planificación
            numero_videos_requeridos INTEGER DEFAULT 0,
            numero_videos_generados INTEGER DEFAULT 0,
            
            -- Timestamps
            fecha_anadido DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX idx_productos_activo ON productos(activo)")
    
    # TABLA 2: producto_bofs (⭐ CORE - Brief Original Final)
    print("   ⭐ Creando tabla: producto_bofs")
    cursor.execute("""
        CREATE TABLE producto_bofs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            
            -- Metadata
            version INTEGER DEFAULT 1,
            activo BOOLEAN DEFAULT 1,
            
            -- Contenido completo (output Custom GPT)
            deal_math TEXT NOT NULL,
            guion_audio TEXT NOT NULL,
            seo_text TEXT NOT NULL,
            overlay_line1 TEXT,
            overlay_line2 TEXT,
            hashtags TEXT NOT NULL,
            
            -- Tracking de uso
            usado_count INTEGER DEFAULT 0,
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)
    cursor.execute("CREATE INDEX idx_bof_producto ON producto_bofs(producto_id)")
    cursor.execute("CREATE INDEX idx_bof_uso ON producto_bofs(producto_id, usado_count)")
    cursor.execute("CREATE INDEX idx_bof_activo ON producto_bofs(activo)")
    
    # TABLA 3: audios
    print("   🎵 Creando tabla: audios")
    cursor.execute("""
        CREATE TABLE audios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            bof_id INTEGER,
            
            -- Archivo
            filename TEXT NOT NULL,
            prefijo TEXT,
            duracion REAL,
            
            -- Generación
            metodo_generacion TEXT DEFAULT 'manual',
            guion_texto TEXT,
            
            -- Tracking
            usado_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (producto_id) REFERENCES productos(id),
            FOREIGN KEY (bof_id) REFERENCES producto_bofs(id)
        )
    """)
    cursor.execute("CREATE INDEX idx_audio_producto ON audios(producto_id)")
    cursor.execute("CREATE INDEX idx_audio_bof ON audios(bof_id)")
    cursor.execute("CREATE INDEX idx_audio_prefijo ON audios(prefijo)")
    
    # TABLA 4: material (hooks y brolls)
    print("   🎬 Creando tabla: material")
    cursor.execute("""
        CREATE TABLE material (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('hook', 'broll')),
            
            -- Archivo
            filename TEXT NOT NULL,
            
            -- Metadata hooks
            hook_id TEXT,
            start_time REAL DEFAULT 0,
            
            -- Metadata brolls
            grupo TEXT,
            
            -- Info general
            duracion REAL,
            
            -- Generación (para futuro)
            metodo_generacion TEXT DEFAULT 'manual',
            prompt_usado TEXT,
            
            -- Tracking
            usado_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (producto_id) REFERENCES productos(id),
            UNIQUE(producto_id, filename)
        )
    """)
    cursor.execute("CREATE INDEX idx_material_tipo ON material(tipo)")
    cursor.execute("CREATE INDEX idx_material_hook_id ON material(hook_id)")
    cursor.execute("CREATE INDEX idx_material_grupo ON material(grupo)")
    cursor.execute("CREATE INDEX idx_material_producto ON material(producto_id)")
    
    # TABLA 5: videos (⭐ CORE)
    print("   📹 Creando tabla: videos")
    cursor.execute("""
        CREATE TABLE videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            producto_id INTEGER NOT NULL,
            cuenta TEXT NOT NULL,
            batch_number INTEGER,
            
            -- Material usado
            hook_id INTEGER,
            broll_ids TEXT,
            audio_id INTEGER,
            bof_id INTEGER,
            
            -- Info pre-calculada (para Sheet)
            hook_display TEXT,
            deal_math TEXT,
            seo_text TEXT,
            hashtags TEXT,
            overlay_text TEXT,
            url_producto TEXT,
            
            -- Estado y calendario
            estado TEXT DEFAULT 'Generado' CHECK(estado IN ('Generado', 'En Calendario', 'Borrador', 'Programado', 'Descartado')),
            fecha_prog DATE,
            hora TIME,
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (producto_id) REFERENCES productos(id),
            FOREIGN KEY (hook_id) REFERENCES material(id),
            FOREIGN KEY (audio_id) REFERENCES audios(id),
            FOREIGN KEY (bof_id) REFERENCES producto_bofs(id)
        )
    """)
    cursor.execute("CREATE INDEX idx_video_estado ON videos(estado)")
    cursor.execute("CREATE INDEX idx_video_cuenta ON videos(cuenta)")
    cursor.execute("CREATE INDEX idx_video_producto ON videos(producto_id)")
    cursor.execute("CREATE INDEX idx_video_fecha_prog ON videos(fecha_prog)")
    cursor.execute("CREATE INDEX idx_video_batch ON videos(batch_number)")
    cursor.execute("CREATE INDEX idx_video_bof ON videos(bof_id)")
    
    # TABLA 6: combinaciones_usadas
    print("   🔒 Creando tabla: combinaciones_usadas")
    cursor.execute("""
        CREATE TABLE combinaciones_usadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            hook_id INTEGER NOT NULL,
            broll_ids TEXT NOT NULL,
            audio_id INTEGER NOT NULL,
            combo_hash TEXT UNIQUE NOT NULL,
            video_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (producto_id) REFERENCES productos(id),
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
    """)
    cursor.execute("CREATE INDEX idx_combo_hash ON combinaciones_usadas(combo_hash)")
    cursor.execute("CREATE INDEX idx_combo_producto ON combinaciones_usadas(producto_id)")
    
    # TABLA 7: cuentas_config
    print("   ⚙️  Creando tabla: cuentas_config")
    cursor.execute("""
        CREATE TABLE cuentas_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            nombre_display TEXT NOT NULL,
            
            -- Overlay
            overlay_style TEXT NOT NULL,
            descripcion TEXT,
            
            -- Estado
            activa BOOLEAN DEFAULT 1,
            
            -- Configuración calendario
            videos_por_dia INTEGER DEFAULT 2,
            max_mismo_hook_por_dia INTEGER DEFAULT 1,
            max_mismo_producto_por_dia INTEGER DEFAULT 0,
            
            -- Horarios
            horario_inicio TIME DEFAULT '08:00',
            horario_fin TIME DEFAULT '21:30',
            zona_horaria TEXT DEFAULT 'Europe/Madrid',
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX idx_cuentas_activa ON cuentas_config(activa)")
    
    # Commit y cerrar
    conn.commit()
    conn.close()
    
    print(f"\n✅ Base de datos creada exitosamente: {DB_PATH}")
    print(f"   Tablas creadas: 7")
    print(f"   Tamaño: {os.path.getsize(DB_PATH) / 1024:.2f} KB")
    
    return True


def verify_database():
    """Verifica que la base de datos se creó correctamente"""
    print(f"\n🔍 Verificando base de datos...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Listar tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        'productos',
        'producto_bofs',
        'audios',
        'material',
        'videos',
        'combinaciones_usadas',
        'cuentas_config'
    ]
    
    print(f"\n📋 Tablas encontradas:")
    for table in tables:
        status = "✅" if table in expected_tables else "❓"
        print(f"   {status} {table}")
    
    # Verificar que todas las esperadas existen
    missing = set(expected_tables) - set(tables)
    if missing:
        print(f"\n⚠️  Tablas faltantes: {missing}")
        return False
    
    conn.close()
    print(f"\n✅ Verificación completa - Base de datos OK")
    return True


def main():
    """Función principal"""
    print("=" * 60)
    print("  🗄️  AUTOTOK - Creación de Base de Datos SQLite")
    print("=" * 60)
    
    # Crear database
    if not create_database():
        return 1
    
    # Verificar
    if not verify_database():
        return 1
    
    print("\n" + "=" * 60)
    print("  ✅ CREACIÓN COMPLETADA")
    print("=" * 60)
    print(f"\n📁 Ubicación: {os.path.abspath(DB_PATH)}")
    print(f"\n🎯 Próximo paso:")
    print(f"   python scripts/migrate_data.py")
    print("=" * 60 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
