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
def venta():
    data = request.json
    producto = data.get('producto')
    cantidad = int(data.get('cantidad'))

    # Buscar todas las sucursales con stock del producto
    disponibles = Stock.query.filter(
        Stock.producto == producto,
        Stock.cantidad > 0
    ).order_by(Stock.cantidad.desc()).all()

    total_disponible = sum([s.cantidad for s in disponibles])

    if total_disponible < cantidad:
        return jsonify({"error": "Stock insuficiente"}), 400

    restante = cantidad
    for s in disponibles:
        if restante == 0:
            break
        a_descontar = min(s.cantidad, restante)
        s.cantidad -= a_descontar
        restante -= a_descontar

    db.session.commit()
    print(f"[VENTA] Producto vendido: {producto} - Cantidad: {cantidad}")
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
