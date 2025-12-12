"""
Script de ayuda para ejecutar el scraper de elecciones
Facilita la ejecución para diferentes elecciones
"""

import argparse
import sys
import json

def listar_elecciones(config_path='config_elecciones.json'):
    """Lista las elecciones disponibles en la configuración"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("\n📋 Elecciones disponibles:")
        print("=" * 60)
        for key, eleccion in config.get('elecciones', {}).items():
            print(f"  • {key}")
            print(f"    Nombre: {eleccion.get('nombre', 'N/A')}")
            print(f"    URL: {eleccion.get('url', 'N/A')}")
            print(f"    Candidatos: {len(eleccion.get('mapeo_candidatos', {}))}")
            print()
        print("=" * 60)
        
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo de configuración: {config_path}")
        print("💡 Asegúrate de que existe config_elecciones.json")
    except json.JSONDecodeError as e:
        print(f"❌ Error al leer el archivo de configuración: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Script de ayuda para ejecutar el scraper de elecciones',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--listar', action='store_true',
                        help='Lista las elecciones disponibles en la configuración')
    parser.add_argument('--eleccion', type=str,
                        help='Ejecuta el scraper para la elección especificada')
    parser.add_argument('--headless', action='store_true',
                        help='Ejecutar en modo headless')
    parser.add_argument('--comunas', type=int,
                        help='Límite de comunas a procesar (útil para pruebas)')
    
    args = parser.parse_args()
    
    if args.listar:
        listar_elecciones()
        return 0
    
    if args.eleccion:
        # Importar y ejecutar el scraper
        try:
            from scraper_modular import main as scraper_main
            # Construir argumentos para el scraper
            sys.argv = ['scraper_modular.py', '--eleccion', args.eleccion]
            if args.headless:
                sys.argv.append('--headless')
            if args.comunas:
                sys.argv.extend(['--comunas', str(args.comunas)])
            
            return scraper_main()
        except ImportError as e:
            print(f"❌ Error importando el scraper: {e}")
            print("💡 Asegúrate de que scraper_modular.py existe en el directorio")
            return 1
    else:
        parser.print_help()
        print("\n💡 Tip: Usa --listar para ver las elecciones disponibles")
        print("💡 Tip: Usa --eleccion <clave> para ejecutar el scraper")
        return 0

if __name__ == "__main__":
    sys.exit(main())

