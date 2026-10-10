"""Primer examen practico: ETL en Python (POO) y MySQL."""

from datetime import datetime
from getpass import getpass
from pathlib import Path

import mysql.connector
import pandas as pd


class ETLAlmacen:
    """Extrae transacciones, transforma sus datos y los carga en MySQL."""

    def __init__(self, ruta_csv, config_mysql):
        self.ruta_csv = Path(ruta_csv)
        self.config_mysql = config_mysql

    def extraer(self):
        try:
            datos = pd.read_csv(self.ruta_csv, encoding="utf-8-sig")
        except FileNotFoundError as error:
            raise FileNotFoundError(
                f"No se encontro el CSV: {self.ruta_csv}"
            ) from error
        except (OSError, UnicodeError, pd.errors.ParserError) as error:
            raise RuntimeError(f"No se pudo leer el CSV: {error}") from error

        columnas = {
            "id_transaccion", "producto", "cantidad", "precio_unitario",
            "fecha_registro", "correo_empleado",
        }
        faltantes = columnas - set(datos.columns)
        if faltantes:
            raise ValueError(f"Faltan columnas en el CSV: {sorted(faltantes)}")

        print(f"[1/3] EXTRACCION: {len(datos)} registros leidos del CSV.")
        return datos

    @staticmethod
    def normalizar_fecha(valor):
        formatos = ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y")
        for formato in formatos:
            try:
                return datetime.strptime(str(valor).strip(), formato).strftime("%Y-%m-%d")
            except ValueError:
                continue
        raise ValueError(f"Fecha no reconocida en el CSV: {valor!r}")

    def transformar(self, datos):
        datos = datos.copy()
        datos["cantidad"] = pd.to_numeric(datos["cantidad"], errors="coerce")
        datos["precio_unitario"] = pd.to_numeric(datos["precio_unitario"], errors="coerce")

        validos = (
            datos["cantidad"].notna()
            & datos["precio_unitario"].notna()
            & (datos["cantidad"] > 0)
            & (datos["precio_unitario"] > 0)
        )
        descartados = len(datos) - int(validos.sum())
        datos = datos.loc[validos].copy()

        duplicados = int(datos.duplicated(subset="id_transaccion").sum())
        datos = datos.drop_duplicates(subset="id_transaccion")

        datos["producto"] = (
            datos["producto"].fillna("").astype(str)
            .str.strip().str.replace(r"\s+", " ", regex=True).str.upper()
        )
        datos["correo_empleado"] = (
            datos["correo_empleado"].fillna("").astype(str).str.strip().str.lower()
        )
        datos["fecha_registro"] = datos["fecha_registro"].apply(self.normalizar_fecha)
        datos["total_venta"] = (
            datos["cantidad"] * datos["precio_unitario"]
        ).round(2)

        print(f"[2/3] TRANSFORMACION: {descartados} registros invalidos descartados.")
        print(f"[2/3] TRANSFORMACION: {duplicados} IDs duplicados descartados.")
        print(f"[2/3] TRANSFORMACION: {len(datos)} registros limpios.")
        return datos

    def cargar(self, datos):
        conexion = None
        cursor = None
        try:
            conexion = mysql.connector.connect(**self.config_mysql)
            cursor = conexion.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historial_ventas (
                    id_transaccion INT PRIMARY KEY,
                    producto VARCHAR(150) NOT NULL,
                    cantidad INT NOT NULL,
                    precio_unitario DECIMAL(12, 2) NOT NULL,
                    fecha_registro DATE NOT NULL,
                    correo_empleado VARCHAR(150) NOT NULL,
                    total_venta DECIMAL(14, 2) NOT NULL
                ) ENGINE=InnoDB
            """)

            registros = [
                (
                    int(fila.id_transaccion),
                    str(fila.producto),
                    int(fila.cantidad),
                    float(fila.precio_unitario),
                    str(fila.fecha_registro),
                    str(fila.correo_empleado),
                    float(fila.total_venta),
                )
                for fila in datos.itertuples(index=False)
            ]
            sql = """
                INSERT INTO historial_ventas (
                    id_transaccion, producto, cantidad, precio_unitario,
                    fecha_registro, correo_empleado, total_venta
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    producto = VALUES(producto),
                    cantidad = VALUES(cantidad),
                    precio_unitario = VALUES(precio_unitario),
                    fecha_registro = VALUES(fecha_registro),
                    correo_empleado = VALUES(correo_empleado),
                    total_venta = VALUES(total_venta)
            """
            if registros:
                cursor.executemany(sql, registros)
            conexion.commit()

            cursor.execute("SELECT COUNT(*) FROM historial_ventas")
            cantidad_en_mysql = cursor.fetchone()[0]
            print(f"[3/3] CARGA: {len(registros)} registros enviados a MySQL.")
            print(f"[3/3] CARGA: {cantidad_en_mysql} registros en historial_ventas.")
        except mysql.connector.Error as error:
            if conexion is not None and conexion.is_connected():
                conexion.rollback()
            raise RuntimeError(f"Fallo la carga en MySQL: {error}") from error
        finally:
            if cursor is not None:
                cursor.close()
            if conexion is not None and conexion.is_connected():
                conexion.close()

    def ejecutar(self):
        datos_originales = self.extraer()
        datos_limpios = self.transformar(datos_originales)
        self.cargar(datos_limpios)
        print("[OK] Proceso ETL terminado correctamente.")


if __name__ == "__main__":
    configuracion = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": getpass("Escribe tu contrasena de MySQL y presiona Enter: "),
        "database": "etl_almacen",
    }
    etl = ETLAlmacen(Path(__file__).parent / "transacciones_almacen.csv", configuracion)
    try:
        etl.ejecutar()
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"[ERROR] {error}")
        raise SystemExit(1) from error
