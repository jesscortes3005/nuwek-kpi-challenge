"""Punto de entrada para importar los datos.

Uso:  python -m scripts.import_ventas [--csv data/ventas.csv]
"""
import argparse  # permite recibir opciones desde la línea de comandos

from app.etl.importer import importar


def main():
    # Define la opción --csv; si no se indica, usa data/ventas.csv
    parser = argparse.ArgumentParser(description="Limpia ventas.csv y lo carga a la base de datos.")
    parser.add_argument("--csv", default="data/ventas.csv", help="ruta del CSV (default: data/ventas.csv)")
    args = parser.parse_args()

    # Ejecuta todo el proceso ETL e imprime el resumen
    reporte = importar(args.csv)
    print("=== Reporte de importación ===")
    print(reporte)


# Esto evita que main() se ejecute si otro archivo solo importa este módulo
if __name__ == "__main__":
    main()
