from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from models import Stock
from extensions import db
from transbank_config import tx
import requests
from datetime import datetime, timedelta

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
        # Valor fallback (revisar si es correcto)
        return 0.0011

def obtener_tasa_cambio_cached():
    ahora = datetime.utcnow()  # Mejor usar UTC
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

@app.route('/api/stock')
def get_stock():
    sucursales = []
    casa_matriz = None

    stocks = Stock.query.all()
    for s in stocks:
        info = {
            "producto": s.producto,
            "sucursal": s.sucursal,
            "cantidad": s.cantidad,
            "precio": s.precio
        }
        if s.sucursal.lower() == "casa matriz":
            casa_matriz = info
        else:
            sucursales.append(info)

    return jsonify({"sucursales": sucursales, "casa_matriz": casa_matriz})

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

    stock_producto = Stock.query.filter_by(producto=producto).first()
    if not stock_producto:
        return jsonify({"error": "Producto no encontrado"}), 404

    monto = stock_producto.precio * cantidad

    try:
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
        print(f"Error al iniciar pago Transbank: {e}")
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
            # Aquí podrías actualizar stock, enviar email, etc.
            return render_template('pago_exitoso.html', detalle=response)
        else:
            return render_template('pago_fallido.html', detalle=response)

    except Exception as e:
        print("❌ Error al procesar el resultado del pago:", e)
        return "Error al procesar el pago", 500


if __name__ == '__main__':
    app.run(debug=True)
