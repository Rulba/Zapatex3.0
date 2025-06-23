import base64
import os
import time
import grpc
import sys

# Importar db y modelo Stock para crear tablas
from extensions import db
from models import Stock

# Flask app context para crear tablas
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zapatex.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    print("Creando tablas en la base de datos...")
    db.create_all()
    print("Tablas creadas.")

# Agregar la ruta al módulo gRPC
grpc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'zapatex_grpc'))
sys.path.insert(0, grpc_path)

import productos_pb2
import productos_pb2_grpc

def cargar_imagen_base64(ruta_imagen):
    with open(ruta_imagen, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

ruta_imagenes = os.path.join(os.path.dirname(__file__), "static", "images")

productos_temp = {}

productos_crudos = [
    ("ZapatoX", "Sucursal 1", 31, 34990, "zapatox.png"),
    ("ZapatoX", "Sucursal 2", 0, 33990, "zapatox.png"),
    ("ZapatoX", "Sucursal 3", 100, 35990, "zapatoX.png"),
    ("ZapatoX", "Casa Matriz", 10, 34990, "zapatoX.png"),

    ("Zapatilla Y", "Sucursal 1", 5, 27990, "zapatillay.png"),
    ("Zapatilla Y", "Sucursal 2", 18, 28990, "zapatillaY.png"),
    ("Zapatilla Y", "Sucursal 3", 0, 26990, "zapatillaY.png"),
    ("Zapatilla Y", "Casa Matriz", 25, 29990, "zapatillaY.png"),

    ("BotínZ", "Sucursal 1", 50, 44990, "botinz.png"),
    ("BotínZ", "Sucursal 2", 5, 45990, "botinZ.png"),
    ("BotínZ", "Casa Matriz", 15, 43990, "botinZ.png"),

    ("Sandalia K", "Sucursal 3", 30, 19990, "sandaliaK.png"),
    ("Sandalia K", "Sucursal 1", 20, 20990, "sandaliaK.png"),

    ("Zapato Ejecutivo", "Casa Matriz", 12, 54990, "zapatoejecutivo.png")
]

for nombre, sucursal, cantidad, precio, imagen in productos_crudos:
    if nombre not in productos_temp:
        productos_temp[nombre] = {
            "nombre": nombre,
            "precio": precio,
            "imagen": imagen,
            "stock": []
        }
    productos_temp[nombre]["stock"].append((sucursal, cantidad))

with grpc.insecure_channel('localhost:50051') as channel:
    stub = productos_pb2_grpc.ProductoServiceStub(channel)

    for i, (nombre, info) in enumerate(productos_temp.items()):
        producto_id = int(time.time()) + i
        imagen_path = os.path.join(ruta_imagenes, info["imagen"])
        imagen_b64 = cargar_imagen_base64(imagen_path)

        stock_items = [
            productos_pb2.StockPorSucursal(sucursal=s, cantidad=c)
            for s, c in info["stock"]
        ]

        request = productos_pb2.ProductoRequest(
            id=producto_id,
            nombre=nombre,
            precio=info["precio"],
            imagen_base64=imagen_b64,
            stock=stock_items
        )

        response = stub.AgregarProducto(request)
        if response.exito:
            print(f"✅ Producto '{nombre}' agregado correctamente.")
        else:
            print(f"❌ Error agregando '{nombre}': {response.mensaje}")
