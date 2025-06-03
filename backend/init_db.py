from flask import Flask
from extensions import db
from models import Stock

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zapatex.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.drop_all()
    db.create_all()

    productos = [
        # ZapatoX en distintas sucursales
        Stock(sucursal='Sucursal 1', producto='ZapatoX', cantidad=31, precio=34990),
        Stock(sucursal='Sucursal 2', producto='ZapatoX', cantidad=0, precio=33990),
        Stock(sucursal='Sucursal 3', producto='ZapatoX', cantidad=100, precio=35990),
        Stock(sucursal='Casa Matriz', producto='ZapatoX', cantidad=10, precio=34990),

        # Zapatilla Y
        Stock(sucursal='Sucursal 1', producto='Zapatilla Y', cantidad=5, precio=27990),
        Stock(sucursal='Sucursal 2', producto='Zapatilla Y', cantidad=18, precio=28990),
        Stock(sucursal='Sucursal 3', producto='Zapatilla Y', cantidad=0, precio=26990),
        Stock(sucursal='Casa Matriz', producto='Zapatilla Y', cantidad=25, precio=29990),

        # BotínZ
        Stock(sucursal='Sucursal 1', producto='BotínZ', cantidad=50, precio=44990),
        Stock(sucursal='Sucursal 2', producto='BotínZ', cantidad=5, precio=45990),
        Stock(sucursal='Casa Matriz', producto='BotínZ', cantidad=15, precio=43990),

        # Sandalia K
        Stock(sucursal='Sucursal 3', producto='Sandalia K', cantidad=30, precio=19990),
        Stock(sucursal='Sucursal 1', producto='Sandalia K', cantidad=20, precio=20990),

        # Zapato Ejecutivo
        Stock(sucursal='Casa Matriz', producto='Zapato Ejecutivo', cantidad=12, precio=54990),
    ]

    db.session.add_all(productos)
    db.session.commit()

    print("📦 Base de datos inicializada con productos realistas.")
