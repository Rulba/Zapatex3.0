from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from models import Stock
from extensions import db
from flask import request, jsonify, redirect, url_for, render_template
from transbank_config import tx


app = Flask(__name__, template_folder='templates')
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

    # Obtener sucursales con stock del producto
    disponibles = Stock.query.filter(
        Stock.producto == producto,
        Stock.cantidad > 0
    ).order_by(Stock.cantidad.desc()).all()

    total_disponible = sum([s.cantidad for s in disponibles])
    if total_disponible < cantidad:
        return jsonify({"error": "Stock insuficiente"}), 400

    # 👉 Paso 1: Buscar si hay alguna sucursal que pueda cubrir sola la cantidad
    for sucursal in disponibles:
        if sucursal.cantidad >= cantidad:
            sucursal.cantidad -= cantidad
            db.session.commit()
            print(f"[VENTA] Producto vendido desde {sucursal.sucursal}: {cantidad} unidades")
            return jsonify({"mensaje": "Venta desde una sola sucursal realizada con éxito"})

    # 👉 Paso 2: Repartir entre varias si ninguna sola alcanza
    restante = cantidad
    for s in disponibles:
        if restante == 0:
            break
        a_descontar = min(s.cantidad, restante)
        s.cantidad -= a_descontar
        restante -= a_descontar

    db.session.commit()
    print(f"[VENTA] Producto vendido (repartido): {producto} - Cantidad total: {cantidad}")
    return jsonify({"mensaje": "Venta repartida entre sucursales realizada con éxito"})



@app.route('/iniciar_pago', methods=['POST'])
def iniciar_pago():
    datos = request.json
    producto = datos.get('producto')
    cantidad = int(datos.get('cantidad', 1))

    # Simula cálculo del total (puedes hacerlo más real si quieres)
    monto = 1000 * cantidad

    # Aquí harías normalmente la llamada a Transbank, pero ahora solo simulas
    return jsonify({
        "url": "/resultado_pago_simulado",
        "token": f"token_simulado_{producto}_{cantidad}"
    })

@app.route('/resultado_pago_simulado', methods=['POST'])
def resultado_pago_simulado():
    producto = request.form.get('producto')
    cantidad = int(request.form.get('cantidad', 1))

    disponibles = Stock.query.filter(
        Stock.producto == producto,
        Stock.cantidad > 0
    ).order_by(Stock.cantidad.desc()).all()

    total_disponible = sum([s.cantidad for s in disponibles])
    if total_disponible < cantidad:
        return render_template('pago_fallido.html', detalle={"status": "FAILED"})

    restante = cantidad
    for s in disponibles:
        if restante == 0:
            break
        a_descontar = min(s.cantidad, restante)
        s.cantidad -= a_descontar
        restante -= a_descontar

    db.session.commit()

    return render_template('pago_exitoso.html', detalle={
        'amount': 1000 * cantidad,
        'buy_order': f'simulado-{producto}-{cantidad}',
        'authorization_code': 'SIM-123',
        'card_detail': {'card_number': '**** **** **** 1111'},
        'status': 'AUTHORIZED'
    })


#@app.route('/resultado_pago')
#def resultado_pago():
    token = request.args.get('token_ws')
    try:
        response = tx.commit(token)

        print("✅ Resultado pago:", response)

        if response['status'] == 'AUTHORIZED':
            return render_template('pago_exitoso.html', detalle=response)
        else:
            return render_template('pago_fallido.html', detalle=response)

    except Exception as e:
        print("❌ Error al procesar el resultado del pago:", e)
        return "Error al procesar el pago", 500


if __name__ == '__main__':
    app.run(debug=True)
