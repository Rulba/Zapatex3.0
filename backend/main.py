from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from models import Stock
from extensions import db
from transbank_config import tx
import requests
from datetime import datetime, timedelta
import grpc
import sys
import os

# Ruta a zapatex_grpc dentro de backend
grpc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'zapatex_grpc'))
print(f"Agregando ruta: {grpc_path}")
sys.path.insert(0, grpc_path)

import productos_pb2
import productos_pb2_grpc

app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zapatex.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Cache simple para evitar múltiples llamadas a la API de tasa de cambio
tasa_cache = {"valor": None, "ultima_actualizacion": None}

def obtener_tasa_cambio():
    url = "https://api.exchangerate.host/latest"
    params = {"base": "CLP", "symbols": "USD"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data["rates"]["USD"]
    except Exception as e:
        print(f"Error al obtener tasa de cambio: {e}")
        return 0.0011

def obtener_tasa_cambio_cached():
    ahora = datetime.utcnow()
    if (
        tasa_cache["valor"] is None or 
        (ahora - tasa_cache["ultima_actualizacion"]) > timedelta(minutes=30)
    ):
        tasa_cache["valor"] = obtener_tasa_cambio()
        tasa_cache["ultima_actualizacion"] = ahora
    return tasa_cache["valor"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/agregar_producto')
def agregar_producto():
    return render_template('agregar_producto.html')

@app.route('/api/agregar_producto', methods=['POST'])
def api_agregar_producto():
    data = request.get_json()

    try:
        nombre = data['nombre']
        precio = float(data['precio'])
        tipo = data['tipo']
        imagen_base64 = data['imagen_base64']
        stock_dict = data['stock']

        # Guardar imagen como archivo físico en static/images
        import base64

        nombre_archivo = f"{nombre.replace(' ', '_')}_{int(datetime.now().timestamp())}.png"
        ruta_relativa = os.path.join("static", "images", nombre_archivo)
        ruta_absoluta = os.path.join(os.path.dirname(__file__), ruta_relativa)

        os.makedirs(os.path.dirname(ruta_absoluta), exist_ok=True)
        with open(ruta_absoluta, "wb") as f:
            f.write(base64.b64decode(imagen_base64))

        # Preparar stock para gRPC
        stock_items = [
            productos_pb2.StockPorSucursal(sucursal=s, cantidad=c)
            for s, c in stock_dict.items()
        ]

        import time
        producto_id = int(time.time())

        request_grpc = productos_pb2.ProductoRequest(
            id=producto_id,
            nombre=nombre,
            precio=precio,
            imagen_base64=imagen_base64,
            stock=stock_items
        )

        options = [
            ('grpc.max_receive_message_length', 20 * 1024 * 1024),  # 20MB
            ('grpc.max_send_message_length', 20 * 1024 * 1024)
        ]
        with grpc.insecure_channel('localhost:50051', options=options) as channel:
            stub = productos_pb2_grpc.ProductoServiceStub(channel)
            response = stub.AgregarProducto(request_grpc)

        if response.exito:
            return jsonify({
                "mensaje": "Producto agregado correctamente",
                "producto_id": producto_id,
                "imagen_guardada_en": ruta_relativa
            }), 200
        else:
            return jsonify({"error": response.mensaje}), 400

    except Exception as e:
        print("❌ Error al agregar producto vía Flask → gRPC:", e)
        return jsonify({"error": "Error interno al procesar el producto"}), 500

@app.route('/api/stock')
def get_stock():
    try:
        options = [
            ('grpc.max_receive_message_length', 20 * 1024 * 1024),  # 20MB
            ('grpc.max_send_message_length', 20 * 1024 * 1024)
        ]
        with grpc.insecure_channel('localhost:50051', options=options) as channel:
            stub = productos_pb2_grpc.ProductoServiceStub(channel)
            response = stub.ListarProductos(productos_pb2.Empty())

        sucursales = []
        casa_matriz = None

        for p in response.productos:
            print(f"▶ Procesando producto: {p.nombre} (ID: {p.id})")
            print(f"   - Precio: {p.precio}")
            print(f"   - Stock total: {len(p.stock)} sucursales")

            for stock_item in p.stock:
                print(f"   - Sucursal: {stock_item.sucursal}, Cantidad: {stock_item.cantidad}")
                info = {
                    "producto": p.nombre,
                    "sucursal": stock_item.sucursal,
                    "cantidad": stock_item.cantidad,
                    "precio": p.precio,
                    "imagen_base64": p.imagen_base64 or ""
                }
                if stock_item.sucursal.lower() == "casa matriz":
                    casa_matriz = info
                else:
                    sucursales.append(info)

        return jsonify({"sucursales": sucursales, "casa_matriz": casa_matriz})

    except Exception as e:
        import traceback
        print("❌ Ocurrió un error en /api/stock:")
        traceback.print_exc()
        return jsonify({"error": "No se pudo obtener stock"}), 500

@app.route('/api/usd')
def convertir_usd():
    try:
        clp = float(request.args.get('clp', 0))
    except ValueError:
        return jsonify({"error": "Parámetro 'clp' inválido"}), 400

    tasa = obtener_tasa_cambio_cached()
    usd = round(clp * tasa, 2)
    return jsonify({"usd": usd})

@app.route('/venta', methods=['POST'])
def venta():
    data = request.json
    producto = data.get('producto')
    try:
        cantidad = int(data.get('cantidad'))
        if cantidad <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"error": "Cantidad inválida"}), 400

    disponibles = Stock.query.filter(
        Stock.producto == producto,
        Stock.cantidad > 0
    ).order_by(Stock.cantidad.desc()).all()

    total_disponible = sum(s.cantidad for s in disponibles)
    if total_disponible < cantidad:
        return jsonify({"error": "Stock insuficiente"}), 400

    try:
        # Intentar vender desde una sola sucursal
        for sucursal in disponibles:
            if sucursal.cantidad >= cantidad:
                sucursal.cantidad -= cantidad
                db.session.commit()
                return jsonify({"mensaje": "Venta desde una sola sucursal realizada con éxito"})

        # Si no es posible, repartir la venta
        restante = cantidad
        for s in disponibles:
            if restante == 0:
                break
            a_descontar = min(s.cantidad, restante)
            s.cantidad -= a_descontar
            restante -= a_descontar

        db.session.commit()
        return jsonify({"mensaje": "Venta repartida entre sucursales realizada con éxito"})

    except Exception as e:
        db.session.rollback()
        print(f"Error al procesar la venta: {e}")
        return jsonify({"error": "Error interno en el servidor"}), 500

@app.route('/iniciar_pago', methods=['POST'])
def iniciar_pago():
    datos = request.json
    producto = datos.get('producto')
    try:
        cantidad = int(datos.get('cantidad', 1))
        if cantidad <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({"error": "Cantidad inválida"}), 400

    # Obtener el producto desde gRPC
    try:
        options = [
            ('grpc.max_receive_message_length', 20 * 1024 * 1024),
            ('grpc.max_send_message_length', 20 * 1024 * 1024)
        ]
        with grpc.insecure_channel('localhost:50051', options=options) as channel:
            stub = productos_pb2_grpc.ProductoServiceStub(channel)
            response = stub.ListarProductos(productos_pb2.Empty())

        producto_grpc = next((p for p in response.productos if p.nombre == producto), None)

        if not producto_grpc:
            return jsonify({"error": "Producto no encontrado"}), 404

        monto = producto_grpc.precio * cantidad

        response = tx.create(
            buy_order=f"order_{producto}_{cantidad}_{int(datetime.utcnow().timestamp())}",
            session_id="session_123",
            amount=monto,
            return_url=request.host_url + "resultado_pago"
        )

        return jsonify({
            "url": response.url,
            "token": response.token
        })
    except Exception as e:
        print(f"❌ Error al iniciar pago Transbank:", e)
        return jsonify({"error": f"Error al iniciar pago: {e}"}), 500

@app.route('/resultado_pago', methods=['GET', 'POST'])
def resultado_pago():
    token = request.args.get('token_ws') or request.form.get('token_ws')
    if not token:
        return "Token no proporcionado", 400

    try:
        response = tx.commit(token)
        print("✅ Resultado pago:", response)

        if response.status == 'AUTHORIZED':
            return render_template('pago_exitoso.html', detalle=response)
        else:
            return render_template('pago_fallido.html', detalle=response)

    except Exception as e:
        print("❌ Error al procesar el resultado del pago:", e)
        return "Error al procesar el pago", 500

if __name__ == '__main__':
    app.run(debug=True)
