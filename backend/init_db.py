from main import app
from models import db, Stock

with app.app_context():
    db.drop_all()
    db.create_all()

    # Datos de prueba
    productos = [
        Stock(sucursal='Sucursal 1', producto='ZapatoX', cantidad=31, precio=333),
        Stock(sucursal='Sucursal 2', producto='ZapatoX', cantidad=23, precio=222),
        Stock(sucursal='Sucursal 3', producto='ZapatoX', cantidad=100, precio=1111),
        Stock(sucursal='Casa Matriz', producto='ZapatoX', cantidad=10, precio=999),
    ]

    db.session.add_all(productos)
    db.session.commit()

    print("📦 Base de datos inicializada con datos de prueba.")
