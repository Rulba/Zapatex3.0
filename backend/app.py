from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zapatex.db'
db = SQLAlchemy(app)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sucursal = db.Column(db.String(50))
    cantidad = db.Column(db.Integer)
    precio = db.Column(db.Float)

@app.route('/')
def index():
    stocks = Stock.query.all()
    return render_template('index.html', stocks=stocks)

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

if __name__ == '__main__':
    app.run(debug=True)
