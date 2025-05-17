from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from models import Stock


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zapatex.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


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


if __name__ == '__main__':
    app.run(debug=True)
