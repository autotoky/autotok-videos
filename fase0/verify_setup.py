"""
✅ VERIFY SETUP
Script para verificar que todo está configurado correctamente
"""

import os
import sys
import json

def check_python_version():
    """Verifica versión de Python"""
    print("🐍 Verificando versión de Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} - Se requiere 3.8+")
        return False

def check_dependencies():
    """Verifica dependencias instaladas"""
    print("\n📦 Verificando dependencias...")
    
    deps = {
        'gspread': 'Google Sheets API client',
        'google.auth': 'Google Authentication',
    }
    
    all_ok = True
    for module, description in deps.items():
        try:
            __import__(module)
            print(f"   ✅ {module} - {description}")
        except ImportError:
            print(f"   ❌ {module} - NO INSTALADO")
            all_ok = False
    
    if not all_ok:
        print("\n   💡 Instala con: pip install -r requirements.txt")
    
    return all_ok

def check_credentials():
    """Verifica archivo de credenciales"""
    print("\n🔑 Verificando credenciales...")
    
    if not os.path.exists('service_account.json'):
        print("   ❌ service_account.json NO ENCONTRADO")
        print("   💡 Sigue el PASO 2 de SETUP_COMPLETE.md")
        return False
    
    try:
        with open('service_account.json', 'r') as f:
            creds = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing = [f for f in required_fields if f not in creds]
        
        if missing:
            print(f"   ❌ Credenciales incompletas. Faltan: {', '.join(missing)}")
            return False
        
        print(f"   ✅ service_account.json encontrado")
        print(f"   📧 Email: {creds['client_email']}")
        print(f"\n   ⚠️  IMPORTANTE: Comparte las sheets con este email (permisos Editor)")
        return True
        
    except json.JSONDecodeError:
        print("   ❌ service_account.json corrupto (no es JSON válido)")
        return False
    except Exception as e:
        print(f"   ❌ Error leyendo credenciales: {e}")
        return False

def check_config():
    """Verifica archivo de configuración"""
    print("\n⚙️  Verificando configuración...")
    
    if not os.path.exists('config.py'):
        print("   ❌ config.py NO ENCONTRADO")
        return False
    
    try:
        import config
        
        required = ['SHEETS_CONFIG', 'COSTES', 'BOF_CONFIG']
        missing = [r for r in required if not hasattr(config, r)]
        
        if missing:
            print(f"   ❌ Configuración incompleta. Faltan: {', '.join(missing)}")
            return False
        
        print("   ✅ config.py correcto")
        print(f"   📊 {len(config.SHEETS_CONFIG)} sheets configuradas")
        return True
        
    except Exception as e:
        print(f"   ❌ Error en config.py: {e}")
        return False

def check_sheets_connection():
    """Intenta conectar con Google Sheets"""
    print("\n📊 Probando conexión con Google Sheets...")
    
    try:
        from sheets_manager import SheetsManager
        
        manager = SheetsManager()
        sheets_count = len(manager.sheets)
        
        print(f"   ✅ Conectado exitosamente")
        print(f"   📄 {sheets_count} sheets accesibles:")
        for name in manager.sheets.keys():
            print(f"      • {name}")
        
        # Probar lectura
        try:
            data = manager.read_carol_input()
            print(f"\n   📖 Lectura exitosa: {len(data)} registros en carol_input")
        except Exception as e:
            print(f"\n   ⚠️  Advertencia leyendo datos: {e}")
        
        return True
        
    except FileNotFoundError:
        print("   ❌ service_account.json no encontrado")
        return False
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        print("\n   💡 Posibles causas:")
        print("      • No diste permisos al service account en las sheets")
        print("      • El email del service account es incorrecto")
        print("      • Las APIs no están activadas en Google Cloud")
        return False

def check_files():
    """Verifica que todos los archivos necesarios existen"""
    print("\n📁 Verificando archivos del sistema...")
    
    required_files = {
        'config.py': 'Configuración',
        'sheets_manager.py': 'Gestor Google Sheets',
        'prompt_generator.py': 'Generador de prompts',
        'bof_learning.py': 'Sistema aprendizaje BOF',
        'main.py': 'Script principal',
        'requirements.txt': 'Dependencias'
    }
    
    all_ok = True
    for filename, description in required_files.items():
        if os.path.exists(filename):
            print(f"   ✅ {filename} - {description}")
        else:
            print(f"   ❌ {filename} - NO ENCONTRADO")
            all_ok = False
    
    return all_ok

def main():
    """Ejecuta todas las verificaciones"""
    print("\n" + "="*60)
    print("🔍 VERIFICACIÓN DE SETUP - SISTEMA TIKTOK SHOP")
    print("="*60)
    
    checks = [
        ("Python", check_python_version),
        ("Dependencias", check_dependencies),
        ("Archivos", check_files),
        ("Credenciales", check_credentials),
        ("Configuración", check_config),
        ("Conexión Sheets", check_sheets_connection)
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ Error verificando {name}: {e}")
            results[name] = False
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
    
    all_ok = all(results.values())
    
    if all_ok:
        print("\n" + "🎉 " * 10)
        print("✅ ¡TODO LISTO! El sistema está correctamente configurado.")
        print("🎉 " * 10)
        print("\n💡 Siguiente paso: Ejecuta 'python main.py' para iniciar")
    else:
        print("\n" + "⚠️ " * 10)
        print("❌ Hay problemas de configuración")
        print("⚠️ " * 10)
        print("\n💡 Revisa SETUP_COMPLETE.md para instrucciones detalladas")
    
    print("\n" + "="*60 + "\n")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
