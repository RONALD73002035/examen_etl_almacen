# Primer examen practico: ETL con Python y MySQL

Proyecto ETL desarrollado con programacion orientada a objetos (POO).

## Que hace

- **Extraccion:** lee el archivo `transacciones_almacen.csv` y maneja errores de lectura.
- **Transformacion:** elimina registros con cantidad o precio no positivos/nulos; quita duplicados por identificador; elimina espacios; convierte productos a mayusculas, correos a minusculas y fechas a `YYYY-MM-DD`; calcula `total_venta`.
- **Carga:** crea `historial_ventas` si no existe, inserta los registros usando `executemany`, confirma con `commit` y usa `rollback` ante errores.

## Requisitos

- Python 3, MySQL Server en ejecucion, MySQL Workbench (para verificar).
- Un archivo `transacciones_almacen.csv` junto a `main.py`.

## Pasos

1. En MySQL Workbench, abrir la conexion local y ejecutar:
   ```sql
   CREATE DATABASE IF NOT EXISTS etl_almacen;
   ```
2. En la terminal, desde esta carpeta, instalar dependencias:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Ejecutar:
   ```bash
   python main.py
   ```
4. Ingresar la contrasena de MySQL cuando se solicite (no se vera al escribir).
5. En MySQL Workbench comprobar:
   ```sql
   USE etl_almacen;
   SELECT * FROM historial_ventas ORDER BY id_transaccion;
   SELECT COUNT(*) AS registros_finales FROM historial_ventas;
   ```

Con el CSV original entregado para el examen, el proceso debe leer **100** filas, descartar **3** invalidas y cargar **97** registros validos si la tabla esta vacia.

La clave de MySQL **no esta guardada en el codigo**: se solicita en la terminal. El CSV de clase va incluido solo en el ZIP de trabajo y se excluye del repositorio publico con `.gitignore`; confirma si puedes publicarlo antes de subirlo a GitHub.
