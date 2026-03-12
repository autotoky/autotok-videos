#!/usr/bin/env python3
"""Ver videos en DB por cuenta"""
import sqlite3
import sys

DB_PATH = "autotok.db"
cuenta = sys.argv[1] if len(sys.argv) > 1 else "lotopdevicky"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    SELECT filename, estado, fecha_prog, hora
    FROM videos 
    WHERE cuenta = ?
    ORDER BY filename
""", (cuenta,))

print(f"\n📹 Videos de {cuenta}:\n")
for filename, estado, fecha, hora in cursor.fetchall():
    fecha_hora = f"{fecha} {hora}" if fecha and hora else ""
    print(f"  {filename[:60]:<60} | {estado:<15} | {fecha_hora}")

cursor.execute("SELECT COUNT(*) FROM videos WHERE cuenta = ?", (cuenta,))
total = cursor.fetchone()[0]
print(f"\nTotal: {total} videos\n")
