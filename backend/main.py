from flask import Flask, render_template, jsonify, request, Response, stream_with_context, url_for
from flask_sqlalchemy import SQLAlchemy
from models import Stock
from extensions import db
import queue
import time
import threading
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

clientes_sse = []

def generar_evento_stock_bajo():
    while True:
        time.sleep(5)
        try:
            options = [
                ('grpc.max_receive_message_length', 20 * 1024 * 1024),
                ('grpc.max_send_message_length', 20 * 1024 * 1024)
            ]
            with grpc.insecure_channel('localhost:50051', options=options) as channel:
                stub = productos_pb2_grpc.ProductoServiceStub(channel)
                respuesta = stub.ListarProductos(productos_pb2.Empty())

            alertas = []
            for producto in respuesta.productos:
                for s in producto.stock:
                    if s.cantidad < 10:
                        alertas.append({
                            "producto": producto.nombre,
                            "sucursal": s.sucursal,
                            "cantidad": s.cantidad
                        })

            if alertas:
                from json import dumps
                mensaje = f"data: {dumps(alertas)}\n\n"
                for cliente in clientes_sse:
                    try:
                        cliente.put(mensaje)
                    except:
                        pass

        except Exception as e:
            print("\u274c Error en hilo SSE:", e)

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

@app.route('/gestionar_productos')
def gestionar_productos():
    return render_template('gestion_productos.html')

@app.route('/api/agregar_producto', methods=['POST'])
def api_agregar_producto():
    data = request.get_json()
    try:
        nombre = data['nombre']
        precio = float(data['precio'])
        tipo = data['tipo']
        imagen_base64 = data['imagen_base64']
        stock_dict = data['stock']

        import base64
        nombre_archivo = f"{nombre.replace(' ', '_')}_{int(datetime.now().timestamp())}.png"
        ruta_relativa = os.path.join("static", "images", nombre_archivo)
        ruta_absoluta = os.path.join(os.path.dirname(__file__), ruta_relativa)
        os.makedirs(os.path.dirname(ruta_absoluta), exist_ok=True)
        with open(ruta_absoluta, "wb") as f:
            f.write(base64.b64decode(imagen_base64))

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
            ('grpc.max_receive_message_length', 20 * 1024 * 1024),
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
        print("\u274c Error al agregar producto vía Flask → gRPC:", e)
        return jsonify({"error": "Error interno al procesar el producto"}), 500

@app.route('/api/stock')
def get_stock():
    try:
        options = [
            ('grpc.max_receive_message_length', 20 * 1024 * 1024),
            ('grpc.max_send_message_length', 20 * 1024 * 1024)
        ]
        with grpc.insecure_channel('localhost:50051', options=options) as channel:
            stub = productos_pb2_grpc.ProductoServiceStub(channel)
            response = stub.ListarProductos(productos_pb2.Empty())

        sucursales = []
        casa_matriz = None

        for p in response.productos:
            for stock_item in p.stock:
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
        print("\u274c Ocurrió un error en /api/stock:")
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
    data = request.get_json()
    producto_nombre = data.get('producto')
    cantidad = data.get('cantidad')
    sucursal = data.get('sucursal')

    if not producto_nombre or not sucursal or not cantidad:
        return jsonify({"error": "Faltan datos: producto, sucursal o cantidad"}), 400

    try:
        cantidad = int(cantidad)
        if cantidad <= 0:
            return jsonify({"error": "Cantidad debe ser mayor a 0"}), 400
    except ValueError:
        return jsonify({"error": "Cantidad inválida"}), 400

    options = [
        ('grpc.max_receive_message_length', 20 * 1024 * 1024),
        ('grpc.max_send_message_length', 20 * 1024 * 1024)
    ]

    try:
        with grpc.insecure_channel('localhost:50051', options=options) as channel:
            stub = productos_pb2_grpc.ProductoServiceStub(channel)

            response = stub.ListarProductos(productos_pb2.Empty())
            producto = next((p for p in response.productos if p.nombre == producto_nombre), None)
            if not producto:
                return jsonify({"error": "Producto no encontrado"}), 404

            stock_sucursal = next((s for s in producto.stock if s.sucursal == sucursal), None)
            if not stock_sucursal:
                return jsonify({"error": f"No existe stock en sucursal {sucursal}"}), 404

            if stock_sucursal.cantidad < cantidad:
                return jsonify({"error": f"Stock insuficiente en {sucursal}. Solo quedan {stock_sucursal.cantidad} unidades."}), 400

            nuevo_stock = []
            for s in producto.stock:
                if s.sucursal == sucursal:
                    nueva_cantidad = s.cantidad - cantidad
                    if nueva_cantidad < 0:
                        return jsonify({"error": f"Stock insuficiente al intentar actualizar."}), 400
                    nuevo_stock.append(productos_pb2.StockPorSucursal(sucursal=s.sucursal, cantidad=nueva_cantidad))
                else:
                    nuevo_stock.append(productos_pb2.StockPorSucursal(sucursal=s.sucursal, cantidad=s.cantidad))

            request_actualizacion = productos_pb2.ProductoRequest(
                id=producto.id,
                nombre=producto.nombre,
                precio=producto.precio,
                imagen_base64=producto.imagen_base64,
                stock=nuevo_stock
            )

            respuesta = stub.ActualizarStock(request_actualizacion)

            if respuesta.exito:
                return jsonify({"mensaje": "Venta procesada y stock actualizado correctamente"})
            else:
                return jsonify({"error": respuesta.mensaje}), 500

    except grpc.RpcError as e:
        return jsonify({"error": f"Error en comunicación gRPC: {e}"}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {e}"}), 500

# Cambiado para usar URL local y token simulado
@app.route('/iniciar_pago', methods=['POST'])
def iniciar_pago():
    data = request.get_json()
    producto = data.get('producto')
    cantidad = data.get('cantidad')
    # Simulamos token o id de orden
    token = "token_simulado_123"

    url = url_for('resultado_pago')  # Genera "/resultado_pago"

    return jsonify({"url": url, "token": token})

# Endpoint que recibe POST del formulario y muestra resultado de pago
@app.route('/resultado_pago', methods=['GET', 'POST'])
def resultado_pago():
    if request.method == 'POST':
        token_ws = request.form.get('token_ws')
        producto = request.form.get('producto')
        cantidad = request.form.get('cantidad')

        detalle = {
            'buy_order': token_ws,
            'amount': cantidad,
            'authorization_code': '123456',  # simulado
            'card_detail': {'card_number': '**** **** **** 1234'}
        }

        return render_template('resultado_pago.html', detalle=detalle)
    else:
        return "Acceso directo no permitido", 403

@app.route('/api/stock/modificar', methods=['POST'])
def modificar_stock_producto():
    data = request.get_json()
    producto_nombre = data.get('producto')
    sucursal_nombre = data.get('sucursal')
    cantidad = data.get('cantidad')
    accion = data.get('accion')

    if not producto_nombre or not sucursal_nombre or accion not in ('agregar', 'quitar', 'eliminar'):
        return jsonify({'error': 'Faltan datos o acción inválida'}), 400

    try:
        cantidad = int(cantidad)
        if cantidad < 0:
            return jsonify({'error': 'Cantidad no puede ser negativa'}), 400
    except (TypeError, ValueError):
        return jsonify({'error': 'Cantidad inválida'}), 400

    options = [
        ('grpc.max_receive_message_length', 20 * 1024 * 1024),
        ('grpc.max_send_message_length', 20 * 1024 * 1024)
    ]

    try:
        with grpc.insecure_channel('localhost:50051', options=options) as channel:
            stub = productos_pb2_grpc.ProductoServiceStub(channel)

            response = stub.ListarProductos(productos_pb2.Empty())
            
            producto = next((p for p in response.productos if p.nombre == producto_nombre), None)
            if not producto:
                return jsonify({'error': 'Producto no encontrado'}), 404

            nuevo_stock = []
            sucursal_encontrada = False

            for s in producto.stock:
                if s.sucursal == sucursal_nombre:
                    sucursal_encontrada = True
                    if accion == 'eliminar':
                        continue
                    elif accion == 'agregar':
                        nueva_cantidad = s.cantidad + cantidad
                    elif accion == 'quitar':
                        if s.cantidad < cantidad:
                            return jsonify({'error': f'Stock insuficiente en {sucursal_nombre}'}), 400
                        nueva_cantidad = s.cantidad - cantidad
                    else:
                        nueva_cantidad = s.cantidad

                    nuevo_stock.append(productos_pb2.StockPorSucursal(
                        sucursal=s.sucursal,
                        cantidad=nueva_cantidad
                    ))
                else:
                    nuevo_stock.append(productos_pb2.StockPorSucursal(
                        sucursal=s.sucursal,
                        cantidad=s.cantidad
                    ))

            if not sucursal_encontrada and accion == 'agregar':
                nuevo_stock.append(productos_pb2.StockPorSucursal(
                    sucursal=sucursal_nombre,
                    cantidad=cantidad
                ))

            request_actualizacion = productos_pb2.ProductoRequest(
                id=producto.id,
                nombre=producto.nombre,
                precio=producto.precio,
                imagen_base64=producto.imagen_base64,
                stock=nuevo_stock
            )

            respuesta = stub.ActualizarStock(request_actualizacion)

            if respuesta.exito:
                return jsonify({
                    'mensaje': f'Acción "{accion}" realizada correctamente en {sucursal_nombre}',
                    'nuevo_stock': [{ "sucursal": s.sucursal, "cantidad": s.cantidad } for s in nuevo_stock]
                })
            else:
                return jsonify({'error': respuesta.mensaje}), 500

    except grpc.RpcError as rpc_e:
        return jsonify({'error': f'Error en comunicación gRPC: {rpc_e}'}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error interno: {e}'}), 500

threading.Thread(target=generar_evento_stock_bajo, daemon=True).start()

@app.route('/stream_stock_bajo')
def stream_stock_bajo():
    def event_stream():
        q = queue.Queue()
        clientes_sse.append(q)
        try:
            while True:
                mensaje = q.get()
                yield mensaje
        except GeneratorExit:
            clientes_sse.remove(q)

    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
