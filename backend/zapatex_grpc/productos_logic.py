import sqlite3
from typing import List, Dict, Tuple, Optional

DB_PATH = "zapatex.db"

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def agregar_producto(data: Dict) -> Tuple[bool, str]:
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO productos (id, nombre, precio, imagen_base64) VALUES (?, ?, ?, ?)",
            (data['id'], data['nombre'], data['precio'], data.get('imagen_base64', None))
        )

        # Insertar stock por sucursal
        for s in data['stock']:
            cursor.execute(
                "INSERT INTO stock (producto_id, sucursal, cantidad) VALUES (?, ?, ?)",
                (data['id'], s['sucursal'], s['cantidad'])
            )

        conn.commit()
        conn.close()
        return True, "Producto agregado"
    except sqlite3.IntegrityError as e:
        return False, f"Error: El producto con id {data['id']} ya existe."
    except Exception as e:
        return False, f"Error inesperado: {e}"

def obtener_producto(id: int) -> Optional[Dict]:
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM productos WHERE id = ?", (id,))
    producto_row = cursor.fetchone()

    if not producto_row:
        conn.close()
        return None

    cursor.execute("SELECT sucursal, cantidad FROM stock WHERE producto_id = ?", (id,))
    stock_rows = cursor.fetchall()
    stock = [{"sucursal": row["sucursal"], "cantidad": row["cantidad"]} for row in stock_rows]

    producto = {
        "id": producto_row["id"],
        "nombre": producto_row["nombre"],
        "precio": producto_row["precio"],
        "imagen_base64": producto_row["imagen_base64"],
        "stock": stock
    }
    conn.close()
    return producto

def listar_productos() -> List[Dict]:
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM productos")
    productos_rows = cursor.fetchall()

    productos = []
    for p in productos_rows:
        cursor.execute("SELECT sucursal, cantidad FROM stock WHERE producto_id = ?", (p["id"],))
        stock_rows = cursor.fetchall()
        stock = [{"sucursal": row["sucursal"], "cantidad": row["cantidad"]} for row in stock_rows]

        productos.append({
            "id": p["id"],
            "nombre": p["nombre"],
            "precio": p["precio"],
            "imagen_base64": p["imagen_base64"],
            "stock": stock
        })
    conn.close()
    return productos

def actualizar_stock(data: Dict) -> Tuple[bool, str]:
    try:
        conn = conectar()
        cursor = conn.cursor()

        # Verificamos que el producto exista
        cursor.execute("SELECT 1 FROM productos WHERE id = ?", (data['id'],))
        if not cursor.fetchone():
            conn.close()
            return False, "Producto no encontrado"

        # Actualizamos el stock: borramos el stock antiguo para ese producto y luego insertamos el nuevo
        cursor.execute("DELETE FROM stock WHERE producto_id = ?", (data['id'],))

        for s in data['stock']:
            cursor.execute(
                "INSERT INTO stock (producto_id, sucursal, cantidad) VALUES (?, ?, ?)",
                (data['id'], s['sucursal'], s['cantidad'])
            )

        conn.commit()
        conn.close()
        return True, "Stock actualizado correctamente"
    except Exception as e:
        return False, f"Error al actualizar stock: {e}"
