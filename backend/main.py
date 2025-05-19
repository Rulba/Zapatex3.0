from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from models import Stock
from extensions import db
from flask import request, jsonify, redirect, url_for, render_template
from transbank_config import tx


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zapatex.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/vender', methods=['POST'])
def vender():
    data = request.json
    sucursal = data['sucursal']
    cantidad = data['cantidad']

    stock = Stock.query.filter_by(sucursal=sucursal).first()
    if stock and stock.cantidad >= cantidad:
        stock.cantidad -= cantidad
        db.session.commit()
        return jsonify({'status': 'ok'})
    else:
        return jsonify({'status': 'error', 'message': 'No hay suficiente stock'}), 400
    
@app.route('/api/stock')
def get_stock():
    sucursales = []
    casa_matriz = None

    stocks = Stock.query.all()
    for s in stocks:
        info = {
            "producto": s.producto,  # ✅ Agrega esta línea
            "sucursal": s.sucursal,
            "cantidad": s.cantidad,
            "precio": s.precio
        }
        if s.sucursal.lower() == "casa matriz":
            casa_matriz = info
        else:
            sucursales.append(info)

    return jsonify({
        "sucursales": sucursales,
        "casa_matriz": casa_matriz
    })


@app.route('/api/usd')
def convertir_usd():
    clp = float(request.args.get('clp', 0))
    tasa = 900  # puedes cambiar esto por una API real después
    usd = round(clp / tasa, 2)
    return jsonify({"usd": usd})

@app.route('/venta', methods=['POST'])
def procesar_venta():
    data = request.get_json()
    producto = data.get('producto')
    cantidad = data.get('cantidad')

    if not producto or not cantidad:
        return jsonify({"error": "Faltan datos"}), 400

    disponibles = Stock.query.filter(
        Stock.producto == producto,
        Stock.cantidad > 0
    ).order_by(Stock.sucursal).all()

    stock_total = sum([s.cantidad for s in disponibles])
    if cantidad > stock_total:
        return jsonify({"error": "No hay suficiente stock disponible"}), 400

    restante = cantidad
    for stock in disponibles:
        if restante == 0:
            break
        usar = min(stock.cantidad, restante)
        stock.cantidad -= usar
        restante -= usar

    db.session.commit()
    return jsonify({"mensaje": "Venta procesada con éxito"})



@app.route('/iniciar_pago', methods=['POST'])
def iniciar_pago():
    datos = request.json
    producto = datos.get('producto')
    cantidad = datos.get('cantidad', 1)

    # Solo para demo, usa un monto fijo (puedes cambiarlo)
    monto = 1000 * cantidad

    # Identificadores únicos de prueba
    buy_order = f"pedido-{producto}-{cantidad}"
    session_id = "session1234"
    return_url = url_for('resultado_pago', _external=True)

    response = tx.create(buy_order, session_id, monto, return_url)
    url_webpay = response['url']
    token = response['token']

    return jsonify({'url': url_webpay, 'token': token})


@app.route('/resultado_pago')
def resultado_pago():
    token = request.args.get('token_ws')
    response = tx.commit(token)

    if response['status'] == 'AUTHORIZED':
        return render_template('pago_exitoso.html', detalle=response)
    else:
        return render_template('pago_fallido.html', detalle=response)


if __name__ == '__main__':
    app.run(debug=True)
